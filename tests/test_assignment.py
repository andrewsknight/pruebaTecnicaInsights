import pytest
import asyncio
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from domain.entities.agent import Agent, AgentStatus
from domain.entities.call import Call, CallStatus
from domain.entities.assignment import Assignment, AssignmentStatus
from domain.services.assignment_service import AssignmentService, LongestIdleTimeStrategy

class TestAssignmentService:
    """Test cases for assignment service"""
    
    @pytest.fixture
    def assignment_service(self):
        """Create assignment service instance"""
        return AssignmentService(LongestIdleTimeStrategy())
    
    @pytest.fixture
    def sample_agents(self):
        """Create sample agents for testing"""
        agents = []
        
        # Agent with recent call (short idle time)
        agent1 = Agent(
            id="agent-1",
            name="Agent 1",
            agent_type="agente_tipo_1",
            status=AgentStatus.AVAILABLE
        )
        agent1.last_call_end_time = datetime(2023, 1, 1, 12, 0, 0)  # Recent
        agents.append(agent1)
        
        # Agent with older call (longer idle time)
        agent2 = Agent(
            id="agent-2",
            name="Agent 2",
            agent_type="agente_tipo_1",
            status=AgentStatus.AVAILABLE
        )
        agent2.last_call_end_time = datetime(2023, 1, 1, 11, 0, 0)  # Older
        agents.append(agent2)
        
        # Agent with no previous calls (longest idle time)
        agent3 = Agent(
            id="agent-3",
            name="Agent 3",
            agent_type="agente_tipo_2",
            status=AgentStatus.AVAILABLE
        )
        # No last_call_end_time set (None = infinite idle time)
        agents.append(agent3)
        
        return agents
    
    @pytest.fixture
    def sample_call(self):
        """Create sample call for testing"""
        return Call(
            id="call-1",
            phone_number="+1555000001",
            call_type="llamada_tipo_1",
            status=CallStatus.PENDING
        )
    
    def test_longest_idle_time_strategy_selects_correct_agent(self, assignment_service, sample_agents, sample_call):
        """Test that longest idle time strategy selects agent with longest idle time"""
        strategy = assignment_service.strategy
        
        selected_agent = strategy.select_agent(sample_agents, sample_call)
        
        # Should select agent3 (no previous calls = infinite idle time)
        assert selected_agent is not None
        assert selected_agent.id == "agent-3"
        assert selected_agent.last_call_end_time is None
    
    def test_assignment_service_creates_assignment(self, assignment_service, sample_agents, sample_call):
        """Test that assignment service creates proper assignment"""
        assignment, selected_agent, assignment_time = assignment_service.assign_call(
            sample_call, sample_agents
        )
        
        # Should create assignment successfully
        assert assignment is not None
        assert selected_agent is not None
        assert assignment_time >= 0
        
        # Verify assignment properties
        assert assignment.call_id == sample_call.id
        assert assignment.agent_id == selected_agent.id
        assert assignment.status == AssignmentStatus.ACTIVE
        
        # Verify call is assigned
        assert sample_call.status == CallStatus.ASSIGNED
        assert sample_call.assigned_agent_id == selected_agent.id
        
        # Verify agent is busy
        assert selected_agent.status == AgentStatus.BUSY
        assert selected_agent.current_call_id == sample_call.id
    
    def test_assignment_fails_with_no_available_agents(self, assignment_service, sample_call):
        """Test assignment fails when no agents are available"""
        # Create busy agents
        busy_agents = [
            Agent(
                id="busy-agent-1",
                name="Busy Agent 1",
                agent_type="agente_tipo_1",
                status=AgentStatus.BUSY
            )
        ]
        
        assignment, selected_agent, assignment_time = assignment_service.assign_call(
            sample_call, busy_agents
        )
        
        # Should fail assignment
        assert assignment is None
        assert selected_agent is None
        assert assignment_time >= 0
        
        # Call should remain pending
        assert sample_call.status == CallStatus.PENDING
    
    def test_assignment_fails_with_already_assigned_call(self, assignment_service, sample_agents):
        """Test assignment fails when call is already assigned"""
        # Create already assigned call
        assigned_call = Call(
            id="assigned-call",
            phone_number="+1555000002",
            call_type="llamada_tipo_1",
            status=CallStatus.ASSIGNED
        )
        
        assignment, selected_agent, assignment_time = assignment_service.assign_call(
            assigned_call, sample_agents
        )
        
        # Should fail assignment
        assert assignment is None
        assert selected_agent is None
        assert assignment_time >= 0
    
    def test_performance_validation(self, assignment_service):
        """Test assignment performance validation"""
        # Test assignment under 100ms (should pass)
        assert assignment_service.validate_assignment_performance(50.0) == True
        assert assignment_service.validate_assignment_performance(100.0) == True
        
        # Test assignment over 100ms (should fail)
        assert assignment_service.validate_assignment_performance(150.0) == False
    
    def test_assignment_metrics_calculation(self, assignment_service):
        """Test assignment metrics calculation"""
        # Create sample assignments
        assignments = []
        
        for i in range(5):
            assignment = Assignment(
                id=f"assignment-{i}",
                call_id=f"call-{i}",
                agent_id=f"agent-{i}",
                status=AssignmentStatus.COMPLETED
            )
            assignment.assignment_time_ms = 50.0 + (i * 10)  # 50, 60, 70, 80, 90 ms
            assignments.append(assignment)
        
        metrics = assignment_service.get_assignment_metrics(assignments)
        
        # Verify metrics
        assert metrics["total_assignments"] == 5
        assert metrics["avg_assignment_time_ms"] == 70.0  # Average of 50,60,70,80,90
        assert metrics["max_assignment_time_ms"] == 90.0
        assert metrics["min_assignment_time_ms"] == 50.0
        assert metrics["assignments_under_100ms"] == 5  # All under 100ms
        assert metrics["performance_compliance_rate"] == 1.0  # 100% compliance
    
    def test_empty_metrics_calculation(self, assignment_service):
        """Test metrics calculation with empty assignments list"""
        metrics = assignment_service.get_assignment_metrics([])
        
        # Should handle empty list gracefully
        assert metrics["total_assignments"] == 0
        assert metrics["avg_assignment_time_ms"] == 0
        assert metrics["performance_compliance_rate"] == 0

