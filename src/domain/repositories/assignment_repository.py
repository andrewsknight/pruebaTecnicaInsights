from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from domain.entities.assignment import Assignment, AssignmentStatus
from infrastructure.database.models import AssignmentModel
from infrastructure.database.connection import db_connection

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
    
    async def delete(self, assignment_id: str) -> bool:
        """Delete assignment"""
        async with db_connection.get_session() as session:
            stmt = delete(AssignmentModel).where(AssignmentModel.id == assignment_id)
            result = await session.execute(stmt)
            
            return result.rowcount > 0