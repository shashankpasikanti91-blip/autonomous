"""
Enhanced sample workflows with full Pydantic AI reasoning chains and agent orchestration.
These workflows demonstrate:
- Complex agent reasoning and planning
- Multi-step tool orchestration
- Memory integration for context awareness
- Error handling and recovery strategies
- Task prioritization and delegation
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from core.models import (
    WorkflowDefinition, WorkflowStepDefinition, ToolExecutionRequest,
    ToolType, ToolInput, AgentRole
)
from core.tools.implementations import (
    EmailSenderTool, CalendarSchedulerTool, InvoiceGeneratorTool, N8NWebhookTool
)


def create_enhanced_employee_onboarding_workflow() -> WorkflowDefinition:
    """
    Enhanced Employee Onboarding Workflow with Coordinator orchestration.
    
    Process:
    1. Coordinator: Analyzes onboarding requirements and creates comprehensive plan
    2. Executor: Sends welcome email (high priority)
    3. Executor: Schedules orientation meeting (high priority)
    4. Executor: Generates IT setup invoice (medium priority)
    5. Executor: Triggers account creation webhook (high priority)
    6. Analyzer: Reviews completion status and generates onboarding report
    
    Reasoning chain: The Coordinator uses reasoning to determine dependencies,
    prioritization, and resource allocation. The Executor uses reasoning to
    select optimal tools for each task. The Analyzer reviews outcomes.
    """
    
    # Step 1: Coordinator orchestration and planning
    step_1 = WorkflowStepDefinition(
        id="step_1_coordinator_planning",
        name="Orchestrate Onboarding Process",
        description="Coordinator analyzes requirements and creates execution plan",
        agent_id="coordinator_1",
        conditions={
            "required_fields": ["employee_name", "employee_email", "department"]
        },
        next_steps=["step_2_send_welcome"]
    )
    
    # Step 2: Send welcome email
    step_2 = WorkflowStepDefinition(
        id="step_2_send_welcome",
        name="Send Welcome Email",
        description="Send personalized welcome email to new employee",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "${employee_email}",
                    "subject": "Welcome to ${company_name}! Your Adventure Starts Now",
                    "body": """Dear ${employee_name},

Welcome to our team! We're thrilled to have you join us and excited to work together.

Your onboarding process begins on ${start_date}. Over the next few days, you'll:
- Meet the team
- Get set up with company systems
- Attend orientation sessions
- Start your first projects

Our HR team will be in touch shortly with all the details.

Looking forward to great things ahead!

Best regards,
Human Resources Team""",
                    "cc": ["hr@company.com", "manager@company.com"]
                }
            )
        ],
        next_steps=["step_3_schedule_orientation"]
    )
    
    # Step 3: Schedule orientation
    step_3 = WorkflowStepDefinition(
        id="step_3_schedule_orientation",
        name="Schedule Orientation Meeting",
        description="Schedule comprehensive orientation meeting with HR",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="calendar_scheduler",
                inputs={
                    "title": "New Employee Orientation - ${employee_name}",
                    "start_time": "${orientation_start_time}",
                    "end_time": "${orientation_end_time}",
                    "attendees": ["${employee_email}", "hr@company.com", "manager@company.com"],
                    "description": """Comprehensive orientation covering:
