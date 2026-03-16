"""
Agent Orchestration Service

Manages:
- Agent routing based on workflow requirements
- Async task execution with proper concurrency control
- Memory context maintenance
- Error handling with retries
- Logging and monitoring
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
import asyncio
from enum import Enum

from core.models import (
    WorkflowExecution, ExecutionStatus, Event, 
    AgentResponse, ReasoningChain
)
from core.workflows.engine import EventBus
from core.agents.base import BaseAgent
from core.memory.implementations import HybridMemory
from utils.logger import get_logger
from services.connectors import ServiceConnectorFactory


logger = get_logger(__name__)


class ExecutionStrategy(str, Enum):
    """Execution strategies for orchestration."""
    SEQUENTIAL = "sequential"  # One step after another
    PARALLEL = "parallel"  # All steps at once
    BATCHED = "batched"  # Groups of steps
    PRIORITY_BASED = "priority_based"  # By priority


class RetryPolicy:
    """Retry policy configuration."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_ms: float = 100.0,
        max_delay_ms: float = 10000.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.exponential_base = exponential_base
    
    def get_delay_ms(self, attempt: int) -> float:
        """Calculate delay for attempt using exponential backoff."""
        delay = self.initial_delay_ms * (self.exponential_base ** attempt)
        return min(delay, self.max_delay_ms)


