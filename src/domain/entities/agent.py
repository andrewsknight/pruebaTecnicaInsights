from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class AgentStatus(Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    PAUSED = "PAUSED"
    OFFLINE = "OFFLINE"

@dataclass
class Agent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    agent_type: str = ""
    status: AgentStatus = AgentStatus.OFFLINE
    last_call_end_time: Optional[datetime] = None
    current_call_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_available(self) -> bool:
        """Check if agent is available to take calls"""
        return self.status == AgentStatus.AVAILABLE
    
    def assign_call(self, call_id: str) -> None:
        """Assign a call to this agent"""
        if not self.is_available():
            raise ValueError(f"Agent {self.id} is not available")
        
        self.status = AgentStatus.BUSY
        self.current_call_id = call_id
        self.updated_at = datetime.utcnow()
    
    def complete_call(self) -> None:
        """Mark call as completed and make agent available"""
        if self.status != AgentStatus.BUSY:
            raise ValueError(f"Agent {self.id} is not currently busy")
        
        self.status = AgentStatus.AVAILABLE
        self.last_call_end_time = datetime.utcnow()
        self.current_call_id = None
        self.updated_at = datetime.utcnow()
    
    def set_available(self) -> None:
        """Set agent as available"""
        self.status = AgentStatus.AVAILABLE
        self.updated_at = datetime.utcnow()
    
    def set_paused(self) -> None:
        """Set agent as paused"""
        self.status = AgentStatus.PAUSED
        self.updated_at = datetime.utcnow()
    
    def get_idle_time_seconds(self) -> float:
        """Get idle time in seconds since last call ended"""
        if self.last_call_end_time is None:
            # If no previous call, return a large number for priority
            return float('inf')
        
        return (datetime.utcnow() - self.last_call_end_time).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "last_call_end_time": self.last_call_end_time.isoformat() if self.last_call_end_time else None,
            "current_call_id": self.current_call_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "idle_time_seconds": self.get_idle_time_seconds() if self.get_idle_time_seconds() != float('inf') else None
        }