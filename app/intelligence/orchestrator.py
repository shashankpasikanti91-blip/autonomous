"""
Intelligence orchestrator: coordinates all autonomous intelligence components.

Provides unified API for intelligent workflow creation and execution.
"""

from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
import os

from app.intelligence.models import (
    ToolRegistry,
    ToolSignature,
    AgentRegistry,
    AgentCapability,
    WorkflowExecution,
    WorkflowTemplate,
    SafetyConstraint,
    generate_id,
)
from app.intelligence.prompt_compiler import PromptParser, WorkflowCompiler
from app.intelligence.agent_router import AgentRouter, ToolSelector
from app.intelligence.learning_system import (
    LearningMemory,
    AdaptiveRetryStrategy,
    FirstPrinciplesSuggester,
)
from app.intelligence.reasoning_tracer import (
    ReasoningTraceStore,
    ReasoningReplayer,
    ReasoningFailureDetector,
    ReasoningImprovementSuggester,
)
from app.intelligence.autonomous_executor import (
    AutonomousExecutor,
    SafetyConstraintManager,
)


class IntelligenceOrchestrator:
    """Main orchestrator for autonomous intelligence layer."""
    
    def __init__(self):
        """Initialize orchestrator with all components."""
        # Registries
        self.tool_registry = ToolRegistry()
        self.agent_registry = AgentRegistry()
        
        # Core components
        self.prompt_parser = PromptParser()
        self.workflow_compiler = WorkflowCompiler(self.tool_registry, self.agent_registry)
        self.agent_router = AgentRouter(self.agent_registry, self.tool_registry)
        self.tool_selector = ToolSelector(self.tool_registry)
        
        # Learning and reasoning
        self.learning_memory = LearningMemory(
            retention_hours=int(os.getenv("TELEMETRY_RETENTION_HOURS", "720"))
        )
        self.trace_store = ReasoningTraceStore()
        self.retry_strategy = AdaptiveRetryStrategy(self.learning_memory)
        self.improvement_suggester = FirstPrinciplesSuggester(self.learning_memory)
        
        # Reasoning analysis
        self.reasoning_replayer = ReasoningReplayer(self.trace_store)
        self.failure_detector = ReasoningFailureDetector(self.trace_store)
        self.improvement_suggester_reasoning = ReasoningImprovementSuggester(self.trace_store)
        
        # Execution
        self.executor = AutonomousExecutor(
            self.prompt_parser,
            self.workflow_compiler,
            self.agent_router,
            self.tool_selector,
            self.learning_memory,
            self.trace_store,
            self.tool_registry,
        )
        
        self.safety_manager = SafetyConstraintManager()
        
        # Storage
        self.workflow_templates: Dict[str, WorkflowTemplate] = {}
        self.execution_history: Dict[str, WorkflowExecution] = {}
    
    # ========== Tool Registration ==========
    
    def register_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        capabilities: Set[str],
        implementation: Optional[Callable] = None,
        input_schema: Optional[Dict] = None,
        output_schema: Optional[Dict] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Register a tool."""
        signature = ToolSignature(
            tool_id=tool_id,
            name=name,
            description=description,
            capabilities=capabilities,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            provider=provider,
            **kwargs,
        )
        
        self.tool_registry.add_tool(signature)
        
        if implementation:
            self.executor.register_tool(tool_id, implementation)
    
    def register_tools_from_adapters(self) -> None:
        """Register tools from Phase 4 integration adapters."""
        # Email adapter tools
        self.register_tool(
            tool_id="email_send",
            name="Send Email",
            description="Send a single email",
            capabilities={"email", "send", "communication"},
            input_schema={
                "to_address": "string",
                "subject": "string",
                "body_html": "string",
            },
            output_schema={"email_id": "string"},
            provider="email_adapter",
        )
        
        self.register_tool(
            tool_id="email_send_batch",
            name="Send Batch Emails",
            description="Send templated emails in batch",
            capabilities={"email", "send", "batch", "communication"},
            input_schema={
                "recipients": "array",
                "template_id": "string",
                "variables": "object",
            },
            output_schema={"batch_id": "string", "count": "integer"},
            provider="email_adapter",
        )
        
        # Messaging adapter tools
        self.register_tool(
            tool_id="messaging_send",
            name="Send Message",
            description="Send WhatsApp message",
            capabilities={"messaging", "send", "communication"},
            input_schema={
                "phone_number": "string",
                "message": "string",
            },
            output_schema={"message_id": "string"},
            provider="messaging_adapter",
        )
        
        # Calendar adapter tools
        self.register_tool(
            tool_id="calendar_create_event",
            name="Create Calendar Event",
            description="Create event in Google Calendar",
            capabilities={"calendar", "create", "scheduling"},
            input_schema={
                "title": "string",
                "start_time": "datetime",
                "end_time": "datetime",
                "attendees": "array",
            },
            output_schema={"event_id": "string"},
            provider="calendar_adapter",
        )
        
        self.register_tool(
            tool_id="calendar_find_slots",
            name="Find Available Slots",
            description="Find available time slots",
            capabilities={"calendar", "search", "scheduling"},
            input_schema={
                "start_time": "datetime",
                "end_time": "datetime",
                "duration_minutes": "integer",
                "attendees": "array",
            },
            output_schema={"available_slots": "array"},
            provider="calendar_adapter",
        )
        
        # CRM adapter tools
        self.register_tool(
            tool_id="crm_create_contact",
            name="Create Contact",
            description="Create new contact",
            capabilities={"crm", "create", "contact"},
            input_schema={
                "first_name": "string",
                "last_name": "string",
                "email": "string",
                "phone": "string",
            },
            output_schema={"contact_id": "string"},
            provider="crm_adapter",
        )
        
        self.register_tool(
            tool_id="crm_search_contacts",
            name="Search Contacts",
            description="Search for contacts",
            capabilities={"crm", "search", "contact"},
            input_schema={
                "query": "string",
                "limit": "integer",
            },
            output_schema={"results": "array"},
            provider="crm_adapter",
        )
    
    # ========== Agent Registration ==========
    
    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        description: str,
        supported_operations: Set[str],
        expertise_level: float = 1.0,
        availability: float = 1.0,
        specializations: Optional[Set[str]] = None,
    ) -> None:
        """Register an agent."""
        capability = AgentCapability(
            agent_id=agent_id,
            agent_name=agent_name,
            description=description,
            supported_operations=supported_operations,
            supported_tools=set(),  # Will be inferred from operations
            expertise_level=expertise_level,
            availability=availability,
            specializations=specializations or set(),
        )
        
        self.agent_registry.add_agent(capability)
    
    def register_default_agents(self) -> None:
        """Register default agents."""
        # Email agent
        self.register_agent(
            agent_id="agent_email",
            agent_name="Email Specialist",
            description="Handles email operations",
            supported_operations={
                "send_email",
                "send_batch_emails",
                "get_email_status",
            },
            expertise_level=9.0,
            availability=0.99,
            specializations={"high_volume", "templating"},
        )
        
        # Messaging agent
        self.register_agent(
            agent_id="agent_messaging",
            agent_name="Messaging Specialist",
            description="Handles messaging operations",
            supported_operations={
                "send_message",
                "send_template_message",
                "get_message_status",
            },
            expertise_level=8.5,
            availability=0.98,
            specializations={"real_time", "multimedia"},
        )
        
        # Calendar agent
        self.register_agent(
            agent_id="agent_calendar",
            agent_name="Calendar Specialist",
            description="Handles calendar operations",
            supported_operations={
                "create_event",
                "find_available_slots",
                "update_event",
                "delete_event",
            },
            expertise_level=8.0,
            availability=0.99,
            specializations={"scheduling", "conflict_resolution"},
        )
        
        # CRM agent
        self.register_agent(
            agent_id="agent_crm",
            agent_name="CRM Specialist",
            description="Handles CRM operations",
            supported_operations={
                "create_contact",
                "get_contact",
                "update_contact",
                "search_contacts",
                "create_deal",
                "log_activity",
            },
            expertise_level=9.0,
            availability=0.95,
            specializations={"data_management", "insights"},
        )
    
    # ========== Execution API ==========
    
    async def execute_from_prompt(
        self,
        user_query: str,
        correlation_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> WorkflowExecution:
        """Execute workflow from natural language prompt."""
        execution = await self.executor.execute_autonomous(
            user_query,
            correlation_id=correlation_id,
            max_retries=max_retries,
        )
        
        # Store in history
        self.execution_history[execution.execution_id] = execution
        
        return execution
    
    # ========== Learning API ==========
    
    def get_learnings_for_operation(self, operation: str) -> List[Dict[str, Any]]:
        """Get learnings for an operation."""
        pattern_key = f"operation:{operation}"
        records = self.learning_memory.get_learnings_for_pattern(pattern_key)
        
        return [
            {
                "pattern": r.pattern_description,
                "success_rate": 1.0 if r.success else 0.0,
                "latency_ms": r.latency_ms,
                "recommendation": r.recommendation,
            }
            for r in records
        ]
    
    def get_improvement_suggestions(self, execution_id: str) -> List[str]:
        """Get suggestions to improve a workflow."""
        if execution_id not in self.execution_history:
            return []
        
        execution = self.execution_history[execution_id]
        executions = list(self.execution_history.values())
        
        return self.improvement_suggester.suggest_optimizations(executions)
    
    # ========== Reasoning API ==========
    
    def replay_reasoning(self, trace_id: str) -> Dict[str, Any]:
        """Replay a reasoning chain."""
        return self.reasoning_replayer.replay_trace(trace_id)
    
    def analyze_reasoning_quality(self, trace_id: str) -> Dict[str, Any]:
        """Analyze quality of reasoning."""
        return self.reasoning_replayer.analyze_reasoning_confidence(trace_id)
    
    def detect_reasoning_failures(self, trace_id: str, execution_id: Optional[str] = None) -> List[Dict]:
        """Detect failures in reasoning."""
        execution = None
        if execution_id:
            execution = self.execution_history.get(execution_id)
        
        return self.failure_detector.detect_failures(trace_id, execution)
    
    def suggest_reasoning_improvements(self, trace_id: str, execution_id: Optional[str] = None) -> List[str]:
        """Suggest improvements to reasoning."""
        execution = None
        if execution_id:
            execution = self.execution_history.get(execution_id)
        
        return self.improvement_suggester_reasoning.suggest_improvements(trace_id, execution)
    
    # ========== Template API ==========
    
    def save_workflow_template(
        self,
        template_id: str,
        name: str,
        description: str,
        category: str,
        pattern: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Save a workflow template."""
        template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            user_query_pattern=pattern,
            workflow_plan=None,  # TODO: persist actual plan
            parameters=parameters,
            success_rate=0.8,
            average_duration_seconds=10.0,
        )
        
        self.workflow_templates[template_id] = template
    
    def get_templates_for_category(self, category: str) -> List[WorkflowTemplate]:
        """Get templates for a category."""
        return [t for t in self.workflow_templates.values() if t.category == category]
    
    # ========== Safety API ==========
    
    def add_safety_constraint(
        self,
        constraint_id: str,
        name: str,
        constraint_type: str,
        applies_to: Set[str],
        **kwargs,
    ) -> None:
        """Add safety constraint."""
        constraint = SafetyConstraint(
            constraint_id=constraint_id,
            name=name,
            description=kwargs.get("description", ""),
            constraint_type=constraint_type,
            applies_to=applies_to,
            **{k: v for k, v in kwargs.items() if k != "description"},
        )
        
        self.safety_manager.add_constraint(constraint)
    
    # ========== Stats API ==========
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        completed = [e for e in self.execution_history.values() 
                    if e.status.value == "completed"]
        failed = [e for e in self.execution_history.values() 
                 if e.status.value == "failed"]
        
        total_executions = len(self.execution_history)
        success_rate = len(completed) / total_executions if total_executions > 0 else 0.0
        
        avg_latency = (
            sum(e.total_latency_ms for e in completed) / len(completed)
            if completed else 0.0
        )
        
        return {
            "total_executions": total_executions,
            "successful_executions": len(completed),
            "failed_executions": len(failed),
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "tools_registered": len(self.tool_registry.tools),
            "agents_registered": len(self.agent_registry.agents),
            "templates_registered": len(self.workflow_templates),
            "learning_records": len(self.learning_memory.records),
        }


# Global orchestrator instance
_orchestrator: Optional[IntelligenceOrchestrator] = None


def get_intelligence_orchestrator() -> IntelligenceOrchestrator:
    """Get or create global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IntelligenceOrchestrator()
        _orchestrator.register_default_agents()
        _orchestrator.register_tools_from_adapters()
    return _orchestrator
