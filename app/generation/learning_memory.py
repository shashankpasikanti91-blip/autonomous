"""
App learning memory - tracks analytics and recommends app evolution.

Monitors app usage, detects improvement opportunities, and learns from patterns.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import math


class AppMetricType(str, Enum):
    """Type of app metric."""
    USAGE_COUNT = "usage_count"
    ERROR_RATE = "error_rate"
    AVG_RESPONSE_TIME = "avg_response_time"
    PEAK_LOAD = "peak_load"
    USER_COUNT = "user_count"
    FEATURE_ADOPTION = "feature_adoption"


class ImprovementCategory(str, Enum):
    """Category of improvement."""
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    USABILITY = "usability"
    SCALABILITY = "scalability"
    SECURITY = "security"
    FEATURE_REQUEST = "feature_request"


@dataclass
class AppMetricRecord:
    """Record of app metric over time."""
    metric_id: str
    instance_id: str
    metric_type: AppMetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsagePattern:
    """Pattern in app usage."""
    pattern_id: str
    instance_id: str
    pattern_type: str  # peak_hours, common_routes, user_flows, errors
    description: str
    occurrences: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppLearningRecord:
    """Learning record for app improvement."""
    learning_id: str
    instance_id: str
    category: ImprovementCategory
    title: str
    description: str
    evidence: List[str]  # Supporting data points
    confidence: float = 0.0
    recommended_action: str = ""
    implementation_effort: str = "medium"
    expected_benefit: str = "medium"
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Collects metrics from app usage."""
    
    def __init__(self):
        self.metrics: Dict[str, List[AppMetricRecord]] = {}
    
    def record_metric(self, record: AppMetricRecord) -> None:
        """Record a metric."""
        key = f"{record.instance_id}_{record.metric_type.value}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(record)
    
    def get_metric_history(
        self,
        instance_id: str,
        metric_type: AppMetricType,
        hours: int = 24
    ) -> List[AppMetricRecord]:
        """Get metric history for period."""
        key = f"{instance_id}_{metric_type.value}"
        if key not in self.metrics:
            return []
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self.metrics[key] if m.timestamp >= cutoff]
    
    def get_metric_statistics(
        self,
        instance_id: str,
        metric_type: AppMetricType,
        hours: int = 24
    ) -> Dict[str, float]:
        """Get statistics for metric."""
        records = self.get_metric_history(instance_id, metric_type, hours)
        if not records:
            return {}
        
        values = [r.value for r in records]
        
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "median": sorted(values)[len(values) // 2]
        }


class PatternDetector:
    """Detects patterns in app usage."""
    
    def __init__(self):
        self.patterns: Dict[str, List[UsagePattern]] = {}
    
    def detect_peak_hours(
        self,
        instance_id: str,
        logs: List[Any]
    ) -> Optional[UsagePattern]:
        """Detect peak usage hours."""
        
        if not logs:
            return None
        
        # Bucket logs by hour
        hour_counts = {}
        for log in logs:
            if hasattr(log, 'timestamp'):
                hour = log.timestamp.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return None
        
        # Find peak hour
        peak_hour = max(hour_counts, key=hour_counts.get)
        peak_count = hour_counts[peak_hour]
        avg_count = sum(hour_counts.values()) / len(hour_counts)
        
        if peak_count > avg_count * 1.5:  # At least 50% above average
            pattern = UsagePattern(
                pattern_id=f"peak_{instance_id}",
                instance_id=instance_id,
                pattern_type="peak_hours",
                description=f"Peak usage at hour {peak_hour}:00",
                occurrences=peak_count,
                confidence=min(1.0, (peak_count - avg_count) / avg_count)
            )
            return pattern
        
        return None
    
    def detect_common_routes(
        self,
        instance_id: str,
        logs: List[Any]
    ) -> List[UsagePattern]:
        """Detect commonly used routes."""
        
        route_counts = {}
        for log in logs:
            if hasattr(log, 'operation'):
                route = log.operation
                route_counts[route] = route_counts.get(route, 0) + 1
        
        patterns = []
        total = sum(route_counts.values())
        
        for route, count in route_counts.items():
            if count > total * 0.1:  # More than 10% of traffic
                confidence = count / total
                pattern = UsagePattern(
                    pattern_id=f"route_{instance_id}_{route}",
                    instance_id=instance_id,
                    pattern_type="common_routes",
                    description=f"Route '{route}' used {count} times",
                    occurrences=count,
                    confidence=confidence
                )
                patterns.append(pattern)
        
        return patterns
    
    def detect_error_patterns(
        self,
        instance_id: str,
        logs: List[Any]
    ) -> List[UsagePattern]:
        """Detect error patterns."""
        
        error_types = {}
        total_logs = len(logs)
        
        for log in logs:
            if hasattr(log, 'status') and log.status == 'error':
                if hasattr(log, 'error'):
                    error_msg = log.error.split(":")[0]
                    error_types[error_msg] = error_types.get(error_msg, 0) + 1
        
        patterns = []
        
        for error_type, count in error_types.items():
            error_rate = count / max(total_logs, 1)
            if error_rate > 0.02:  # More than 2% error rate
                pattern = UsagePattern(
                    pattern_id=f"error_{instance_id}_{error_type}",
                    instance_id=instance_id,
                    pattern_type="errors",
                    description=f"Error '{error_type}' occurred {count} times",
                    occurrences=count,
                    confidence=error_rate
                )
                patterns.append(pattern)
        
        return patterns
    
    def store_pattern(self, pattern: UsagePattern) -> None:
        """Store detected pattern."""
        if pattern.instance_id not in self.patterns:
            self.patterns[pattern.instance_id] = []
        self.patterns[pattern.instance_id].append(pattern)
    
    def get_patterns(
        self,
        instance_id: str,
        pattern_type: Optional[str] = None
    ) -> List[UsagePattern]:
        """Get patterns for instance."""
        if instance_id not in self.patterns:
            return []
        
        patterns = self.patterns[instance_id]
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        return patterns