class TestLongestIdleTimeStrategy:
    """Test cases for longest idle time strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance"""
        return LongestIdleTimeStrategy()
    
    def test_strategy_with_empty_agent_list(self, strategy):
        """Test strategy with empty agent list"""
        call = Call(phone_number="+1555000001", call_type="llamada_tipo_1")
        
        selected_agent = strategy.select_agent([], call)
        
        assert selected_agent is None
    
    def test_strategy_with_no_available_agents(self, strategy):
        """Test strategy when no agents are available"""
        busy_agents = [
            Agent(
                id="busy-1",
                name="Busy Agent 1",
                agent_type="agente_tipo_1",
                status=AgentStatus.BUSY
            ),
            Agent(
                id="paused-1",
                name="Paused Agent 1",
                agent_type="agente_tipo_1",
                status=AgentStatus.PAUSED
            )
        ]
        
        call = Call(phone_number="+1555000001", call_type="llamada_tipo_1")
        
        selected_agent = strategy.select_agent(busy_agents, call)
        
        assert selected_agent is None
    
    def test_strategy_priority_order(self, strategy):
        """Test that strategy correctly prioritizes agents by idle time"""
        # Create agents with different idle times
        now = datetime.utcnow()
        
        agents = [
            Agent(id="recent", name="Recent", agent_type="agente_tipo_1", status=AgentStatus.AVAILABLE),
            Agent(id="old", name="Old", agent_type="agente_tipo_1", status=AgentStatus.AVAILABLE),
            Agent(id="never", name="Never", agent_type="agente_tipo_1", status=AgentStatus.AVAILABLE)
        ]
        
        # Set different last call end times
        agents[0].last_call_end_time = now  # Most recent (shortest idle)
        agents[1].last_call_end_time = datetime(2023, 1, 1, 10, 0, 0)  # Older (longer idle)
        # agents[2] has no last_call_end_time (longest idle)
        
        call = Call(phone_number="+1555000001", call_type="llamada_tipo_1")
        
        selected_agent = strategy.select_agent(agents, call)
        
        # Should select agent with no previous calls (longest idle time)
        assert selected_agent is not None
        assert selected_agent.id == "never"

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])