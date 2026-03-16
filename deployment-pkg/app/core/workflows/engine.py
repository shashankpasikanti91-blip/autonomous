"""
Asynchronous workflow engine with event-driven architecture.
"""
from typing import Any, Dict, List, Optional, Callable
import asyncio
from datetime import datetime
from core.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowStepDefinition,
    ExecutionStatus, Event
)
from core.agents.base import BaseAgent
from utils.logger import get_logger
from utils.errors import WorkflowException


logger = get_logger(__name__)


class EventBus:
    """
    Event bus for event-driven architecture.
    Handles event publishing and subscription.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.logger = get_logger(f"{__name__}.EventBus")
    
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.logger.info(f"Subscribed to event: {event_type}")
    
    async def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            self.logger.info(f"Unsubscribed from event: {event_type}")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event object to publish
        """
        self.event_history.append(event)
        self.logger.info(f"Publishing event: {event.event_type}")
        
        handlers = self.subscribers.get(event.event_type, [])
        
        # Execute all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(self, event_type: Optional[str] = None) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            return [e for e in self.event_history if e.event_type == event_type]
        return self.event_history


class WorkflowEngine:
    """
    Asynchronous workflow execution engine.
    Coordinates agent execution and tool usage.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.logger = get_logger(f"{__name__}.WorkflowEngine")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the engine."""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self.workflows[workflow.id] = workflow
        self.logger.info(f"Registered workflow: {workflow.id}")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            
        Returns:
            Workflow execution record
        """
        try:
            if workflow_id not in self.workflows:
                raise WorkflowException(
                    f"Workflow {workflow_id} not found",
                    code="WORKFLOW_NOT_FOUND"
                )
            
            workflow = self.workflows[workflow_id]
            execution = WorkflowExecution(
                id=f"exec_{hash(str(datetime.utcnow()))}",
                workflow_id=workflow_id,
                status=ExecutionStatus.RUNNING
            )
            
            self.executions[execution.id] = execution
            
            # Publish start event
            await self.event_bus.publish(Event(
                id=f"event_{len(self.event_bus.event_history)}",
                event_type="workflow_started",
                source="WorkflowEngine",
                data={"workflow_id": workflow_id, "execution_id": execution.id},
                correlation_id=execution.id
            ))
            
            # Execute steps
            current_step_id = workflow.entry_point
            
            while current_step_id:
                step = next((s for s in workflow.steps if s.id == current_step_id), None)
                
                if not step:
                    break
                
                execution.current_step = current_step_id
                
                # Execute step
                try:
                    await self._execute_step(step, execution, input_data or {})
                    execution.steps_executed.append(current_step_id)
                except Exception as e:
                    execution.errors.append(str(e))
                    self.logger.error(f"Step execution failed: {str(e)}")
                
                # Determine next step
                current_step_id = step.next_steps[0] if step.next_steps else None
            
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            # Publish completion event
            await self.event_bus.publish(Event(
                id=f"event_{len(self.event_bus.event_history)}",
                event_type="workflow_completed",
                source="WorkflowEngine",
                data={"workflow_id": workflow_id, "execution_id": execution.id},
                correlation_id=execution.id
            ))
            
            self.logger.info(f"Workflow execution completed: {execution.id}")
            return execution
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            self.logger.error(error_msg)
            raise WorkflowException(error_msg)
    
    async def _execute_step(
        self,
        step: WorkflowStepDefinition,
        execution: WorkflowExecution,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Execute a single workflow step asynchronously.
        Handles agent invocation, tool execution, error handling, and memory integration.
        """
        self.logger.info(f"[STEP_EXECUTION] Executing step: {step.id} - {step.name}")
        
        # Publish step started event
        await self.event_bus.publish(Event(
            id=f"event_{len(self.event_bus.event_history)}",
            event_type="step_started",
            source="WorkflowEngine",
            data={
                "step_id": step.id,
                "step_name": step.name,
                "execution_id": execution.id,
                "timestamp": datetime.utcnow().isoformat()
            },
            correlation_id=execution.id
        ))
        
        step_results = {}
        
        try:
            # Execute agent if assigned
            if step.agent_id and step.agent_id in self.agents:
                agent = self.agents[step.agent_id]
                execution.agents_involved.append(step.agent_id)
                
                self.logger.info(
                    f"[STEP_EXECUTION] Agent {agent.name} "
                    f"({agent.role.value}) processing step {step.id}"
                )
                
                # Prepare input for agent
                agent_input = {
                    "task": step.name,
                    "objective": step.description,
                    "context": input_data,
                    "tools": list(agent.tools.keys())
                }
                
                # Process with agent (includes reasoning chain)
                agent_response = await agent.process(agent_input)
                
                # Store agent response data
                step_results["agent_response"] = agent_response.model_dump()
                step_results["reasoning_chain"] = (
                    agent_response.reasoning_chain.model_dump()
                    if agent_response.reasoning_chain else None
                )
                step_results["execution_plan"] = (
                    agent_response.execution_plan.model_dump()
                    if agent_response.execution_plan else None
                )
                step_results["memory_accessed"] = agent_response.memory_accessed
                
                # Update execution results
                if agent_response.result:
                    execution.results = execution.results or {}
                    execution.results[step.id] = agent_response.result
                
                self.logger.info(
                    f"[STEP_EXECUTION] Agent {agent.name} completed "
                    f"with status: {agent_response.status.value}"
                )
            
            # Execute tools asynchronously
            if step.tool_calls:
                self.logger.info(
                    f"[STEP_EXECUTION] Executing {len(step.tool_calls)} tool calls"
                )
                
                tool_execution_tasks = []
                
                for tool_request in step.tool_calls:
                    if step.agent_id and step.agent_id in self.agents:
                        agent = self.agents[step.agent_id]
                        
                        self.logger.info(
                            f"[STEP_EXECUTION] Queuing tool: {tool_request.tool_id}"
                        )
                        
                        # Create async task for tool execution
                        task = asyncio.create_task(
                            agent.execute_tool(tool_request)
                        )
                        tool_execution_tasks.append(task)
                
                # Execute all tools concurrently
                if tool_execution_tasks:
                    tool_results = await asyncio.gather(
                        *tool_execution_tasks,
                        return_exceptions=False
                    )
                    
                    for result in tool_results:
                        if result:
                            execution.tool_calls.append(result)
                            self.logger.info(
                                f"[STEP_EXECUTION] Tool {result.tool_id} "
                                f"completed with status: {result.status.value}"
                            )
            
            step_results["status"] = "completed"
            
        except Exception as e:
            error_msg = f"Step execution failed: {str(e)}"
            self.logger.error(f"[STEP_EXECUTION] {error_msg}")
            execution.errors.append(error_msg)
            step_results["status"] = "failed"
            step_results["error"] = error_msg
        
        # Store step results
        execution.results = execution.results or {}
        execution.results[step.id] = step_results
        execution.steps_executed.append(step.id)
        
        # Publish step completed event
        await self.event_bus.publish(Event(
            id=f"event_{len(self.event_bus.event_history)}",
            event_type="step_completed",
            source="WorkflowEngine",
            data={
                "step_id": step.id,
                "step_name": step.name,
                "execution_id": execution.id,
                "status": step_results.get("status", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            },
            correlation_id=execution.id
        ))
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution details."""
        return self.executions.get(execution_id)
    
    def list_executions(self, workflow_id: Optional[str] = None) -> List[WorkflowExecution]:
        """List all executions, optionally filtered by workflow."""
        executions = list(self.executions.values())
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        return executions
    
    async def get_event_history(
        self,
        execution_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[Event]:
        """Get event history."""
        events = self.event_bus.get_history(event_type)
        
        if execution_id:
            events = [e for e in events if e.correlation_id == execution_id]
        
        return events
