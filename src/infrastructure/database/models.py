from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    agent_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="OFFLINE")
    last_call_end_time = Column(DateTime, nullable=True)
    current_call_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("AssignmentModel", back_populates="agent")

class CallModel(Base):
    __tablename__ = "calls"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(50), nullable=False)
    call_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    assigned_agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    qualification_result = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Relationships
    assignments = relationship("AssignmentModel", back_populates="call")

class AssignmentModel(Base):
    __tablename__ = "assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    assignment_time_ms = Column(Float, nullable=True)
    expected_duration_seconds = Column(Float, nullable=True)
    actual_duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    call = relationship("CallModel", back_populates="assignments")
    agent = relationship("AgentModel", back_populates="assignments")

class SystemMetricsModel(Base):
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # assignment, qualification, performance
    agent_type = Column(String(50), nullable=True)
    call_type = Column(String(50), nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class TestRunModel(Base):
    __tablename__ = "test_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_name = Column(String(255), nullable=False)
    num_calls = Column(Integer, nullable=False)
    num_agents = Column(Integer, nullable=False)
    call_duration_mean = Column(Float, nullable=False)
    call_duration_std = Column(Float, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="RUNNING")
    results_summary = Column(Text, nullable=True)  # JSON string with results