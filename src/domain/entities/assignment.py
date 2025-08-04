from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class AssignmentStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class Assignment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    call_id: str = ""
    agent_id: str = ""
    status: AssignmentStatus = AssignmentStatus.PENDING
    assignment_time_ms: Optional[float] = None
    expected_duration_seconds: Optional[float] = None
    actual_duration_seconds: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def activate(self, assignment_time_ms: float, expected_duration_seconds: float) -> None:
        """Activate the assignment"""
        if self.status != AssignmentStatus.PENDING:
            raise ValueError(f"Assignment {self.id} cannot be activated. Current status: {self.status}")
        
        self.status = AssignmentStatus.ACTIVE
        self.assignment_time_ms = assignment_time_ms
        self.expected_duration_seconds = expected_duration_seconds
        self.activated_at = datetime.utcnow()
    
    def complete(self, actual_duration_seconds: float) -> None:
        """Complete the assignment"""
        if self.status != AssignmentStatus.ACTIVE:
            raise ValueError(f"Assignment {self.id} cannot be completed. Current status: {self.status}")
        
        self.status = AssignmentStatus.COMPLETED
        self.actual_duration_seconds = actual_duration_seconds
        self.completed_at = datetime.utcnow()
    
    def fail(self, reason: str = "") -> None:
        """Mark assignment as failed"""
        self.status = AssignmentStatus.FAILED
        self.completed_at = datetime.utcnow()
    
    def get_duration_variance(self) -> Optional[float]:
        """Get variance between expected and actual duration"""
        if self.expected_duration_seconds is None or self.actual_duration_seconds is None:
            return None
        return abs(self.actual_duration_seconds - self.expected_duration_seconds)
    
    def to_dict(self) -> dict:
        """Convert assignment to dictionary"""
        return {
            "id": self.id,
            "call_id": self.call_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "assignment_time_ms": self.assignment_time_ms,
            "expected_duration_seconds": self.expected_duration_seconds,
            "actual_duration_seconds": self.actual_duration_seconds,
            "duration_variance": self.get_duration_variance(),
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }