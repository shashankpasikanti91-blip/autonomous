"""
N8N Webhook Compatibility Layer

Provides endpoints compatible with N8N workflow automation:
- Webhook receiver for N8N triggers
- Structured request/response format
- Authentication and validation
- Execution tracking and logging
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from enum import Enum
import json
from pydantic import BaseModel, Field
from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================================
# N8N Request/Response Models
# ============================================================================

class WebhookAuth(BaseModel):
    """Webhook authentication."""
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    
    def is_valid(self, expected_api_key: Optional[str] = None) -> bool:
        """Validate authentication."""
        if expected_api_key and self.api_key:
            return self.api_key == expected_api_key
        return True


class N8NWorkflowInput(BaseModel):
    """Input from N8N workflow."""
    workflow_id: str = Field(..., description="ID of the workflow")
    trigger_name: str = Field(..., description="Name of the trigger")
    execution_id: Optional[str] = None
    timestamp: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict, description="Workflow data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class N8NWebhookResponse(BaseModel):
    """Response to N8N webhook."""
    success: bool
    execution_id: str
    workflow_id: str
    trigger_name: str
    status: str  # "queued", "processing", "completed", "failed"
    message: str
    results: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class WebhookExecutionLog(BaseModel):
    """Log entry for webhook execution."""
    webhook_id: str
    execution_id: str
    workflow_id: str
    trigger_name: str
    status: str
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class N8NWebhookDefinition(BaseModel):
    """Definition of an N8N webhook."""
    workflow_id: str
    trigger_name: str
    webhook_url: str
    required_fields: List[str] = Field(default_factory=list)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


# ============================================================================
# N8N Webhook Handler
# ============================================================================

class N8NWebhookHandler:
    """Handles N8N webhook requests."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.execution_logs: Dict[str, WebhookExecutionLog] = {}
        logger.info("N8N webhook handler initialized")
    
    def validate_request(
        self,
        headers: Dict[str, str],
        auth_header: Optional[str] = None
    ) -> bool:
        """Validate webhook request."""
        if not self.api_key:
            return True
        
        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                return token == self.api_key
        
        return headers.get("X-API-Key") == self.api_key
    
    async def handle_webhook(
        self,
        request_data: N8NWorkflowInput,
        handler_func: Any
    ) -> N8NWebhookResponse:
        """
        Handle incoming webhook.
        
        Args:
            request_data: Webhook input data
            handler_func: Async function to handle the webhook
        
        Returns:
            Webhook response
        """
        start_time = datetime.now(timezone.utc)
        execution_id = request_data.execution_id or f"exec_{hash(str(start_time))}"
        
        logger.info(
            f"[WEBHOOK] Received: workflow={request_data.workflow_id}, "
            f"trigger={request_data.trigger_name}, "
            f"execution={execution_id}"
        )
        
        try:
            # Call handler function
            results = await handler_func(request_data)
            
            response = N8NWebhookResponse(
                success=True,
                execution_id=execution_id,
                workflow_id=request_data.workflow_id,
                trigger_name=request_data.trigger_name,
                status="completed",
                message="Workflow executed successfully",
                results=results
            )
            
            # Log execution
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_entry = WebhookExecutionLog(
                webhook_id=f"wh_{hash(request_data.workflow_id)}",
                execution_id=execution_id,
                workflow_id=request_data.workflow_id,
                trigger_name=request_data.trigger_name,
                status="completed",
                request_data=request_data.to_dict(),
                response_data=response.to_dict(),
                duration_ms=duration_ms
            )
            self.execution_logs[execution_id] = log_entry
            
            logger.info(
                f"[WEBHOOK] Completed: execution={execution_id}, "
                f"duration={duration_ms:.0f}ms"
            )
            
            return response
        
        except Exception as e:
            logger.error(f"[WEBHOOK] Error: {str(e)}")
            
            response = N8NWebhookResponse(
                success=False,
                execution_id=execution_id,
                workflow_id=request_data.workflow_id,
                trigger_name=request_data.trigger_name,
                status="failed",
                message=f"Workflow execution failed: {str(e)}",
                errors=[{"error": str(e), "type": type(e).__name__}]
            )
            
            # Log failure
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_entry = WebhookExecutionLog(
                webhook_id=f"wh_{hash(request_data.workflow_id)}",
                execution_id=execution_id,
                workflow_id=request_data.workflow_id,
                trigger_name=request_data.trigger_name,
                status="failed",
                request_data=request_data.to_dict(),
                response_data=response.to_dict(),
                error=str(e),
                duration_ms=duration_ms
            )
            self.execution_logs[execution_id] = log_entry
            
            return response
    
    def get_execution_log(self, execution_id: str) -> Optional[WebhookExecutionLog]:
        """Get execution log."""
        return self.execution_logs.get(execution_id)
    
    def get_workflow_logs(self, workflow_id: str) -> List[WebhookExecutionLog]:
        """Get logs for a workflow."""
        return [
            log for log in self.execution_logs.values()
            if log.workflow_id == workflow_id
        ]


