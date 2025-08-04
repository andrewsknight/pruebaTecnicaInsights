from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid
import asyncio

from ...domain.entities.agent import Agent, AgentStatus
from ...domain.entities.call import Call, CallStatus, QualificationResult
from ...domain.repositories.agent_repository import AgentRepository
from ...application.orchestrator import call_orchestrator
from ...config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class CreateCallRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number of the call")
    call_type: str = Field(..., description="Type of call (e.g., llamada_tipo_1)")

class CallResponse(BaseModel):
    id: str
    phone_number: str
    call_type: str
    status: str
    assigned_agent_id: Optional[str] = None
    qualification_result: str
    created_at: str
    assigned_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    wait_time_seconds: Optional[float] = None

class CreateAgentRequest(BaseModel):
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Type of agent (e.g., agente_tipo_1)")

class AgentResponse(BaseModel):
    id: str
    name: str
    agent_type: str
    status: str
    last_call_end_time: Optional[str] = None
    current_call_id: Optional[str] = None
    created_at: str
    updated_at: str
    idle_time_seconds: Optional[float] = None

class UpdateAgentStatusRequest(BaseModel):
    status: str = Field(..., description="New agent status (AVAILABLE, PAUSED, OFFLINE)")

class AssignmentResponse(BaseModel):
    success: bool
    assignment_id: Optional[str] = None
    agent_id: Optional[str] = None
    call_id: str
    assignment_time_ms: float
    message: str

class SystemStatusResponse(BaseModel):
    timestamp: str
    agents: Dict[str, int]
    active_assignments: int
    metrics: Dict[str, float]
    system_health: Dict[str, Any]

# Create FastAPI app
app = FastAPI(
    title="Call Assignment System",
    description="Multi-tenant call assignment system with high performance requirements",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global repository instances
agent_repository = AgentRepository()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from ...infrastructure.database.connection import db_connection
    from ...infrastructure.cache.redis_client import redis_client
    
    logger.info("Starting Call Assignment System...")
    
    # Initialize database
    await db_connection.initialize()
    logger.info("Database initialized")
    
    # Initialize Redis
    await redis_client.initialize()
    logger.info("Redis initialized")
    
    logger.info("Call Assignment System started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from ...infrastructure.database.connection import db_connection
    from ...infrastructure.cache.redis_client import redis_client
    
    logger.info("Shutting down Call Assignment System...")
    
    await db_connection.close()
    await redis_client.close()
    
    logger.info("Call Assignment System shutdown complete")

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    from ...infrastructure.cache.redis_client import redis_client
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": await redis_client.health_check()
    }

# Call endpoints
@app.post("/calls", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_and_assign_call(request: CreateCallRequest):
    """Create a new call and attempt immediate assignment"""
    try:
        # Create call entity
        call = Call(
            phone_number=request.phone_number,
            call_type=request.call_type,
            status=CallStatus.PENDING
        )
        
        # Validate call type
        if call.call_type not in settings.call_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid call_type. Must be one of: {settings.call_types}"
            )
        
        # Attempt assignment
        result = await call_orchestrator.assign_call(call)
        
        return AssignmentResponse(
            success=result.success,
            assignment_id=result.assignment.id if result.assignment else None,
            agent_id=result.agent.id if result.agent else None,
            call_id=call.id,
            assignment_time_ms=result.assignment_time_ms,
            message=result.message
        )
        
    except Exception as e:
        logger.error(f"Error creating call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete("/calls/{call_id}", status_code=status.HTTP_200_OK)
async def cancel_call(call_id: str):
    """Cancel/abandon a call"""
    try:
        success = await call_orchestrator.cancel_call(call_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call {call_id} not found or cannot be cancelled"
            )
        
        return {"message": f"Call {call_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: str):
    """Get call details"""
    try:
        from ...infrastructure.cache.redis_client import redis_client
        
        call_data = await redis_client.get_call_status(call_id)
        
        if not call_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call {call_id} not found"
            )
        
        # Convert to response model
        response = CallResponse(
            id=call_data["id"],
            phone_number=call_data["phone_number"],
            call_type=call_data["call_type"],
            status=call_data["status"],
            assigned_agent_id=call_data["assigned_agent_id"] if call_data["assigned_agent_id"] else None,
            qualification_result=call_data["qualification_result"],
            created_at=call_data["created_at"],
            assigned_at=call_data["assigned_at"] if call_data["assigned_at"] else None,
            completed_at=call_data["completed_at"] if call_data["completed_at"] else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Agent endpoints
@app.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent"""
    try:
        # Validate agent type
        if request.agent_type not in settings.agent_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_type. Must be one of: {settings.agent_types}"
            )
        
        # Create agent entity
        agent = Agent(
            name=request.name,
            agent_type=request.agent_type,
            status=AgentStatus.OFFLINE
        )
        
        # Save agent
        saved_agent = await agent_repository.save(agent)
        
        return AgentResponse(**saved_agent.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/agents", response_model=List[AgentResponse])
async def get_agents():
    """Get all agents"""
    try:
        agents = await agent_repository.find_all()
        return [AgentResponse(**agent.to_dict()) for agent in agents]
        
    except Exception as e:
        logger.error(f"Error getting agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent details"""
    try:
        agent = await agent_repository.find_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        return AgentResponse(**agent.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.put("/agents/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(agent_id: str, request: UpdateAgentStatusRequest):
    """Update agent status"""
    try:
        # Validate status
        try:
            new_status = AgentStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in AgentStatus]}"
            )
        
        # Update status
        success = await agent_repository.update_status(agent_id, new_status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Return updated agent
        agent = await agent_repository.find_by_id(agent_id)
        return AgentResponse(**agent.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/agents/available", response_model=List[AgentResponse])
async def get_available_agents():
    """Get all available agents ordered by idle time"""
    try:
        agents = await agent_repository.find_available()
        return [AgentResponse(**agent.to_dict()) for agent in agents]
        
    except Exception as e:
        logger.error(f"Error getting available agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# System endpoints
@app.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status and metrics"""
    try:
        status_data = await call_orchestrator.get_system_status()
        
        if "error" in status_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=status_data["error"]
            )
        
        return SystemStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/system/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        from ...infrastructure.cache.redis_client import redis_client
        
        metrics = await redis_client.get_all_metrics()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Webhook receiver for testing
@app.post("/webhook")
async def receive_webhook(payload: Dict[str, Any]):
    """Receive webhook notifications (for testing purposes)"""
    logger.info(f"Received webhook: {payload.get('event_type', 'unknown')}")
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}