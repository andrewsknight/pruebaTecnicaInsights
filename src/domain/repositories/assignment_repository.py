from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..entities.assignment import Assignment, AssignmentStatus
from ...infrastructure.database.models import AssignmentModel
from ...infrastructure.database.connection import db_connection

class AssignmentRepositoryInterface(ABC):
    """Abstract interface for assignment repository"""
    
    @abstractmethod
    async def save(self, assignment: Assignment) -> Assignment:
        """Save or update an assignment"""
        pass
    
    @abstractmethod
    async def find_by_id(self, assignment_id: str) -> Optional[Assignment]:
        """Find assignment by ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Assignment]:
        """Find all assignments"""
        pass
    
    @abstractmethod
    async def find_by_call_id(self, call_id: str) -> Optional[Assignment]:
        """Find assignment by call ID"""
        pass
    
    @abstractmethod
    async def find_by_agent_id(self, agent_id: str) -> List[Assignment]:
        """Find assignments by agent ID"""
        pass
    
    @abstractmethod
    async def delete(self, assignment_id: str) -> bool:
        """Delete assignment"""
        pass

class AssignmentRepository(AssignmentRepositoryInterface):
    """PostgreSQL implementation of assignment repository"""
    
    def __init__(self):
        pass
    
    def _model_to_entity(self, model: AssignmentModel) -> Assignment:
        """Convert database model to domain entity"""
        return Assignment(
            id=model.id,
            call_id=model.call_id,
            agent_id=model.agent_id,
            status=AssignmentStatus(model.status),
            assignment_time_ms=model.assignment_time_ms,
            expected_duration_seconds=model.expected_duration_seconds,
            actual_duration_seconds=model.actual_duration_seconds,
            created_at=model.created_at,
            activated_at=model.activated_at,
            completed_at=model.completed_at
        )
    
    def _entity_to_model(self, assignment: Assignment, model: Optional[AssignmentModel] = None) -> AssignmentModel:
        """Convert domain entity to database model"""
        if model is None:
            model = AssignmentModel()
        
        model.id = assignment.id
        model.call_id = assignment.call_id
        model.agent_id = assignment.agent_id
        model.status = assignment.status.value
        model.assignment_time_ms = assignment.assignment_time_ms
        model.expected_duration_seconds = assignment.expected_duration_seconds
        model.actual_duration_seconds = assignment.actual_duration_seconds
        model.created_at = assignment.created_at
        model.activated_at = assignment.activated_at
        model.completed_at = assignment.completed_at
        
        return model
    
    async def save(self, assignment: Assignment) -> Assignment:
        """Save or update an assignment"""
        async with db_connection.get_session() as session:
            # Check if assignment exists
            stmt = select(AssignmentModel).where(AssignmentModel.id == assignment.id)
            result = await session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            if existing_model:
                # Update existing
                model = self._entity_to_model(assignment, existing_model)
            else:
                # Create new
                model = self._entity_to_model(assignment)
                session.add(model)
            
            await session.flush()
            
            return self._model_to_entity(model)
    
    async def find_by_id(self, assignment_id: str) -> Optional[Assignment]:
        """Find assignment by ID"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(AssignmentModel.id == assignment_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            
            return None
    
    async def find_all(self) -> List[Assignment]:
        """Find all assignments"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).order_by(AssignmentModel.created_at.desc())
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
    
    async def find_by_call_id(self, call_id: str) -> Optional[Assignment]:
        """Find assignment by call ID"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(AssignmentModel.call_id == call_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            
            return None
    
    async def find_by_agent_id(self, agent_id: str) -> List[Assignment]:
        """Find assignments by agent ID"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(
                AssignmentModel.agent_id == agent_id
            ).order_by(AssignmentModel.created_at.desc())
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
    
    async def find_active_assignments(self) -> List[Assignment]:
        """Find all active assignments"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(
                AssignmentModel.status == AssignmentStatus.ACTIVE.value
            ).order_by(AssignmentModel.activated_at.desc())
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
    
    async def find_completed_assignments(self, 
                                       start_date: datetime = None, 
                                       end_date: datetime = None) -> List[Assignment]:
        """Find completed assignments within date range"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(
                AssignmentModel.status == AssignmentStatus.COMPLETED.value
            )
            
            if start_date:
                stmt = stmt.where(AssignmentModel.completed_at >= start_date)
            
            if end_date:
                stmt = stmt.where(AssignmentModel.completed_at <= end_date)
            
            stmt = stmt.order_by(AssignmentModel.completed_at.desc())
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
    
    async def delete(self, assignment_id: str) -> bool:
        """Delete assignment"""
        async with db_connection.get_session() as session:
            stmt = delete(AssignmentModel).where(AssignmentModel.id == assignment_id)
            result = await session.execute(stmt)
            
            return result.rowcount > 0
    
    async def get_assignment_statistics(self, 
                                      start_date: datetime = None, 
                                      end_date: datetime = None) -> Dict[str, Any]:
        """Get assignment statistics"""
        async with db_connection.get_session() as session:
            
            # Base query
            base_stmt = select(AssignmentModel)
            
            if start_date:
                base_stmt = base_stmt.where(AssignmentModel.created_at >= start_date)
            
            if end_date:
                base_stmt = base_stmt.where(AssignmentModel.created_at <= end_date)
            
            # Get all assignments in range
            result = await session.execute(base_stmt)
            assignments = [self._model_to_entity(model) for model in result.scalars().all()]
            
            if not assignments:
                return {
                    "total_assignments": 0,
                    "by_status": {},
                    "performance_metrics": {},
                    "duration_statistics": {}
                }
            
            # Calculate statistics
            stats = {
                "total_assignments": len(assignments),
                "by_status": {},
                "performance_metrics": {},
                "duration_statistics": {}
            }
            
            # Count by status
            for status in AssignmentStatus:
                count = sum(1 for a in assignments if a.status == status)
                stats["by_status"][status.value] = count
            
            # Performance metrics
            assignment_times = [a.assignment_time_ms for a in assignments if a.assignment_time_ms is not None]
            
            if assignment_times:
                stats["performance_metrics"] = {
                    "avg_assignment_time_ms": sum(assignment_times) / len(assignment_times),
                    "max_assignment_time_ms": max(assignment_times),
                    "min_assignment_time_ms": min(assignment_times),
                    "assignments_under_100ms": sum(1 for t in assignment_times if t <= 100),
                    "performance_compliance_rate": sum(1 for t in assignment_times if t <= 100) / len(assignment_times)
                }
            
            # Duration statistics
            completed_assignments = [a for a in assignments if a.status == AssignmentStatus.COMPLETED]
            
            if completed_assignments:
                actual_durations = [a.actual_duration_seconds for a in completed_assignments if a.actual_duration_seconds is not None]
                expected_durations = [a.expected_duration_seconds for a in completed_assignments if a.expected_duration_seconds is not None]
                
                if actual_durations:
                    stats["duration_statistics"] = {
                        "avg_actual_duration_seconds": sum(actual_durations) / len(actual_durations),
                        "max_actual_duration_seconds": max(actual_durations),
                        "min_actual_duration_seconds": min(actual_durations)
                    }
                
                if expected_durations and actual_durations and len(expected_durations) == len(actual_durations):
                    duration_variances = [abs(actual - expected) for actual, expected in zip(actual_durations, expected_durations)]
                    stats["duration_statistics"]["avg_duration_variance_seconds"] = sum(duration_variances) / len(duration_variances)
                    stats["duration_statistics"]["max_duration_variance_seconds"] = max(duration_variances)
            
            return stats
    
    async def find_assignments_by_performance(self, 
                                            min_assignment_time_ms: float = None,
                                            max_assignment_time_ms: float = None) -> List[Assignment]:
        """Find assignments filtered by performance criteria"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel)
            
            if min_assignment_time_ms is not None:
                stmt = stmt.where(AssignmentModel.assignment_time_ms >= min_assignment_time_ms)
            
            if max_assignment_time_ms is not None:
                stmt = stmt.where(AssignmentModel.assignment_time_ms <= max_assignment_time_ms)
            
            stmt = stmt.order_by(AssignmentModel.assignment_time_ms.asc())
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
    
    async def count_by_status(self, status: AssignmentStatus) -> int:
        """Count assignments by status"""
        async with db_connection.get_session() as session:
            stmt = select(AssignmentModel).where(AssignmentModel.status == status.value)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return len(models)
    
    async def get_agent_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get performance summary for a specific agent"""
        assignments = await self.find_by_agent_id(agent_id)
        
        if not assignments:
            return {
                "agent_id": agent_id,
                "total_assignments": 0,
                "completed_assignments": 0,
                "avg_assignment_time_ms": 0,
                "avg_call_duration_seconds": 0
            }
        
        completed = [a for a in assignments if a.status == AssignmentStatus.COMPLETED]
        assignment_times = [a.assignment_time_ms for a in assignments if a.assignment_time_ms is not None]
        call_durations = [a.actual_duration_seconds for a in completed if a.actual_duration_seconds is not None]
        
        return {
            "agent_id": agent_id,
            "total_assignments": len(assignments),
            "completed_assignments": len(completed),
            "avg_assignment_time_ms": sum(assignment_times) / len(assignment_times) if assignment_times else 0,
            "avg_call_duration_seconds": sum(call_durations) / len(call_durations) if call_durations else 0,
            "performance_compliance_rate": sum(1 for t in assignment_times if t <= 100) / len(assignment_times) if assignment_times else 0
        }