class ImprovementRecommender:
    """Recommends improvements based on usage patterns."""
    
    def __init__(self):
        self.recommendations: Dict[str, List[AppLearningRecord]] = {}
    
    def recommend_improvements(
        self,
        instance_id: str,
        metrics_collector: MetricsCollector,
        pattern_detector: PatternDetector
    ) -> List[AppLearningRecord]:
        """Generate improvement recommendations."""
        
        recommendations = []
        
        # Check error rate
        error_stats = metrics_collector.get_metric_statistics(
            instance_id,
            AppMetricType.ERROR_RATE,
            24
        )
        
        if error_stats and error_stats.get('mean', 0) > 0.05:
            rec = AppLearningRecord(
                learning_id=f"rec_errors_{instance_id}",
                instance_id=instance_id,
                category=ImprovementCategory.RELIABILITY,
                title="High Error Rate",
                description=f"Error rate is {error_stats['mean']*100:.1f}% which exceeds healthy threshold",
                evidence=[
                    f"Mean error rate: {error_stats['mean']*100:.1f}%",
                    f"Peak error rate: {error_stats.get('max', 0)*100:.1f}%"
                ],
                confidence=0.9,
                recommended_action="Review error logs and implement error recovery",
                implementation_effort="medium",
                expected_benefit="high"
            )
            recommendations.append(rec)
        
        # Check performance
        response_time_stats = metrics_collector.get_metric_statistics(
            instance_id,
            AppMetricType.AVG_RESPONSE_TIME,
            24
        )
        
        if response_time_stats and response_time_stats.get('mean', 0) > 500:
            rec = AppLearningRecord(
                learning_id=f"rec_perf_{instance_id}",
                instance_id=instance_id,
                category=ImprovementCategory.PERFORMANCE,
                title="Slow Response Times",
                description=f"Average response time is {response_time_stats['mean']:.0f}ms",
                evidence=[
                    f"Mean response time: {response_time_stats['mean']:.0f}ms",
                    f"p95 response time: {response_time_stats.get('max', 0):.0f}ms"
                ],
                confidence=0.85,
                recommended_action="Add caching, optimize queries, or scale infrastructure",
                implementation_effort="high",
                expected_benefit="high"
            )
            recommendations.append(rec)
        
        # Check peak load handling
        peak_load_stats = metrics_collector.get_metric_statistics(
            instance_id,
            AppMetricType.PEAK_LOAD,
            24
        )
        
        if peak_load_stats:
            load_variance = (peak_load_stats.get('max', 0) - peak_load_stats.get('min', 0)) / max(peak_load_stats.get('mean', 1), 1)
            if load_variance > 3:
                rec = AppLearningRecord(
                    learning_id=f"rec_scaling_{instance_id}",
                    instance_id=instance_id,
                    category=ImprovementCategory.SCALABILITY,
                    title="Variable Load Patterns",
                    description="Detected significant variance in load throughout day",
                    evidence=[
                        f"Load variance ratio: {load_variance:.2f}x",
                        f"Min load: {peak_load_stats.get('min', 0):.0f}",
                        f"Max load: {peak_load_stats.get('max', 0):.0f}"
                    ],
                    confidence=0.8,
                    recommended_action="Implement auto-scaling or load balancing",
                    implementation_effort="high",
                    expected_benefit="medium"
                )
                recommendations.append(rec)
        
        # Check error patterns from detector
        error_patterns = pattern_detector.get_patterns(instance_id, "errors")
        if len(error_patterns) > 2:
            rec = AppLearningRecord(
                learning_id=f"rec_stability_{instance_id}",
                instance_id=instance_id,
                category=ImprovementCategory.RELIABILITY,
                title="Multiple Error Types",
                description=f"Detected {len(error_patterns)} different error patterns",
                evidence=[
                    f"Error pattern: {p.description}" for p in error_patterns[:3]
                ],
                confidence=0.75,
                recommended_action="Implement comprehensive error handling and logging",
                implementation_effort="medium",
                expected_benefit="medium"
            )
            recommendations.append(rec)
        
        # Store recommendations
        if instance_id not in self.recommendations:
            self.recommendations[instance_id] = []
        self.recommendations[instance_id].extend(recommendations)
        
        return recommendations


