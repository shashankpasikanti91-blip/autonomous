"""
Emergent AI - Autonomous Intelligence Platform

Phase 1-5 Complete Architecture:
- Phase 3: Service Integrations (Email, Messaging, Calendar, CRM)
- Phase 4: Hardened Integration Adapters with Health Monitoring
- Phase 5: Autonomous Intelligence Layer with Learning
"""

# Phase 5: Autonomous Intelligence
from app.intelligence import (
    get_intelligence_orchestrator,
    IntelligenceOrchestrator,
    PromptParser,
    WorkflowCompiler,
    AgentRouter,
    ToolSelector,
    LearningMemory,
    ReasoningTraceStore,
    AutonomousExecutor,
)

# Phase 4: Hardened Integrations
from app.integrations import (
    get_email_adapter,
    get_messaging_adapter,
    get_calendar_adapter,
    get_crm_adapter,
    get_health_monitor,
    get_credential_manager,
    get_integration_telemetry,
)

__all__ = [
    # Intelligence Layer
    "get_intelligence_orchestrator",
    "IntelligenceOrchestrator",
    "PromptParser",
    "WorkflowCompiler",
    "AgentRouter",
    "ToolSelector",
    "LearningMemory",
    "ReasoningTraceStore",
    "AutonomousExecutor",
    # Integration Adapters
    "get_email_adapter",
    "get_messaging_adapter",
    "get_calendar_adapter",
    "get_crm_adapter",
    "get_health_monitor",
    "get_credential_manager",
    "get_integration_telemetry",
]
