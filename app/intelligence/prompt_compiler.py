"""
Prompt-to-workflow compiler: converts user intent into executable workflow plans.

Parses natural language, extracts intent, generates dynamic execution plans.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
import re
import json
from enum import Enum

from app.intelligence.models import (
    TaskDefinition,
    TaskStatus,
    WorkflowStep,
    WorkflowPlan,
    ReasoningStep,
    ReasoningTrace,
    ReasoningType,
    generate_id,
)


class IntentType(str, Enum):
    """Recognized types of user intent."""
    SEND_COMMUNICATION = "send_communication"  # Email, message, etc.
    RETRIEVE_DATA = "retrieve_data"  # Lookup contact, check status, etc.
    CREATE_RESOURCE = "create_resource"  # Create event, contact, deal, etc.
    UPDATE_RESOURCE = "update_resource"
    DELETE_RESOURCE = "delete_resource"
    SEARCH_AND_FILTER = "search_and_filter"
    SCHEDULE_ACTION = "schedule_action"
    BATCH_OPERATION = "batch_operation"
    CONDITIONAL_WORKFLOW = "conditional_workflow"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Extracted intent from user query."""
    intent_type: IntentType
    primary_action: str
    target_resource: str
    parameters: Dict[str, Any]
    confidence: float
    alternative_intents: List[Tuple[IntentType, float]] = None


class PromptParser:
    """Parse user natural language prompts into structured intents."""
    
    def __init__(self):
        """Initialize parser with intent patterns."""
        self.intent_keywords = {
            IntentType.SEND_COMMUNICATION: {"send", "email", "message", "notify", "alert", "contact"},
            IntentType.RETRIEVE_DATA: {"get", "fetch", "lookup", "find", "search", "check", "status"},
            IntentType.CREATE_RESOURCE: {"create", "new", "add", "generate", "make", "book", "schedule"},
            IntentType.UPDATE_RESOURCE: {"update", "change", "modify", "edit", "sync", "refresh"},
            IntentType.DELETE_RESOURCE: {"delete", "remove", "cancel", "discard", "clear"},
            IntentType.SEARCH_AND_FILTER: {"search", "filter", "list", "find", "query"},
            IntentType.BATCH_OPERATION: {"batch", "multiple", "bulk", "all"},
        }
        
        self.resource_keywords = {
            "email": {"email", "mail", "send email"},
            "contact": {"contact", "person", "user", "lead"},
            "event": {"event", "meeting", "calendar", "appointment"},
            "deal": {"deal", "opportunity"},
            "message": {"message", "text", "whatsapp", "sms", "notification"},
            "campaign": {"campaign", "blast", "compaign"},
        }
    
    def parse(self, user_query: str) -> ParsedIntent:
        """Parse user query into structured intent."""
        query_lower = user_query.lower()
        
        # Detect intent type
        intent_scores = {}
        for intent_type, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                intent_scores[intent_type] = score / len(keywords)
        
        if not intent_scores:
            intent_type = IntentType.UNKNOWN
            confidence = 0.0
        else:
            intent_type = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[intent_type], 1.0)
        
        # Detect resource being modified
        target_resource = "unknown"
        for resource, keywords in self.resource_keywords.items():
            if any(kw in query_lower for kw in keywords):
                target_resource = resource
                break
        
        # Extract primary action
        primary_action = self._extract_action(query_lower, intent_type)
        
        # Extract parameters from query
        parameters = self._extract_parameters(user_query, intent_type, target_resource)
        
        # Find alternative intents
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(intent, score) for intent, score in sorted_intents[1:3]]
        
        return ParsedIntent(
            intent_type=intent_type,
            primary_action=primary_action,
            target_resource=target_resource,
            parameters=parameters,
            confidence=confidence,
            alternative_intents=alternatives if alternatives else None,
        )
    
    def _extract_action(self, query_lower: str, intent_type: IntentType) -> str:
        """Extract the primary action verb."""
        action_patterns = {
            IntentType.SEND_COMMUNICATION: ["send", "email", "message", "notify"],
            IntentType.RETRIEVE_DATA: ["get", "fetch", "lookup", "find"],
            IntentType.CREATE_RESOURCE: ["create", "add", "new", "schedule"],
            IntentType.UPDATE_RESOURCE: ["update", "modify", "change"],
            IntentType.DELETE_RESOURCE: ["delete", "remove", "cancel"],
        }
        
        if intent_type in action_patterns:
            for action in action_patterns[intent_type]:
                if action in query_lower:
                    return action
        
        return "execute"
    
    def _extract_parameters(
        self, query: str, intent_type: IntentType, target_resource: str
    ) -> Dict[str, Any]:
        """Extract parameters from query text."""
        params = {}
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        if emails:
            params["to_addresses"] = emails
        
        # Phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, query)
        if phones:
            params["phone_numbers"] = phones
        
        # Quoted strings (likely content)
        quoted_pattern = r'"([^"]*)"'
        quotes = re.findall(quoted_pattern, query)
        if quotes:
            if intent_type == IntentType.SEND_COMMUNICATION:
                params["subject"] = quotes[0] if len(quotes) > 0 else None
                params["body"] = quotes[1] if len(quotes) > 1 else None
        
        # Numbers (amounts, counts, etc.)
        number_pattern = r'\b\d+\b'
        numbers = re.findall(number_pattern, query)
        if numbers:
            params["count"] = int(numbers[0]) if len(numbers) > 0 else 1
        
        # Date/time (basic detection)
        if any(word in query.lower() for word in ["today", "tomorrow", "next week", "next month"]):
            params["timing"] = "scheduled"
        
        params["target_resource"] = target_resource
        
        return params


