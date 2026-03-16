"""
Sample workflows demonstrating agent execution with tool usage and memory interaction.
"""
from typing import Dict, Any
from core.models import (
    WorkflowDefinition, WorkflowStepDefinition, ToolExecutionRequest,
    ToolType, ToolInput
)
from core.tools.implementations import (
    EmailSenderTool, CalendarSchedulerTool, InvoiceGeneratorTool, N8NWebhookTool
)


def create_employee_onboarding_workflow() -> WorkflowDefinition:
    """
    Sample workflow: Automated employee onboarding process.
    
    Steps:
    1. Send welcome email
    2. Schedule orientation meeting
    3. Generate access credentials invoice
    4. Trigger N8N workflow for account creation
    """
    
    step_1 = WorkflowStepDefinition(
        id="step_1_send_welcome",
        name="Send Welcome Email",
        description="Send welcome email to new employee",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "new_employee@example.com",
                    "subject": "Welcome to our company!",
                    "body": "We're excited to have you on board. Your onboarding begins tomorrow.",
                    "cc": ["hr@example.com"]
                }
            )
        ],
        next_steps=["step_2_schedule_orientation"]
    )
    
    step_2 = WorkflowStepDefinition(
        id="step_2_schedule_orientation",
        name="Schedule Orientation",
        description="Schedule orientation meeting with HR",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="calendar_scheduler",
                inputs={
                    "title": "Employee Orientation",
                    "start_time": "2024-02-25T09:00:00Z",
                    "end_time": "2024-02-25T11:00:00Z",
                    "attendees": ["new_employee@example.com", "hr@example.com"],
                    "description": "Introduction to company policies and systems"
                }
            )
        ],
        next_steps=["step_3_generate_credentials_invoice"]
    )
    
    step_3 = WorkflowStepDefinition(
        id="step_3_generate_credentials_invoice",
        name="Generate Onboarding Invoice",
        description="Generate invoice for IT setup costs",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="invoice_generator",
                inputs={
                    "client_name": "New Employee",
                    "amount": 500.00,
                    "due_date": "2024-03-10",
                    "items": [
                        {"description": "Laptop Setup", "cost": 300},
                        {"description": "Software Licenses", "cost": 200}
                    ],
                    "send_email": True
                }
            )
        ],
        next_steps=["step_4_trigger_account_creation"]
    )
    
    step_4 = WorkflowStepDefinition(
        id="step_4_trigger_account_creation",
        name="Trigger Account Creation",
        description="Trigger N8N workflow for system account creation",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="n8n_webhook",
                inputs={
                    "workflow_id": "employee_account_creation",
                    "payload": {
                        "employee_email": "new_employee@example.com",
                        "employee_name": "New Employee",
                        "department": "Engineering"
                    }
                }
            )
        ],
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_employee_onboarding",
        name="Employee Onboarding",
        description="Automated employee onboarding workflow",
        steps=[step_1, step_2, step_3, step_4],
        entry_point="step_1_send_welcome",
        agents=["executor_1"],
        timeout=3600,
        metadata={
            "category": "HR",
            "complexity": "medium",
            "requires_approval": False
        }
    )


def create_meeting_scheduling_workflow() -> WorkflowDefinition:
    """
    Sample workflow: Automated meeting scheduling with confirmations.
    
    Steps:
    1. Coordinator analyzes meeting requirements
    2. Executor schedules meeting
    3. Send confirmation emails
    """
    
    step_1 = WorkflowStepDefinition(
        id="step_1_analyze_requirements",
        name="Analyze Meeting Requirements",
        description="Analyze and plan meeting details",
        agent_id="coordinator_1",
        next_steps=["step_2_schedule"]
    )
    
    step_2 = WorkflowStepDefinition(
        id="step_2_schedule",
        name="Schedule Meeting",
        description="Schedule the meeting",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="calendar_scheduler",
                inputs={
                    "title": "Team Sync Meeting",
                    "start_time": "2024-02-26T14:00:00Z",
                    "end_time": "2024-02-26T15:00:00Z",
                    "attendees": ["team@example.com"],
                    "description": "Weekly team synchronization"
                }
            )
        ],
        next_steps=["step_3_send_confirmations"]
    )
    
    step_3 = WorkflowStepDefinition(
        id="step_3_send_confirmations",
        name="Send Confirmations",
        description="Send confirmation emails to attendees",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "team@example.com",
                    "subject": "Meeting Confirmation: Team Sync",
                    "body": "Your meeting has been scheduled for Feb 26, 2024 at 2:00 PM UTC"
                }
            )
        ],
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_meeting_scheduling",
        name="Meeting Scheduling",
        description="Automated meeting scheduling with confirmations",
        steps=[step_1, step_2, step_3],
        entry_point="step_1_analyze_requirements",
        agents=["coordinator_1", "executor_1"],
        timeout=1800,
        metadata={
            "category": "Calendar",
            "complexity": "low",
            "requires_approval": False
        }
    )


