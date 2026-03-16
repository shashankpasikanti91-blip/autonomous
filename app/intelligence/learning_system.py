"""
Learning feedback system: capture outcomes and improve execution strategies.

Records learnings from executions to enable adaptive retry and optimization.
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.intelligence.models import (
    LearningRecord,
    LearningType,
    ExecutionFeedback,
    WorkflowExecution,
    TaskExecution,
    WorkflowTemplate,
    generate_id,
)


class LearningMemory:
    """In-memory learning storage with pattern recognition."""
    
    def __init__(self, retention_hours: int = 720):  # 30 days default
        """Initialize learning memory."""
        self.records: Dict[str, LearningRecord] = {}
        self.feedback: Dict[str, ExecutionFeedback] = {}
        self.retention_hours = retention_hours
        self.patterns = defaultdict(list)
    
    def record_learning(
        self,
        execution_id: str,
        learning_type: LearningType,
        pattern_description: str,
        pattern_data: Dict[str, Any],
        success: bool,
        latency_ms: float,
        confidence: float = 0.8,
        recommendation: Optional[str] = None,
        retry_strategy: Optional[str] = None,
    ) -> LearningRecord:
        """Record a learning from an execution."""
        record = LearningRecord(
            record_id=generate_id("learning"),
            learning_type=learning_type,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            pattern_description=pattern_description,
            pattern_data=pattern_data,
            success=success,
            latency_ms=latency_ms,
            confidence=confidence,
            recommendation=recommendation,
            retry_strategy=retry_strategy,
        )
        
        self.records[record.record_id] = record
        
        # Index by pattern
        key = f"{learning_type.value}:{pattern_description}"
        self.patterns[key].append(record)
        
        return record
    
    def record_feedback(
        self,
        execution_id: str,
        user_id: str,
        rating: int,
        was_successful: bool,
        issues: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
    ) -> ExecutionFeedback:
        """Record user feedback on execution."""
        feedback = ExecutionFeedback(
            feedback_id=generate_id("feedback"),
            execution_id=execution_id,
            user_id=user_id,
            overall_rating=rating,
            was_successful=was_successful,
            issues_encountered=issues or [],
            improvements_suggested=improvements or [],
        )
        
        self.feedback[feedback.feedback_id] = feedback
        return feedback
    
    def get_learnings_for_pattern(self, pattern_key: str) -> List[LearningRecord]:
        """Get all learnings matching a pattern."""
        return self.patterns.get(pattern_key, [])
    
    def get_success_rate_for_pattern(self, pattern_key: str) -> float:
        """Calculate success rate for a pattern."""
        records = self.get_learnings_for_pattern(pattern_key)
        if not records:
            return 0.5  # Default confidence
        
        successes = sum(1 for r in records if r.success)
        return successes / len(records)
    
    def get_average_latency_for_pattern(self, pattern_key: str) -> float:
        """Get average latency for a pattern."""
        records = self.get_learnings_for_pattern(pattern_key)
        if not records:
            return 0.0
        
        return sum(r.latency_ms for r in records) / len(records)
    
    def find_similar_patterns(
        self,
        execution_data: Dict[str, Any],
        similarity_threshold: float = 0.7,
    ) -> List[LearningRecord]:
        """Find previously learned similar patterns."""
        similar = []
        
        for records in self.patterns.values():
            for record in records:
                # Simple similarity: compare key fields
                similarity = self._calculate_similarity(execution_data, record.pattern_data)
                if similarity >= similarity_threshold:
                    similar.append(record)
        
        # Sort by recency
        similar.sort(key=lambda r: r.timestamp, reverse=True)
        
        return similar
    
    def _calculate_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate similarity between two data dicts."""
        # Simple implementation: check matching keys/values
        matching = 0
        total = 0
        
        for key in set(data1.keys()) | set(data2.keys()):
            total += 1
            if key in data1 and key in data2:
                if data1[key] == data2[key]:
                    matching += 1
        
        return matching / total if total > 0 else 0.5
    
    def cleanup_old_records(self) -> int:
        """Remove records older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        to_delete = []
        
        for record_id, record in self.records.items():
            if record.timestamp < cutoff:
                to_delete.append(record_id)
        
        for record_id in to_delete:
            del self.records[record_id]
        
        return len(to_delete)


class AdaptiveRetryStrategy:
    """Learns optimal retry strategies from execution history."""
    
    def __init__(self, learning_memory: LearningMemory):
        """Initialize with learning memory."""
        self.memory = learning_memory
    
    def get_retry_strategy(
        self,
        task_operation: str,
        error_type: str,
        previous_attempts: int,
    ) -> Dict[str, Any]:
        """Get adaptive retry strategy based on learnings."""
        pattern_key = f"retry:{task_operation}:{error_type}"
        records = self.memory.get_learnings_for_pattern(pattern_key)
        
        if not records:
            # Default strategy
            return {
                "should_retry": previous_attempts < 3,
                "backoff_seconds": min(2 ** previous_attempts, 60),
                "next_agent_pool": "all",
            }
        
        # Analyze success patterns
        successful = [r for r in records if r.success]
        success_rate = len(successful) / len(records) if records else 0.0
        
        # If this error type rarely succeeds on retry, don't retry
        if success_rate < 0.2 and previous_attempts > 0:
            return {
                "should_retry": False,
                "reason": "Low historical retry success rate",
            }
        
        # Extract strategy from most recent successful attempt
        if successful:
            best_record = max(successful, key=lambda r: r.timestamp)
            return {
                "should_retry": True,
                "backoff_seconds": best_record.pattern_data.get("backoff_seconds", 2 ** previous_attempts),
                "next_agent_pool": best_record.pattern_data.get("next_agent", "alternative"),
                "recommended_strategy": best_record.retry_strategy,
            }
        
        # Conservative fallback
        return {
            "should_retry": previous_attempts < 2,
            "backoff_seconds": 2 ** previous_attempts,
            "next_agent_pool": "alternative",
        }


class FirstPrinciplesSuggester:
    """Suggests workflow improvements based on learnings."""
    
    def __init__(self, learning_memory: LearningMemory):
        """Initialize suggester."""
        self.memory = learning_memory
    
    def suggest_optimizations(
        self,
        workflow_executions: List[WorkflowExecution],
    ) -> List[str]:
        """Suggest workflow optimizations."""
        suggestions = []
        
        if not workflow_executions:
            return suggestions
        
        # Analyze success patterns
        successful = [w for w in workflow_executions if w.status.value == "completed"]
        failed = [w for w in workflow_executions if w.status.value == "failed"]
        
        success_rate = len(successful) / len(workflow_executions) if workflow_executions else 0.0
        
        # Suggestion 1: If success rate is low, parallelization might help
        if success_rate < 0.7:
            suggestions.append(
                "Consider enabling parallel execution for independent tasks to improve reliability"
            )
        
        # Suggestion 2: Analyze latency
        avg_latencies = [w.total_latency_ms for w in successful]
        if avg_latencies:
            avg_latency = sum(avg_latencies) / len(avg_latencies)
            if avg_latency > 10000:  # >10 seconds
                suggestions.append (
                    "Long execution time detected. Consider breaking workflow into smaller steps"
                )
        
        # Suggestion 3: Error patterns
        error_counts = defaultdict(int)
        for execution in failed:
            if execution.error:
                error_counts[execution.error] += 1
        
        if error_counts:
            top_error = max(error_counts, key=error_counts.get)
            if error_counts[top_error] > len(failed) * 0.5:
                suggestions.append(
                    f"Frequently encountering error: '{top_error}'. "
                    "Consider adding explicit error handling or fallback steps"
                )
        
        # Suggestion 4: Task dependencies
        for execution in workflow_executions:
            task_failures = [t for t in execution.task_executions.values() 
                           if t.status.value == "failed"]
            if task_failures:
                dependent_tasks = [t for t in execution.task_executions.values()
                                 if any(tf.task_id in t.dependencies for tf in task_failures)]
                if dependent_tasks:
                    suggestions.append(
                        f"Task failures cause dependent tasks to fail. "
                        "Consider explicit retry logic or fallback strategies"
                    )
        
        return suggestions
    
    def suggest_agent_specialization(
        self,
        agent_id: str,
        task_operations: List[str],
    ) -> Optional[str]:
        """Suggest what an agent should specialize in."""
        # Analyze past performance
        success_by_op = defaultdict(list)
        
        for pattern_key, records in defaultdict(list).items():
            if agent_id in pattern_key:
                for record in records:
                    op = record.pattern_data.get("operation")
                    if op:
                        success_by_op[op].append(record.success)
        
        # Find best-performing operations
        best_ops = []
        for op, successes in success_by_op.items():
            if successes:
                success_rate = sum(successes) / len(successes)
                if success_rate > 0.85:
                    best_ops.append((op, success_rate))
        
        if best_ops:
            best_op = max(best_ops, key=lambda x: x[1])
            return f"Agent shows strong performance with {best_op[0]} ({best_op[1]:.0%})"
        
        return None


class WorkflowTemplateGenerator:
    """Generate reusable templates from successful executions."""
    
    def __init__(self, learning_memory: LearningMemory):
        """Initialize generator."""
        self.memory = learning_memory
    
    def generate_template_from_execution(
        self,
        execution: WorkflowExecution,
        success_rate_threshold: float = 0.8,
    ) -> Optional[WorkflowTemplate]:
        """Generate reusable template from successful execution."""
        if execution.status.value != "completed":
            return None
        
        # Check if similar executions are successful
        similar = self.memory.find_similar_patterns(
            {
                "intent": execution.user_intent,
                "workflow_type": execution.plan_id,
            },
            similarity_threshold=0.7,
        )
        
        if not similar or len(similar) < 3:
            return None
        
        success_count = sum(1 for r in similar if r.success)
        success_rate = success_count / len(similar)
        
        if success_rate < success_rate_threshold:
            return None
        
        # Create template
        template = WorkflowTemplate(
            template_id=generate_id("template"),
            name=f"Template: {execution.user_intent[:50]}",
            description=f"Auto-generated from {len(similar)} successful executions",
            category="auto_generated",
            user_query_pattern=execution.user_intent,
            workflow_plan=execution.task_executions,  # TODO: fix type
            parameters=execution.results,
            success_rate=success_rate,
            average_duration_seconds=sum(r.latency_ms for r in similar) / len(similar) / 1000,
            average_cost=0.1 * len(similar),
            learning_records=[r.record_id for r in similar],
        )
        
        return template