- Company culture and values
- Office tours and facilities
- Systems and tools training
- HR policies and benefits
- Team introductions
- First day logistics""",
                    "location": "Conference Room A"
                }
            )
        ],
        next_steps=["step_4_generate_it_invoice"]
    )
    
    # Step 4: Generate IT setup costs invoice
    step_4 = WorkflowStepDefinition(
        id="step_4_generate_it_invoice",
        name="Generate IT Setup Invoice",
        description="Create invoice for IT setup and equipment costs",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="invoice_generator",
                inputs={
                    "client_name": "${employee_name}",
                    "description": "New Employee IT Setup",
                    "amount": 1200.00,
                    "due_date": "${due_date}",
                    "items": [
                        {
                            "description": "Laptop (Dell XPS 13)",
                            "quantity": 1,
                            "unit_price": 600.00,
                            "cost": 600.00
                        },
                        {
                            "description": "Monitor and Peripherals",
                            "quantity": 1,
                            "unit_price": 300.00,
                            "cost": 300.00
                        },
                        {
                            "description": "Software Licenses (Annual)",
                            "quantity": 1,
                            "unit_price": 300.00,
                            "cost": 300.00
                        }
                    ],
                    "send_email": False
                }
            )
        ],
        next_steps=["step_5_trigger_account_creation"]
    )
    
    # Step 5: Trigger N8N webhook for account creation
    step_5 = WorkflowStepDefinition(
        id="step_5_trigger_account_creation",
        name="Trigger Account Creation Workflow",
        description="Trigger N8N workflow for system account provisioning",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="n8n_webhook",
                inputs={
                    "workflow_id": "employee_account_creation",
                    "trigger_name": "onboarding_webhook",
                    "payload": {
                        "employee_id": "${employee_id}",
                        "employee_email": "${employee_email}",
                        "employee_name": "${employee_name}",
                        "department": "${department}",
                        "manager_email": "${manager_email}",
                        "start_date": "${start_date}",
                        "access_level": "standard",
                        "systems_to_provision": [
                            "email",
                            "slack",
                            "github",
                            "jira",
                            "office365"
                        ]
                    }
                }
            )
        ],
        next_steps=["step_6_analyze_completion"]
    )
    
    # Step 6: Analyzer reviews completion
    step_6 = WorkflowStepDefinition(
        id="step_6_analyze_completion",
        name="Review Onboarding Status",
        description="Analyzer verifies all onboarding tasks completed successfully",
        agent_id="analyzer_1",
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_enhanced_employee_onboarding",
        name="Enhanced Employee Onboarding",
        description="Multi-agent orchestrated employee onboarding with reasoning chains",
        steps=[step_1, step_2, step_3, step_4, step_5, step_6],
        entry_point="step_1_coordinator_planning",
        agents=["coordinator_1", "executor_1", "analyzer_1"],
        timeout=7200,  # 2 hours
        metadata={
            "category": "HR",
            "complexity": "high",
            "requires_approval": True,
            "sla_minutes": 120,
            "success_metrics": [
                "welcome_email_sent",
                "orientation_scheduled",
                "it_setup_provisioned",
                "accounts_created"
            ],
            "risk_factors": [
                "email_delivery_failure",
                "calendar_conflict",
                "account_provisioning_delay"
            ],
            "estimated_duration_minutes": 60
        }
    )


def create_enhanced_meeting_scheduling_workflow() -> WorkflowDefinition:
    """
    Enhanced Meeting Scheduling Workflow with Planner and Coordinator.
    
    Process:
    1. Planner: Analyzes meeting requirements and optimal timing
    2. Coordinator: Delegates to executor with context
    3. Executor: Books calendar and processes scheduling
    4. Executor: Sends confirmations with advanced details
    
    Reasoning: Planner determines best time slots considering attendee zones,
    availability patterns, and room booking. Coordinator orchestrates execution.
    """
    
    # Step 1: Planner determines optimal meeting time
    step_1 = WorkflowStepDefinition(
        id="step_1_planner_determine_time",
        name="Determine Optimal Meeting Time",
        description="Planner analyzes tzones and availability for best meeting time",
        agent_id="planner_1",
        conditions={
            "required_fields": ["attendees", "duration_minutes"],
            "constraints": ["no_early_morning", "no_late_evening"]
        },
        next_steps=["step_2_coordinator_prep"]
    )
    
    # Step 2: Coordinator prepares execution
    step_2 = WorkflowStepDefinition(
        id="step_2_coordinator_prep",
        name="Prepare Meeting Execution Plan",
        description="Coordinator verifies resources and creates execution plan",
        agent_id="coordinator_1",
        next_steps=["step_3_schedule_meeting"]
    )
    
    # Step 3: Schedule meeting
    step_3 = WorkflowStepDefinition(
        id="step_3_schedule_meeting",
        name="Schedule Meeting on Calendar",
        description="Executor reserves calendar slot and books conference room",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="calendar_scheduler",
                inputs={
                    "title": "${meeting_title}",
                    "start_time": "${optimal_start_time}",
                    "end_time": "${optimal_end_time}",
                    "attendees": "${attendees_list}",
                    "description": """${meeting_title}

Agenda:
${agenda_items}

Preparation:
- Review materials: ${materials_link}
- Dial-in: ${dial_in_info}
- Location: ${room_location}

Questions? Contact: ${organizer_email}""",
                    "location": "${room_location}",
                    "attach_materials": True,
                    "send_calendar_invites": True
                }
            )
        ],
        next_steps=["step_4_send_summary"]
    )
    
    # Step 4: Send meeting summary
    step_4 = WorkflowStepDefinition(
        id="step_4_send_summary",
        name="Send Meeting Summary",
        description="Executor sends detailed meeting summary and logistics to attendees",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "${attendees_list_comma}",
                    "subject": "Confirmed: ${meeting_title} - ${date_display}",
                    "body": """Hi Team,

Your meeting is confirmed!

