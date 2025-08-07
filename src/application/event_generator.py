import asyncio
import random
import time
from typing import List, Dict, Any
from datetime import datetime
import logging

from domain.entities.agent import Agent, AgentStatus
from domain.entities.call import Call, CallStatus
from domain.repositories.agent_repository import AgentRepository
from application.orchestrator import call_orchestrator
from config.settings import settings

logger = logging.getLogger(__name__)

class EventGenerator:
    """Generator for simulating call and agent events"""
    
    def __init__(self):
        self.agent_repository = AgentRepository()
        self.generated_calls: List[Call] = []
        self.generated_agents: List[Agent] = []
        self.is_running = False
        
    async def generate_test_agents(self, num_agents: int) -> List[Agent]:
        """Generate test agents with random distribution across agent types"""
        agents = []
        
        for i in range(num_agents):
            # Random distribution across agent types
            agent_type = random.choice(settings.agent_types)
            
            agent = Agent(
                name=f"Agent_{i+1:03d}",
                agent_type=agent_type,
                status=AgentStatus.AVAILABLE  # Start all agents as available
            )
            
            # Save agent to database
            saved_agent = await self.agent_repository.save(agent)
            agents.append(saved_agent)
            
            logger.info(f"Generated agent: {agent.name} ({agent.agent_type})")
        
        self.generated_agents = agents
        return agents
    
    async def generate_test_calls(self, num_calls: int) -> List[Call]:
        """Generate test calls with equal distribution across call types"""
        calls = []
        
        # Equal distribution across call types
        calls_per_type = num_calls // len(settings.call_types)
        remaining_calls = num_calls % len(settings.call_types)
        
        call_count = 0
        
        for i, call_type in enumerate(settings.call_types):
            # Calculate number of calls for this type
            type_call_count = calls_per_type
            if i < remaining_calls:
                type_call_count += 1
            
            for j in range(type_call_count):
                call = Call(
                    phone_number=f"+1555{call_count:06d}",
                    call_type=call_type,
                    status=CallStatus.PENDING
                )
                
                calls.append(call)
                call_count += 1
                
                logger.debug(f"Generated call: {call.phone_number} ({call.call_type})")
        
        # Shuffle calls to randomize order
        random.shuffle(calls)
        
        self.generated_calls = calls
        return calls
    
    async def simulate_call_arrivals(self, calls: List[Call], arrival_rate_per_second: float = 10, max_concurrent: int = 10) -> Dict[str, Any]:
        """
        Simulate call arrivals and assignment
        
        Args:
            calls: List of calls to process
            arrival_rate_per_second: Rate of call arrivals per second
            max_concurrent: Maximum concurrent call processing
            
        Returns:
            Dict with simulation results
        """
        start_time = time.time()
        results = {
            "total_calls": len(calls),
            "successful_assignments": 0,
            "failed_assignments": 0,
            "assignment_times": [],
            "saturated_calls": 0,
            "total_duration": 0,
            "calls_per_second": 0
        }
        
        self.is_running = True
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_call(call: Call):
            """Process a single call"""
            async with semaphore:
                if not self.is_running:
                    return
                
                try:
                    result = await call_orchestrator.assign_call(call)
                    
                    if result.success:
                        results["successful_assignments"] += 1
                        results["assignment_times"].append(result.assignment_time_ms)
                        logger.info(f"Call {call.id} assigned in {result.assignment_time_ms:.2f}ms")
                    else:
                        results["failed_assignments"] += 1
                        if "saturated" in result.message.lower():
                            results["saturated_calls"] += 1
                        logger.warning(f"Call {call.id} assignment failed: {result.message}")
                        
                except Exception as e:
                    results["failed_assignments"] += 1
                    logger.error(f"Error processing call {call.id}: {str(e)}")
        
        # Calculate inter-arrival time
        inter_arrival_time = 1.0 / arrival_rate_per_second if arrival_rate_per_second > 0 else 0
        
        # Create tasks for all calls
        tasks = []
        
        for i, call in enumerate(calls):
            if not self.is_running:
                break
            
            # Schedule call with arrival delay
            if i > 0 and inter_arrival_time > 0:
                await asyncio.sleep(inter_arrival_time)
            
            task = asyncio.create_task(process_call(call))
            tasks.append(task)
            
            logger.debug(f"Scheduled call {i+1}/{len(calls)}: {call.id}")
        
        # Wait for all calls to be processed
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate final metrics
        end_time = time.time()
        results["total_duration"] = end_time - start_time
        results["calls_per_second"] = len(calls) / results["total_duration"] if results["total_duration"] > 0 else 0
        
        logger.info(f"Simulation completed: {results['successful_assignments']}/{results['total_calls']} calls assigned")
        
        return results
    
    async def simulate_agent_login_logout(self, agents: List[Agent], login_probability: float = 0.8) -> None:
        """Simulate random agent login/logout during test"""
        
        async def agent_status_simulator():
            while self.is_running:
                try:
                    # Wait random interval
                    await asyncio.sleep(random.uniform(5, 15))
                    
                    if not self.is_running:
                        break
                    
                    # Pick random agent
                    agent = random.choice(agents)

                    if agent.status == AgentStatus.BUSY:
                        continue 
                    
                    # Determine new status based on current status
                    if agent.status == AgentStatus.AVAILABLE:
                        # Small chance to go to pause
                        if random.random() < 0.1:
                            agent.set_paused()
                            await self.agent_repository.save(agent)
                            logger.info(f"Agent {agent.name} set to PAUSED")
                    
                    elif agent.status == AgentStatus.PAUSED:
                        # High chance to go back to available
                        if random.random() < 0.7:
                            agent.set_available()
                            await self.agent_repository.save(agent)
                            logger.info(f"Agent {agent.name} set to AVAILABLE")
                    
                    elif agent.status == AgentStatus.OFFLINE:
                        # Medium chance to login
                        if random.random() < login_probability:
                            agent.set_available()
                            await self.agent_repository.save(agent)
                            logger.info(f"Agent {agent.name} logged in (AVAILABLE)")
                            
                except Exception as e:
                    logger.error(f"Error in agent status simulation: {str(e)}")
        
        # Start background task
        asyncio.create_task(agent_status_simulator())
    
    async def wait_for_all_calls_completion(self, timeout_seconds: float = 300) -> bool:
        """Wait for all active calls to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            status = await call_orchestrator.get_system_status()
            active_assignments = status.get("active_assignments", 0)
            
            if active_assignments == 0:
                logger.info("All calls completed")
                return True
            
            logger.info(f"Waiting for {active_assignments} active assignments to complete...")
            await asyncio.sleep(2)
        
        logger.warning(f"Timeout waiting for call completion after {timeout_seconds} seconds")
        return False
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        logger.info("Simulation stopped")
    
    async def cleanup_test_data(self):
        """Clean up generated test data"""
        try:
            # Remove generated agents
            for agent in self.generated_agents:
                await self.agent_repository.delete(agent.id)
            
            # Clear Redis data
            from infrastructure.cache.redis_client import redis_client
            await redis_client.clear_all_data()
            
            logger.info("Test data cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def generate_realistic_load(self, duration_seconds: int = 60, 
                                    calls_per_minute: int = 100) -> Dict[str, Any]:
        """
        Generate realistic load pattern for testing
        
        Args:
            duration_seconds: Duration of load test
            calls_per_minute: Target calls per minute
            
        Returns:
            Dict with load test results
        """
        calls_per_second = calls_per_minute / 60.0
        total_calls = int(duration_seconds * calls_per_second)
        
        logger.info(f"Starting realistic load test: {total_calls} calls over {duration_seconds} seconds")
        
        # Generate calls on-demand
        results = {
            "duration_seconds": duration_seconds,
            "target_calls_per_minute": calls_per_minute,
            "actual_calls_generated": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "assignment_times": [],
            "performance_metrics": {}
        }
        
        start_time = time.time()
        self.is_running = True
        
        async def generate_and_process_call():
            """Generate and immediately process a call"""
            call_type = random.choice(settings.call_types)
            call = Call(
                phone_number=f"+1555{int(time.time()*1000) % 1000000:06d}",
                call_type=call_type,
                status=CallStatus.PENDING
            )
            
            try:
                result = await call_orchestrator.assign_call(call)
                
                if result.success:
                    results["successful_assignments"] += 1
                    results["assignment_times"].append(result.assignment_time_ms)
                else:
                    results["failed_assignments"] += 1
                
                results["actual_calls_generated"] += 1
                
            except Exception as e:
                logger.error(f"Error processing generated call: {str(e)}")
                results["failed_assignments"] += 1
        
        # Generate calls at specified rate
        inter_arrival_time = 1.0 / calls_per_second
        next_call_time = start_time
        
        while time.time() - start_time < duration_seconds and self.is_running:
            current_time = time.time()
            
            if current_time >= next_call_time:
                # Generate call
                asyncio.create_task(generate_and_process_call())
                next_call_time += inter_arrival_time
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.01)
        
        # Calculate performance metrics
        if results["assignment_times"]:
            results["performance_metrics"] = {
                "avg_assignment_time_ms": sum(results["assignment_times"]) / len(results["assignment_times"]),
                "max_assignment_time_ms": max(results["assignment_times"]),
                "min_assignment_time_ms": min(results["assignment_times"]),
                "p95_assignment_time_ms": sorted(results["assignment_times"])[int(0.95 * len(results["assignment_times"]))],
                "success_rate": results["successful_assignments"] / (results["successful_assignments"] + results["failed_assignments"]),
                "calls_under_100ms": sum(1 for t in results["assignment_times"] if t <= 100),
                "performance_compliance": sum(1 for t in results["assignment_times"] if t <= 100) / len(results["assignment_times"])
            }
        
        logger.info(f"Load test completed: {results['actual_calls_generated']} calls processed")
        
        return results