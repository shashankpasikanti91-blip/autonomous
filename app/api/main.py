"""
FastAPI application with endpoints for workflows, agents, and execution logs.

Production-ready orchestration platform with:
- Complete agent orchestration
- Service connectors for external integrations
- N8N webhook compatibility
- Workflow-specific endpoints
- Error handling and retries
"""
from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Core models and engines
from core.models import (
    WorkflowDefinition, WorkflowExecution, AgentState,
    ExecutionStatus, Event, WorkflowStepDefinition
)
from core.workflows.engine import WorkflowEngine, EventBus
from core.agents.concrete import CoordinatorAgent, ExecutorAgent, AnalyzerAgent, PlannerAgent
from core.tools.implementations import (
    EmailSenderTool, CalendarSchedulerTool, InvoiceGeneratorTool,
    N8NWebhookTool
)
from core.memory.implementations import HybridMemory

# Services and connectors
from services.orchestration import (
    AgentOrchestrationService, OrchestrationContext, ExecutionStrategy, RetryPolicy
)
from services.connectors import (
    ServiceConnectorFactory, GmailConnector, WhatsAppConnector,
    GoogleCalendarConnector, PayrollProcessor, InvoiceGenerator,
    HubSpotConnector, VisaMonitor
)

# Lazy import to avoid circular dependencies
N8NWorkflowRegistry = None

def _get_n8n_registry():
    global N8NWorkflowRegistry
    if N8NWorkflowRegistry is None:
        from services.n8n_webhooks import N8NWorkflowRegistry as NWR
        N8NWorkflowRegistry = NWR
    return N8NWorkflowRegistry

# API Routes
from api.workflows import WORKFLOW_ROUTERS
from api.n8n import n8n_router
from api.records import router as records_router
from api.payroll import router as payroll_router
from api.industry_router import router as industry_router
from api.tenants import router as tenants_router

# Tenant middleware
from middleware.tenant import TenantMiddleware

# Industry config
from industry.config import list_industries

# Firebase and integrations
from integrations.firebase import (
    FirebaseClient, AuthenticationManager, FirestoreManager,
    RealtimeNotificationManager
)

# Configuration
from config.settings import settings
from utils.logger import get_logger
from utils.errors import PlatformException


logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Autonomous HR & Business Operations Intelligence Platform",
    description="Production-ready orchestration backbone with full AI reasoning and external integrations",
    version="2.0.0"
)

# Tenant resolution middleware (must be added before CORS)
app.add_middleware(
    TenantMiddleware,
    platform_domain=settings.platform_domain,
)

# CORS — configured from environment (ALLOWED_ORIGINS)
def _build_origin_regex(domain: str) -> str:
    domain = domain.replace(".", "\\.")
    return rf"https?://(.+\.)?{domain}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=_build_origin_regex(settings.platform_domain),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
event_bus = EventBus()
workflow_engine = WorkflowEngine(event_bus=event_bus)
hybrid_memory = HybridMemory()
firebase_client = FirebaseClient()
auth_manager = AuthenticationManager(firebase_client)
firestore_manager = FirestoreManager(firebase_client)
notification_manager = RealtimeNotificationManager(firebase_client)

# Initialize default agents
executor_agent = ExecutorAgent(
    agent_id="executor_1",
    tools=[
        EmailSenderTool(),
        CalendarSchedulerTool(),
        InvoiceGeneratorTool(),
        N8NWebhookTool(),
    ],
    memory=hybrid_memory
)
coordinator_agent = CoordinatorAgent(
    agent_id="coordinator_1",
    memory=hybrid_memory
)
analyzer_agent = AnalyzerAgent(
    agent_id="analyzer_1",
    memory=hybrid_memory
)
planner_agent = PlannerAgent(
    agent_id="planner_1",
    memory=hybrid_memory
)

workflow_engine.register_agent(executor_agent)
workflow_engine.register_agent(coordinator_agent)
workflow_engine.register_agent(analyzer_agent)
workflow_engine.register_agent(planner_agent)

# ============================================================================
# Service Orchestration Setup
# ============================================================================

# Initialize service connector factory
service_factory = ServiceConnectorFactory()

# Register service connectors based on configuration
if settings.email_provider == "gmail":
    email_connector = GmailConnector(
        service_account_key=settings.gmail_service_account_key,
        from_address=settings.gmail_from_address
    )
    service_factory.register_connector("email", email_connector)

