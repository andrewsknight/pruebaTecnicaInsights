from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from domain.entities.agent import Agent, AgentStatus
from infrastructure.database.models import AgentModel
from infrastructure.database.connection import db_connection
from infrastructure.cache.redis_client import redis_client

class AgentRepositoryInterface(ABC):
    """Abstract interface for agent repository"""
    
    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        """Save or update an agent"""
        pass
    
    @abstractmethod
    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find agent by ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Agent]:
        """Find all agents"""
        pass
    
    @abstractmethod
    async def find_available(self) -> List[Agent]:
        """Find all available agents"""
        pass
    
    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete agent"""
        pass

class AgentRepository(AgentRepositoryInterface):
    """PostgreSQL + Redis implementation of agent repository"""
    
    def __init__(self):
        pass
    
    def _model_to_entity(self, model: AgentModel) -> Agent:
        """Convert database model to domain entity"""
        return Agent(
            id=str(model.id),  # Ensure string conversion
            name=model.name or "",
            agent_type=model.agent_type or "",
            status=AgentStatus(model.status.value if hasattr(model.status, 'value') else model.status),
            last_call_end_time=model.last_call_end_time,
            current_call_id=str(model.current_call_id) if model.current_call_id else None,
            created_at=model.created_at or datetime.utcnow(),
            updated_at=model.updated_at or datetime.utcnow()
        )
    
    def _entity_to_model(self, agent: Agent, model: Optional[AgentModel] = None) -> AgentModel:
        """Convert domain entity to database model"""
        if model is None:
            model = AgentModel()
        
        # Handle UUID conversion properly
        if isinstance(agent.id, str):
            try:
                model.id = uuid.UUID(agent.id) if agent.id else uuid.uuid4()
            except ValueError:
                model.id = uuid.uuid4()
        else:
            model.id = agent.id or uuid.uuid4()
        
        model.name = agent.name or ""
        model.agent_type = agent.agent_type or ""
        model.status = agent.status or AgentStatus.OFFLINE  # SQLAlchemy will handle enum conversion
        model.last_call_end_time = agent.last_call_end_time
        
        # Handle current_call_id UUID conversion
        if agent.current_call_id:
            try:
                if isinstance(agent.current_call_id, str):
                    model.current_call_id = uuid.UUID(agent.current_call_id)
                else:
                    model.current_call_id = agent.current_call_id
            except ValueError:
                model.current_call_id = None
        else:
            model.current_call_id = None
            
        model.created_at = agent.created_at or datetime.utcnow()
        model.updated_at = agent.updated_at or datetime.utcnow()
        
        return model
    
    async def save(self, agent: Agent) -> Agent:
        """Save or update an agent"""
        async with db_connection.get_session() as session:
            try:
                # Convert string ID to UUID for database query
                if agent.id:
                    try:
                        agent_uuid = uuid.UUID(agent.id) if isinstance(agent.id, str) else agent.id
                    except ValueError:
                        agent_uuid = uuid.uuid4()
                        agent.id = str(agent_uuid)
                else:
                    agent_uuid = uuid.uuid4()
                    agent.id = str(agent_uuid)
                
                # Check if agent exists
                stmt = select(AgentModel).where(AgentModel.id == agent_uuid)
                result = await session.execute(stmt)
                existing_model = result.scalar_one_or_none()
                
                if existing_model:
                    # Update existing
                    model = self._entity_to_model(agent, existing_model)
                else:
                    # Create new
                    model = self._entity_to_model(agent)
                    session.add(model)
                
                await session.commit()
                await session.refresh(model)
                
                # Convert back to entity
                saved_agent = self._model_to_entity(model)
                
                # Update Redis cache
                await redis_client.set_agent_status(saved_agent)
                
                return saved_agent
                
            except Exception as e:
                await session.rollback()
                print(f"Save agent error: {e}")
                raise e
    
    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find agent by ID"""
        if not agent_id:
            return None
            
        try:
            # Try Redis first for real-time data
            redis_data = await redis_client.get_agent_status(agent_id)
            if redis_data and redis_data.get("id"):
                return Agent(
                    id=redis_data["id"],
                    name=redis_data.get("name", ""),
                    agent_type=redis_data.get("agent_type", ""),
                    status=AgentStatus(redis_data.get("status", "OFFLINE")),
                    last_call_end_time=datetime.fromisoformat(redis_data["last_call_end_time"]) if redis_data.get("last_call_end_time") else None,
                    current_call_id=redis_data.get("current_call_id"),
                    updated_at=datetime.fromisoformat(redis_data["updated_at"]) if redis_data.get("updated_at") else datetime.utcnow()
                )
        except Exception as redis_error:
            print(f"Redis lookup failed: {redis_error}")
        
        # Fallback to database
        async with db_connection.get_session() as session:
            try:
                agent_uuid = uuid.UUID(agent_id) if isinstance(agent_id, str) else agent_id
                stmt = select(AgentModel).where(AgentModel.id == agent_uuid)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    agent = self._model_to_entity(model)
                    # Update Redis cache
                    await redis_client.set_agent_status(agent)
                    return agent
                
                return None
            except Exception as e:
                print(f"Database lookup failed: {e}")
                return None
    
    async def find_all(self) -> List[Agent]:
        """Find all agents"""
        async with db_connection.get_session() as session:
            try:
                stmt = select(AgentModel).order_by(AgentModel.created_at)
                result = await session.execute(stmt)
                models = result.scalars().all()
                
                agents = [self._model_to_entity(model) for model in models]
                
                # Update Redis cache for all agents
                for agent in agents:
                    await redis_client.set_agent_status(agent)
                
                return agents
            except Exception as e:
                print(f"Find all agents failed: {e}")
                return []
    
    async def find_available(self) -> List[Agent]:
        """Find all available agents ordered by idle time (longest first)"""
        try:
            # Get available agent IDs from Redis (already sorted by idle time)
            available_agent_ids = await redis_client.get_available_agents()
            
            if available_agent_ids:
                # Get agent details for the available agents
                agents = []
                for agent_id in available_agent_ids:
                    agent = await self.find_by_id(agent_id)
                    if agent and agent.is_available():
                        agents.append(agent)
                return agents
        except Exception as redis_error:
            print(f"Redis available agents lookup failed: {redis_error}")
        
        # Fallback to database
        async with db_connection.get_session() as session:
            try:
                stmt = select(AgentModel).where(
                    AgentModel.status == AgentStatus.AVAILABLE
                ).order_by(AgentModel.last_call_end_time.asc().nulls_first())
                
                result = await session.execute(stmt)
                models = result.scalars().all()
                
                agents = [self._model_to_entity(model) for model in models]
                
                # Update Redis cache
                for agent in agents:
                    await redis_client.set_agent_status(agent)
                
                return agents
            except Exception as e:
                print(f"Database available agents lookup failed: {e}")
                return []
    
    async def delete(self, agent_id: str) -> bool:
        """Delete agent"""
        if not agent_id:
            return False
            
        async with db_connection.get_session() as session:
            try:
                agent_uuid = uuid.UUID(agent_id) if isinstance(agent_id, str) else agent_id
                stmt = delete(AgentModel).where(AgentModel.id == agent_uuid)
                result = await session.execute(stmt)
                await session.commit()
                
                # Remove from Redis
                await redis_client.remove_agent(agent_id)
                
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                print(f"Delete agent failed: {e}")
                return False
    
    async def count_by_status(self, status: AgentStatus) -> int:
        """Count agents by status"""
        async with db_connection.get_session() as session:
            try:
                stmt = select(AgentModel).where(AgentModel.status == status)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return len(models)
            except Exception as e:
                print(f"Count by status failed: {e}")
                return 0
    
    async def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        try:
            agent = await self.find_by_id(agent_id)
            if not agent:
                return False
            
            if status == AgentStatus.AVAILABLE:
                agent.set_available()
            elif status == AgentStatus.PAUSED:
                agent.set_paused()
            
            await self.save(agent)
            return True
        except Exception as e:
            print(f"Update status failed: {e}")
            return False