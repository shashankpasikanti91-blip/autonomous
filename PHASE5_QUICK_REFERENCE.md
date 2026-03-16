# Phase 5: Autonomous Intelligence - Quick Reference

**TL;DR**: One-line prompts → intelligent workflows with auto-learning and improvement.

---

## 1. Basic Usage

```python
from app.intelligence import get_intelligence_orchestrator

orchestrator = get_intelligence_orchestrator()

# Execute workflow from natural language
execution = await orchestrator.execute_from_prompt(
    "Send personalized emails to contacts in sales region"
)

print(f"Status: {execution.status}")
print(f"Results: {execution.results}")
```

---

## 2. Execute & Get Results

```python
# Execute
execution = await orchestrator.execute_from_prompt(
    user_query="Send email to alice@test.com with subject 'Hello'",
    correlation_id="optional_tracking_id",
    max_retries=3
)

# Check results
if execution.status.value == "completed":
    print(f"✓ Success in {execution.total_latency_ms:.0f}ms")
    for task_id, task in execution.task_executions.items():
        print(f"  - {task_id}: {task.result}")
else:
    print(f"✗ Failed: {execution.error}")
```

---

## 3. Learn From Results

```python
# Get improvement suggestions
suggestions = orchestrator.get_improvement_suggestions(execution.execution_id)
for suggestion in suggestions:
    print(f"💡 {suggestion}")

# Get learnings for operation
learnings = orchestrator.get_learnings_for_operation("send_email")
for learning in learnings:
    print(f"Success rate: {learning['success_rate']:.0%}")
    print(f"Avg latency: {learning['latency_ms']:.0f}ms")
```

---

## 4. Debug Reasoning

```python
# Replay decision chain
replay = orchestrator.replay_reasoning(execution.reasoning_trace_id)
print(f"Steps: {replay['steps_count']}")
print(f"Decision tree:\n{replay['decision_tree']}")

# Check for reasoning problems
failures = orchestrator.detect_reasoning_failures(
    execution.reasoning_trace_id
)
for failure in failures:
    print(f"⚠️  {failure['type']}: {failure.get('reasoning')}")

# Get improvement suggestions
suggestions = orchestrator.suggest_reasoning_improvements(
    execution.reasoning_trace_id
)
for suggestion in suggestions:
    print(f"→ {suggestion}")
```

---

## 5. Supported Intents

| Intent | Example | Auto-Operations |
|--------|---------|-----------------|
| Send Communication | "Send email to alice@test.com" | Lookup contact → Send email → Log activity |
| Retrieve Data | "Get recent contacts" | Search contacts → Return results |
| Create Resource | "Create meeting with team" | Find available time → Create event → Notify attendees |
| Update Resource | "Update contact info" | Lookup contact → Update fields → Sync CRM |
| Delete Resource | "Remove contact" | Lookup contact → Delete → Confirm |
| Batch Operation | "Email top 100 contacts" | Search → Chunk → Send in batches |
| Scheduled Action | "Send email tomorrow at 9am" | Parse time → Schedule → Execute |
| Conditional | "If no activity, send reminder" | Query → Conditional logic → Send |

---

## 6. Working With Agents

### Default Agents

```python
# 4 default agents registered:
# - agent_email: Email Specialist
# - agent_messaging: Messaging Specialist
# - agent_calendar: Calendar Specialist
# - agent_crm: CRM Specialist

# Register custom agent
orchestrator.register_agent(
    agent_id="agent_analytics",
    agent_name="Analytics Engine",
    description="Handles data analysis",
    supported_operations={"analyze_trends", "generate_report"},
    expertise_level=9.0,
    availability=0.99,
    specializations={"performance", "insights"}
)
```

---

## 7. Working With Tools

### Auto-Registered Tools

```python
# Tools auto-discovered from Phase 4 adapters:
# Email: email_send, email_send_batch
# Messaging: messaging_send, messaging_send_template, messaging_get_status
# Calendar: calendar_create_event, calendar_find_slots, calendar_update_event
# CRM: crm_create_contact, crm_search_contacts, crm_create_activity, etc.

# Usage (automatic - no direct calls needed):
# System selects best tool based on:
# - Success rate
# - Latency
# - Cost
# - Rate limits
# - Current availability
```

### Register Custom Tool

```python
async def my_custom_tool(param1: str, param2: int) -> dict:
    # Your implementation
    return {"result": "done"}

orchestrator.register_tool(
    tool_id="custom_my_tool",
    name="My Custom Tool",
    description="Does something specific",
    capabilities={"custom", "analysis"},
    implementation=my_custom_tool,
    input_schema={
        "param1": "string",
        "param2": "integer"
    },
    output_schema={
        "result": "string"
    }
)
```

---

## 8. Monitor Execution

