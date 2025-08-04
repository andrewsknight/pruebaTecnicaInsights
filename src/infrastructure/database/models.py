from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

# Import the enums from domain entities
from domain.entities.agent import AgentStatus
from domain.entities.call import CallStatus, QualificationResult
from domain.entities.assignment import AssignmentStatus

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, default=lambda: uuid.UUID('00000000-0000-0000-0000-000000000001'))
    name = Column(String(255), nullable=False)
    agent_type = Column(String(50), nullable=False)
    status = Column(Enum(AgentStatus, name="agent_status_enum"), nullable=False, default=AgentStatus.OFFLINE)
    last_call_end_time = Column(DateTime(timezone=True), nullable=True)
    current_call_id = Column(UUID(as_uuid=True), nullable=True)
    capabilities = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("AssignmentModel", back_populates="agent")

class CallModel(Base):
    __tablename__ = "calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, default=lambda: uuid.UUID('00000000-0000-0000-0000-000000000001'))
    phone_number = Column(String(50), nullable=False)
    call_type = Column(String(50), nullable=False)
    status = Column(Enum(CallStatus, name="call_status_enum"), nullable=False, default=CallStatus.PENDING)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    qualification_result = Column(Enum(QualificationResult, name="qualification_result_enum"), nullable=False, default=QualificationResult.PENDING)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    call_metadata = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default
    
    # Relationships
    assignments = relationship("AssignmentModel", back_populates="call")

class AssignmentModel(Base):
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, default=lambda: uuid.UUID('00000000-0000-0000-0000-000000000001'))
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    status = Column(Enum(AssignmentStatus, name="assignment_status_enum"), nullable=False, default=AssignmentStatus.PENDING)
    assignment_time_ms = Column(Float, nullable=True)
    expected_duration_seconds = Column(Float, nullable=True)
    actual_duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    assignment_metadata = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default
    
    # Relationships
    call = relationship("CallModel", back_populates="assignments")
    agent = relationship("AgentModel", back_populates="assignments")

class TenantModel(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    configuration = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemMetricsModel(Base):
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # assignment, qualification, performance
    agent_type = Column(String(50), nullable=True)
    call_type = Column(String(50), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    metrics_metadata = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default

class TestRunModel(Base):
    __tablename__ = "test_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(255), nullable=False)
    num_calls = Column(Integer, nullable=False)
    num_agents = Column(Integer, nullable=False)
    call_duration_mean = Column(Float, nullable=False)
    call_duration_std = Column(Float, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="RUNNING")
    results_summary = Column(Text, nullable=True)  # JSON string with results
    test_metadata = Column(JSONB, nullable=True, default=dict)  # Use JSONB type with dict default