class AppLearningMemory:
    """Learning memory system for generated apps."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.pattern_detector = PatternDetector()
        self.recommender = ImprovementRecommender()
        self.all_learnings: Dict[str, List[AppLearningRecord]] = {}
    
    async def analyze_and_learn(
        self,
        instance_id: str,
        execution_logs: List[Any]
    ) -> Dict[str, Any]:
        """Analyze execution logs and learn from them."""
        
        if not execution_logs:
            return {
                "patterns_detected": [],
                "recommendations": [],
                "learning_records": []
            }
        
        # Detect patterns
        peak_pattern = self.pattern_detector.detect_peak_hours(instance_id, execution_logs)
        if peak_pattern:
            self.pattern_detector.store_pattern(peak_pattern)
        
        route_patterns = self.pattern_detector.detect_common_routes(instance_id, execution_logs)
        for pattern in route_patterns:
            self.pattern_detector.store_pattern(pattern)
        
        error_patterns = self.pattern_detector.detect_error_patterns(instance_id, execution_logs)
        for pattern in error_patterns:
            self.pattern_detector.store_pattern(pattern)
        
        all_patterns = [peak_pattern] if peak_pattern else []
        all_patterns.extend(route_patterns)
        all_patterns.extend(error_patterns)
        
        # Generate recommendations
        recommendations = self.recommender.recommend_improvements(
            instance_id,
            self.metrics_collector,
            self.pattern_detector
        )
        
        # Create learning records from recommendations
        learning_records = []
        for rec in recommendations:
            learning_records.append(rec)
        
        if instance_id not in self.all_learnings:
            self.all_learnings[instance_id] = []
        self.all_learnings[instance_id].extend(learning_records)
        
        return {
            "patterns_detected": len(all_patterns),
            "pattern_details": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence
                }
                for p in all_patterns
            ],
            "recommendations": len(recommendations),
            "recommendation_details": [
                {
                    "category": r.category.value,
                    "title": r.title,
                    "confidence": r.confidence,
                    "effort": r.implementation_effort,
                    "benefit": r.expected_benefit
                }
                for r in recommendations
            ],
            "learning_records": len(learning_records)
        }
    
    def get_app_insights(self, instance_id: str) -> Dict[str, Any]:
        """Get comprehensive insights for app."""
        
        patterns = self.pattern_detector.get_patterns(instance_id)
        learnings = self.all_learnings.get(instance_id, [])
        
        # Group by category
        by_category = {}
        for learning in learnings:
            cat = learning.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(learning)
        
        insights = {
            "instance_id": instance_id,
            "total_patterns": len(patterns),
            "total_learnings": len(learnings),
            "patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "occurrences": p.occurrences,
                    "confidence": p.confidence
                }
                for p in patterns
            ],
            "learnings_by_category": {
                cat: [
                    {
                        "title": l.title,
                        "description": l.description,
                        "confidence": l.confidence,
                        "recommended_action": l.recommended_action
                    }
                    for l in learnings
                ]
                for cat, learnings in by_category.items()
            },
            "top_recommendations": self._get_top_recommendations(learnings)
        }
        
        return insights
    
    def _get_top_recommendations(
        self,
        learnings: List[AppLearningRecord]
    ) -> List[Dict[str, Any]]:
        """Get top N recommendations by confidence."""
        
        # Sort by confidence and effort-benefit ratio
        scored = []
        for learning in learnings:
            effort_score = {"low": 3, "medium": 2, "high": 1}.get(learning.implementation_effort, 1)
            benefit_score = {"low": 1, "medium": 2, "high": 3}.get(learning.expected_benefit, 1)
            score = learning.confidence * effort_score * benefit_score
            scored.append((learning, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "title": learning.title,
                "category": learning.category.value,
                "description": learning.description,
                "action": learning.recommended_action,
                "confidence": learning.confidence,
                "score": score
            }
            for learning, score in scored[:5]
        ]
