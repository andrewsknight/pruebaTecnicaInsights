#!/usr/bin/env python3
"""
Call Assignment System - Main Entry Point

This is the main entry point for the call assignment system.
It provides a CLI interface to run different modes:
- API Server
- Test Runner
- Load Testing
- System Status

Usage:
    python src/main.py api                    # Start API server
    python src/main.py test                   # Run full test suite
    python src/main.py test --quick           # Run quick validation test
    python src/main.py test --stress 5       # Run 5-minute stress test
    python src/main.py load --duration 60    # Run load test for 60 seconds
    python src/main.py status                 # Show system status
    python src/main.py cleanup               # Clean up test data
"""

import asyncio
import click
import logging
import uvicorn
from datetime import datetime
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from application.test_runner import TestRunner
from application.event_generator import EventGenerator
from infrastructure.database.connection import db_connection
from infrastructure.cache.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def initialize_system():
    """Initialize database and Redis connections"""
    logger.info("Initializing Call Assignment System...")
    
    try:
        # Initialize database
        await db_connection.initialize()
        logger.info("✅ Database initialized")
        
        # Initialize Redis
        await redis_client.initialize()
        logger.info("✅ Redis initialized")
        
        logger.info("🚀 System initialization complete")
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {str(e)}")
        raise

async def shutdown_system():
    """Cleanup system resources"""
    logger.info("Shutting down Call Assignment System...")
    
    try:
        await db_connection.close()
        await redis_client.close()
        logger.info("✅ System shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

@click.group()
def cli():
    """Call Assignment System CLI"""
    pass

@cli.command()
@click.option('--host', default=settings.api_host, help='Host to bind to')
@click.option('--port', default=settings.api_port, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def api(host, port, reload):
    """Start the API server"""
    click.echo(f"🚀 Starting Call Assignment API on {host}:{port}")
    
    # Import here to avoid circular imports
    from infrastructure.api.rest_api import app
    
    uvicorn.run(
        "infrastructure.api.rest_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

@cli.command()
@click.option('--quick', is_flag=True, help='Run quick validation test')
@click.option('--stress', type=int, metavar='MINUTES', help='Run stress test for N minutes')
@click.option('--calls', type=int, help='Number of calls to generate')
@click.option('--agents', type=int, help='Number of agents to generate')
def test(quick, stress, calls, agents):
    """Run test suite"""
    asyncio.run(_run_test(quick, stress, calls, agents))

async def _run_test(quick, stress, calls, agents):
    """Internal test runner"""
    await initialize_system()
    
    try:
        test_runner = TestRunner()
        
        if quick:
            click.echo("🧪 Running quick validation test...")
            results = await test_runner.run_quick_validation_test()
            
        elif stress:
            click.echo(f"⚡ Running {stress}-minute stress test...")
            results = await test_runner.run_performance_stress_test(duration_minutes=stress)
            
        else:
            click.echo("🔬 Running full test suite...")
            results = await test_runner.run_full_test_suite(num_calls=calls, num_agents=agents)
        
        # Display results summary
        _display_test_results(results)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        click.echo(f"❌ Test failed: {str(e)}", err=True)
        
    finally:
        await shutdown_system()

@cli.command()
@click.option('--duration', default=60, help='Duration in seconds')
@click.option('--calls-per-minute', default=100, help='Target calls per minute')
@click.option('--agents', default=20, help='Number of agents')
def load(duration, calls_per_minute, agents):
    """Run load test"""
    asyncio.run(_run_load_test(duration, calls_per_minute, agents))

async def _run_load_test(duration, calls_per_minute, agents):
    """Internal load test runner"""
    await initialize_system()
    
    try:
        click.echo(f"⚡ Running load test: {calls_per_minute} calls/min for {duration} seconds")
        
        event_generator = EventGenerator()
        
        # Generate agents
        await event_generator.generate_test_agents(agents)
        
        # Run load test
        results = await event_generator.generate_realistic_load(
            duration_seconds=duration,
            calls_per_minute=calls_per_minute
        )
        
        # Display results
        click.echo("\n📊 Load Test Results:")
        click.echo(f"Duration: {results['duration_seconds']} seconds")
        click.echo(f"Calls Generated: {results['actual_calls_generated']}")
        click.echo(f"Successful Assignments: {results['successful_assignments']}")
        click.echo(f"Failed Assignments: {results['failed_assignments']}")
        
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            click.echo(f"Average Assignment Time: {metrics.get('avg_assignment_time_ms', 0):.2f}ms")
            click.echo(f"Success Rate: {metrics.get('success_rate', 0):.2%}")
            click.echo(f"Performance Compliance: {metrics.get('performance_compliance', 0):.2%}")
        
    except Exception as e:
        logger.error(f"Load test failed: {str(e)}")
        click.echo(f"❌ Load test failed: {str(e)}", err=True)
        
    finally:
        await shutdown_system()

@cli.command()
def status():
    """Show system status"""
    asyncio.run(_show_status())

async def _show_status():
    """Internal status display"""
    await initialize_system()
    
    try:
        from application.orchestrator import call_orchestrator
        
        status = await call_orchestrator.get_system_status()
        
        click.echo("📊 System Status:")
        click.echo(f"Timestamp: {status['timestamp']}")
        
        # Agents
        agents = status.get('agents', {})
        click.echo(f"\n👥 Agents:")
        click.echo(f"  Total: {agents.get('total', 0)}")
        click.echo(f"  Available: {agents.get('available', 0)}")
        click.echo(f"  Busy: {agents.get('busy', 0)}")
        click.echo(f"  Paused: {agents.get('paused', 0)}")
        click.echo(f"  Offline: {agents.get('offline', 0)}")
        
        # Active assignments
        click.echo(f"\n📞 Active Assignments: {status.get('active_assignments', 0)}")
        
        # Metrics
        metrics = status.get('metrics', {})
        if metrics:
            click.echo(f"\n📈 Metrics:")
            for key, value in metrics.items():
                click.echo(f"  {key}: {value}")
        
        # Health
        health = status.get('system_health', {})
        if health:
            click.echo(f"\n🏥 System Health:")
            for key, value in health.items():
                status_icon = "✅" if value else "❌"
                click.echo(f"  {status_icon} {key}: {value}")
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        click.echo(f"❌ Status check failed: {str(e)}", err=True)
        
    finally:
        await shutdown_system()

@cli.command()
def cleanup():
    """Clean up test data"""
    asyncio.run(_cleanup())

async def _cleanup():
    """Internal cleanup"""
    await initialize_system()
    
    try:
        event_generator = EventGenerator()
        await event_generator.cleanup_test_data()
        click.echo("✅ Test data cleanup completed")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        click.echo(f"❌ Cleanup failed: {str(e)}", err=True)
        
    finally:
        await shutdown_system()

@cli.command()
def demo():
    """Run a demonstration of the system"""
    asyncio.run(_run_demo())

async def _run_demo():
    """Run a demonstration"""
    await initialize_system()
    
    try:
        click.echo("🎭 Starting Call Assignment System Demo")
        click.echo("=" * 50)
        
        # Create some demo agents
        from domain.repositories.agent_repository import AgentRepository
        from domain.entities.agent import Agent, AgentStatus
        
        agent_repo = AgentRepository()
        demo_agents = []
        
        click.echo("👥 Creating demo agents...")
        for i, agent_type in enumerate(settings.agent_types[:2]):  # Create 2 types
            for j in range(2):  # 2 agents per type
                agent = Agent(
                    name=f"Demo Agent {i*2+j+1}",
                    agent_type=agent_type,
                    status=AgentStatus.AVAILABLE
                )
                saved_agent = await agent_repo.save(agent)
                demo_agents.append(saved_agent)
                click.echo(f"  ✅ Created {agent.name} ({agent.agent_type})")
        
        click.echo(f"\n📞 Simulating calls...")
        
        # Create and assign some demo calls
        from domain.entities.call import Call, CallStatus
        from application.orchestrator import call_orchestrator
        
        demo_calls = []
        for i, call_type in enumerate(settings.call_types[:2]):  # Test 2 call types
            call = Call(
                phone_number=f"+1555000{i:03d}",
                call_type=call_type,
                status=CallStatus.PENDING
            )
            demo_calls.append(call)
            
            click.echo(f"  📞 Assigning call {call.phone_number} ({call.call_type})...")
            
            result = await call_orchestrator.assign_call(call)
            
            if result.success:
                click.echo(f"    ✅ Assigned in {result.assignment_time_ms:.2f}ms to agent {result.agent.name}")
            else:
                click.echo(f"    ❌ Assignment failed: {result.message}")
        
        # Wait a bit and show status
        await asyncio.sleep(2)
        
        click.echo(f"\n📊 Current system status:")
        status = await call_orchestrator.get_system_status()
        
        agents = status.get('agents', {})
        click.echo(f"  Available agents: {agents.get('available', 0)}")
        click.echo(f"  Busy agents: {agents.get('busy', 0)}")
        click.echo(f"  Active assignments: {status.get('active_assignments', 0)}")
        
        click.echo(f"\n🎉 Demo completed! Check the logs for detailed information.")
        click.echo(f"💡 Try running 'python src/main.py test --quick' for a full test.")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        click.echo(f"❌ Demo failed: {str(e)}", err=True)
        
    finally:
        await shutdown_system()

def _display_test_results(results):
    """Display test results in a formatted way"""
    click.echo("\n" + "="*60)
    click.echo("📋 TEST RESULTS SUMMARY")
    click.echo("="*60)
    
    if "final_report" in results:
        report = results["final_report"]
        
        # Executive summary
        summary = report.get("executive_summary", {})
        outcome = summary.get("test_outcome", "UNKNOWN")
        outcome_icon = "✅" if outcome == "PASSED" else "❌"
        
        click.echo(f"\n{outcome_icon} Test Outcome: {outcome}")
        
        if "total_calls_processed" in summary:
            click.echo(f"📞 Total Calls Processed: {summary['total_calls_processed']}")
        
        if "assignment_success_rate" in summary:
            click.echo(f"📈 Assignment Success Rate: {summary['assignment_success_rate']:.2%}")
        
        if "performance_compliance" in summary:
            click.echo(f"⚡ Performance Compliance: {summary['performance_compliance']}")
        
        # Key findings
        findings = summary.get("key_findings", [])
        if findings:
            click.echo(f"\n🔍 Key Findings:")
            for finding in findings:
                click.echo(f"  {finding}")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            click.echo(f"\n💡 Recommendations:")
            for rec in recommendations:
                click.echo(f"  • {rec}")
    
    # Test metadata
    metadata = results.get("test_metadata", {})
    if "total_duration_seconds" in metadata:
        click.echo(f"\n⏱️  Total Test Duration: {metadata['total_duration_seconds']:.1f} seconds")
    
    click.echo("\n" + "="*60)

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        click.echo(f"❌ Application error: {str(e)}", err=True)
        sys.exit(1)