class WorkflowCompiler:
    """Compile parsed intents into executable workflow plans."""
    
    def __init__(self, tool_registry=None, agent_registry=None):
        """Initialize compiler."""
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry
        self.reasoning_steps = []
    
    def compile(
        self,
        parsed_intent: ParsedIntent,
        user_query: str,
        correlation_id: str = None,
    ) -> Tuple[WorkflowPlan, ReasoningTrace]:
        """Compile parsed intent into workflow plan."""
        if correlation_id is None:
            correlation_id = generate_id("compile")
        
        # Create reasoning trace to track compilation
        trace = ReasoningTrace(
            trace_id=generate_id("trace"),
            execution_id=correlation_id,
            user_query=user_query,
            created_at=datetime.utcnow(),
        )
        
        # Step 1: Analyze intent
        analysis_step = self._reasoning_step(
            ReasoningType.ANALYSIS,
            {
                "user_query": user_query,
                "parsed_intent": str(parsed_intent),
            },
            f"Analyzed user query and extracted intent type: {parsed_intent.intent_type.value}",
            {
                "intent_type": parsed_intent.intent_type.value,
                "confidence": parsed_intent.confidence,
                "primary_action": parsed_intent.primary_action,
            },
            parsed_intent.confidence,
        )
        trace.steps.append(analysis_step)
        
        # Step 2: Generate tasks based on intent
        tasks = self._generate_tasks(parsed_intent, trace)
        
        # Step 3: Plan workflow steps
        steps = self._plan_workflow_steps(tasks, trace)
        
        # Step 4: Create workflow plan
        plan = WorkflowPlan(
            plan_id=generate_id("plan"),
            name=f"Workflow for: {user_query[:50]}",
            description=f"Auto-generated plan for {parsed_intent.intent_type.value}",
            user_intent=user_query,
            confidence=parsed_intent.confidence,
            steps=steps,
            estimated_duration_seconds=self._estimate_duration(tasks),
            estimated_cost=self._estimate_cost(tasks),
            tags={parsed_intent.intent_type.value, parsed_intent.target_resource},
        )
        
        trace.final_plan_id = plan.plan_id
        
        # Final reflection step
        reflection_step = self._reasoning_step(
            ReasoningType.REFLECTION,
            {
                "task_count": len(tasks),
                "step_count": len(steps),
                "estimated_duration": plan.estimated_duration_seconds,
            },
            f"Generated workflow plan with {len(steps)} steps containing {len(tasks)} tasks",
            {
                "plan_id": plan.plan_id,
                "status": "ready_for_execution",
            },
            0.95,
        )
        trace.steps.append(reflection_step)
        
        return plan, trace
    
    def _generate_tasks(self, intent: ParsedIntent, trace: ReasoningTrace) -> List[TaskDefinition]:
        """Generate tasks from parsed intent."""
        tasks = []
        
        planning_step = self._reasoning_step(
            ReasoningType.PLANNING,
            {
                "intent_type": intent.intent_type.value,
                "target_resource": intent.target_resource,
                "parameters": intent.parameters,
            },
            "Generating tasks from intent",
            {},
            0.9,
        )
        
        # Task generation depends on intent type
        if intent.intent_type == IntentType.SEND_COMMUNICATION:
            # Generate send task
            task = TaskDefinition(
                task_id=generate_id("task"),
                name="Send Communication",
                description=f"Send {intent.target_resource}",
                operation=f"send_{intent.target_resource}",
                parameters=intent.parameters,
                timeout_seconds=60.0,
                max_retries=3,
            )
            tasks.append(task)
            
            planning_step.output_decision["tasks_generated"] = 1
            planning_step.output_decision["task_types"] = ["send"]
        
        elif intent.intent_type == IntentType.RETRIEVE_DATA:
            # Generate lookup task
            task = TaskDefinition(
                task_id=generate_id("task"),
                name="Retrieve Data",
                description=f"Look up {intent.target_resource}",
                operation=f"get_{intent.target_resource}",
                parameters=intent.parameters,
                timeout_seconds=30.0,
                max_retries=2,
            )
            tasks.append(task)
            
            planning_step.output_decision["tasks_generated"] = 1
            planning_step.output_decision["task_types"] = ["retrieve"]
        
        elif intent.intent_type == IntentType.CREATE_RESOURCE:
            # Generate creation task
            task = TaskDefinition(
                task_id=generate_id("task"),
                name="Create Resource",
                description=f"Create new {intent.target_resource}",
                operation=f"create_{intent.target_resource}",
                parameters=intent.parameters,
                timeout_seconds=60.0,
                max_retries=2,
            )
            tasks.append(task)
            
            planning_step.output_decision["tasks_generated"] = 1
            planning_step.output_decision["task_types"] = ["create"]
        
        elif intent.intent_type == IntentType.BATCH_OPERATION:
            # Generate multiple tasks
            count = intent.parameters.get("count", 1)
            for i in range(count):
                task = TaskDefinition(
                    task_id=generate_id("task"),
                    name=f"Batch Item {i+1}",
                    description=f"Execute batch operation {i+1}",
                    operation=f"batch_{intent.primary_action}",
                    parameters={**intent.parameters, "index": i},
                    timeout_seconds=60.0,
                    max_retries=2,
                )
                tasks.append(task)
            
            planning_step.output_decision["tasks_generated"] = len(tasks)
            planning_step.output_decision["task_types"] = ["batch"]
        
        else:
            # Generic task
            task = TaskDefinition(
                task_id=generate_id("task"),
                name=intent.primary_action.title(),
                description=f"Execute {intent.primary_action}",
                operation=intent.primary_action,
                parameters=intent.parameters,
                timeout_seconds=300.0,
                max_retries=2,
            )
            tasks.append(task)
        
        trace.steps.append(planning_step)
        
        return tasks
    
    def _plan_workflow_steps(self, tasks: List[TaskDefinition], trace: ReasoningTrace) -> List[WorkflowStep]:
        """Organize tasks into workflow steps."""
        steps = []
        
        # For now, simple approach: one step per task or parallel batch
        if len(tasks) == 1:
            step = WorkflowStep(
                step_id=generate_id("step"),
                step_number=1,
                name="Execute Task",
                description=tasks[0].description,
                tasks=tasks,
                parallel_execution=False,
            )
            steps.append(step)
        
        elif len(tasks) <= 3:
            # Small batch - try parallel
            step = WorkflowStep(
                step_id=generate_id("step"),
                step_number=1,
                name="Execute Batch",
                description=f"Execute {len(tasks)} tasks",
                tasks=tasks,
                parallel_execution=True,
            )
            steps.append(step)
        
        else:
            # Large batch - sequential in chunks
            chunk_size = 5
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i:i+chunk_size]
                step = WorkflowStep(
                    step_id=generate_id("step"),
                    step_number=i // chunk_size + 1,
                    name=f"Batch {i // chunk_size + 1}",
                    description=f"Execute {len(chunk)} tasks",
                    tasks=chunk,
                    parallel_execution=True,
                )
                steps.append(step)
        
        return steps
    
    def _estimate_duration(self, tasks: List[TaskDefinition]) -> float:
        """Estimate execution time."""
        # Default: 1-5 seconds per task
        return len(tasks) * 2.5
    
    def _estimate_cost(self, tasks: List[TaskDefinition]) -> float:
        """Estimate cost in credits."""
        # Default: minimal cost
        return len(tasks) * 0.1
    
    def _reasoning_step(
        self,
        reasoning_type: ReasoningType,
        input_context: Dict[str, Any],
        reasoning_text: str,
        output_decision: Dict[str, Any],
        confidence: float,
    ) -> ReasoningStep:
        """Create a reasoning step."""
        return ReasoningStep(
            step_id=generate_id("reasoning"),
            reasoning_type=reasoning_type,
            timestamp=datetime.utcnow(),
            input_context=input_context,
            reasoning_text=reasoning_text,
            output_decision=output_decision,
            confidence=confidence,
        )