class OrchestrationContext:
    """Context maintained across an orchestration run."""
    
    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        initial_data: Dict[str, Any]
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.initial_data = initial_data
        self.step_results: Dict[str, Any] = {}
        self.agent_reasoning: Dict[str, ReasoningChain] = {}
        self.memory_access_log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
    
    def add_step_result(self, step_id: str, result: Any) -> None:
        """Add result from a step."""
        self.step_results[step_id] = result
        logger.info(f"[ORCHESTRATION] Step result: {step_id}")
    
    def add_reasoning(self, agent_id: str, reasoning: ReasoningChain) -> None:
        """Add reasoning from agent."""
        self.agent_reasoning[agent_id] = reasoning
    
    def add_error(self, step_id: str, error: str, details: Dict[str, Any] = None) -> None:
        """Record error."""
        self.errors.append({
            "step_id": step_id,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_execution_duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        end = self.end_time or datetime.now(timezone.utc)
        delta = end - self.start_time
        return delta.total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "initial_data": self.initial_data,
            "step_results": self.step_results,
            "agent_reasoning": {
                k: v.model_dump() if hasattr(v, 'model_dump') else v 
                for k, v in self.agent_reasoning.items()
            },
            "errors": self.errors,
            "duration_ms": self.get_execution_duration_ms(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class AgentOrchestrationService:
    """Orchestrates agent execution across workflows."""
    
    def __init__(
        self,
        event_bus: EventBus,
        memory: HybridMemory,
        service_factory: ServiceConnectorFactory
    ):
        self.event_bus = event_bus
        self.memory = memory
        self.service_factory = service_factory
        self.agents: Dict[str, BaseAgent] = {}
        self.retry_policy = RetryPolicy()
        self.default_strategy = ExecutionStrategy.SEQUENTIAL
        logger.info("Agent orchestration service initialized")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent for orchestration."""
        self.agents[agent.agent_id] = agent
        logger.info(f"[ORCHESTRATION] Agent registered: {agent.agent_id}")
    
    def set_retry_policy(self, policy: RetryPolicy) -> None:
        """Set retry policy."""
        self.retry_policy = policy
    
    async def route_task(
        self,
        context: OrchestrationContext,
        agent_id: str,
        task_data: Dict[str, Any],
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Route a task to an agent with retry logic.
        
        Args:
            context: Orchestration context
            agent_id: Agent to route to
            task_data: Task input data
            tools: Specific tools agent should use
        
        Returns:
            Agent response
        """
        if agent_id not in self.agents:
            error_msg = f"Agent not found: {agent_id}"
            context.add_error("routing", error_msg)
            logger.error(f"[ORCHESTRATION] {error_msg}")
            raise ValueError(error_msg)
        
        agent = self.agents[agent_id]
        attempt = 0
        
        while attempt <= self.retry_policy.max_retries:
            try:
                logger.info(
                    f"[ORCHESTRATION] Routing task to {agent_id} "
                    f"(attempt {attempt + 1})"
                )
                
                # Publish event
                await self.event_bus.publish(Event(
                    id=f"event_{hash(str(datetime.now(timezone.utc)))}",
                    event_type="task_routed",
                    source="Orchestration",
                    data={
                        "agent_id": agent_id,
                        "attempt": attempt + 1,
                        "task_data": task_data
                    }
                ))
                
                # Execute with agent
                agent_response = await agent.process(
                    input_data=task_data,
                    context={"execution_id": context.execution_id}
                )
                
                # Store reasoning if available
                if hasattr(agent_response, 'reasoning_chain') and agent_response.reasoning_chain:
                    context.add_reasoning(agent_id, agent_response.reasoning_chain)
                
                logger.info(f"[ORCHESTRATION] Task completed by {agent_id}")
                
                return agent_response.model_dump() if hasattr(agent_response, 'model_dump') else agent_response
            
            except Exception as e:
                logger.error(f"[ORCHESTRATION] Task failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt < self.retry_policy.max_retries:
                    delay_ms = self.retry_policy.get_delay_ms(attempt)
                    logger.info(f"[ORCHESTRATION] Retrying in {delay_ms}ms")
                    await asyncio.sleep(delay_ms / 1000.0)
                    attempt += 1
                else:
                    context.add_error(f"agent_{agent_id}", str(e), {"attempts": attempt + 1})
                    raise
    
    async def execute_workflow(
        self,
        context: OrchestrationContext,
        steps: List[Dict[str, Any]],
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        Execute workflow steps using specified strategy.
        
        Args:
            context: Orchestration context
            steps: List of workflow steps
            strategy: Execution strategy
        
        Returns:
            Execution results
        """
        logger.info(f"[ORCHESTRATION] Starting workflow with {len(steps)} steps ({strategy.value})")
        
        try:
            if strategy == ExecutionStrategy.SEQUENTIAL:
                result = await self._execute_sequential(context, steps)
            elif strategy == ExecutionStrategy.PARALLEL:
                result = await self._execute_parallel(context, steps)
            elif strategy == ExecutionStrategy.BATCHED:
                result = await self._execute_batched(context, steps)
            elif strategy == ExecutionStrategy.PRIORITY_BASED:
                result = await self._execute_priority_based(context, steps)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            context.end_time = datetime.now(timezone.utc)
            logger.info(f"[ORCHESTRATION] Workflow completed successfully")
            
            return result
        
        except Exception as e:
            context.end_time = datetime.now(timezone.utc)
            context.add_error("workflow", str(e))
            logger.error(f"[ORCHESTRATION] Workflow failed: {str(e)}")
            raise
    
    async def _execute_sequential(
        self,
        context: OrchestrationContext,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute steps sequentially."""
        logger.info("[ORCHESTRATION] Executing sequentially")
        
        for step in steps:
            step_id = step.get("id")
            agent_id = step.get("agent_id")
            task_data = step.get("data", {})
            tools = step.get("tools")
            
            try:
                result = await self.route_task(
                    context, agent_id, task_data, tools
                )
                context.add_step_result(step_id, result)
            except Exception as e:
                logger.error(f"[ORCHESTRATION] Step {step_id} failed: {str(e)}")
                context.add_error(step_id, str(e))
                raise
        
        return context.to_dict()
    
    async def _execute_parallel(
        self,
        context: OrchestrationContext,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute steps in parallel."""
        logger.info("[ORCHESTRATION] Executing in parallel")
        
        tasks = []
        step_map = {}
        
        for step in steps:
            step_id = step.get("id")
            agent_id = step.get("agent_id")
            task_data = step.get("data", {})
            tools = step.get("tools")
            
            step_map[step_id] = {
                "index": len(tasks),
                "agent_id": agent_id,
                "task_data": task_data,
                "tools": tools
            }
            
            task = self.route_task(context, agent_id, task_data, tools)
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step_id, step_info in step_map.items():
                result = results[step_info["index"]]
                if isinstance(result, Exception):
                    context.add_error(step_id, str(result))
                else:
                    context.add_step_result(step_id, result)
        
        except Exception as e:
            logger.error(f"[ORCHESTRATION] Parallel execution failed: {str(e)}")
            raise
        
        return context.to_dict()
    
    async def _execute_batched(
        self,
        context: OrchestrationContext,
        steps: List[Dict[str, Any]],
        batch_size: int = 3
    ) -> Dict[str, Any]:
        """Execute steps in batches."""
        logger.info(f"[ORCHESTRATION] Executing in batches of {batch_size}")
        
        for i in range(0, len(steps), batch_size):
            batch = steps[i:i+batch_size]
            logger.info(f"[ORCHESTRATION] Processing batch {i//batch_size + 1}")
            
            tasks = []
            for step in batch:
                agent_id = step.get("agent_id")
                task_data = step.get("data", {})
                tools = step.get("tools")
                
                task = self.route_task(context, agent_id, task_data, tools)
                tasks.append((step.get("id"), task))
            
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            for (step_id, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    context.add_error(step_id, str(result))
                else:
                    context.add_step_result(step_id, result)
        
        return context.to_dict()
    
    async def _execute_priority_based(
        self,
        context: OrchestrationContext,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute steps by priority."""
        logger.info("[ORCHESTRATION] Executing by priority")
        
        # Sort by priority (higher first)
        sorted_steps = sorted(
            steps,
            key=lambda s: s.get("priority", 0),
            reverse=True
        )
        
        return await self._execute_sequential(context, sorted_steps)
    
    async def execute_with_fallback(
        self,
        context: OrchestrationContext,
        primary_step: Dict[str, Any],
        fallback_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute primary step with fallback options.
        
        Args:
            context: Orchestration context
            primary_step: Primary step to execute
            fallback_steps: Fallback steps if primary fails
        
        Returns:
            Execution result
        """
        logger.info("[ORCHESTRATION] Executing with fallback")
        
        try:
            result = await self.route_task(
                context,
                primary_step.get("agent_id"),
                primary_step.get("data", {}),
                primary_step.get("tools")
            )
            context.add_step_result(primary_step.get("id"), result)
            return result
        
        except Exception as e:
            logger.warning(f"[ORCHESTRATION] Primary failed: {str(e)}")
            
            if fallback_steps:
                logger.info(f"[ORCHESTRATION] Executing {len(fallback_steps)} fallback steps")
                for fallback in fallback_steps:
                    try:
                        result = await self.route_task(
                            context,
                            fallback.get("agent_id"),
                            fallback.get("data", {}),
                            fallback.get("tools")
                        )
                        context.add_step_result(fallback.get("id"), result)
                        return result
                    except Exception as fb_error:
                        logger.error(f"Fallback failed: {str(fb_error)}")
                        continue
            
            raise