# ============================================================================
# N8N Workflow Definitions
# ============================================================================

class N8NWorkflowDefinition:
    """Define N8N workflow compatibility."""
    
    def __init__(
        self,
        workflow_id: str,
        trigger_name: str,
        webhook_url: str,
        required_fields: List[str],
        response_schema: Dict[str, str]
    ):
        self.workflow_id = workflow_id
        self.trigger_name = trigger_name
        self.webhook_url = webhook_url
        self.required_fields = required_fields
        self.response_schema = response_schema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "trigger_name": self.trigger_name,
            "webhook_url": self.webhook_url,
            "required_fields": self.required_fields,
            "response_schema": self.response_schema
        }


# ============================================================================
# Standard N8N Workflows for Platform
# ============================================================================

def get_employee_onboarding_webhook_definition() -> N8NWorkflowDefinition:
    """Define employee onboarding N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_employee_onboarding",
        trigger_name="employee_created",
        webhook_url="/webhooks/n8n/onboarding",
        required_fields=[
            "employee_id",
            "employee_name",
            "employee_email",
            "department",
            "start_date"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "welcome_email_sent": "boolean",
            "orientation_scheduled": "boolean",
            "account_created": "boolean"
        }
    )


def get_recruitment_webhook_definition() -> N8NWorkflowDefinition:
    """Define recruitment N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_recruitment",
        trigger_name="candidate_applied",
        webhook_url="/webhooks/n8n/recruitment",
        required_fields=[
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "position_id",
            "resume_url"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "screening_status": "string",
            "next_steps": "string"
        }
    )


def get_payroll_webhook_definition() -> N8NWorkflowDefinition:
    """Define payroll N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_payroll",
        trigger_name="payroll_processing",
        webhook_url="/webhooks/n8n/payroll",
        required_fields=[
            "payroll_period",
            "employee_ids",
            "company_id"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "total_processed": "integer",
            "total_amount": "number",
            "failed_count": "integer"
        }
    )


def get_invoice_webhook_definition() -> N8NWorkflowDefinition:
    """Define invoice N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_invoice",
        trigger_name="invoice_created",
        webhook_url="/webhooks/n8n/invoice",
        required_fields=[
            "invoice_id",
            "client_id",
            "amount",
            "due_date"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "invoice_number": "string",
            "sent_to_client": "boolean"
        }
    )


def get_meeting_webhook_definition() -> N8NWorkflowDefinition:
    """Define meeting scheduling N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_meeting",
        trigger_name="meeting_requested",
        webhook_url="/webhooks/n8n/meeting",
        required_fields=[
            "meeting_id",
            "participants",
            "start_time",
            "duration_minutes",
            "title"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "meeting_scheduled": "boolean",
            "calendar_invite_sent": "boolean"
        }
    )


def get_sales_webhook_definition() -> N8NWorkflowDefinition:
    """Define sales lead N8N webhook."""
    return N8NWorkflowDefinition(
        workflow_id="n8n_sales",
        trigger_name="lead_generated",
        webhook_url="/webhooks/n8n/sales",
        required_fields=[
            "lead_id",
            "lead_name",
            "lead_email",
            "company_name",
            "lead_source"
        ],
        response_schema={
            "workflow_id": "string",
            "execution_id": "string",
            "status": "string",
            "lead_qualified": "boolean",
            "assigned_to": "string"
        }
    )


# ============================================================================
# N8N Workflow Registry
# ============================================================================

class N8NWorkflowRegistry:
    """Registry for N8N workflow definitions."""
    
    def __init__(self):
        self.workflows: Dict[str, N8NWorkflowDefinition] = {}
        self._register_default_workflows()
    
    def _register_default_workflows(self) -> None:
        """Register all platform workflows."""
        workflows = [
            get_employee_onboarding_webhook_definition(),
            get_recruitment_webhook_definition(),
            get_payroll_webhook_definition(),
            get_invoice_webhook_definition(),
            get_meeting_webhook_definition(),
            get_sales_webhook_definition()
        ]
        
        for workflow in workflows:
            self.register(workflow)
    
    def register(self, workflow: N8NWorkflowDefinition) -> None:
        """Register a workflow."""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"[N8N] Workflow registered: {workflow.workflow_id}")
    
    def get(self, workflow_id: str) -> Optional[N8NWorkflowDefinition]:
        """Get workflow definition."""
        return self.workflows.get(workflow_id)
    
    def list_all(self) -> List[N8NWorkflowDefinition]:
        """List all workflows."""
        return list(self.workflows.values())
    
    def get_webhook_urls(self) -> Dict[str, str]:
        """Get all webhook URLs."""
        return {
            wf.workflow_id: wf.webhook_url
            for wf in self.workflows.values()
        }
    
    def validate_webhook_input(
        self,
        workflow_id: str,
        data: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate webhook input against workflow schema.
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        workflow = self.get(workflow_id)
        if not workflow:
            return False, ["Workflow not found"]
        
        missing_fields = [
            field for field in workflow.required_fields
            if field not in data
        ]
        
        return len(missing_fields) == 0, missing_fields
