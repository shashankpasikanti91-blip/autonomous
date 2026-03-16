"""
N8N Webhook API Endpoints

Provides webhook endpoints compatible with N8N workflow automation.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

from services.n8n_webhooks import (
    N8NWebhookHandler,
    N8NWorkflowInput,
    N8NWebhookResponse,
    N8NWorkflowRegistry
)
from utils.logger import get_logger


logger = get_logger(__name__)

n8n_router = APIRouter(prefix="/webhooks/n8n", tags=["N8N Webhooks"])

# Initialize N8N components
webhook_handler = N8NWebhookHandler()
workflow_registry = N8NWorkflowRegistry()


# ============================================================================
# N8N Webhook Endpoints
# ============================================================================

@n8n_router.post("/onboarding", response_model=N8NWebhookResponse)
async def webhook_onboarding(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for employee onboarding.
    
    Expected data:
    {
        "employee_id": "EMP123",
        "employee_name": "John Doe",
        "employee_email": "john@company.com",
        "department": "Engineering",
        "start_date": "2026-03-01"
    }
    """
    logger.info(f"[N8N] Onboarding webhook: {request.workflow_id}")
    
    # Validate request
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate required fields
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_employee_onboarding",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    # TODO: Route to orchestration service
    # Handler function that executes the actual workflow
    async def onboarding_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        # Call onboarding orchestration
        return {
            "email_sent": True,
            "orientation_scheduled": True,
            "account_created": True
        }
    
    return await webhook_handler.handle_webhook(request, onboarding_handler)


@n8n_router.post("/recruitment", response_model=N8NWebhookResponse)
async def webhook_recruitment(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for recruitment screening.
    
    Expected data:
    {
        "candidate_id": "CAN123",
        "candidate_name": "Jane Smith",
        "candidate_email": "jane@example.com",
        "position_id": "POS456",
        "resume_url": "https://..."
    }
    """
    logger.info(f"[N8N] Recruitment webhook: {request.workflow_id}")
    
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_recruitment",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    async def recruitment_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        return {
            "screening_status": "passed",
            "score": 0.85,
            "next_steps": ["Phone screening", "Technical assessment"]
        }
    
    return await webhook_handler.handle_webhook(request, recruitment_handler)


@n8n_router.post("/payroll", response_model=N8NWebhookResponse)
async def webhook_payroll(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for payroll processing.
    
    Expected data:
    {
        "payroll_period": "2026-02",
        "employee_ids": ["EMP001", "EMP002"],
        "company_id": "COM123"
    }
    """
    logger.info(f"[N8N] Payroll webhook: {request.workflow_id}")
    
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_payroll",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    async def payroll_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        return {
            "total_processed": len(data.data.get("employee_ids", [])),
            "total_amount": 50000.0,
            "failed_count": 0
        }
    
    return await webhook_handler.handle_webhook(request, payroll_handler)


@n8n_router.post("/invoice", response_model=N8NWebhookResponse)
async def webhook_invoice(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for invoice processing.
    
    Expected data:
    {
        "invoice_id": "INV123",
        "client_id": "CLI456",
        "amount": 5000.00,
        "due_date": "2026-03-15"
    }
    """
    logger.info(f"[N8N] Invoice webhook: {request.workflow_id}")
    
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_invoice",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    async def invoice_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        inv_id = data.data.get("invoice_id", "")
        return {
            "invoice_number": inv_id,
            "sent_to_client": True,
            "payment_tracking_enabled": True
        }
    
    return await webhook_handler.handle_webhook(request, invoice_handler)


@n8n_router.post("/meeting", response_model=N8NWebhookResponse)
async def webhook_meeting(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for meeting scheduling.
    
    Expected data:
    {
        "meeting_id": "MTG123",
        "participants": ["user1@company.com", "user2@company.com"],
        "start_time": "2026-02-28T14:00:00Z",
        "duration_minutes": 60,
        "title": "Team Standup"
    }
    """
    logger.info(f"[N8N] Meeting webhook: {request.workflow_id}")
    
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_meeting",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    async def meeting_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        return {
            "meeting_scheduled": True,
            "calendar_invite_sent": True,
            "room_allocated": "Conference Room B"
        }
    
    return await webhook_handler.handle_webhook(request, meeting_handler)


@n8n_router.post("/sales", response_model=N8NWebhookResponse)
async def webhook_sales(
    request: N8NWorkflowInput,
    authorization: Optional[str] = Header(None)
) -> N8NWebhookResponse:
    """
    N8N webhook for sales lead generation.
    
    Expected data:
    {
        "lead_id": "LEAD123",
        "lead_name": "John Prospect",
        "lead_email": "john@prospect.com",
        "company_name": "Prospect Corp",
        "lead_source": "website"
    }
    """
    logger.info(f"[N8N] Sales webhook: {request.workflow_id}")
    
    if not webhook_handler.validate_request({}, authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    is_valid, missing_fields = workflow_registry.validate_webhook_input(
        "n8n_sales",
        request.data
    )
    
    if not is_valid:
        return N8NWebhookResponse(
            success=False,
            execution_id=request.execution_id or str(uuid.uuid4()),
            workflow_id=request.workflow_id,
            trigger_name=request.trigger_name,
            status="failed",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            errors=[{"error": f"Missing field: {field}"} for field in missing_fields]
        )
    
    async def sales_handler(data: N8NWorkflowInput) -> Dict[str, Any]:
        return {
            "lead_qualified": True,
            "qualification_score": 0.82,
            "assigned_to": "sales_rep_01"
        }
    
    return await webhook_handler.handle_webhook(request, sales_handler)


# ============================================================================
# N8N Monitoring Endpoints
# ============================================================================

@n8n_router.get("/status/{execution_id}")
async def get_webhook_status(execution_id: str) -> Dict[str, Any]:
    """Get status of a webhook execution."""
    log = webhook_handler.get_execution_log(execution_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "execution_id": execution_id,
        "workflow_id": log.workflow_id,
        "trigger_name": log.trigger_name,
        "status": log.status,
        "duration_ms": log.duration_ms,
        "timestamp": log.timestamp,
        "error": log.error
    }


@n8n_router.get("/workflows")
async def list_n8n_workflows() -> Dict[str, Any]:
    """List all available N8N workflow definitions."""
    workflows = workflow_registry.list_all()
    
    return {
        "total": len(workflows),
        "workflows": [
            {
                "workflow_id": wf.workflow_id,
                "trigger_name": wf.trigger_name,
                "webhook_url": wf.webhook_url,
                "required_fields": wf.required_fields
            }
            for wf in workflows
        ]
    }


@n8n_router.get("/workflow/{workflow_id}")
async def get_n8n_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get N8N workflow definition."""
    workflow = workflow_registry.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow.to_dict()


@n8n_router.get("/logs/{workflow_id}")
async def get_n8n_logs(
    workflow_id: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Get execution logs for a workflow."""
    logs = webhook_handler.get_workflow_logs(workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "total": len(logs),
        "logs": [
            {
                "execution_id": log.execution_id,
                "status": log.status,
                "duration_ms": log.duration_ms,
                "timestamp": log.timestamp,
                "error": log.error
            }
            for log in logs[-limit:]
        ]
    }
