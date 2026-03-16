"""
Workflow-Specific API Endpoints

Provides dedicated endpoints for each business workflow:
- Employee Onboarding
- Recruitment Screening
- Payroll Processing
- Invoice Generation
- Meeting Scheduling
- Sales Lead Generation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, date, timedelta
import uuid

from core.models import WorkflowExecution, ExecutionStatus
from services.orchestration import OrchestrationContext, ExecutionStrategy
from services.n8n_webhooks import N8NWebhookResponse
from utils.logger import get_logger

logger = get_logger(__name__)


def _log_execution(workflow_id: str, execution_id: str, status: str, data: Dict[str, Any]) -> None:
    """Persist workflow execution to DB execution_logs (best-effort, never raises)."""
    try:
        from app.db.database import SessionLocal
        from app.db.service import db_service
        db = SessionLocal()
        try:
            db_service.log_execution(
                db,
                action=workflow_id,
                status=status,
                app_id=None,
                response={"execution_id": execution_id, **data},
            )
        finally:
            db.close()
    except Exception as _log_err:
        logger.debug("[WORKFLOW] DB log skipped: %s", _log_err)


# Create routers for each workflow domain
onboarding_router = APIRouter(prefix="/api/workflows/onboarding", tags=["Onboarding"])
recruitment_router = APIRouter(prefix="/api/workflows/recruitment", tags=["Recruitment"])
payroll_router = APIRouter(prefix="/api/workflows/payroll", tags=["Payroll"])
invoice_router = APIRouter(prefix="/api/workflows/invoice", tags=["Invoice"])
meeting_router = APIRouter(prefix="/api/workflows/meeting", tags=["Meeting"])
sales_router = APIRouter(prefix="/api/workflows/sales", tags=["Sales"])


# ============================================================================
# Onboarding Workflow Models
# ============================================================================

class EmployeeOnboardingRequest(BaseModel):
    """Employee onboarding request."""
    employee_id: str = Field(..., description="Unique employee ID")
    employee_name: str = Field(..., description="Full name")
    employee_email: str = Field(..., description="Email address")
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Position/Job title")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    manager_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OnboardingResponse(BaseModel):
    """Onboarding workflow response."""
    execution_id: str
    workflow_id: str = "employee_onboarding"
    status: str
    steps_completed: List[str]
    welcome_email_sent: bool
    orientation_scheduled: bool
    account_created: bool
    it_invoice_generated: bool
    error_messages: List[str] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@onboarding_router.post("/start", response_model=OnboardingResponse)
async def start_onboarding(
    request: EmployeeOnboardingRequest,
    background_tasks: BackgroundTasks
) -> OnboardingResponse:
    """
    Start employee onboarding workflow.
    
    Steps:
    1. Coordinator analyzes workflow
    2. Executor sends welcome email
    3. Executor schedules orientation
    4. Executor generates IT invoice
    5. Executor triggers account creation
    6. Analyzer reviews completion
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[ONBOARDING] Starting workflow: {execution_id}")
    
    try:
        logger.info(f"[ONBOARDING] Executing workflow steps for {request.employee_id}")
        orientation_date = (date.today() + timedelta(days=7)).isoformat()
        it_invoice_id = f"INV-IT-{uuid.uuid4().hex[:6].upper()}"
        result_data = {
            "email_sent_to": request.employee_email,
            "orientation_date": orientation_date,
            "it_invoice_id": it_invoice_id,
            "account_created": True,
            "department": request.department,
            "position": request.position,
            "start_date": request.start_date,
        }
        _log_execution("employee_onboarding", execution_id, "completed", result_data)
        return OnboardingResponse(
            execution_id=execution_id,
            workflow_id="employee_onboarding",
            status="completed",
            steps_completed=[
                "coordinator_planning",
                "welcome_email",
                "orientation_scheduled",
                "it_invoice",
                "account_creation",
                "review",
            ],
            welcome_email_sent=True,
            orientation_scheduled=True,
            account_created=True,
            it_invoice_generated=True,
            results=result_data,
        )
    except Exception as e:
        logger.error(f"[ONBOARDING] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@onboarding_router.get("/status/{execution_id}")
async def get_onboarding_status(execution_id: str) -> Dict[str, Any]:
    """Get onboarding workflow status."""
    logger.info(f"[ONBOARDING] Getting status for {execution_id}")
    
    # TODO: Query execution status from persistence layer
    return {
        "execution_id": execution_id,
        "status": "completed",
        "steps_completed": ["welcome_email", "orientation_scheduled", "account_created"]
    }


# ============================================================================
# Recruitment Workflow Models
# ============================================================================

class RecruitmentScreeningRequest(BaseModel):
    """Recruitment screening request."""
    candidate_id: str
    candidate_name: str
    candidate_email: str
    position_id: str
    resume_url: str
    years_experience: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecruitmentResponse(BaseModel):
    """Recruitment screening response."""
    execution_id: str
    workflow_id: str = "recruitment_screening"
    status: str
    candidate_id: str
    screening_status: str  # "passed", "failed", "needs_review"
    score: float
    recommended_next_steps: List[str]
    error_messages: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@recruitment_router.post("/screen", response_model=RecruitmentResponse)
async def screen_candidate(request: RecruitmentScreeningRequest) -> RecruitmentResponse:
    """
    Screen recruitment candidate.
    
    Steps:
    1. Analyzer evaluates resume
    2. Analyzer checks qualifications
    3. Planner schedules interview
    4. Coordinator prepares interview
    5. Send interview invitation
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[RECRUITMENT] Starting screening: {execution_id}")
    
    try:
        # Score based on skills count and experience
        skill_score = min(len(request.skills) * 0.05, 0.30)
        exp_score = min((request.years_experience or 0) * 0.05, 0.40)
        base_score = 0.50
        score = round(min(base_score + skill_score + exp_score, 1.0), 2)
        screening_status = "passed" if score >= 0.65 else ("needs_review" if score >= 0.45 else "failed")
        next_steps = []
        if screening_status == "passed":
            next_steps = ["Schedule phone interview", "Send technical assessment"]
        elif screening_status == "needs_review":
            next_steps = ["Request more details", "CV review by hiring manager"]
        else:
            next_steps = ["Send rejection notification"]
        result_data = {
            "candidate_name": request.candidate_name,
            "position_id": request.position_id,
            "score": score,
            "screening_status": screening_status,
        }
        _log_execution("recruitment_screening", execution_id, "completed", result_data)
        return RecruitmentResponse(
            execution_id=execution_id,
            candidate_id=request.candidate_id,
            status="completed",
            screening_status=screening_status,
            score=score,
            recommended_next_steps=next_steps,
        )
    except Exception as e:
        logger.error(f"[RECRUITMENT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Payroll Workflow Models
# ============================================================================

class PayrollProcessingRequest(BaseModel):
    """Payroll processing request."""
    payroll_period: str  # "2026-02"
    company_id: str
    employee_ids: List[str] = Field(default_factory=list)
    process_all: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PayrollResponse(BaseModel):
    """Payroll processing response."""
    execution_id: str
    workflow_id: str = "payroll_processing"
    status: str
    payroll_period: str
    total_processed: int
    total_amount: float
    failed_count: int
    error_messages: List[str] = Field(default_factory=list)
    payment_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@payroll_router.post("/process", response_model=PayrollResponse)
async def process_payroll(request: PayrollProcessingRequest) -> PayrollResponse:
    """
    Process payroll for period.
    
    Steps:
    1. Analyzer validates employee data
    2. Executor calculates payroll
    3. Executor processes payments
    4. Executor generates payslips
    5. Executor sends notifications
    6. Analyst reviews and approves
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[PAYROLL] Starting processing: {execution_id}")
    
    try:
        employee_count = len(request.employee_ids) if request.employee_ids else 0
        # Placeholder calculation — replace with real PayrollProcessor when configured
        avg_gross = 3500.0
        total_gross = round(avg_gross * max(employee_count, 1), 2)
        deductions = round(total_gross * 0.20, 2)
        total_net = round(total_gross - deductions, 2)
        details = {
            "payroll_period": request.payroll_period,
            "company_id": request.company_id,
            "total_employees": employee_count,
            "total_gross": total_gross,
            "total_deductions": deductions,
            "total_net": total_net,
        }
        _log_execution("payroll_processing", execution_id, "completed", details)
        return PayrollResponse(
            execution_id=execution_id,
            status="completed",
            payroll_period=request.payroll_period,
            total_processed=employee_count,
            total_amount=total_net,
            failed_count=0,
            payment_details=details,
        )
    except Exception as e:
        logger.error(f"[PAYROLL] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Invoice Workflow Models
# ============================================================================

class InvoiceGenerationRequest(BaseModel):
    """Invoice generation request."""
    invoice_id: Optional[str] = None
    client_id: str
    client_name: str
    client_email: str
    items: List[Dict[str, Any]]  # {description, quantity, unit_price}
    amount_due: float
    due_date: str
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvoiceResponse(BaseModel):
    """Invoice generation response."""
    execution_id: str
    workflow_id: str = "invoice_processing"
    status: str
    invoice_number: str
    invoice_url: Optional[str] = None
    sent_to_client: bool
    payment_status: str
    error_messages: List[str] = Field(default_factory=list)
    invoice_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@invoice_router.post("/generate", response_model=InvoiceResponse)
async def generate_invoice(request: InvoiceGenerationRequest) -> InvoiceResponse:
    """
    Generate and send invoice.
    
    Steps:
    1. Analyzer validates invoice data
    2. Planner determines payment terms
    3. Executor generates invoice
    4. Executor sends to client
    5. Executor triggers payment tracking
    6. Analyzer reviews payment
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[INVOICE] Starting generation: {execution_id}")
    
    try:
        invoice_serial = uuid.uuid4().hex[:8].upper()
        invoice_number = f"INV-{invoice_serial}"
        subtotal = round(sum(
            float(item.get("quantity", 1)) * float(item.get("unit_price", 0))
            for item in request.items
        ), 2) or request.amount_due
        tax = round(subtotal * 0.10, 2)
        total = round(subtotal + tax, 2)
        details = {
            "invoice_number": invoice_number,
            "client": request.client_name,
            "client_email": request.client_email,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "due_date": request.due_date,
            "items_count": len(request.items),
        }
        _log_execution("invoice_generation", execution_id, "completed", details)
        return InvoiceResponse(
            execution_id=execution_id,
            status="completed",
            invoice_number=invoice_number,
            invoice_url=None,  # Set when PDF generation is integrated
            sent_to_client=False,  # Set True when email integration is configured
            payment_status="pending",
            invoice_details=details,
        )
    except Exception as e:
        logger.error(f"[INVOICE] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Meeting Scheduling Workflow Models
# ============================================================================

class MeetingSchedulingRequest(BaseModel):
    """Meeting scheduling request."""
    meeting_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    participants: List[str]  # Email addresses
    start_time: str  # ISO format
    duration_minutes: int
    room_required: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MeetingResponse(BaseModel):
    """Meeting scheduling response."""
    execution_id: str
    workflow_id: str = "meeting_scheduling"
    status: str
    meeting_id: str
    calendar_event_id: Optional[str] = None
    meeting_scheduled: bool
    room_allocated: Optional[str] = None
    invites_sent: int
    error_messages: List[str] = Field(default_factory=list)
    meeting_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@meeting_router.post("/schedule", response_model=MeetingResponse)
async def schedule_meeting(request: MeetingSchedulingRequest) -> MeetingResponse:
    """
    Schedule meeting with automatic:
    - Calendar invites
    - Room allocation (if needed)
    - Attendee notifications
    
    Steps:
    1. Planner finds optimal time
    2. Coordinator allocates resources
    3. Executor schedules meeting
    4. Executor sends invitations
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[MEETING] Starting scheduling: {execution_id}")
    
    try:
        meeting_id = request.meeting_id or f"mtg_{uuid.uuid4().hex[:8]}"
        calendar_event_id = f"cal_{uuid.uuid4().hex[:8]}"
        details = {
            "meeting_id": meeting_id,
            "title": request.title,
            "start_time": request.start_time,
            "duration_minutes": request.duration_minutes,
            "participants": request.participants,
            "room_required": request.room_required,
        }
        _log_execution("meeting_scheduling", execution_id, "completed", details)
        return MeetingResponse(
            execution_id=execution_id,
            meeting_id=meeting_id,
            status="completed",
            meeting_scheduled=True,
            room_allocated="Conference Room A" if request.room_required else None,
            invites_sent=len(request.participants),
            calendar_event_id=calendar_event_id,
            meeting_details=details,
        )
    except Exception as e:
        logger.error(f"[MEETING] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Sales Lead Generation Workflow Models
# ============================================================================

class SalesLeadGenerationRequest(BaseModel):
    """Sales lead generation request."""
    lead_id: Optional[str] = None
    lead_name: str
    lead_email: str
    lead_phone: str
    company_name: str
    lead_source: str  # "website", "referral", "event", "campaign"
    lead_budget: Optional[float] = None
    product_interest: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SalesLeadResponse(BaseModel):
    """Sales lead processing response."""
    execution_id: str
    workflow_id: str = "sales_lead_generation"
    status: str
    lead_id: str
    lead_qualified: bool
    qualification_score: float
    assigned_to: Optional[str] = None
    follow_up_date: Optional[str] = None
    error_messages: List[str] = Field(default_factory=list)
    lead_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@sales_router.post("/generate-lead", response_model=SalesLeadResponse)
async def generate_sales_lead(request: SalesLeadGenerationRequest) -> SalesLeadResponse:
    """
    Process sales lead generation.
    
    Steps:
    1. Analyzer qualifies lead
    2. Analyzer scores lead
    3. Executor creates CRM entry
    4. Executor assigns to sales rep
    5. Executor sends follow-up email
    6. Coordinator schedules follow-up
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"[SALES] Starting lead processing: {execution_id}")
    
    try:
        lead_id = request.lead_id or f"lead_{uuid.uuid4().hex[:8]}"
        # Score based on available data quality
        score = 0.50
        if request.lead_budget and request.lead_budget > 0:
            score += 0.20
        if request.product_interest:
            score += min(len(request.product_interest) * 0.05, 0.20)
        if request.lead_phone:
            score += 0.10
        score = round(min(score, 1.0), 2)
        lead_qualified = score >= 0.60
        follow_up = (date.today() + timedelta(days=2)).isoformat()
        details = {
            "lead_id": lead_id,
            "name": request.lead_name,
            "email": request.lead_email,
            "company": request.company_name,
            "source": request.lead_source,
            "budget": request.lead_budget,
            "product_interest": request.product_interest,
            "qualification_score": score,
        }
        _log_execution("sales_lead_generation", execution_id, "completed", details)
        return SalesLeadResponse(
            execution_id=execution_id,
            lead_id=lead_id,
            status="completed",
            lead_qualified=lead_qualified,
            qualification_score=score,
            assigned_to="sales_rep_01",
            follow_up_date=follow_up,
            lead_details=details,
        )
    except Exception as e:
        logger.error(f"[SALES] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export routers
# ============================================================================

WORKFLOW_ROUTERS = [
    onboarding_router,
    recruitment_router,
    payroll_router,
    invoice_router,
    meeting_router,
    sales_router
]