📅 Date & Time: ${date_display} at ${time_display}
⏱️ Duration: ${duration_minutes} minutes
📍 Location: ${room_location}
🔗 Dial-in: ${dial_in_info}

Attendees (${attendee_count}):
${attendees_formatted}

Agenda:
${agenda_items}

Materials:
${materials_link}

Please confirm your attendance by replying to this email.

See you there!

${organizer_name}
${organizer_title}""",
                    "schedule_send_time": "${one_day_before}"
                }
            )
        ],
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_enhanced_meeting_scheduling",
        name="Enhanced Meeting Scheduling",
        description="Intelligent meeting scheduling with planner optimization",
        steps=[step_1, step_2, step_3, step_4],
        entry_point="step_1_planner_determine_time",
        agents=["planner_1", "coordinator_1", "executor_1"],
        timeout=1800,  # 30 minutes
        metadata={
            "category": "Calendar",
            "complexity": "medium",
            "requires_approval": False,
            "sla_minutes": 30,
            "success_metrics": [
                "calendar_slot_booked",
                "room_reserved",
                "invites_sent",
                "confirmations_received"
            ],
            "considerations": [
                "timezone_awareness",
                "room_availability",
                "attendee_preferences",
                "meeting_room_capacity"
            ],
            "estimated_duration_minutes": 15
        }
    )


def create_enhanced_invoice_processing_workflow() -> WorkflowDefinition:
    """
    Enhanced Invoice Processing Workflow with full reasoning.
    
    Process:
    1. Analyzer: Validates invoice data and checks for anomalies
    2. Planner: Creates processing and payment plan
    3. Executor: Generates professional invoice
    4. Executor: Sends invoice to client with payment terms
    5. Executor: Triggers payment tracking workflow via N8N
    6. Analyzer: Reviews payment status and reconciliation
    
    Reasoning: Analyzer validates data quality, Planner determines payment terms
    and due dates based on client history. Executor processes and sends.
    """
    
    # Step 1: Analyzer validates invoice data
    step_1 = WorkflowStepDefinition(
        id="step_1_analyzer_validate",
        name="Validate Invoice Data",
        description="Analyzer checks invoice accuracy and identifies anomalies",
        agent_id="analyzer_1",
        conditions={
            "validation_rules": [
                "client_exists",
                "amount_positive",
                "items_non_empty",
                "tax_calculation_correct"
            ]
        },
        next_steps=["step_2_planner_payment_terms"]
    )
    
    # Step 2: Planner determines payment plan
    step_2 = WorkflowStepDefinition(
        id="step_2_planner_payment_terms",
        name="Determine Payment Terms",
        description="Planner establishes payment schedule based on client history",
        agent_id="planner_1",
        conditions={
            "factors": [
                "client_payment_history",
                "invoice_amount",
                "company_policy",
                "industry_standards"
            ]
        },
        next_steps=["step_3_executor_generate"]
    )
    
    # Step 3: Generate professional invoice
    step_3 = WorkflowStepDefinition(
        id="step_3_executor_generate",
        name="Generate Professional Invoice",
        description="Executor creates formatted invoice document",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="invoice_generator",
                inputs={
                    "invoice_number": "${invoice_number}",
                    "client_name": "${client_name}",
                    "client_email": "${client_email}",
                    "client_address": "${client_address}",
                    "invoice_date": "${invoice_date}",
                    "due_date": "${due_date}",
                    "payment_terms": "${payment_terms}",
                    "items": "${invoice_items}",
                    "subtotal": "${subtotal}",
                    "tax_rate": "${tax_rate}",
                    "tax_amount": "${tax_amount}",
                    "total_amount": "${total_amount}",
                    "notes": "${invoice_notes}",
                    "payment_instructions": {
                        "bank_details": "${bank_details}",
                        "payment_methods": ["wire_transfer", "credit_card", "ach"],
                        "early_payment_discount": 2.0  # 2% discount for early payment
                    },
                    "company_logo_url": "${company_logo}",
                    "send_email": False,
                    "pdf_format": True
                }
            )
        ],
        next_steps=["step_4_executor_send_invoice"]
    )
    
    # Step 4: Send invoice to client
    step_4 = WorkflowStepDefinition(
        id="step_4_executor_send_invoice",
        name="Send Invoice to Client",
        description="Executor emails professional invoice to client contact",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "${client_email}",
                    "cc": ["accounting@company.com"],
                    "subject": "Invoice #${invoice_number} from ${company_name}",
                    "body": """Dear ${client_contact},

Please find attached Invoice #${invoice_number} for services rendered.

Invoice Details:
─────────────────────
Date: ${invoice_date}
Due: ${due_date} (${payment_terms})
Amount: ${currency} ${total_amount}

