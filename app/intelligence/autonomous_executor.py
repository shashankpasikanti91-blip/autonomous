"""
Autonomous execution loop: goal-based execution with plan-execute-reflect-improve cycle.

Main execution engine coordinating all intelligence components.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Coroutine
from datetime import datetime, timedelta
from enum import Enum

from app.intelligence.models import (
    WorkflowPlan,
    WorkflowExecution,
    WorkflowStatus,
    TaskExecution,
    TaskStatus,
    ReasoningTrace,
    SafetyConstraint,
    generate_id,
)
from app.intelligence.prompt_compiler import PromptParser, WorkflowCompiler
from app.intelligence.agent_router import AgentRouter, ToolSelector
from app.intelligence.learning_system import LearningMemory, AdaptiveRetryStrategy
from app.intelligence.reasoning_tracer import ReasoningTraceStore


class ExecutionPhase(str, Enum):
    """Phases of autonomous execution."""
    PLANNING = "planning"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    REFLECTION = "reflection"
    LEARNING = "learning"


class AutonomousExecutor:
    """Main autonomous execution engine."""
    
    def __init__(
        self,
        prompt_parser: PromptParser,
        workflow_compiler: WorkflowCompiler,
        agent_router: AgentRouter,
        tool_selector: ToolSelector,
        learning_memory: LearningMemory,
        trace_store: ReasoningTraceStore,
        tool_registry=None,
        safety_constraints: Optional[List[SafetyConstraint]] = None,
    ):
        """Initialize executor."""
        self.parser = prompt_parser
        self.compiler = workflow_compiler
        self.agent_router = agent_router
        self.tool_selector = tool_selector
        self.learning_memory = learning_memory
        self.trace_store = trace_store
        self.tool_registry = tool_registry
        self.safety_constraints = safety_constraints or []
        
        self.retry_strategy = AdaptiveRetryStrategy(learning_memory)
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.tool_implementations = {}  # Map tool_id -> implementation
    
    def register_tool(self, tool_id: str, implementation: Callable) -> None:
        """Register tool implementation."""
        self.tool_implementations[tool_id] = implementation
    
    async def execute_autonomous(
        self,
        user_query: str,
        correlation_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> WorkflowExecution:
        """
        Execute workflow autonomously from user query.
        
        Handles: parsing → planning → execution → reflection → learning.
        """
        if correlation_id is None:
            correlation_id = generate_id("exec")
        
        # Phase 1: Planning
        parsed_intent = self.parser.parse(user_query)
        plan, reasoning_trace = self.compiler.compile(
            parsed_intent,
            user_query,
            correlation_id,
        )
        
        # Create execution record
        execution = WorkflowExecution(
            execution_id=correlation_id,
            workflow_template_id=None,
            plan_id=plan.plan_id,
            status=WorkflowStatus.CREATED,
            started_at=datetime.utcnow(),
            user_intent=user_query,
            reasoning_trace_id=reasoning_trace.trace_id,
        )
        
        self.active_executions[execution.execution_id] = execution
        self.trace_store.store_trace(reasoning_trace)
        
        try:
            # Phase 2: Execute plan
            execution = await self._execute_plan(execution, plan, max_retries)
            
            # Phase 3: Reflect on execution
            await self._reflect_on_execution(execution);
            
            # Phase 4: Learn from execution
            await self._learn_from_execution(execution)
            
        except Exception as e:
            execution.error = str(e)
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
        
        return execution
    
    async def _execute_plan(
        self,
        execution: WorkflowExecution,
        plan: WorkflowPlan,
        max_retries: int,
    ) -> WorkflowExecution:
        """Execute a workflow plan."""
        execution.status = WorkflowStatus.RUNNING
        start_time = datetime.utcnow()
        
        for step in plan.steps:
            step_results = await self._execute_step(execution, step, max_retries)
            
            # Check stop conditions
            if step.stop_on_failure:
                failed_tasks = [t for t in step_results if t[1].status == TaskStatus.FAILED]
                if failed_tasks:
                    execution.error = f"Step failed: {failed_tasks[0][1].error}"
                    execution.status = WorkflowStatus.FAILED
                    execution.completed_at = datetime.utcnow()
                    return execution
        
        execution.status = WorkflowStatus.COMPLETED
        execution.completed_at = datetime.utcnow()
        execution.total_latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return execution
    
    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step,
        max_retries: int,
    ) -> List[tuple]:
        """Execute a single workflow step."""
        task_results = []
        
        if step.parallel_execution:
            # Execute tasks in parallel
            tasks = [
                self._execute_task(execution, task, max_retries)
                for task in step.tasks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            task_results = [(task, result) for task, result in zip(step.tasks, results)]
        else:
            # Execute tasks sequentially
            for task in step.tasks:
                result = await self._execute_task(execution, task, max_retries)
                task_results.append((task, result))
        
        return task_results
    
    async def _execute_task(
        self,
        execution: WorkflowExecution,
        task,
        max_retries: int,
        attempt: int = 0,
    ) -> TaskExecution:
        """Execute a single task with retry logic."""
        # Create task execution record
        task_exec = TaskExecution(
            execution_id=generate_id("task_exec"),
            task_id=task.task_id,
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            input_parameters=task.parameters,
        )
        
        execution.task_executions[task.task_id] = task_exec
        
        try:
            # Check safety constraints
            if not self._check_safety(task):
                task_exec.status = TaskStatus.FAILED
                task_exec.error = "Safety constraint violated"
                return task_exec
            
            # Select agent and tool
            agent_id, agent_confidence, agent_info = await self.agent_router.select_agent_for_task(
                task,
                [],  # reasoning trace steps
            )
            
            tool_sig, tool_confidence, tool_info = await self.tool_selector.select_tool_for_task(
                task,
                [],
            )
            
            task_exec.agent_id = agent_id
            task_exec.tool_id = tool_sig.tool_id if tool_sig else None
            
            # Mark agent as busy
            if agent_id:
                await self.agent_router.mark_agent_busy(agent_id)
            
            # Execute tool
            result = await self._call_tool(tool_sig, task)
            
            # Mark agent as free
            if agent_id:
                await self.agent_router.mark_agent_free(agent_id)
            
            task_exec.result = result
            task_exec.status = TaskStatus.COMPLETED
            task_exec.completed_at = datetime.utcnow()
            task_exec.latency_ms = (
                (datetime.utcnow() - task_exec.started_at).total_seconds() * 1000
            )
            
        except Exception as e:
            task_exec.error = str(e)
            task_exec.error_category = type(e).__name__
            
            # Adaptive retry logic
            if attempt < max_retries and attempt < task.max_retries:
                retry_strategy = self.retry_strategy.get_retry_strategy(
                    task.operation,
                    task_exec.error_category,
                    attempt,
                )
                
                if retry_strategy.get("should_retry"):
                    await asyncio.sleep(retry_strategy.get("backoff_seconds", 1))
                    task_exec.retry_count += 1
                    task_exec.status = TaskStatus.RETRYING
                    return await self._execute_task(execution, task, max_retries, attempt + 1)
            
            task_exec.status = TaskStatus.FAILED
            task_exec.completed_at = datetime.utcnow()
        
        return task_exec
    
    async def _call_tool(self, tool_sig, task) -> Any:
        """Call tool implementation."""
        if not tool_sig or tool_sig.tool_id not in self.tool_implementations:
            raise ValueError(f"Tool {tool_sig.tool_id if tool_sig else 'unknown'} not implemented")
        
        tool_impl = self.tool_implementations[tool_sig.tool_id]
        
        # Call tool (may be async or sync)
        if asyncio.iscoroutinefunction(tool_impl):
            return await tool_impl(**task.parameters)
        else:
            return tool_impl(**task.parameters)
    
    def _check_safety(self, task) -> bool:
        """Check if task violates safety constraints."""
        for constraint in self.safety_constraints:
            if task.task_id in constraint.applies_to or "*" in constraint.applies_to:
                # Check specific constraints
                if constraint.blocked_operations and task.operation in constraint.blocked_operations:
                    return False
        
        return True
    
    async def _reflect_on_execution(self, execution: WorkflowExecution) -> None:
        """Reflect on execution results."""
        # Analyze what went well/poorly
        completed_count = sum(1 for t in execution.task_executions.values() 
                            if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in execution.task_executions.values() 
                         if t.status == TaskStatus.FAILED)
        
        success_rate = (
            completed_count / len(execution.task_executions)
            if execution.task_executions else 0.0
        )
        
        print(f"Execution reflection: {success_rate:.0%} success rate "
              f"({completed_count} completed, {failed_count} failed)")
    
    async def _learn_from_execution(self, execution: WorkflowExecution) -> None:
        """Learn from execution results."""
        success = execution.status == WorkflowStatus.COMPLETED
        
        # Record learning
        self.learning_memory.record_learning(
            execution_id=execution.execution_id,
            learning_type="success" if success else "failure",
            pattern_description=execution.user_intent or "unknown",
            pattern_data={
                "workflow_plan_id": execution.plan_id,
                "task_count": len(execution.task_executions),
                "duration_ms": execution.total_latency_ms,
            },
            success=success,
            latency_ms=execution.total_latency_ms,
            confidence=0.8,
        )
        
        print(f"Learning recorded: {'Success' if success else 'Failure'} "
              f"in {execution.total_latency_ms:.0f}ms")


class SafetyConstraintManager:
    """Manage safety constraints for autonomous execution."""
    
    def __init__(self):
        """Initialize manager."""
        self.constraints: Dict[str, SafetyConstraint] = {}
    
    def add_constraint(self, constraint: SafetyConstraint) -> None:
        """Add safety constraint."""
        self.constraints[constraint.constraint_id] = constraint
    
    def check_constraint(self, agent_id: str, operation: str, cost: float = 0.0) -> bool:
        """Check if operation is allowed."""
        for constraint in self.constraints.values():
            if agent_id in constraint.applies_to or "*" in constraint.applies_to:
                # Check cost limit
                if (constraint.max_cost_per_workflow is not None 
                    and cost > constraint.max_cost_per_workflow):
                    return False
                
                # Check blocked operations
                if operation in constraint.blocked_operations:
                    return False
        
        return True
    
    def get_rate_limit_for_agent(self, agent_id: str) -> Optional[int]:
        """Get rate limit for an agent."""
        for constraint in self.constraints.values():
            if agent_id in constraint.applies_to:
                return constraint.max_api_calls_per_hour
        
        return None
