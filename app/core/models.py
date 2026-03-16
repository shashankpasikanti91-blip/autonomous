"""
Pydantic models for the core framework.
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Enumeration of agent roles."""
    COORDINATOR = "coordinator"
    EXECUTOR = "executor"
    ANALYZER = "analyzer"
    PLANNER = "planner"


class ExecutionStatus(str, Enum):
    """Enumeration of execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolType(str, Enum):
    """Enumeration of tool types."""
    EMAIL = "email"
    CALENDAR = "calendar"
    INVOICE = "invoice"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class ToolInput(BaseModel):
    """Input specification for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Definition of a tool that can be used by agents."""
    id: str
    name: str
    description: str
    tool_type: ToolType
    inputs: List[ToolInput]
    outputs: List[str]
    retry_policy: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Retry configuration (max_retries, backoff_factor, etc.)"
    )


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""
    tool_id: str
    inputs: Dict[str, Any]
    timeout: Optional[int] = None


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    tool_id: str
    status: ExecutionStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """A message in the agent communication."""
    id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class Memory(BaseModel):
    """Represents a memory entry."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """State of an agent."""
    agent_id: str
    role: AgentRole
    current_task: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    memories: List[Memory] = Field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStepDefinition(BaseModel):
    """Definition of a step in a workflow."""
    id: str
    name: str
    description: str
    agent_id: Optional[str] = None
    tool_calls: List[ToolExecutionRequest] = Field(default_factory=list)
    conditions: Optional[Dict[str, Any]] = None
    next_steps: List[str] = Field(default_factory=list)


class WorkflowExecution(BaseModel):
    """Execution record of a workflow."""
    id: str
    workflow_id: str
    status: ExecutionStatus
    current_step: Optional[str] = None
    steps_executed: List[str] = Field(default_factory=list)
    agents_involved: List[str] = Field(default_factory=list)
    tool_calls: List[ToolExecutionResult] = Field(default_factory=list)
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Definition of a workflow."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStepDefinition]
    entry_point: str
    agents: List[str] = Field(default_factory=list)
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    """Event in the event-driven architecture."""
    id: str
    event_type: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningStep(BaseModel):
    """Single step in an agent's reasoning chain."""
    step_number: int
    thinking: str
    observation: Optional[str] = None
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class ReasoningChain(BaseModel):
    """Complete reasoning chain for decision making."""
    task_context: str
    initial_analysis: str
    steps: List[ReasoningStep] = Field(default_factory=list)
    final_decision: str
    reasoning_time_ms: Optional[int] = None


class ActionSelection(BaseModel):
    """Selection of action(s) to take based on reasoning."""
    action_type: str  # "tool_execution", "delegation", "skip", "escalate"
    selected_tool_id: Optional[str] = None
    rationale: str
    priority: int = Field(ge=1, le=5, default=3)  # 1=low, 5=critical
    estimated_outcome: Optional[str] = None
    fallback_actions: List[str] = Field(default_factory=list)


class TaskPrioritization(BaseModel):
    """Task prioritization information."""
    task_id: str
    priority_score: float = Field(ge=0.0, le=1.0)
    urgency_level: str  # "low", "medium", "high", "critical"
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration_seconds: Optional[int] = None
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)


class ToolSelectionContext(BaseModel):
    """Context for tool selection by agents."""
    available_tools: Dict[str, str]  # tool_id -> tool_name
    task_requirements: List[str]
    agent_capabilities: List[str]
    constraints: Optional[Dict[str, Any]] = None
    previous_attempts: List[str] = Field(default_factory=list)


class ToolCallPlanned(BaseModel):
    """Planned tool call with reasoning."""
    tool_id: str
    tool_name: str
    inputs: Dict[str, Any]
    reasoning: str
    expected_output_schema: Optional[Dict[str, Any]] = None
    success_criteria: List[str] = Field(default_factory=list)
    on_failure: Optional[str] = None


class ExecutionPlan(BaseModel):
    """Complete execution plan for a task."""
    task_id: str
    objective: str
    approach: str
    steps: List[ToolCallPlanned] = Field(default_factory=list)
    prioritized_tasks: List[TaskPrioritization] = Field(default_factory=list)
    risk_assessment: Optional[str] = None
    estimated_total_time_seconds: Optional[int] = None


class AgentResponse(BaseModel):
    """Response from an agent."""
    agent_id: str
    status: ExecutionStatus
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reasoning_chain: Optional[ReasoningChain] = None
    action_selected: Optional[ActionSelection] = None
    execution_plan: Optional[ExecutionPlan] = None
    memory_accessed: List[str] = Field(default_factory=list)
