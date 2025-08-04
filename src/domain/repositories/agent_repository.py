import redis.asyncio as redis
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

from ...config.settings import settings
from ...domain.entities.agent import Agent, AgentStatus
from ...domain.entities.call import Call, CallStatus

class RedisClient:
    """Redis client for real-time state management"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        # Test connection
        await self.redis.ping()
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    # Agent operations
    async def set_agent_status(self, agent: Agent):
        """Set agent status in Redis"""
        key = f"agent:{agent.id}:status"
        data = {
            "id": agent.id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "status": agent.status.value,
            "last_call_end_time": agent.last_call_end_time.isoformat() if agent.last_call_end_time else None,
            "current_call_id": agent.current_call_id,
            "updated_at": agent.updated_at.isoformat(),
            "idle_time_seconds": agent.get_idle_time_seconds()
        }
        
        await self.redis.hset(key, mapping=data)
        
        # Update available agents sorted set if agent is available
        if agent.is_available():
            await self.redis.zadd(
                "available_agents",
                {agent.id: agent.get_idle_time_seconds()}
            )
        else:
            await self.redis.zrem("available_agents", agent.id)
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get agent status from Redis"""
        key = f"agent:{agent_id}:status"
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        return data
    
    async def get_available_agents(self, limit: int = None) -> List[str]:
        """Get available agents sorted by idle time (longest first)"""
        if limit:
            agent_ids = await self.redis.zrevrange("available_agents", 0, limit - 1)
        else:
            agent_ids = await self.redis.zrevrange("available_agents", 0, -1)
        
        return agent_ids
    
    async def remove_agent(self, agent_id: str):
        """Remove agent from Redis"""
        await self.redis.delete(f"agent:{agent_id}:status")
        await self.redis.zrem("available_agents", agent_id)
    
    # Call operations
    async def set_call_status(self, call: Call):
        """Set call status in Redis"""
        key = f"call:{call.id}:status"
        data = {
            "id": call.id,
            "phone_number": call.phone_number,
            "call_type": call.call_type,
            "status": call.status.value,
            "assigned_agent_id": call.assigned_agent_id or "",
            "qualification_result": call.qualification_result.value,
            "created_at": call.created_at.isoformat(),
            "assigned_at": call.assigned_at.isoformat() if call.assigned_at else "",
            "completed_at": call.completed_at.isoformat() if call.completed_at else ""
        }
        
        await self.redis.hset(key, mapping=data)
        
        # Add to pending calls queue if pending
        if call.status == CallStatus.PENDING:
            await self.redis.lpush("pending_calls", call.id)
    
    async def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get call status from Redis"""
        key = f"call:{call_id}:status"
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        return data
    
    async def get_pending_calls(self, count: int = 10) -> List[str]:
        """Get pending calls"""
        call_ids = await self.redis.lrange("pending_calls", 0, count - 1)
        return call_ids
    
    async def remove_pending_call(self, call_id: str):
        """Remove call from pending queue"""
        await self.redis.lrem("pending_calls", 0, call_id)
    
    # Assignment operations
    async def create_assignment_lock(self, call_id: str, ttl_seconds: int = 5) -> bool:
        """Create distributed lock for assignment"""
        key = f"assignment_lock:{call_id}"
        result = await self.redis.set(key, datetime.utcnow().isoformat(), nx=True, ex=ttl_seconds)
        return result is not None
    
    async def release_assignment_lock(self, call_id: str):
        """Release assignment lock"""
        key = f"assignment_lock:{call_id}"
        await self.redis.delete(key)
    
    # Metrics operations
    async def increment_metric(self, metric_name: str, value: float = 1):
        """Increment a metric counter"""
        await self.redis.incrbyfloat(f"metric:{metric_name}", value)
    
    async def set_metric(self, metric_name: str, value: float):
        """Set a metric value"""
        await self.redis.set(f"metric:{metric_name}", value)
    
    async def get_metric(self, metric_name: str) -> Optional[float]:
        """Get metric value"""
        value = await self.redis.get(f"metric:{metric_name}")
        return float(value) if value else None
    
    async def get_all_metrics(self) -> Dict[str, float]:
        """Get all metrics"""
        keys = await self.redis.keys("metric:*")
        if not keys:
            return {}
        
        values = await self.redis.mget(keys)
        metrics = {}
        
        for key, value in zip(keys, values):
            metric_name = key.replace("metric:", "")
            metrics[metric_name] = float(value) if value else 0.0
        
        return metrics
    
    # System operations
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def clear_all_data(self):
        """Clear all data (for testing)"""
        await self.redis.flushdb()

# Global Redis instance
redis_client = RedisClient()