```python
# Get system stats
stats = orchestrator.get_system_stats()
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']:.0%}")
print(f"Avg latency: {stats['avg_latency_ms']:.0f}ms")
print(f"Tools: {stats['tools_registered']}")
print(f"Agents: {stats['agents_registered']}")
print(f"Learning records: {stats['learning_records']}")
```

---

## 9. Safety & Constraints

```python
# Limit cost per workflow
orchestrator.add_safety_constraint(
    constraint_id="max_cost",
    name="Cost Limit",
    constraint_type="cost_limit",
    applies_to={"email_send_batch", "crm_create_activity"},
    max_cost_per_workflow=100.0
)

# Block sensitive operations
orchestrator.add_safety_constraint(
    constraint_id="no_deletes",
    name="Prevent Deletes",
    constraint_type="scope",
    applies_to={"*"},
    blocked_operations={"delete_contact", "delete_event"}
)

# Rate limiting
orchestrator.add_safety_constraint(
    constraint_id="api_rate_limit",
    name="API Limits",
    constraint_type="rate_limit",
    applies_to={"agent_crm"},
    max_api_calls_per_hour=5000
)
```

---

## 10. Workflow Templates

```python
# Save workflow template
orchestrator.save_workflow_template(
    template_id="lead_nurture_v1",
    name="Lead Nurture Workflow",
    description="Auto-generated from successful executions",
    category="crm_workflow",
    pattern="For new contacts, create activity, send welcome email",
    parameters={"email_template": "welcome_v2"}
)

# Get templates for category
templates = orchestrator.get_templates_for_category("email_campaign")
for template in templates:
    print(f"{template.name}: {template.success_rate:.0%} success")

# Templates auto-generated from frequent successful patterns
# Reuses optimal agent/tool/strategy selections
```

---

## 11. Error Handling

```python
try:
    execution = await orchestrator.execute_from_prompt(user_query)
except Exception as e:
    print(f"Execution failed: {e}")

# Check execution result
if execution.error:
    print(f"Workflow error: {execution.error}")

# Inspect task failures
for task_id, task_exec in execution.task_executions.items():
    if task_exec.status.value == "failed":
        print(f"Task {task_id} failed: {task_exec.error}")
        print(f"Category: {task_exec.error_category}")
        print(f"Retries: {task_exec.retry_count}")
```

---

## 12. Async Execution

```python
import asyncio

async def main():
    orchestrator = get_intelligence_orchestrator()
    
    # Single execution
    exec1 = await orchestrator.execute_from_prompt("Send emails")
    
    # Parallel executions
    exec2, exec3 = await asyncio.gather(
        orchestrator.execute_from_prompt("Create events"),
        orchestrator.execute_from_prompt("Update contacts")
    )
    
    print(f"Completed {3} workflows in parallel")

asyncio.run(main())
```

---

## 13. Cost Estimation

```python
# Execution includes cost estimate
execution = await orchestrator.execute_from_prompt(user_query)

plan = execution.plan_id
print(f"Estimated cost: ${plan.estimated_cost:.2f}")
print(f"Actual cost: varies based on tool execution")

# Check tool costs
tools = orchestrator.tool_registry.tools.values()
for tool in tools:
    print(f"{tool.name}: ${tool.cost_per_call:.4f} per call")
```

---

## 14. Performance Tips

```python
# ✓ DO: Use natural language - system optimizes automatically
execution = await orchestrator.execute_from_prompt(
    "Send personalized emails to top contacts"
)

# ✓ DO: Let system learn - success rate improves over time
# After 10+ similar executions, system pre-optimizes

# ✓ DO: Check suggestions - improve your queries
suggestions = orchestrator.get_improvement_suggestions(exec_id)

# ✗ DON'T: Over-specify - let system route and select
# Bad: "Use email_send_batch tool with agent_email"
# Good: "Send emails in batch"

# ✗ DON'T: Ignore errors - check reasoning for issues
failures = orchestrator.detect_reasoning_failures(trace_id)
```

---

## 15. Integration with Phase 4

```python
# Phase 4 still works
from app.integrations import get_email_adapter
adapter = get_email_adapter()
response = await adapter.call(operation="send_email", parameters={...})

# Phase 5 uses Phase 4 under the hood
from app.intelligence import get_intelligence_orchestrator
orchestrator = get_intelligence_orchestrator()  # Uses adapters internally
execution = await orchestrator.execute_from_prompt("Send that email")

# Both work simultaneously - no conflicts
```

---

## Status

✅ **Operational** - Autonomous intelligence layer ready for use
✅ **Compatible** - All Phase 4 adapters and integrations work transparently
✅ **Learning** - System improves with every execution
✅ **Safe** - Supports cost limits, rate limiting, and operation blocking
✅ **Debuggable** - Complete reasoning traces and failure detection

**Next**: Use in production, monitor learning effectiveness, extend with custom tools.