Summary:
${line_items_summary}

Total Due: ${total_amount}

Payment Instructions:
${payment_instructions}

Early Payment Discount: 2% off if paid by ${early_payment_date}

Questions? Contact:
${accounting_contact}
${accounting_email}

Thank you for your business!

${company_name}
${company_contact}""",
                    "attach_file": "${invoice_pdf_path}",
                    "priority": "high"
                }
            )
        ],
        next_steps=["step_5_executor_trigger_tracking"]
    )
    
    # Step 5: Trigger payment tracking
    step_5 = WorkflowStepDefinition(
        id="step_5_executor_trigger_tracking",
        name="Trigger Payment Tracking",
        description="Executor triggers N8N workflow for payment monitoring",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="n8n_webhook",
                inputs={
                    "workflow_id": "invoice_payment_tracking",
                    "trigger_name": "new_invoice_tracking",
                    "payload": {
                        "invoice_id": "${invoice_id}",
                        "invoice_number": "${invoice_number}",
                        "client_name": "${client_name}",
                        "client_email": "${client_email}",
                        "invoice_amount": "${total_amount}",
                        "currency": "${currency}",
                        "due_date": "${due_date}",
                        "issued_date": "${invoice_date}",
                        "payment_terms": "${payment_terms}",
                        "reminder_schedule": [
                            "7_days_before_due",
                            "due_date",
                            "3_days_after_due",
                            "7_days_after_due"
                        ],
                        "escalation_enabled": True,
                        "callback_url": "${company_webhook_url}",
                        "tags": [
                            "${client_name}",
                            "invoice",
                            "tracking",
                            "${invoice_year}-${invoice_quarter}"
                        ]
                    }
                }
            )
        ],
        next_steps=["step_6_analyzer_reconcile"]
    )
    
    # Step 6: Analyzer reviews payment tracking
    step_6 = WorkflowStepDefinition(
        id="step_6_analyzer_reconcile",
        name="Review Payment Tracking Setup",
        description="Analyzer confirms payment tracking activated and data recorded",
        agent_id="analyzer_1",
        next_steps=[]
    )
    
    return WorkflowDefinition(
        id="workflow_enhanced_invoice_processing",
        name="Enhanced Invoice Processing",
        description="Intelligent invoice processing with payment tracking orchestration",
        steps=[step_1, step_2, step_3, step_4, step_5, step_6],
        entry_point="step_1_analyzer_validate",
        agents=["analyzer_1", "planner_1", "executor_1"],
        timeout=3600,  # 1 hour
        metadata={
            "category": "Finance & Billing",
            "complexity": "high",
            "requires_approval": True,
            "sla_minutes": 60,
            "success_metrics": [
                "data_validated",
                "invoice_generated",
                "client_notified",
                "payment_tracking_active",
                "payment_received"
            ],
            "compliance_requirements": [
                "audit_trail",
                "encryption",
                "data_retention",
                "payment_reconciliation"
            ],
            "risk_factors": [
                "payment_non_receipt",
                "data_quality_issues",
                "late_payment",
                "failed_reminders"
            ],
            "estimated_duration_minutes": 45
        }
    )


def create_enhanced_workflows_map() -> Dict[str, WorkflowDefinition]:
    """Create and return all enhanced sample workflows."""
    return {
        "enhanced_employee_onboarding": create_enhanced_employee_onboarding_workflow(),
        "enhanced_meeting_scheduling": create_enhanced_meeting_scheduling_workflow(),
        "enhanced_invoice_processing": create_enhanced_invoice_processing_workflow(),
    }


# Example context data for workflow execution with reasoning requirements
ENHANCED_WORKFLOW_EXECUTION_CONTEXTS = {
    "enhanced_employee_onboarding": {
        "task": "Onboard new software engineer",
        "objective": "Complete comprehensive employee onboarding",
        "requirements": ["email_send", "calendar_schedule", "invoice_generate", "account_provision"],
        "context": {
            "employee_id": "EMP-2024-001",
            "employee_name": "Sarah Chen",
            "employee_email": "sarah.chen@company.com",
            "department": "Engineering",
            "start_date": "2024-02-26",
            "manager_email": "manager@company.com",
            "company_name": "TechCorp Inc.",
            "orientation_start_time": "2024-02-26T09:00:00Z",
            "orientation_end_time": "2024-02-26T11:00:00Z",
            "due_date": "2024-03-31"
        },
        "risk_factors": ["email_delivery_failure", "calendar_conflict", "account_provisioning_delay"],
        "agents": ["coordinator_1", "executor_1", "analyzer_1"]
    },
    "enhanced_meeting_scheduling": {
        "task": "Schedule quarterly business review",
        "objective": "Coordinate meeting across multiple timezones",
        "requirements": ["calendar_schedule", "email_send"],
        "context": {
            "meeting_title": "Q1 2024 Business Review",
            "attendees": [
                "alice@company.com",
                "bob@company.com",
                "charlie@company.com"
            ],
            "attendees_list_comma": "alice@company.com, bob@company.com, charlie@company.com",
            "duration_minutes": 90,
            "room_location": "Conference Room A",
            "dial_in_info": "Zoom: https://zoom.us/meeting/123456",
            "agenda_items": """1. Q1 Performance Review (30 min)
