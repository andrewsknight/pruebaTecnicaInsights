import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..domain.entities.agent import Agent, AgentStatus
from ..domain.entities.call import Call, CallStatus, QualificationResult
from ..domain.entities.assignment import Assignment, AssignmentStatus
from ..domain.services.assignment_service import AssignmentService
from ..domain.services.qualification_service import QualificationService
from ..domain.repositories.agent_repository import AgentRepository
from ..infrastructure.cache.redis_client import redis_client
from ..infrastructure.api.webhook_client import WebhookClient
from ..config.settings import settings

logger = logging.getLogger(__name__)

class AssignmentResult:
    """Result of an assignment attempt"""
    
    def __init__(self, success: bool, assignment: Optional[Assignment] = None, 
                 agent: Optional[Agent] = None, message: str = "", 
                 assignment_time_ms: float = 0):
        self.success = success
        self.assignment = assignment
        self.agent = agent
        self.message = message
        self.assignment_time_ms = assignment_time_ms

class CallOrchestrator:
    """Main orchestrator for call assignment and lifecycle management"""
    
    def __init__(self):
        self.assignment_service = AssignmentService()
        self.qualification_service = QualificationService(settings.conversion_matrix)
        self.agent_repository = AgentRepository()
        self.webhook_client = WebhookClient()
        self.active_assignments: Dict[str, Assignment] = {}  # call_id -> assignment
        self.call_timers: Dict[str, asyncio.Task] = {}  # call_id -> timer task
        
    async def assign_call(self, call: Call) -> AssignmentResult:
        """
        Assign a call to an available agent
        
        Args:
            call: Call to assign
            
        Returns:
            AssignmentResult with assignment details
        """
        start_time = time.time()
        
        try:
            # Update call status in Redis
            await redis_client.set_call_status(call)
            
            # Try to acquire assignment lock to prevent race conditions
            if not await redis_client.create_assignment_lock(call.id):
                assignment_time_ms = (time.time() - start_time) * 1000
                return AssignmentResult(
                    success=False,
                    message="Race condition detected - call is being processed",
                    assignment_time_ms=assignment_time_ms
                )
            
            try:
                # Get available agents
                available_agents = await self.agent_repository.find_available()
                
                if not available_agents:
                    assignment_time_ms = (time.time() - start_time) * 1000
                    await self._handle_saturation(call, assignment_time_ms)
                    return AssignmentResult(
                        success=False,
                        message="No agents available - system saturated",
                        assignment_time_ms=assignment_time_ms
                    )
                
                # Perform assignment using domain service
                assignment, selected_agent, assignment_time_ms = self.assignment_service.assign_call(
                    call, available_agents
                )
                
                if not assignment or not selected_agent:
                    return AssignmentResult(
                        success=False,
                        message="Assignment failed - agent selection error",
                        assignment_time_ms=assignment_time_ms
                    )
                
                # Validate performance requirement
                if not self.assignment_service.validate_assignment_performance(assignment_time_ms):
                    logger.warning(f"Assignment time {assignment_time_ms}ms exceeds 100ms limit")
                
                # Generate call duration
                expected_duration = self.qualification_service.generate_duration(
                    settings.call_duration_mean,
                    settings.call_duration_std
                )
                
                assignment.expected_duration_seconds = expected_duration
                
                # Store active assignment
                self.active_assignments[call.id] = assignment
                
                # Update entities in Redis
                await redis_client.set_call_status(call)
                await redis_client.set_agent_status(selected_agent)
                await redis_client.remove_pending_call(call.id)
                
                # Schedule call completion
                await self._schedule_call_completion(call, selected_agent, assignment, expected_duration)
                
                # Notify external system
                await self._notify_assignment(assignment, selected_agent, call)
                
                # Update metrics
                await redis_client.increment_metric("calls_assigned")
                await redis_client.set_metric("last_assignment_time_ms", assignment_time_ms)
                
                logger.info(f"Call {call.id} assigned to agent {selected_agent.id} in {assignment_time_ms:.2f}ms")
                
                return AssignmentResult(
                    success=True,
                    assignment=assignment,
                    agent=selected_agent,
                    message="Assignment successful",
                    assignment_time_ms=assignment_time_ms
                )
                
            finally:
                # Always release the lock
                await redis_client.release_assignment_lock(call.id)
                
        except Exception as e:
            assignment_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error assigning call {call.id}: {str(e)}")
            await redis_client.increment_metric("assignment_errors")
            
            return AssignmentResult(
                success=False,
                message=f"Assignment error: {str(e)}",
                assignment_time_ms=assignment_time_ms
            )
    
    async def _schedule_call_completion(self, call: Call, agent: Agent, 
                                      assignment: Assignment, duration_seconds: float):
        """Schedule automatic call completion after duration"""
        
        async def complete_call_after_delay():
            try:
                await asyncio.sleep(duration_seconds)
                await self._complete_call(call.id, agent.id, assignment.id, duration_seconds)
            except asyncio.CancelledError:
                logger.info(f"Call completion timer cancelled for call {call.id}")
            except Exception as e:
                logger.error(f"Error completing call {call.id}: {str(e)}")
        
        # Store timer task
        timer_task = asyncio.create_task(complete_call_after_delay())
        self.call_timers[call.id] = timer_task
    
    async def _complete_call(self, call_id: str, agent_id: str, assignment_id: str, actual_duration: float):
        """Complete a call and perform qualification"""
        try:
            # Get entities
            agent = await self.agent_repository.find_by_id(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found for call completion")
                return
            
            # Get call from Redis
            call_data = await redis_client.get_call_status(call_id)
            if not call_data:
                logger.error(f"Call {call_id} not found for completion")
                return
            
            # Recreate call entity
            call = Call(
                id=call_data["id"],
                phone_number=call_data["phone_number"],
                call_type=call_data["call_type"],
                status=CallStatus(call_data["status"]),
                assigned_agent_id=call_data["assigned_agent_id"] if call_data["assigned_agent_id"] else None,
                qualification_result=QualificationResult(call_data["qualification_result"]),
                created_at=datetime.fromisoformat(call_data["created_at"]),
                assigned_at=datetime.fromisoformat(call_data["assigned_at"]) if call_data["assigned_at"] else None
            )
            
            # Perform qualification
            qualification = self.qualification_service.qualify_call(agent.agent_type, call.call_type)
            
            # Update entities
            call.complete_call(actual_duration, qualification)
            agent.complete_call()
            
            # Update assignment
            if call_id in self.active_assignments:
                assignment = self.active_assignments[call_id]
                assignment.complete(actual_duration)
                del self.active_assignments[call_id]
            
            # Update Redis
            await redis_client.set_call_status(call)
            await redis_client.set_agent_status(agent)
            
            # Clean up timer
            if call_id in self.call_timers:
                del self.call_timers[call_id]
            
            # Notify external systems
            await self._notify_call_completion(call, agent, qualification)
            
            # Update metrics
            await redis_client.increment_metric("calls_completed")
            await redis_client.increment_metric(f"calls_{qualification.value.lower()}")
            await redis_client.set_metric("last_call_duration", actual_duration)
            
            logger.info(f"Call {call_id} completed: {qualification.value}, duration: {actual_duration:.1f}s")
            
        except Exception as e:
            logger.error(f"Error completing call {call_id}: {str(e)}")
            await redis_client.increment_metric("completion_errors")
    
    async def _handle_saturation(self, call: Call, assignment_time_ms: float):
        """Handle system saturation (no available agents)"""
        # Update call status
        call.status = CallStatus.FAILED
        await redis_client.set_call_status(call)
        
        # Notify external system
        await self.webhook_client.notify_saturation(call, assignment_time_ms)
        
        # Update metrics
        await redis_client.increment_metric("calls_saturated")
        
        logger.warning(f"Call {call.id} failed due to saturation")
    
    async def _notify_assignment(self, assignment: Assignment, agent: Agent, call: Call):
        """Notify external system of assignment"""
        try:
            await self.webhook_client.notify_assignment(assignment, agent, call)
        except Exception as e:
            logger.error(f"Failed to notify assignment for call {call.id}: {str(e)}")
    
    async def _notify_call_completion(self, call: Call, agent: Agent, qualification: QualificationResult):
        """Notify external system of call completion"""
        try:
            await self.webhook_client.notify_completion(call, agent, qualification)
        except Exception as e:
            logger.error(f"Failed to notify completion for call {call.id}: {str(e)}")
    
    async def cancel_call(self, call_id: str) -> bool:
        """Cancel a call (abandon scenario)"""
        try:
            # Cancel timer if exists
            if call_id in self.call_timers:
                self.call_timers[call_id].cancel()
                del self.call_timers[call_id]
            
            # Update call status
            call_data = await redis_client.get_call_status(call_id)
            if call_data:
                call = Call(
                    id=call_data["id"],
                    phone_number=call_data["phone_number"],
                    call_type=call_data["call_type"],
                    status=CallStatus(call_data["status"])
                )
                call.abandon_call()
                await redis_client.set_call_status(call)
            
            # Free agent if assigned
            if call_id in self.active_assignments:
                assignment = self.active_assignments[call_id]
                agent = await self.agent_repository.find_by_id(assignment.agent_id)
                if agent:
                    agent.complete_call()  # Make agent available again
                    await redis_client.set_agent_status(agent)
                
                del self.active_assignments[call_id]
            
            await redis_client.increment_metric("calls_abandoned")
            logger.info(f"Call {call_id} cancelled/abandoned")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling call {call_id}: {str(e)}")
            return False
    
    async def get_system_status(self) -> Dict:
        """Get current system status"""
        try:
            # Get metrics from Redis
            metrics = await redis_client.get_all_metrics()
            
            # Get agent counts
            all_agents = await self.agent_repository.find_all()
            available_agents = await self.agent_repository.find_available()
            
            agent_counts = {
                "total": len(all_agents),
                "available": len(available_agents),
                "busy": len([a for a in all_agents if a.status == AgentStatus.BUSY]),
                "paused": len([a for a in all_agents if a.status == AgentStatus.PAUSED]),
                "offline": len([a for a in all_agents if a.status == AgentStatus.OFFLINE])
            }
            
            # Active assignments
            active_count = len(self.active_assignments)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": agent_counts,
                "active_assignments": active_count,
                "metrics": metrics,
                "system_health": {
                    "redis_connected": await redis_client.health_check(),
                    "performance_target_met": metrics.get("last_assignment_time_ms", 0) <= 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}

# Global orchestrator instance
call_orchestrator = CallOrchestrator()