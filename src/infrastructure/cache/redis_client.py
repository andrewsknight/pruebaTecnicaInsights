import redis.asyncio as redis
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

from config.settings import settings
from domain.entities.agent import Agent, AgentStatus
from domain.entities.call import Call, CallStatus

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
        try:
            key = f"agent:{agent.id}:status"
            
            # Calculate idle time safely
            idle_time = agent.get_idle_time_seconds()
            if idle_time == float('inf'):
                idle_time = 999999  # Large number for sorting, but finite
            
            data = {
                "id": str(agent.id),
                "name": agent.name or "",
                "agent_type": agent.agent_type or "",
                "status": agent.status.value if agent.status else "OFFLINE",
                "last_call_end_time": agent.last_call_end_time.isoformat() if agent.last_call_end_time else "",
                "current_call_id": str(agent.current_call_id) if agent.current_call_id else "",
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else datetime.utcnow().isoformat(),
                "idle_time_seconds": str(idle_time)
            }
            
            await self.redis.hset(key, mapping=data)
            
            # Update available agents sorted set if agent is available
            if agent.is_available():
                await self.redis.zadd(
                    "available_agents",
                    {str(agent.id): idle_time}
                )
            else:
                await self.redis.zrem("available_agents", str(agent.id))
                
        except Exception as e:
            print(f"Redis set_agent_status error: {e}")
            # Don't re-raise to avoid breaking the main flow
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get agent status from Redis"""
        try:
            key = f"agent:{agent_id}:status"
            data = await self.redis.hgetall(key)
            
            if not data or not data.get("id"):
                return None
            
            # Ensure all required fields have default values
            return {
                "id": data.get("id", agent_id),
                "name": data.get("name", ""),
                "agent_type": data.get("agent_type", ""),
                "status": data.get("status", "OFFLINE"),
                "last_call_end_time": data.get("last_call_end_time") or None,
                "current_call_id": data.get("current_call_id") or None,
                "updated_at": data.get("updated_at", datetime.utcnow().isoformat()),
                "idle_time_seconds": data.get("idle_time_seconds", "0")
            }
        except Exception as e:
            print(f"Redis get_agent_status error: {e}")
            return None
    
    async def get_available_agents(self, limit: int = None) -> List[str]:
        """Get available agents sorted by idle time (longest first)"""
        try:
            if limit:
                agent_ids = await self.redis.zrevrange("available_agents", 0, limit - 1)
            else:
                agent_ids = await self.redis.zrevrange("available_agents", 0, -1)
            
            return [str(agent_id) for agent_id in agent_ids] if agent_ids else []
        except Exception as e:
            print(f"Redis get_available_agents error: {e}")
            return []
    
    async def remove_agent(self, agent_id: str):
        """Remove agent from Redis"""
        try:
            await self.redis.delete(f"agent:{agent_id}:status")
            await self.redis.zrem("available_agents", str(agent_id))
        except Exception as e:
            print(f"Redis remove_agent error: {e}")
    
    # Call operations
    async def set_call_status(self, call: Call):
        """Set call status in Redis"""
        try:
            key = f"call:{call.id}:status"
            data = {
                "id": str(call.id),
                "phone_number": call.phone_number or "",
                "call_type": call.call_type or "",
                "status": call.status.value if call.status else "PENDING",
                "assigned_agent_id": str(call.assigned_agent_id) if call.assigned_agent_id else "",
                "qualification_result": call.qualification_result.value if call.qualification_result else "PENDING",
                "created_at": call.created_at.isoformat() if call.created_at else datetime.utcnow().isoformat(),
                "assigned_at": call.assigned_at.isoformat() if call.assigned_at else "",
                "completed_at": call.completed_at.isoformat() if call.completed_at else ""
            }
            
            await self.redis.hset(key, mapping=data)
            
            # Add to pending calls queue if pending
            if call.status == CallStatus.PENDING:
                await self.redis.lpush("pending_calls", str(call.id))
        except Exception as e:
            print(f"Redis set_call_status error: {e}")
    
    async def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get call status from Redis"""
        try:
            key = f"call:{call_id}:status"
            data = await self.redis.hgetall(key)
            
            if not data or not data.get("id"):
                return None
            
            return data
        except Exception as e:
            print(f"Redis get_call_status error: {e}")
            return None
    
    async def get_pending_calls(self, count: int = 10) -> List[str]:
        """Get pending calls"""
        try:
            call_ids = await self.redis.lrange("pending_calls", 0, count - 1)
            return [str(call_id) for call_id in call_ids] if call_ids else []
        except Exception as e:
            print(f"Redis get_pending_calls error: {e}")
            return []
    
    async def remove_pending_call(self, call_id: str):
        """Remove call from pending queue"""
        try:
            await self.redis.lrem("pending_calls", 0, str(call_id))
        except Exception as e:
            print(f"Redis remove_pending_call error: {e}")
    
    # Assignment operations
    async def create_assignment_lock(self, call_id: str, ttl_seconds: int = 5) -> bool:
        """Create distributed lock for assignment"""
        try:
            key = f"assignment_lock:{call_id}"
            result = await self.redis.set(key, datetime.utcnow().isoformat(), nx=True, ex=ttl_seconds)
            return result is not None
        except Exception as e:
            print(f"Redis create_assignment_lock error: {e}")
            return False
    
    async def release_assignment_lock(self, call_id: str):
        """Release assignment lock"""
        try:
            key = f"assignment_lock:{call_id}"
            await self.redis.delete(key)
        except Exception as e:
            print(f"Redis release_assignment_lock error: {e}")
    
    # Metrics operations
    async def increment_metric(self, metric_name: str, value: float = 1):
        """Increment a metric counter"""
        try:
            await self.redis.incrbyfloat(f"metric:{metric_name}", value)
        except Exception as e:
            print(f"Redis increment_metric error: {e}")
    
    async def set_metric(self, metric_name: str, value: float):
        """Set a metric value"""
        try:
            await self.redis.set(f"metric:{metric_name}", str(value))
        except Exception as e:
            print(f"Redis set_metric error: {e}")
    
    async def get_metric(self, metric_name: str) -> Optional[float]:
        """Get metric value"""
        try:
            value = await self.redis.get(f"metric:{metric_name}")
            return float(value) if value else None
        except Exception as e:
            print(f"Redis get_metric error: {e}")
            return None
    
    async def get_all_metrics(self) -> Dict[str, float]:
        """Get all metrics"""
        try:
            keys = await self.redis.keys("metric:*")
            if not keys:
                return {}
            
            values = await self.redis.mget(keys)
            metrics = {}
            
            for key, value in zip(keys, values):
                metric_name = key.replace("metric:", "")
                try:
                    metrics[metric_name] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    metrics[metric_name] = 0.0
            
            return metrics
        except Exception as e:
            print(f"Redis get_all_metrics error: {e}")
            return {}
    
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
        try:
            await self.redis.flushdb()
        except Exception as e:
            print(f"Redis clear_all_data error: {e}")

# Global Redis instance
redis_client = RedisClient()