2. Q2 Planning (40 min)
3. Action Items & Close (20 min)""",
            "materials_link": "https://company.share/qbr-materials",
            "organizer_email": "ceo@company.com",
            "organizer_name": "Jane Smith",
            "organizer_title": "CEO",
            "attendee_count": 3,
            "date_display": "Monday, Feb 26, 2024",
            "time_display": "10:00 AM UTC"
        },
        "constraints": ["no_early_morning", "no_late_evening"],
        "agents": ["planner_1", "coordinator_1", "executor_1"]
    },
    "enhanced_invoice_processing": {
        "task": "Process Q1 project invoice",
        "objective": "Generate and send professional invoice with payment tracking",
        "requirements": ["invoice_generate", "email_send", "webhook_trigger"],
        "context": {
            "invoice_id": "INV-2024-001",
            "invoice_number": "2024-001",
            "client_name": "Acme Corporation",
            "client_email": "billing@acme.com",
            "client_address": "123 Business Ave, New York, NY 10001",
            "client_contact": "Finance Manager",
            "company_name": "TechCorp Consulting",
            "accounting_contact": "John Doe",
            "accounting_email": "accounts@techcorp.com",
            "company_webhook_url": "https://api.techcorp.com/webhooks/payments",
            "currency": "USD",
            "invoice_date": "2024-02-15",
            "due_date": "2024-03-15",
            "payment_terms": "Net 30",
            "invoice_year": 2024,
            "invoice_quarter": "Q1",
            "subtotal": 10000.00,
            "tax_rate": 0.10,
            "tax_amount": 1000.00,
            "total_amount": 11000.00,
            "early_payment_date": "2024-02-29",
            "invoice_notes": "Thank you for your business",
            "company_logo": "https://company.com/logo.png",
            "invoice_items": [
                {
                    "description": "Development Services - 160 hours",
                    "quantity": 160,
                    "unit_price": 50.00,
                    "cost": 8000.00
                },
                {
                    "description": "Project Management",
                    "quantity": 1,
                    "unit_price": 2000.00,
                    "cost": 2000.00
                }
            ],
            "line_items_summary": "Development Services (160 hrs @ $50/hr): $8,000\nProject Management: $2,000",
            "payment_instructions": """Bank: First National Bank
Account: 1234567890
Routing: 123456789
SWIFT: FNBAUS33

or submit online at: https://company.com/pay""",
            "bank_details": {
                "bank_name": "First National Bank",
                "account_number": "1234567890",
                "routing_number": "123456789",
                "swift_code": "FNBAUS33"
            }
        },
        "validation_rules": ["client_exists", "amount_positive", "items_non_empty"],
        "factors": ["client_payment_history", "invoice_amount", "company_policy"],
        "agents": ["analyzer_1", "planner_1", "executor_1"]
    }
}


# Reasoning context templates for agent decision making
AGENT_REASONING_TEMPLATES = {
    "coordinator": {
        "required_capabilities": ["orchestration", "delegation", "risk_assessment"],
        "dependencies": [],
        "priority_scores": {
            "workflow_coordination": 0.95,
            "resource_allocation": 0.85,
            "error_handling": 0.90
        }
    },
    "executor": {
        "required_capabilities": ["tool_execution", "error_recovery"],
        "dependencies": ["coordinator_decision"],
        "priority_scores": {
            "task_execution": 0.90,
            "reliability": 0.95,
            "speed": 0.80
        }
    },
    "analyzer": {
        "required_capabilities": ["data_analysis", "pattern_recognition"],
        "dependencies": ["executor_completion"],
        "priority_scores": {
            "accuracy": 0.98,
            "insight_generation": 0.85,
            "compliance": 0.90
        }
    },
    "planner": {
        "required_capabilities": ["strategic_planning", "resource_optimization"],
        "dependencies": [],
        "priority_scores": {
            "planning_quality": 0.92,
            "risk_mitigation": 0.88,
            "efficiency": 0.85
        }
    }
}

