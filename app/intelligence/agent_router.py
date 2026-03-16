"""
Skill-based agent routing: dynamic agent selection and multi-agent collaboration.

Routes tasks to best-suited agents based on capabilities and current state.
"""

from typing import List, Dict, Tuple, Optional, Set, Any
from datetime import datetime
import asyncio

from app.intelligence.models import (
    TaskDefinition,
    AgentCapability,
    ToolSignature,
    AgentRegistry,
    ToolRegistry,
    ReasoningStep,
    ReasoningType,
    generate_id,
)


class AgentRouter:
    """Routes tasks to optimal agents based on capabilities and score."""
    
    def __init__(self, agent_registry: AgentRegistry, tool_registry: ToolRegistry):
        """Initialize router with registries."""
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.agent_load = {}  # Track concurrent tasks per agent
        self.reasoning_steps = []
    
    async def select_agent_for_task(
        self,
        task: TaskDefinition,
        reasoning_trace_steps: List[ReasoningStep],
    ) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """
        Select best agent for a task.
        
        Returns: (agent_id, confidence, reasoning_dict)
        """
        # Find agents capable of this operation
        operation = task.operation
        candidates = self.agent_registry.find_agents_for_operation(operation)
        
        if not candidates:
            return None, 0.0, {"reason": "No agents support this operation"}
        
        # Score each candidate
        scores = {}
        for agent in candidates:
            score = self._score_agent(agent, task)
            scores[agent.agent_id] = score
        
        # Select highest-scoring agent
        if not scores:
            return None, 0.0, {"reason": "No suitable agents found"}
        
        best_agent_id = max(scores, key=scores.get)
        best_agent = self.agent_registry.agents[best_agent_id]
        confidence = scores[best_agent_id]
        
        # Create reasoning step
        reasoning = ReasoningStep(
            step_id=generate_id("reasoning"),
            reasoning_type=ReasoningType.AGENT_SELECTION,
            timestamp=datetime.utcnow(),
            input_context={
                "task_id": task.task_id,
                "operation": operation,
                "candidate_count": len(candidates),
            },
            reasoning_text=f"Selected agent {best_agent.agent_name} for operation {operation}",
            output_decision={
                "selected_agent_id": best_agent_id,
                "selected_agent_name": best_agent.agent_name,
                "candidate_scores": scores,
            },
            confidence=confidence,
            supporting_evidence=[
                f"Agent expertise: {best_agent.expertise_level}",
                f"Availability: {best_agent.availability}",
                f"Specializations: {', '.join(best_agent.specializations) or 'general'}",
            ],
        )
        reasoning_trace_steps.append(reasoning)
        
        return best_agent_id, confidence, {
            "agent_name": best_agent.agent_name,
            "reasoning": reasoning,
        }
    
    def _score_agent(self, agent: AgentCapability, task: TaskDefinition) -> float:
        """Score an agent for a task (0.0-1.0)."""
        score = 0.5  # Base score
        
        # Expertise level (0-10 scale converted to 0-0.5 bonus)
        score += (agent.expertise_level / 10.0) * 0.3
        
        # Availability (direct multiplier)
        score *= agent.availability
        
        # Load balancing (penalize if busy)
        current_load = self.agent_load.get(agent.agent_id, 0)
        load_penalty = (current_load / 10.0) * 0.2  # Rough scaling
        score -= min(load_penalty, 0.3)
        
        # Tool overlap with task
        if task.tool_id and task.tool_id in agent.supported_tools:
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    async def select_agents_for_collaboration(
        self,
        tasks: List[TaskDefinition],
        reasoning_trace_steps: List[ReasoningStep],
    ) -> Dict[str, Tuple[List[str], float]]:
        """
        Select agents for multi-agent collaboration on task set.
        
        Returns: {task_id: ([agent_ids], confidence)}
        """
        assignments = {}
        
        for task in tasks:
            agent_id, confidence, _ = await self.select_agent_for_task(task, reasoning_trace_steps)
            if agent_id:
                assignments[task.task_id] = ([agent_id], confidence)
            else:
                assignments[task.task_id] = ([], 0.0)
        
        # Consider inter-task dependencies for collaboration
        for task in tasks:
            if task.dependencies:
                # Agents on dependent tasks might collaborate
                pass  # Can be enhanced
        
        return assignments
    
    async def mark_agent_busy(self, agent_id: str) -> None:
        """Mark agent as taking on a task."""
        self.agent_load[agent_id] = self.agent_load.get(agent_id, 0) + 1
    
    async def mark_agent_free(self, agent_id: str) -> None:
        """Mark agent as done with a task."""
        self.agent_load[agent_id] = max(0, self.agent_load.get(agent_id, 1) - 1)


