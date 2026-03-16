"""
Base agent framework with Pydantic AI reasoning, planning, and tool usage.
"""
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
from datetime import datetime
from abc import ABC, abstractmethod
from core.models import (
    AgentState, AgentRole, Message, ExecutionStatus, 
    ToolExecutionRequest, ToolExecutionResult, AgentResponse,
    ReasoningChain, ReasoningStep, ActionSelection, ExecutionPlan,
    ToolCallPlanned, TaskPrioritization, ToolSelectionContext
)
from utils.logger import get_logger
from utils.errors import AgentException


logger = get_logger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for tools that agents can use.
    """
    
    def __init__(self, tool_id: str, name: str, description: str):
        self.tool_id = tool_id
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given inputs.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            Dictionary with execution results
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for agent introspection."""
        pass


class BaseAgent(ABC):
    """
    Base agent class with reasoning, planning, and memory integration.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[Any] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.tools = {tool.tool_id: tool for tool in (tools or [])}
        self.memory = memory
        self.state = AgentState(agent_id=agent_id, role=role)
        self.logger = get_logger(f"{__name__}.{name}")
    
    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the agent's message history."""
        message = Message(
            id=f"msg_{len(self.state.messages)}",
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.state.messages.append(message)
        self.logger.info(f"Added message from {role}: {content[:100]}")
    
    async def _build_reasoning_chain(self, task: str, context: Dict[str, Any]) -> ReasoningChain:
        """
        Build a comprehensive reasoning chain for decision making.
        Integrates with memory for contextual analysis.
        """
        start_time = datetime.utcnow()
        
        # Initial analysis from context
        initial_analysis = f"Analyzing task: {task} with context keys: {list(context.keys())}"
        self.logger.info(f"[REASONING] Starting analysis: {initial_analysis}")
        
        steps = []
        
        # Step 1: Understand the problem
        step1 = ReasoningStep(
            step_number=1,
            thinking=f"Breaking down task requirements and identifying constraints",
            observation=f"Task involves: {task[:200]}",
            conclusion="Task scope understood",
            confidence=0.85
        )
        steps.append(step1)
        self.logger.debug(f"[REASONING] Step 1: {step1.conclusion}")
        
        # Step 2: Check memory for similar tasks
        relevant_memories = []
        if self.memory:
            try:
                relevant_memories = await self.memory.retrieve({
                    "type": "execution",
                    "task_pattern": task[:50]
                })
                self.logger.info(f"[REASONING] Retrieved {len(relevant_memories)} relevant memories")
            except Exception as e:
                self.logger.warning(f"[REASONING] Memory retrieval failed: {str(e)}")
        
        step2 = ReasoningStep(
            step_number=2,
            thinking=f"Checking historical patterns and precedents",
            observation=f"Found {len(relevant_memories)} similar past executions",
            conclusion=f"Identified {len(relevant_memories)} precedents for guidance",
            confidence=0.75 if relevant_memories else 0.5
        )
        steps.append(step2)
        self.logger.debug(f"[REASONING] Step 2: {step2.conclusion}")
        
        # Step 3: Identify available tools
        available_tools = {tid: f"Tool_{tid}" for tid in self.tools.keys()}
        step3 = ReasoningStep(
            step_number=3,
            thinking=f"Evaluating available tools for task completion",
            observation=f"Available tools: {list(available_tools.keys())}",
            conclusion=f"Selected {len(available_tools)} tools as candidates",
            confidence=0.90
        )
        steps.append(step3)
        self.logger.debug(f"[REASONING] Step 3: {step3.conclusion}")
        
        # Step 4: Risk assessment
        risk_factors = context.get("risk_factors", [])
        step4 = ReasoningStep(
            step_number=4,
            thinking=f"Assessing risks and mitigation strategies",
            observation=f"Identified risk factors: {risk_factors}",
            conclusion="Risk assessment completed",
            confidence=0.80
        )
        steps.append(step4)
        self.logger.debug(f"[REASONING] Step 4: {step4.conclusion}")
        
        end_time = datetime.utcnow()
        reasoning_time = (end_time - start_time).total_seconds() * 1000
        
        reasoning_chain = ReasoningChain(
            task_context=task,
            initial_analysis=initial_analysis,
            steps=steps,
            final_decision=f"Ready to execute task via available tools",
            reasoning_time_ms=int(reasoning_time)
        )
        
        self.logger.info(f"[REASONING] Completed reasoning chain in {reasoning_time:.0f}ms")
        return reasoning_chain
    
    async def _select_tools(self, task: str, context: Dict[str, Any]) -> List[ActionSelection]:
        """
        Select appropriate tools based on task context.
        Uses reasoning to prioritize tool selection.
        """
        selections = []
        task_requirements = context.get("requirements", [])
        
        self.logger.info(f"[TOOL_SELECTION] Analyzing task requirements: {task_requirements}")
        
        for tool_id, tool in self.tools.items():
            tool_name = tool.name if hasattr(tool, 'name') else tool_id
            
            # Simple matching logic - can be enhanced with embeddings
            is_relevant = any(
                req.lower() in tool_name.lower() 
                for req in task_requirements
            )
            
            if is_relevant or not task_requirements:
                selection = ActionSelection(
                    action_type="tool_execution",
                    selected_tool_id=tool_id,
                    rationale=f"Tool {tool_name} matches task requirements: {task_requirements}",
                    priority=2 if is_relevant else 1,
                    estimated_outcome=f"Successful execution of {tool_name}"
                )
                selections.append(selection)
                self.logger.debug(f"[TOOL_SELECTION] Selected tool: {tool_name} (priority: {selection.priority})")
        
        # Sort by priority
        selections.sort(key=lambda x: x.priority, reverse=True)
        return selections
    
    async def reason(self, task: str, context: Optional[Dict[str, Any]] = None) -> ReasoningChain:
        """
        Reason about a task using structured reasoning chain.
        Enhanced with memory integration and context analysis.
        
        Args:
            task: Task description to reason about
            context: Additional context for reasoning
            
        Returns:
            Reasoning chain with analysis and decision
        """
        context = context or {}
        self.logger.info(f"[REASON] Starting reasoning for task: {task[:100]}")
        
        try:
            reasoning_chain = await self._build_reasoning_chain(task, context)
            
            # Store reasoning in memory
            if self.memory:
                try:
                    await self.memory.store({
                        "type": "reasoning",
                        "agent_id": self.agent_id,
                        "task": task,
                        "reasoning_chain": reasoning_chain.model_dump(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    self.logger.debug("[REASON] Reasoning chain stored in memory")
                except Exception as e:
                    self.logger.warning(f"[REASON] Failed to store reasoning: {str(e)}")
            
            await self.add_message("assistant", f"Reasoning complete: {reasoning_chain.final_decision}")
            return reasoning_chain
            
        except Exception as e:
            self.logger.error(f"[REASON] Reasoning failed: {str(e)}")
            # Return a minimal reasoning chain
            return ReasoningChain(
                task_context=task,
                initial_analysis=str(context),
                steps=[],
                final_decision="Error in reasoning process"
            )
    
    async def plan(self, objective: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create a detailed execution plan using tool selection and reasoning.
        
        Args:
            objective: Objective to plan for
            context: Context for planning
            
        Returns:
            ExecutionPlan with prioritized steps
        """
        context = context or {}
        self.logger.info(f"[PLAN] Creating plan for objective: {objective[:100]}")
        
        try:
            # Select appropriate tools
            tool_selections = await self._select_tools(objective, context)
            
            # Build tool call plans
            tool_calls_planned = []
            for selection in tool_selections:
                if selection.selected_tool_id:
                    tool = self.tools[selection.selected_tool_id]
                    tool_call = ToolCallPlanned(
                        tool_id=selection.selected_tool_id,
                        tool_name=tool.name if hasattr(tool, 'name') else selection.selected_tool_id,
                        inputs=context.get("tool_inputs", {}).get(selection.selected_tool_id, {}),
                        reasoning=selection.rationale,
                        success_criteria=["execution_completed", "result_generated"],
                        on_failure="log_error_and_continue"
                    )
                    tool_calls_planned.append(tool_call)
            
            # Create execution plan
            execution_plan = ExecutionPlan(
                task_id=f"task_{hash(objective)}",
                objective=objective,
                approach="Sequential tool execution with error handling",
                steps=tool_calls_planned,
                prioritized_tasks=[],
                risk_assessment="Standard execution with fallback strategies",
                estimated_total_time_seconds=len(tool_calls_planned) * 5
            )
            
            self.logger.info(f"[PLAN] Plan created with {len(tool_calls_planned)} steps")
            
            # Store plan in memory
            if self.memory:
                try:
                    await self.memory.store({
                        "type": "plan",
                        "agent_id": self.agent_id,
                        "objective": objective,
                        "plan": execution_plan.model_dump(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    self.logger.debug("[PLAN] Plan stored in memory")
                except Exception as e:
                    self.logger.warning(f"[PLAN] Failed to store plan: {str(e)}")
            
            await self.add_message("assistant", f"Plan created: {execution_plan.approach}")
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"[PLAN] Planning failed: {str(e)}")
            # Return a minimal plan
            return ExecutionPlan(
                task_id="error",
                objective=objective,
                approach="Error handling",
                steps=[]
            )
    
    async def execute_tool(self, tool_request: ToolExecutionRequest) -> ToolExecutionResult:
        """
        Execute a tool and return the result.
        """
        try:
            if tool_request.tool_id not in self.tools:
                raise AgentException(
                    f"Tool {tool_request.tool_id} not found",
                    code="TOOL_NOT_FOUND"
                )
            
            tool = self.tools[tool_request.tool_id]
            self.logger.info(f"Executing tool: {tool.name}")
            
            # Execute tool with timeout
            if tool_request.timeout:
                output = await asyncio.wait_for(
                    tool.execute(tool_request.inputs),
                    timeout=tool_request.timeout
                )
            else:
                output = await tool.execute(tool_request.inputs)
            
            result = ToolExecutionResult(
                tool_id=tool_request.tool_id,
                status=ExecutionStatus.COMPLETED,
                output=output
            )
            
            self.logger.info(f"Tool execution completed: {tool.name}")
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Tool execution timed out: {tool_request.tool_id}"
            self.logger.error(error_msg)
            return ToolExecutionResult(
                tool_id=tool_request.tool_id,
                status=ExecutionStatus.FAILED,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolExecutionResult(
                tool_id=tool_request.tool_id,
                status=ExecutionStatus.FAILED,
                error=error_msg
            )
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input and generate a response using reasoning and planning.
        
        Args:
            input_data: Dictionary with input information
            
        Returns:
            Agent response with status and results including reasoning chain
        """
        try:
            self.state.status = ExecutionStatus.RUNNING
            self.logger.info(f"[PROCESS] Agent {self.name} starting processing")
            
            task = input_data.get("task", "")
            objective = input_data.get("objective", "")
            context = input_data.get("context", {})
            tools_to_execute = input_data.get("tools", [])
            
            # Add incoming message
            await self.add_message("user", f"Task: {task}")
            
            # Reason about the task
            self.logger.info(f"[PROCESS] Starting reasoning phase")
            reasoning_chain = await self.reason(task, context)
            
            # Create a plan
            self.logger.info(f"[PROCESS] Starting planning phase")
            execution_plan = await self.plan(objective or task, context)
            
            # Execute planned tools
            self.logger.info(f"[PROCESS] Starting execution phase with {len(execution_plan.steps)} steps")
            tool_results = []
            memory_accessed = []
            
            for i, tool_call in enumerate(execution_plan.steps):
                self.logger.info(f"[PROCESS] Executing step {i+1}/{len(execution_plan.steps)}: {tool_call.tool_name}")
                
                try:
                    tool_request = ToolExecutionRequest(
                        tool_id=tool_call.tool_id,
                        inputs=tool_call.inputs
                    )
                    result = await self.execute_tool(tool_request)
                    tool_results.append(result.model_dump())
                    self.logger.info(f"[PROCESS] Tool {tool_call.tool_name} completed with status: {result.status}")
                    
                except Exception as e:
                    self.logger.error(f"[PROCESS] Tool execution failed: {str(e)}")
            
            # Store execution results in memory if available
            if self.memory:
                try:
                    await self.memory.store({
                        "type": "execution",
                        "agent_id": self.agent_id,
                        "role": self.role.value,
                        "task": task,
                        "reasoning_chain": reasoning_chain.model_dump(),
                        "execution_plan": execution_plan.model_dump(),
                        "tool_results": tool_results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    memory_accessed.append("execution_store")
                    self.logger.info(f"[PROCESS] Execution results stored in memory")
                except Exception as e:
                    self.logger.warning(f"[PROCESS] Failed to store execution results: {str(e)}")
            
            # Determine action selection based on execution
            action_selected = ActionSelection(
                action_type="tool_execution",
                selected_tool_id=execution_plan.steps[0].tool_id if execution_plan.steps else None,
                rationale=reasoning_chain.final_decision,
                priority=3,
                estimated_outcome="Task completed successfully"
            )
            
            self.state.status = ExecutionStatus.COMPLETED
            
            response = AgentResponse(
                agent_id=self.agent_id,
                status=ExecutionStatus.COMPLETED,
                message=f"Processed task: {task}",
                result={
                    "reasoning_quality": reasoning_chain.reasoning_time_ms or 0,
                    "plan_steps": len(execution_plan.steps),
                    "tools_executed": len(tool_results),
                    "messages_count": len(self.state.messages)
                },
                reasoning_chain=reasoning_chain,
                action_selected=action_selected,
                execution_plan=execution_plan,
                memory_accessed=memory_accessed
            )
            
            self.logger.info(f"[PROCESS] Agent {self.name} completed processing")
            return response
            
        except Exception as e:
            self.state.status = ExecutionStatus.FAILED
            error_msg = f"Agent processing failed: {str(e)}"
            self.logger.error(f"[PROCESS] {error_msg}")
            
            return AgentResponse(
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                message=error_msg
            )
    
    def get_state(self) -> AgentState:
        """Get the current agent state."""
        return self.state
    
    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools[tool.tool_id] = tool
        self.logger.info(f"Added tool: {tool.name}")
    
    @abstractmethod
    async def think(self, context: Dict[str, Any]) -> str:
        """
        Agent-specific thinking/reasoning logic.
        TODO: Override in subclasses or integrate with Pydantic AI.
        """
        pass
