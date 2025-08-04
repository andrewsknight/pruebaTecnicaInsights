from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from domain.entities.call import Call, CallStatus, QualificationResult
from infrastructure.database.models import CallModel
from infrastructure.database.connection import db_connection
from infrastructure.cache.redis_client import redis_client

class CallRepositoryInterface(ABC):
    """Abstract interface for call repository"""
    
    @abstractmethod
    async def save(self, call: Call) -> Call:
        """Save or update a call"""
        pass
    
    @abstractmethod
    async def find_by_id(self, call_id: str) -> Optional[Call]:
        """Find call by ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Call]:
        """Find all calls"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: CallStatus) -> List[Call]:
        """Find calls by status"""
        pass
    
    @abstractmethod
    async def delete(self, call_id: str) -> bool:
        """Delete call"""
        pass

class CallRepository(CallRepositoryInterface):
    """PostgreSQL + Redis implementation of call repository"""
    
    def __init__(self):
        pass
    
    def _model_to_entity(self, model: CallModel) -> Call:
        """Convert database model to domain entity"""
        return Call(
            id=model.id,
            phone_number=model.phone_number,
            call_type=model.call_type,
            status=CallStatus(model.status),
            assigned_agent_id=model.assigned_agent_id,
            qualification_result=QualificationResult(model.qualification_result),
            created_at=model.created_at,
            assigned_at=model.assigned_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            duration_seconds=model.duration_seconds
        )
    
    def _entity_to_model(self, call: Call, model: Optional[CallModel] = None) -> CallModel:
        """Convert domain entity to database model"""
        if model is None:
            model = CallModel()
        
        model.id = call.id
        model.phone_number = call.phone_number
        model.call_type = call.call_type
        model.status = call.status.value
        model.assigned_agent_id = call.assigned_agent_id
        model.qualification_result = call.qualification_result.value
        model.created_at = call.created_at
        model.assigned_at = call.assigned_at
        model.started_at = call.started_at
        model.completed_at = call.completed_at
        model.duration_seconds = call.duration_seconds
        
        return model
    
    async def save(self, call: Call) -> Call:
        """Save or update a call"""
        async with db_connection.get_session() as session:
            # Check if call exists
            stmt = select(CallModel).where(CallModel.id == call.id)
            result = await session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            if existing_model:
                # Update existing
                model = self._entity_to_model(call, existing_model)
            else:
                # Create new
                model = self._entity_to_model(call)
                session.add(model)
            
            await session.flush()
            
            # Update Redis cache
            await redis_client.set_call_status(call)
            
            return self._model_to_entity(model)
    
    async def find_by_id(self, call_id: str) -> Optional[Call]:
        """Find call by ID"""
        # Try Redis first for real-time data
        redis_data = await redis_client.get_call_status(call_id)
        if redis_data:
            return Call(
                id=redis_data["id"],
                phone_number=redis_data["phone_number"],
                call_type=redis_data["call_type"],
                status=CallStatus(redis_data["status"]),
                assigned_agent_id=redis_data["assigned_agent_id"] if redis_data["assigned_agent_id"] else None,
                qualification_result=QualificationResult(redis_data["qualification_result"]),
                created_at=datetime.fromisoformat(redis_data["created_at"]),
                assigned_at=datetime.fromisoformat(redis_data["assigned_at"]) if redis_data["assigned_at"] else None,
                completed_at=datetime.fromisoformat(redis_data["completed_at"]) if redis_data["completed_at"] else None
            )
        
        # Fallback to database
        async with db_connection.get_session() as session:
            stmt = select(CallModel).where(CallModel.id == call_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                call = self._model_to_entity(model)
                # Update Redis cache
                await redis_client.set_call_status(call)
                return call
            
            return None
    
    async def find_all(self) -> List[Call]:
        """Find all calls"""
        async with db_connection.get_session() as session:
            stmt = select(CallModel).order_by(CallModel.created_at.desc())
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            calls = [self._model_to_entity(model) for model in models]
            
            # Update Redis cache for recent calls
            for call in calls[:100]:  # Cache only recent 100 calls
                await redis_client.set_call_status(call)
            
            return calls
    
    async def find_by_status(self, status: CallStatus) -> List[Call]:
        """Find calls by status"""
        async with db_connection.get_session() as session:
            stmt = select(CallModel).where(
                CallModel.status == status.value
            ).order_by(CallModel.created_at.desc())
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            calls = [self._model_to_entity(model) for model in models]
            
            # Update Redis cache
            for call in calls:
                await redis_client.set_call_status(call)
            
            return calls
    
    async def delete(self, call_id: str) -> bool:
        """Delete call"""
        async with db_connection.get_session() as session:
            stmt = delete(CallModel).where(CallModel.id == call_id)
            result = await session.execute(stmt)
            
            # Remove from Redis
            await redis_client.remove_pending_call(call_id)
            
            return result.rowcount > 0