"""
Reasoning trace persistence: store, replay, and debug reasoning chains.

Enables inspection of how decisions were made and finds reasoning failures.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

from app.intelligence.models import (
    ReasoningTrace,
    ReasoningStep,
    ReasoningType,
    WorkflowExecution,
    TaskExecution,
    generate_id,
)


class ReasoningTraceStore:
    """Persistent store for reasoning traces."""
    
    def __init__(self):
        """Initialize trace store."""
        self.traces: Dict[str, ReasoningTrace] = {}
        self.step_index: Dict[ReasoningType, Set[str]] = {
            rt: set() for rt in ReasoningType
        }
    
    def store_trace(self, trace: ReasoningTrace) -> str:
        """Store a reasoning trace."""
        self.traces[trace.trace_id] = trace
        
        # Index by reasoning type
        for step in trace.steps:
            self.step_index[step.reasoning_type].add(trace.trace_id)
        
        return trace.trace_id
    
    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Retrieve a reasoning trace."""
        return self.traces.get(trace_id)
    
    def find_traces_by_type(self, reasoning_type: ReasoningType) -> List[ReasoningTrace]:
        """Find all traces containing a reasoning type."""
        trace_ids = self.step_index.get(reasoning_type, set())
        return [self.traces[tid] for tid in trace_ids if tid in self.traces]
    
    def export_trace_to_json(self, trace_id: str) -> Optional[str]:
        """Export trace as JSON for inspection."""
        trace = self.traces.get(trace_id)
        if not trace:
            return None
        
        data = {
            "trace_id": trace.trace_id,
            "execution_id": trace.execution_id,
            "user_query": trace.user_query,
            "created_at": trace.created_at.isoformat(),
            "steps": [
                {
                    "step_id": step.step_id,
                    "reasoning_type": step.reasoning_type.value,
                    "timestamp": step.timestamp.isoformat(),
                    "input_context": step.input_context,
                    "reasoning_text": step.reasoning_text,
                    "output_decision": step.output_decision,
                    "confidence": step.confidence,
                    "supporting_evidence": step.supporting_evidence,
                }
                for step in trace.steps
            ],
            "final_plan_id": trace.final_plan_id,
        }
        
        return json.dumps(data, indent=2)
    
    def cleanup_old_traces(self, days: int = 30) -> int:
        """Remove traces older than N days."""
        cutoff = datetime.utcnow()
        cutoff = cutoff.replace(year=cutoff.year - (1 if cutoff.month == 1 else 0))
        
        to_delete = []
        for trace_id, trace in self.traces.items():
            age_days = (datetime.utcnow() - trace.created_at).days
            if age_days > days:
                to_delete.append(trace_id)
        
        for trace_id in to_delete:
            del self.traces[trace_id]
            # Clean up indexes
            for rt in ReasoningType:
                self.step_index[rt].discard(trace_id)
        
        return len(to_delete)


class ReasoningReplayer:
    """Replay and analyze reasoning chains for debugging."""
    
    def __init__(self, trace_store: ReasoningTraceStore):
        """Initialize replayer."""
        self.trace_store = trace_store
    
    def replay_trace(self, trace_id: str) -> Dict[str, Any]:
        """Replay a trace and return decision tree."""
        trace = self.trace_store.get_trace(trace_id)
        if not trace:
            return {"error": f"Trace {trace_id} not found"}
        
        return {
            "trace_id": trace_id,
            "query": trace.user_query,
            "steps_count": len(trace.steps),
            "decision_tree": self._build_decision_tree(trace.steps),
            "final_plan_id": trace.final_plan_id,
        }
    
    def _build_decision_tree(self, steps: List[ReasoningStep]) -> Dict[str, Any]:
        """Build decision tree from reasoning steps."""
        tree = {
            "root": None,
            "branches": [],
            "leaf": None,
        }
        
        if not steps:
            return tree
        
        # First step is root
        first_step = steps[0]
        tree["root"] = {
            "type": first_step.reasoning_type.value,
            "reasoning": first_step.reasoning_text,
            "confidence": first_step.confidence,
        }
        
        # Middle steps are branches
        for step in steps[1:-1]:
            tree["branches"].append({
                "type": step.reasoning_type.value,
                "reasoning": step.reasoning_text,
                "decision": step.output_decision,
                "confidence": step.confidence,
            })
        
        # Last step is leaf
        if len(steps) > 1:
            last_step = steps[-1]
            tree["leaf"] = {
                "type": last_step.reasoning_type.value,
                "decision": last_step.output_decision,
                "confidence": last_step.confidence,
            }
        
        return tree
    
    def analyze_reasoning_confidence(self, trace_id: str) -> Dict[str, Any]:
        """Analyze confidence levels throughout reasoning."""
        trace = self.trace_store.get_trace(trace_id)
        if not trace:
            return {}
        
        confidences_by_type = {}
        for step in trace.steps:
            rt = step.reasoning_type.value
            if rt not in confidences_by_type:
                confidences_by_type[rt] = []
            confidences_by_type[rt].append(step.confidence)
        
        analysis = {}
        for rt, confidences in confidences_by_type.items():
            analysis[rt] = {
                "min": min(confidences),
                "max": max(confidences),
                "avg": sum(confidences) / len(confidences),
                "count": len(confidences),
            }
        
        overall_confidence = sum(s.confidence for s in trace.steps) / len(trace.steps)
        analysis["overall_confidence"] = overall_confidence
        
        return analysis


