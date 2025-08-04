import aiohttp
import json
import logging
from typing import Dict, Any
from datetime import datetime

from domain.entities.agent import Agent
from domain.entities.call import Call, QualificationResult
from domain.entities.assignment import Assignment
from config.settings import settings

logger = logging.getLogger(__name__)

class WebhookClient:
    """Client for sending webhooks to external systems"""
    
    def __init__(self):
        self.webhook_url = settings.webhook_url
        self.timeout = settings.webhook_timeout
        
    async def notify_assignment(self, assignment: Assignment, agent: Agent, call: Call) -> bool:
        """Notify external system of call assignment"""
        payload = {
            "event_type": "CALL_ASSIGNED",
            "timestamp": datetime.utcnow().isoformat(),
            "assignment": {
                "assignment_id": assignment.id,
                "call_id": assignment.call_id,
                "agent_id": assignment.agent_id,
                "assignment_time_ms": assignment.assignment_time_ms,
                "expected_duration_seconds": assignment.expected_duration_seconds
            },
            "call": {
                "call_id": call.id,
                "phone_number": call.phone_number,
                "call_type": call.call_type,
                "created_at": call.created_at.isoformat(),
                "assigned_at": call.assigned_at.isoformat() if call.assigned_at else None
            },
            "agent": {
                "agent_id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status.value
            }
        }
        
        return await self._send_webhook(payload)
    
    async def notify_completion(self, call: Call, agent: Agent, qualification: QualificationResult) -> bool:
        """Notify external system of call completion"""
        payload = {
            "event_type": "CALL_COMPLETED",
            "timestamp": datetime.utcnow().isoformat(),
            "call": {
                "call_id": call.id,
                "phone_number": call.phone_number,
                "call_type": call.call_type,
                "status": call.status.value,
                "qualification_result": qualification.value,
                "duration_seconds": call.duration_seconds,
                "created_at": call.created_at.isoformat(),
                "assigned_at": call.assigned_at.isoformat() if call.assigned_at else None,
                "completed_at": call.completed_at.isoformat() if call.completed_at else None
            },
            "agent": {
                "agent_id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status.value
            }
        }
        
        return await self._send_webhook(payload)
    
    async def notify_saturation(self, call: Call, assignment_time_ms: float) -> bool:
        """Notify external system of saturation (no agents available)"""
        payload = {
            "event_type": "SYSTEM_SATURATED",
            "timestamp": datetime.utcnow().isoformat(),
            "call": {
                "call_id": call.id,
                "phone_number": call.phone_number,
                "call_type": call.call_type,
                "created_at": call.created_at.isoformat()
            },
            "assignment_attempt": {
                "assignment_time_ms": assignment_time_ms,
                "status": "NO_AGENTS_AVAILABLE"
            }
        }
        
        return await self._send_webhook(payload)
    
    async def notify_agent_status_change(self, agent: Agent, previous_status: str) -> bool:
        """Notify external system of agent status change"""
        payload = {
            "event_type": "AGENT_STATUS_CHANGED",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": {
                "agent_id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "previous_status": previous_status,
                "current_status": agent.status.value,
                "updated_at": agent.updated_at.isoformat()
            }
        }
        
        return await self._send_webhook(payload)
    
    async def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """Send webhook with payload"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Content-Type": "application/json",
                    "X-Event-Source": "call-assignment-system",
                    "X-Event-Timestamp": datetime.utcnow().isoformat()
                }
                
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook sent successfully: {payload['event_type']}")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}: {payload['event_type']}")
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"Webhook client error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected webhook error: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """Check if webhook endpoint is responsive"""
        try:
            payload = {
                "event_type": "HEALTH_CHECK",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._send_webhook(payload)
            
        except Exception as e:
            logger.error(f"Webhook health check failed: {str(e)}")
            return False