def create_invoice_processing_workflow() -> WorkflowDefinition:
    """
    Sample workflow: Automated invoice generation and sending.
    
    Steps:
    1. Analyze invoice requirements
    2. Generate invoice
    3. Send invoice to client
    4. Trigger payment workflow
    """
    
    step_1 = WorkflowStepDefinition(
        id="step_1_analyze_invoice",
        name="Analyze Invoice Requirements",
        description="Analyze and prepare invoice data",
        agent_id="analyzer",  # TODO: Would be created in full implementation
        next_steps=["step_2_generate"]
    )
    
    step_2 = WorkflowStepDefinition(
        id="step_2_generate",
        name="Generate Invoice",
        description="Generate invoice document",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="invoice_generator",
                inputs={
                    "client_name": "Client Corporation",
                    "amount": 5000.00,
                    "due_date": "2024-03-31",
                    "items": [
                        {"description": "Professional Services", "cost": 3000},
                        {"description": "Consulting", "cost": 2000}
                    ]
                }
            )
        ],
        next_steps=["step_3_send_invoice"]
    )
    
    step_3 = WorkflowStepDefinition(
        id="step_3_send_invoice",
        name="Send Invoice",
        description="Email invoice to client",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "finance@client.com",
                    "subject": "Invoice - Professional Services",
                    "body": "Please find attached the invoice for our services. Payment is due by March 31, 2024."
                }
            )
        ],
        next_steps=["step_4_trigger_payment"]
    )
    
    step_4 = WorkflowStepDefinition(
        id="step_4_trigger_payment",
        name="Trigger Payment Workflow",
        description="Send to N8N for payment processing",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="n8n_webhook",
                inputs={
                    "workflow_id": "invoice_payment_tracking",
                    "payload": {
                        "invoice_amount": 5000.00,
                        "client_name": "Client Corporation",
                        "due_date": "2024-03-31"
                    }
                }
            )
        ],
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_invoice_processing",
        name="Invoice Processing",
        description="Automated invoice generation and sending workflow",
        steps=[step_1, step_2, step_3, step_4],
        entry_point="step_1_analyze_invoice",
        agents=["executor_1"],
        timeout=3600,
        metadata={
            "category": "Finance",
            "complexity": "medium",
            "requires_approval": True
        }
    )


def create_workflow_samples() -> Dict[str, WorkflowDefinition]:
    """Create and return all sample workflows."""
    return {
        "employee_onboarding": create_employee_onboarding_workflow(),
        "meeting_scheduling": create_meeting_scheduling_workflow(),
        "invoice_processing": create_invoice_processing_workflow(),
    }


# Example of workflow execution input data
WORKFLOW_EXECUTION_EXAMPLES = {
    "employee_onboarding": {
        "task": "Onboard new employee",
        "objective": "Complete employee onboarding process",
        "employee_name": "John Doe",
        "employee_email": "john.doe@company.com",
        "department": "Engineering",
        "start_date": "2024-02-25"
    },
    "meeting_scheduling": {
        "task": "Schedule team meeting",
        "objective": "Coordinate team meeting",
        "meeting_title": "Weekly Sync",
        "attendees": ["alice@company.com", "bob@company.com"],
        "duration_minutes": 60
    },
    "invoice_processing": {
        "task": "Process invoice",
        "objective": "Generate and send invoice",
        "client_name": "Acme Corp",
        "client_email": "billing@acme.com",
        "project": "Q1 2024 Project",
        "total_amount": 5000.00
    }
}