if settings.whatsapp_api_token:
    whatsapp_connector = WhatsAppConnector(
        api_token=settings.whatsapp_api_token,
        business_account_id=settings.whatsapp_business_account_id
    )
    service_factory.register_connector("messaging", whatsapp_connector)

if settings.calendar_provider == "google":
    calendar_connector = GoogleCalendarConnector(
        service_account_key=settings.google_calendar_key
    )
    service_factory.register_connector("calendar", calendar_connector)

# Payroll and Invoice services
payroll_processor = PayrollProcessor(
    tax_rate=settings.payroll_tax_rate,
    health_insurance=settings.health_insurance_deduction
)
service_factory.register_connector("payroll", payroll_processor)

invoice_generator = InvoiceGenerator(
    business_name=settings.business_name,
    tax_id=settings.tax_id
)
service_factory.register_connector("invoice", invoice_generator)

# CRM connector
if settings.crm_provider == "hubspot":
    crm_connector = HubSpotConnector(api_key=settings.crm_api_key)
    service_factory.register_connector("crm", crm_connector)

# Initialize orchestration service
orchestration_service = AgentOrchestrationService(
    event_bus=event_bus,
    memory=hybrid_memory,
    service_factory=service_factory
)

# Register agents with orchestration service
orchestration_service.register_agent(executor_agent)
orchestration_service.register_agent(coordinator_agent)
orchestration_service.register_agent(analyzer_agent)
orchestration_service.register_agent(planner_agent)

# Set retry policy
orchestration_service.set_retry_policy(
    RetryPolicy(
        max_retries=settings.max_retries,
        initial_delay_ms=settings.retry_delay_ms
    )
)

# Initialize N8N workflow registry
def _get_n8n_workflow_registry():
    try:
        from services.n8n_webhooks import N8NWorkflowRegistry
        return N8NWorkflowRegistry()
    except Exception as e:
        logger.error(f"Failed to initialize N8N workflow registry: {e}")
        return None

n8n_workflow_registry = _get_n8n_workflow_registry()

logger.info("Orchestration services initialized successfully")

# ============================================================================
# Register API Routers
# ============================================================================

# Register workflow-specific routers
for router in WORKFLOW_ROUTERS:
    app.include_router(router)
    logger.info(f"Registered router: {router.prefix}")

# Register N8N webhook router
app.include_router(n8n_router)
logger.info("Registered N8N webhook router")

# Register PostgreSQL records router
app.include_router(records_router)
logger.info("Registered records router (PostgreSQL)")

# Register Payroll operational router
app.include_router(payroll_router)
logger.info("Registered payroll router")

# Register Industry config router
app.include_router(industry_router)
logger.info("Registered industry router")

# Register Tenant router
app.include_router(tenants_router)
logger.info("Registered tenant router")

logger.info(f"[OK] API initialized with {len(WORKFLOW_ROUTERS) + 3} router groups")

# ── Initialise DB tables (idempotent — safe to run every startup) ─────────
try:
    from db.database import init_db
    init_db()
    logger.info("[OK] PostgreSQL tables verified.")
except Exception as _db_err:
    logger.warning("PostgreSQL init skipped: %s", _db_err)



# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint — returns platform status and version."""
    return {
        "status": "healthy",
        "platform": settings.platform_name,
        "version": "2.0.0",
        "environment": settings.env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/platform/info", tags=["Platform"])
async def platform_info(request: Request) -> Dict[str, Any]:
    """Return platform metadata including supported industries and workflows."""
    tenant = getattr(request.state, "tenant_slug", None)
    return {
        "platform": settings.platform_name,
        "domain": settings.platform_domain,
        "version": "2.0.0",
        "tenant": tenant,
        "supported_industries": [i["id"] for i in list_industries()],
        "supported_workflows": [
            "onboarding", "recruitment", "payroll",
            "invoice", "meeting", "sales",
        ],
        "integrations_status": {
            "email": "stub — configure EMAIL_PROVIDER",
            "whatsapp": "stub — configure WHATSAPP_API_TOKEN",
            "calendar": "stub — configure CALENDAR_PROVIDER",
            "firebase": "stub — configure FIREBASE_PROJECT_ID",
            "n8n": "webhook-ready — configure N8N_URL",
            "postgresql": "active",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Agent Management Endpoints
# ============================================================================

@app.get("/agents", tags=["Agents"])
async def list_agents() -> Dict[str, Any]:
    """List all registered agents."""
    try:
        agents = []
        for agent_id, agent in workflow_engine.agents.items():
            agents.append({
                "agent_id": agent_id,
                "name": agent.name,
                "role": agent.role.value,
                "description": agent.description,
                "tools_count": len(agent.tools),
                "status": agent.state.status.value
            })
        return {"agents": agents, "total": len(agents)}
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}", tags=["Agents"])
async def get_agent_state(agent_id: str) -> Dict[str, Any]:
    """Get the state of a specific agent."""
    try:
        if agent_id not in workflow_engine.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent = workflow_engine.agents[agent_id]
        state = agent.get_state()
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "role": agent.role.value,
            "status": state.status.value,
            "current_task": state.current_task,
            "messages_count": len(state.messages),
            "memories_count": len(state.memories),
            "metadata": state.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/tools", tags=["Agents"])
async def get_agent_tools(agent_id: str) -> Dict[str, Any]:
    """Get available tools for an agent."""
    try:
        if agent_id not in workflow_engine.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent = workflow_engine.agents[agent_id]
        tools = [
            {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "description": tool.description,
                "schema": tool.get_schema()
            }
            for tool in agent.tools.values()
        ]
        
        return {"agent_id": agent_id, "tools": tools, "total": len(tools)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Management Endpoints
# ============================================================================

@app.post("/workflows", tags=["Workflows"])
async def create_workflow(workflow: WorkflowDefinition) -> Dict[str, Any]:
    """Register a new workflow."""
    try:
        workflow_engine.register_workflow(workflow)
        
        # Store workflow definition in Firestore
        await firestore_manager.set_document(
            collection="workflows",
            document_id=workflow.id,
            data=workflow.model_dump()
        )
        
        # Publish event
        await event_bus.publish(Event(
            id=f"event_{hash(str(datetime.now(timezone.utc)))}",
            event_type="workflow_created",
            source="API",
            data={"workflow_id": workflow.id}
        ))
        
        logger.info(f"Workflow created: {workflow.id}")
        return {"workflow_id": workflow.id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows", tags=["Workflows"])
async def list_workflows() -> Dict[str, Any]:
    """List all registered workflows."""
    try:
        workflows = []
        for wf_id, workflow in workflow_engine.workflows.items():
            workflows.append({
                "workflow_id": wf_id,
                "name": workflow.name,
                "description": workflow.description,
                "steps_count": len(workflow.steps),
                "agents": workflow.agents
            })
        return {"workflows": workflows, "total": len(workflows)}
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}", tags=["Workflows"])
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get workflow definition."""
    try:
        if workflow_id not in workflow_engine.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = workflow_engine.workflows[workflow_id]
        return workflow.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Execution Endpoints
# ============================================================================

@app.post("/workflows/{workflow_id}/execute", tags=["Execution"])
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any] = Body(default={})
) -> Dict[str, Any]:
    """Execute a workflow."""
    try:
        execution = await workflow_engine.execute_workflow(workflow_id, input_data)
        
        # Store execution in Firestore
        await firestore_manager.set_document(
            collection="executions",
            document_id=execution.id,
            data=execution.model_dump()
        )
        
        logger.info(f"Workflow execution started: {execution.id}")
        return {
            "execution_id": execution.id,
            "workflow_id": workflow_id,
            "status": execution.status.value
        }
    except Exception as e:
        logger.error(f"Failed to execute workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/executions/{execution_id}", tags=["Execution"])
async def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get execution details."""
    try:
        execution = workflow_engine.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "steps_executed": execution.steps_executed,
            "agents_involved": execution.agents_involved,
            "tool_calls_count": len(execution.tool_calls),
            "errors": execution.errors,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "results": execution.results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}/executions", tags=["Execution"])
async def list_workflow_executions(workflow_id: str) -> Dict[str, Any]:
    """List all executions for a workflow."""
    try:
        executions = workflow_engine.list_executions(workflow_id)
        
        execution_list = [
            {
                "execution_id": e.id,
                "status": e.status.value,
                "steps_executed": len(e.steps_executed),
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None
            }
            for e in executions
        ]
        
        return {
            "workflow_id": workflow_id,
            "executions": execution_list,
            "total": len(executions)
        }
    except Exception as e:
        logger.error(f"Failed to list executions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Event and Log Endpoints
# ============================================================================

@app.get("/events", tags=["Events"])
async def get_events(
    event_type: Optional[str] = None,
    execution_id: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get event history."""
    try:
        events = await workflow_engine.get_event_history(
            execution_id=execution_id,
            event_type=event_type
        )
        
        event_list = [
            {
                "event_id": e.id,
                "event_type": e.event_type,
                "source": e.source,
                "timestamp": e.timestamp.isoformat(),
                "data": e.data,
                "correlation_id": e.correlation_id
            }
            for e in events[-limit:]
        ]
        
        return {"events": event_list, "total": len(event_list)}
    except Exception as e:
        logger.error(f"Failed to get events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Memory Endpoints
# ============================================================================

@app.post("/memory/store", tags=["Memory"])
async def store_memory(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store data in hybrid memory."""
    try:
        memory_id = await hybrid_memory.store(data)
        logger.info(f"Memory stored: {memory_id}")
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        logger.error(f"Failed to store memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/retrieve", tags=["Memory"])
async def retrieve_memory(query: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieve data from memory."""
    try:
        results = await hybrid_memory.retrieve(query, limit)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Failed to retrieve memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Processing Endpoints
# ============================================================================

@app.post("/agents/{agent_id}/process", tags=["Agents"])
async def process_with_agent(
    agent_id: str,
    input_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Process input with a specific agent."""
    try:
        if agent_id not in workflow_engine.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent = workflow_engine.agents[agent_id]
        response = await agent.process(input_data)
        
        return {
            "agent_id": agent_id,
            "status": response.status.value,
            "message": response.message,
            "result": response.result,
            "timestamp": response.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process with agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/login", tags=["Authentication"])
async def login(email: str, password: str) -> Dict[str, Any]:
    """Authenticate user and get token."""
    try:
        token = await auth_manager.authenticate_user(email, password)
        return {"token": token, "user_email": email}
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@app.get("/auth/verify", tags=["Authentication"])
async def verify_token(token: str) -> Dict[str, Any]:
    """Verify authentication token."""
    try:
        user_info = await auth_manager.verify_token(token)
        return {"valid": True, "user": user_info}
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# Firestore Management Endpoints
# ============================================================================

@app.post("/data/{collection}/{document_id}", tags=["Data"])
async def set_document(
    collection: str,
    document_id: str,
    data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Store a document in Firestore."""
    try:
        await firestore_manager.set_document(collection, document_id, data)
        return {"status": "stored", "collection": collection, "document_id": document_id}
    except Exception as e:
        logger.error(f"Failed to store document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/{collection}/{document_id}", tags=["Data"])
async def get_document(collection: str, document_id: str) -> Dict[str, Any]:
    """Retrieve a document from Firestore."""
    try:
        doc = await firestore_manager.get_document(collection, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/{collection}", tags=["Data"])
async def query_collection(
    collection: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Query documents from a collection."""
    try:
        docs = await firestore_manager.query_collection(collection, limit=limit)
        return {"documents": docs, "count": len(docs)}
    except Exception as e:
        logger.error(f"Failed to query collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics and Info Endpoints
# ============================================================================

@app.get("/stats", tags=["Stats"])
async def get_statistics() -> Dict[str, Any]:
    """Get platform statistics."""
    try:
        agents = len(workflow_engine.agents)
        workflows = len(workflow_engine.workflows)
        executions = len(workflow_engine.executions)
        events = len(event_bus.event_history)
        
        completed_executions = sum(
            1 for e in workflow_engine.executions.values()
            if e.status == ExecutionStatus.COMPLETED
        )
        failed_executions = sum(
            1 for e in workflow_engine.executions.values()
            if e.status == ExecutionStatus.FAILED
        )
        
        return {
            "agents_count": agents,
            "workflows_count": workflows,
            "executions_count": executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "events_count": events,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", tags=["Info"])
async def get_info() -> Dict[str, Any]:
    """Get platform information."""
    return {
        "name": "Autonomous Business Operations Intelligence Platform",
        "version": "2.0.0",
        "description": "Multi-domain AI orchestration: HR, Recruitment, Payroll, Finance, Sales, Operations",
        "environment": settings.env,
        "debug": settings.debug,
        "agents_registered": len(workflow_engine.agents),
        "workflows_registered": len(workflow_engine.workflows),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(PlatformException)
async def platform_exception_handler(request, exc):
    """Handle platform exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message, "code": exc.code}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload if settings.debug else False
    )
