from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class CallStatus(Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    FAILED = "FAILED"

class QualificationResult(Enum):
    OK = "OK"
    KO = "KO"
    PENDING = "PENDING"

@dataclass
class Call:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str = ""
    call_type: str = ""
    status: CallStatus = CallStatus.PENDING
    assigned_agent_id: Optional[str] = None
    qualification_result: QualificationResult = QualificationResult.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    def assign_to_agent(self, agent_id: str) -> None:
        """Assign call to an agent"""
        if self.status != CallStatus.PENDING:
            raise ValueError(f"Call {self.id} cannot be assigned. Current status: {self.status}")
        
        self.status = CallStatus.ASSIGNED
        self.assigned_agent_id = agent_id
        self.assigned_at = datetime.utcnow()
    
    def start_call(self) -> None:
        """Mark call as started"""
        if self.status != CallStatus.ASSIGNED:
            raise ValueError(f"Call {self.id} must be assigned before starting")
        
        self.status = CallStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def complete_call(self, duration_seconds: float, qualification: QualificationResult) -> None:
        """Complete the call with qualification"""
        if self.status not in [CallStatus.ASSIGNED, CallStatus.IN_PROGRESS]:
            raise ValueError(f"Call {self.id} cannot be completed. Current status: {self.status}")
        
        self.status = CallStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.duration_seconds = duration_seconds
        self.qualification_result = qualification
    
    def abandon_call(self) -> None:
        """Mark call as abandoned"""
        self.status = CallStatus.ABANDONED
        self.completed_at = datetime.utcnow()
    
    def get_wait_time_seconds(self) -> Optional[float]:
        """Get wait time from creation to assignment"""
        if self.assigned_at is None:
            return None
        return (self.assigned_at - self.created_at).total_seconds()
    
    def get_total_duration_seconds(self) -> Optional[float]:
        """Get total time from creation to completion"""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.created_at).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert call to dictionary"""
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "call_type": self.call_type,
            "status": self.status.value,
            "assigned_agent_id": self.assigned_agent_id,
            "qualification_result": self.qualification_result.value,
            "created_at": self.created_at.isoformat(),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "wait_time_seconds": self.get_wait_time_seconds(),
            "total_duration_seconds": self.get_total_duration_seconds()
        }