class ReasoningFailureDetector:
    """Detect failures in reasoning chains."""
    
    def __init__(self, trace_store: ReasoningTraceStore):
        """Initialize detector."""
        self.trace_store = trace_store
    
    def detect_failures(
        self,
        trace_id: str,
        execution: Optional[WorkflowExecution] = None,
    ) -> List[Dict[str, Any]]:
        """Detect reasoning failures in a trace."""
        trace = self.trace_store.get_trace(trace_id)
        if not trace:
            return []
        
        failures = []
        
        # Check 1: Low confidence steps
        for step in trace.steps:
            if step.confidence < 0.5:
                failures.append({
                    "type": "low_confidence",
                    "step_id": step.step_id,
                    "reasoning_type": step.reasoning_type.value,
                    "confidence": step.confidence,
                    "severity": "warning",
                    "reasoning": step.reasoning_text,
                })
        
        # Check 2: Contradictory steps
        for i, step in enumerate(trace.steps[1:], 1):
            prev_step = trace.steps[i-1]
            if self._steps_contradict(prev_step, step):
                failures.append({
                    "type": "contradiction",
                    "step_id": step.step_id,
                    "prev_step_id": prev_step.step_id,
                    "severity": "error",
                })
        
        # Check 3: Execution outcome vs confidence
        if execution and execution.status.value == "failed":
            avg_confidence = sum(s.confidence for s in trace.steps) / len(trace.steps)
            if avg_confidence > 0.8:
                failures.append({
                    "type": "overconfident_failure",
                    "predicted_confidence": avg_confidence,
                    "actual_outcome": "failed",
                    "severity": "critical",
                })
        
        # Check 4: Missing supporting evidence
        for step in trace.steps:
            if not step.supporting_evidence and step.confidence > 0.7:
                failures.append({
                    "type": "unsupported_confidence",
                    "step_id": step.step_id,
                    "reasoning_type": step.reasoning_type.value,
                    "severity": "warning",
                })
        
        return failures
    
    def _steps_contradict(self, step1: ReasoningStep, step2: ReasoningStep) -> bool:
        """Check if two steps contradict each other."""
        # Simple check: if output decision of step1 conflicts with input of step2
        decision_keys = set(step1.output_decision.keys())
        input_keys = set(step2.input_context.keys())
        
        overlap = decision_keys & input_keys
        for key in overlap:
            if step1.output_decision[key] != step2.input_context.get(key):
                return True
        
        return False


class ReasoningImprovementSuggester:
    """Suggest improvements to reasoning chains."""
    
    def __init__(self, trace_store: ReasoningTraceStore):
        """Initialize suggester."""
        self.trace_store = trace_store
    
    def suggest_improvements(
        self,
        trace_id: str,
        execution: Optional[WorkflowExecution] = None,
    ) -> List[str]:
        """Suggest improvements to reasoning."""
        trace = self.trace_store.get_trace(trace_id)
        if not trace:
            return []
        
        suggestions = []
        
        # Suggestion 1: Too many steps
        if len(trace.steps) > 10:
            suggestions.append(
                "Reasoning chain is long. Consider consolidating similar reasoning steps"
            )
        
        # Suggestion 2: Low overall confidence
        avg_confidence = sum(s.confidence for s in trace.steps) / len(trace.steps)
        if avg_confidence < 0.7:
            suggestions.append(
                "Overall confidence is low. Add more analysis steps or gather more context"
            )
        
        # Suggestion 3: No validation steps
        validation_steps = [s for s in trace.steps if s.reasoning_type == ReasoningType.VALIDATION]
        if not validation_steps:
            suggestions.append(
                "No validation steps found. Add explicit validation of key decisions"
            )
        
        # Suggestion 4: Track alternatives
        with_alternatives = [s for s in trace.steps if s.alternative_considered]
        if len(with_alternatives) < len(trace.steps) / 2:
            suggestions.append(
                "Few alternative considerations. Explicitly consider alternatives for key decisions"
            )
        
        # Suggestion 5: If execution failed
        if execution and execution.status.value == "failed":
            error_recovery_steps = [s for s in trace.steps 
                                   if s.reasoning_type == ReasoningType.ERROR_RECOVERY]
            if not error_recovery_steps:
                suggestions.append(
                    "Execution failed but no error recovery reasoning found. "
                    "Add explicit error handling logic to reasoning"
                )
        
        return suggestions


def compare_traces(trace_id1: str, trace_id2: str, store: ReasoningTraceStore) -> Dict[str, Any]:
    """Compare two reasoning traces."""
    trace1 = store.get_trace(trace_id1)
    trace2 = store.get_trace(trace_id2)
    
    if not trace1 or not trace2:
        return {"error": "One or both traces not found"}
    
    comparison = {
        "trace1_id": trace_id1,
        "trace2_id": trace_id2,
        "trace1_steps": len(trace1.steps),
        "trace2_steps": len(trace2.steps),
        "trace1_avg_confidence": sum(s.confidence for s in trace1.steps) / len(trace1.steps),
        "trace2_avg_confidence": sum(s.confidence for s in trace2.steps) / len(trace2.steps),
        "different_reasoning_types": [],
    }
    
    trace1_types = {s.reasoning_type for s in trace1.steps}
    trace2_types = {s.reasoning_type for s in trace2.steps}
    
    if trace1_types != trace2_types:
        comparison["different_reasoning_types"] = list(trace1_types ^ trace2_types)
    
    return comparison
