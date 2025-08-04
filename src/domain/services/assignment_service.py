from typing import List, Optional
from datetime import datetime
import time

from ..entities.agent import Agent, AgentStatus
from ..entities.call import Call, CallStatus
from ..entities.assignment import Assignment, AssignmentStatus

class AssignmentStrategy:
    """Strategy interface for agent assignment"""
    
    def select_agent(self, available_agents: List[Agent], call: Call) -> Optional[Agent]:
        """Select the best agent for the call"""
        raise NotImplementedError

class LongestIdleTimeStrategy(AssignmentStrategy):
    """Assign to agent with longest idle time (as per requirements)"""
    
    def select_agent(self, available_agents: List[Agent], call: Call) -> Optional[Agent]:
        """Select agent with longest idle time"""
        if not available_agents:
            return None
        
        # Filter only available agents
        truly_available = [agent for agent in available_agents if agent.is_available()]
        
        if not truly_available:
            return None
        
        # Sort by idle time (longest first)
        sorted_agents = sorted(
            truly_available,
            key=lambda agent: agent.get_idle_time_seconds(),
            reverse=True
        )
        
        return sorted_agents[0]

class AssignmentService:
    """Domain service for call assignment logic"""
    
    def __init__(self, strategy: AssignmentStrategy = None):
        self.strategy = strategy or LongestIdleTimeStrategy()
    
    def assign_call(self, call: Call, available_agents: List[Agent]) -> tuple[Optional[Assignment], Optional[Agent], float]:
        """
        Assign a call to an available agent
        
        Returns:
            tuple: (Assignment or None, Selected Agent or None, assignment_time_ms)
        """
        start_time = time.time()
        
        # Validate call can be assigned
        if call.status != CallStatus.PENDING:
            assignment_time_ms = (time.time() - start_time) * 1000
            return None, None, assignment_time_ms
        
        # Select agent using strategy
        selected_agent = self.strategy.select_agent(available_agents, call)
        
        if selected_agent is None:
            assignment_time_ms = (time.time() - start_time) * 1000
            return None, None, assignment_time_ms
        
        # Create assignment
        assignment = Assignment(
            call_id=call.id,
            agent_id=selected_agent.id
        )
        
        # Update entities
        try:
            call.assign_to_agent(selected_agent.id)
            selected_agent.assign_call(call.id)
            
            assignment_time_ms = (time.time() - start_time) * 1000
            assignment.activate(assignment_time_ms, expected_duration_seconds=0)  # Will be set later
            
            return assignment, selected_agent, assignment_time_ms
            
        except ValueError as e:
            # Race condition or invalid state
            assignment_time_ms = (time.time() - start_time) * 1000
            return None, None, assignment_time_ms
    
    def validate_assignment_performance(self, assignment_time_ms: float, max_time_ms: float = 100) -> bool:
        """Validate that assignment meets performance requirements"""
        return assignment_time_ms <= max_time_ms
    
    def get_assignment_metrics(self, assignments: List[Assignment]) -> dict:
        """Calculate assignment performance metrics"""
        if not assignments:
            return {
                "total_assignments": 0,
                "avg_assignment_time_ms": 0,
                "max_assignment_time_ms": 0,
                "min_assignment_time_ms": 0,
                "assignments_under_100ms": 0,
                "performance_compliance_rate": 0
            }
        
        assignment_times = [a.assignment_time_ms for a in assignments if a.assignment_time_ms is not None]
        
        if not assignment_times:
            return {
                "total_assignments": len(assignments),
                "avg_assignment_time_ms": 0,
                "max_assignment_time_ms": 0,
                "min_assignment_time_ms": 0,
                "assignments_under_100ms": 0,
                "performance_compliance_rate": 0
            }
        
        under_100ms = sum(1 for t in assignment_times if t <= 100)
        
        return {
            "total_assignments": len(assignments),
            "avg_assignment_time_ms": sum(assignment_times) / len(assignment_times),
            "max_assignment_time_ms": max(assignment_times),
            "min_assignment_time_ms": min(assignment_times),
            "assignments_under_100ms": under_100ms,
            "performance_compliance_rate": under_100ms / len(assignment_times) if assignment_times else 0
        }