"""
Autonomous Intelligence Layer for Emergent AI.

Provides prompt-driven workflow creation, agent routing, learning feedback,
reasoning traces, autonomous execution, and tool discovery.
"""

# Core data models
from app.intelligence.models import (
    TaskStatus,
    WorkflowStatus,
    ReasoningType,
    LearningType,
    ToolSignature,
    AgentCapability,
    TaskDefinition,
    TaskExecution,
    WorkflowStep,
    WorkflowPlan,
    WorkflowExecution,
    ReasoningStep,
    ReasoningTrace,
    LearningRecord,
    WorkflowTemplate,
    ExecutionFeedback,
    SafetyConstraint,
    ToolRegistry,
    AgentRegistry,
    generate_id,
)

# Prompt compilation
from app.intelligence.prompt_compiler import (
    PromptParser,
    WorkflowCompiler,
    IntentType,
)

# Agent routing
from app.intelligence.agent_router import (
    AgentRouter,
    ToolSelector,
)

# Learning system
from app.intelligence.learning_system import (
    LearningMemory,
    AdaptiveRetryStrategy,
    FirstPrinciplesSuggester,
    WorkflowTemplateGenerator,
)

# Reasoning traces
from app.intelligence.reasoning_tracer import (
    ReasoningTraceStore,
    ReasoningReplayer,
    ReasoningFailureDetector,
    ReasoningImprovementSuggester,
    compare_traces,
)

# Autonomous execution
from app.intelligence.autonomous_executor import (
    AutonomousExecutor,
    SafetyConstraintManager,
    ExecutionPhase,
)

# Orchestrator
from app.intelligence.orchestrator import (
    IntelligenceOrchestrator,
    get_intelligence_orchestrator,
)

__all__ = [
    # Models
    "TaskStatus",
    "WorkflowStatus",
    "ReasoningType",
    "LearningType",
    "IntentType",
    "ToolSignature",
    "AgentCapability",
    "TaskDefinition",
    "TaskExecution",
    "WorkflowStep",
    "WorkflowPlan",
    "WorkflowExecution",
    "ReasoningStep",
    "ReasoningTrace",
    "LearningRecord",
    "WorkflowTemplate",
    "ExecutionFeedback",
    "SafetyConstraint",
    "ToolRegistry",
    "AgentRegistry",
    "generate_id",
    # Prompt compilation
    "PromptParser",
    "WorkflowCompiler",
    # Agent routing
    "AgentRouter",
    "ToolSelector",
    # Learning
    "LearningMemory",
    "AdaptiveRetryStrategy",
    "FirstPrinciplesSuggester",
    "WorkflowTemplateGenerator",
    # Reasoning
    "ReasoningTraceStore",
    "ReasoningReplayer",
    "ReasoningFailureDetector",
    "ReasoningImprovementSuggester",
    "compare_traces",
    # Execution
    "AutonomousExecutor",
    "SafetyConstraintManager",
    "ExecutionPhase",
    # Orchestrator
    "IntelligenceOrchestrator",
    "get_intelligence_orchestrator",
]