class ToolSelector:
    """Selects appropriate tools for tasks."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """Initialize with tool registry."""
        self.tool_registry = tool_registry
        self.reasoning_steps = []
    
    async def select_tool_for_task(
        self,
        task: TaskDefinition,
        reasoning_trace_steps: List[ReasoningStep],
    ) -> Tuple[Optional[ToolSignature], float, Dict[str, Any]]:
        """
        Select best tool for a task.
        
        Returns: (tool_signature, confidence, reasoning_dict)
        """
        # If tool_id is specified, use that
        if task.tool_id:
            if task.tool_id in self.tool_registry.tools:
                tool = self.tool_registry.tools[task.tool_id]
                return tool, 1.0, {"reason": "Explicitly specified"}
            else:
                return None, 0.0, {"reason": f"Specified tool {task.tool_id} not found"}
        
        # Find tools by operation
        candidates = self.tool_registry.find_tools_by_operation(task.operation)
        
        if not candidates:
            return None, 0.0, {"reason": "No tools support this operation"}
        
        # Score candidates
        scores = {}
        for tool in candidates:
            score = self._score_tool(tool, task)
            scores[tool.tool_id] = score
        
        if not scores:
            return None, 0.0, {"reason": "No suitable tools"}
        
        best_tool_id = max(scores, key=scores.get)
        best_tool = self.tool_registry.tools[best_tool_id]
        confidence = scores[best_tool_id]
        
        # Create reasoning step
        reasoning = ReasoningStep(
            step_id=generate_id("reasoning"),
            reasoning_type=ReasoningType.TOOL_SELECTION,
            timestamp=datetime.utcnow(),
            input_context={
                "task_id": task.task_id,
                "operation": task.operation,
                "candidate_count": len(candidates),
            },
            reasoning_text=f"Selected tool {best_tool.name} for operation {task.operation}",
            output_decision={
                "selected_tool_id": best_tool_id,
                "selected_tool_name": best_tool.name,
                "candidate_scores": scores,
            },
            confidence=confidence,
            supporting_evidence=[
                f"Tool success rate: {best_tool.success_rate:.1%}",
                f"Average latency: {best_tool.latency_ms:.0f}ms",
                f"Cost: {best_tool.cost_per_call:.2f}",
            ],
        )
        reasoning_trace_steps.append(reasoning)
        
        return best_tool, confidence, {"reasoning": reasoning}
    
    def _score_tool(self, tool: ToolSignature, task: TaskDefinition) -> float:
        """Score a tool for a task (0.0-1.0)."""
        score = 0.5  # Base score
        
        # Success rate (heavy weight)
        score += tool.success_rate * 0.4
        
        # Latency (penalize slow tools)
        latency_penalty = min(tool.latency_ms / 1000.0, 1.0) * 0.1
        score -= latency_penalty
        
        # Cost (slight penalty)
        cost_penalty = min(tool.cost_per_call / 1.0, 0.2)
        score -= cost_penalty
        
        # Availability (check rate limits)
        if tool.rate_limit_per_second < float('inf'):
            score += 0.05  # Prefer rate-limited tools
        
        return min(max(score, 0.0), 1.0)
    
    async def chain_tools_for_workflow(
        self,
        tasks: List[TaskDefinition],
        tool_selections: Dict[str, ToolSignature],
    ) -> List[Tuple[str, str]]:
        """
        Chain tools together based on task dependencies and data flow.
        
        Returns: [(from_tool_id, to_tool_id), ...]
        """
        chains = []
        task_map = {t.task_id: t for t in tasks}
        
        for task in tasks:
            if task.dependencies:
                for dep_task_id in task.dependencies:
                    if dep_task_id in tool_selections and task.task_id in tool_selections:
                        from_tool = tool_selections[dep_task_id]
                        to_tool = tool_selections[task.task_id]
                        chains.append((from_tool.tool_id, to_tool.tool_id))
        
        return chains
