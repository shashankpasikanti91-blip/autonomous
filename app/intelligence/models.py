"""
Core data models for autonomous intelligence layer.

Defines workflows, agents, tools, execution traces, and learning records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4


class TaskStatus(str, Enum):
    """Status of a task in workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowStatus(str, Enum):
    """Status of overall workflow execution."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ReasoningType(str, Enum):
    """Type of reasoning step."""
    ANALYSIS = "analysis"
    DECISION = "decision"
    PLANNING = "planning"
    TOOL_SELECTION = "tool_selection"
    AGENT_SELECTION = "agent_selection"
    VALIDATION = "validation"
    ERROR_RECOVERY = "error_recovery"
    REFLECTION = "reflection"


class LearningType(str, Enum):
    """Type of learning record."""
    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"
    PATTERN = "pattern"
    STRATEGY = "strategy"


@dataclass
class ToolSignature:
    """Describes what a tool can do."""
    tool_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON schema
    output_schema: Dict[str, Any]  # JSON schema
    capabilities: Set[str]  # Tags like {"email", "send", "batch"}
    provider: Optional[str] = None  # e.g., "email_adapter"
    latency_ms: float = 0.0  # Average latency
    success_rate: float = 1.0  # 0.0-1.0
    cost_per_call: float = 0.0  # In credits or cents
    requires_auth: bool = False
    rate_limit_per_second: float = float('inf')
    aliases: List[str] = field(default_factory=list)


@dataclass
class AgentCapability:
    """What an agent is capable of doing."""
    agent_id: str
    agent_name: str
    description: str
    supported_tools: Set[str]  # tool_ids this agent can use
    supported_operations: Set[str]  # e.g., {"email_send", "crm_lookup"}
    expertise_level: float = 1.0  # 0.0-10.0
    availability: float = 1.0  # 0.0-1.0 (uptime/availability)
    collaboration_capable: bool = True
    specializations: Set[str] = field(default_factory=set)  # e.g., {"high_volume", "error_recovery"}


@dataclass
class TaskDefinition:
    """Atomic unit of work in a workflow."""
    task_id: str
    name: str
    description: str
    operation: str  # e.g., "send_email", "lookup_contact"
    parameters: Dict[str, Any]
    tool_id: Optional[str] = None  # Specific tool, or leave None for discovery
    agent_id: Optional[str] = None  # Specific agent, or leave None for routing
    timeout_seconds: float = 300.0
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)  # task_ids this depends on
    fallback_task_id: Optional[str] = None
    success_criteria: Optional[Dict[str, Any]] = None
    tags: Set[str] = field(default_factory=set)


@dataclass
class TaskExecution:
    """Tracking execution of a single task."""
    execution_id: str
    task_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    agent_id: Optional[str] = None
    tool_id: Optional[str] = None
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    error_category: Optional[str] = None
    latency_ms: float = 0.0
    retry_count: int = 0
    reasoning_trace_id: Optional[str] = None


@dataclass
class WorkflowStep:
    """Steps in workflow execution plan."""
    step_id: str
    step_number: int
    name: str
    description: str
    tasks: List[TaskDefinition]
    parallel_execution: bool = False
    stop_on_failure: bool = True
    success_condition: Optional[str] = None


@dataclass
class WorkflowPlan:
    """Execution plan generated from user intent."""
    plan_id: str
    name: str
    description: str
    user_intent: str
    confidence: float  # 0.0-1.0
    steps: List[WorkflowStep]
    estimated_duration_seconds: float
    estimated_cost: float = 0.0
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    """Tracks execution of a complete workflow."""
    execution_id: str
    workflow_template_id: Optional[str]
    plan_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    user_intent: Optional[str] = None
    task_executions: Dict[str, TaskExecution] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    total_latency_ms: float = 0.0
    reasoning_trace_id: Optional[str] = None
    parent_execution_id: Optional[str] = None  # For nested workflows
    learning_record_id: Optional[str] = None


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""
    step_id: str
    reasoning_type: ReasoningType
    timestamp: datetime
    input_context: Dict[str, Any]
    reasoning_text: str
    output_decision: Dict[str, Any]
    confidence: float  # 0.0-1.0
    supporting_evidence: List[str] = field(default_factory=list)
    alternative_considered: List[str] = field(default_factory=list)


@dataclass
class ReasoningTrace:
    """Complete chain of reasoning for an execution."""
    trace_id: str
    execution_id: str
    user_query: str
    created_at: datetime
    steps: List[ReasoningStep] = field(default_factory=list)
    final_plan_id: Optional[str] = None
    replayed_from_trace_id: Optional[str] = None
    improvement_applied: Optional[str] = None


@dataclass
class LearningRecord:
    """Captures learnings from workflow execution."""
    record_id: str
    learning_type: LearningType
    execution_id: str
    timestamp: datetime
    pattern_description: str
    pattern_data: Dict[str, Any]
    success: bool
    latency_ms: float
    confidence: float  # 0.0-1.0
    applicable_workflows: Set[str] = field(default_factory=set)
    applicable_agents: Set[str] = field(default_factory=set)
    applicable_tools: Set[str] = field(default_factory=set)
    recommendation: Optional[str] = None
    retry_strategy: Optional[str] = None


@dataclass
class WorkflowTemplate:
    """Reusable workflow template for common patterns."""
    template_id: str
    name: str
    description: str
    category: str  # e.g., "email_campaign", "lead_nurture"
    user_query_pattern: str  # Regex or semantic pattern
    workflow_plan: WorkflowPlan
    parameters: Dict[str, Any]  # Parameterized slots
    success_rate: float  # Historical success rate
    average_duration_seconds: float
    average_cost: float
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    learning_records: List[str] = field(default_factory=list)  # record_ids


@dataclass
class ExecutionFeedback:
    """Human feedback on execution results."""
    feedback_id: str
    execution_id: str
    user_id: str
    overall_rating: int  # 1-5
    was_successful: bool
    issues_encountered: List[str] = field(default_factory=list)
    improvements_suggested: List[str] = field(default_factory=list)
    additional_notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SafetyConstraint:
    """Safety rules for autonomous execution."""
    constraint_id: str
    name: str
    description: str
    constraint_type: str  # "rate_limit", "cost_limit", "scope", "auth"
    applies_to: Set[str]  # agent_ids or tool_ids
    max_concurrent_executions: Optional[int] = None
    max_cost_per_workflow: Optional[float] = None
    max_api_calls_per_hour: Optional[int] = None
    allowed_operations: Optional[Set[str]] = None
    blocked_operations: Set[str] = field(default_factory=set)
    requires_approval: bool = False
    approval_threshold: Optional[str] = None  # e.g., "cost > $100"


@dataclass
class ToolRegistry:
    """Registry of all available tools."""
    tools: Dict[str, ToolSignature] = field(default_factory=dict)
    tool_capabilities_index: Dict[str, Set[str]] = field(default_factory=dict)  # capability -> tool_ids
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def add_tool(self, signature: ToolSignature) -> None:
        """Register a new tool."""
        self.tools[signature.tool_id] = signature
        for cap in signature.capabilities:
            if cap not in self.tool_capabilities_index:
                self.tool_capabilities_index[cap] = set()
            self.tool_capabilities_index[cap].add(signature.tool_id)
        self.last_updated = datetime.utcnow()
    
    def find_tools_by_capability(self, capability: str) -> List[ToolSignature]:
        """Find all tools with a capability."""
        tool_ids = self.tool_capabilities_index.get(capability, set())
        return [self.tools[tid] for tid in tool_ids if tid in self.tools]
    
    def find_tools_by_operation(self, operation: str) -> List[ToolSignature]:
        """Find all tools supporting an operation."""
        matching = []
        for tool in self.tools.values():
            if operation in tool.capabilities:
                matching.append(tool)
        return matching


@dataclass
class AgentRegistry:
    """Registry of available agents and their capabilities."""
    agents: Dict[str, AgentCapability] = field(default_factory=dict)
    operation_to_agents: Dict[str, Set[str]] = field(default_factory=dict)  # operation -> agent_ids
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def add_agent(self, capability: AgentCapability) -> None:
        """Register an agent and its capabilities."""
        self.agents[capability.agent_id] = capability
        for op in capability.supported_operations:
            if op not in self.operation_to_agents:
                self.operation_to_agents[op] = set()
            self.operation_to_agents[op].add(capability.agent_id)
        self.last_updated = datetime.utcnow()
    
    def find_agents_for_operation(self, operation: str) -> List[AgentCapability]:
        """Find agents capable of an operation."""
        agent_ids = self.operation_to_agents.get(operation, set())
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        # Sort by expertise and availability
        return sorted(agents, key=lambda a: a.expertise_level * a.availability, reverse=True)


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"
