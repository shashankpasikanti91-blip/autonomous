"""
Example usage demonstrating the platform capabilities.
"""
import asyncio
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from core.workflows.engine import WorkflowEngine, EventBus
from core.agents.concrete import ExecutorAgent, CoordinatorAgent
from core.tools.implementations import (
    EmailSenderTool, CalendarSchedulerTool, InvoiceGeneratorTool, N8NWebhookTool
)
from core.memory.implementations import HybridMemory
from examples.sample_workflows import create_workflow_samples, WORKFLOW_EXECUTION_EXAMPLES
from utils.logger import get_logger


logger = get_logger(__name__)


async def main():
    """Run example workflow execution."""
    
    print("=" * 80)
    print("Autonomous HR & Business Operations Intelligence Platform")
    print("Example Workflow Execution")
    print("=" * 80)
    print()
    
    # Initialize components
    event_bus = EventBus()
    workflow_engine = WorkflowEngine(event_bus=event_bus)
    hybrid_memory = HybridMemory()
    
    # Create agents with tools
    tools = [
        EmailSenderTool(),
        CalendarSchedulerTool(),
        InvoiceGeneratorTool(),
        N8NWebhookTool(),
    ]
    
    executor = ExecutorAgent(
        agent_id="executor_1",
        tools=tools,
        memory=hybrid_memory
    )
    
    coordinator = CoordinatorAgent(
        agent_id="coordinator_1",
        memory=hybrid_memory
    )
    
    # Register agents
    workflow_engine.register_agent(executor)
    workflow_engine.register_agent(coordinator)
    
    logger.info("Agents registered")
    print(f"✓ Registered {len(workflow_engine.agents)} agents\n")
    
    # Create and register workflows
    workflows = create_workflow_samples()
    for workflow_key, workflow in workflows.items():
        workflow_engine.register_workflow(workflow)
    
    logger.info(f"Workflows registered: {list(workflows.keys())}")
    print(f"✓ Registered {len(workflows)} workflows\n")
    
    # Display available workflows
    print("Available Workflows:")
    for wf_id, workflow in workflows.items():
        print(f"  • {workflow.name} ({workflow.id})")
        print(f"    Description: {workflow.description}")
        print(f"    Steps: {len(workflow.steps)}")
        print()
    
    # Execute the employee onboarding workflow
    print("=" * 80)
    print("Executing Employee Onboarding Workflow")
    print("=" * 80)
    print()
    
    workflow_id = "workflow_employee_onboarding"
    input_data = WORKFLOW_EXECUTION_EXAMPLES.get("employee_onboarding", {})
    
    try:
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        execution = await workflow_engine.execute_workflow(workflow_id, input_data)
        
        print(f"✓ Workflow execution completed: {execution.id}")
        print(f"  Status: {execution.status.value}")
        print(f"  Steps executed: {len(execution.steps_executed)}")
        print(f"  Agents involved: {execution.agents_involved}")
        print(f"  Tool calls: {len(execution.tool_calls)}")
        print()
        
        # Display execution details
        if execution.results:
            print("Execution Results:")
            for step_id, result in execution.results.items():
                print(f"  • {step_id}: {result}")
            print()
        
        # Display tool execution results
        if execution.tool_calls:
            print("Tool Executions:")
            for tool_call in execution.tool_calls:
                print(f"  • {tool_call.tool_id}: {tool_call.status.value}")
                if tool_call.output:
                    print(f"    Output: {tool_call.output}")
            print()
        
        # Display errors if any
        if execution.errors:
            print("Errors encountered:")
            for error in execution.errors:
                print(f"  • {error}")
            print()
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        print(f"✗ Error: {str(e)}\n")
    
    # Show agents state
    print("=" * 80)
    print("Agent States")
    print("=" * 80)
    print()
    
    for agent in workflow_engine.agents.values():
        state = agent.get_state()
        print(f"Agent: {agent.name} ({agent.agent_id})")
        print(f"  Status: {state.status.value}")
        print(f"  Messages: {len(state.messages)}")
        print(f"  Tools: {len(agent.tools)}")
        print()
    
    # Show memory state
    print("=" * 80)
    print("Memory State")
    print("=" * 80)
    print()
    
    # Store sample data in memory
    await hybrid_memory.store({
        "type": "workflow_execution",
        "workflow_id": workflow_id,
        "execution_id": execution.id if 'execution' in locals() else "unknown",
        "timestamp": "2024-02-21T10:00:00Z",
        "content": "Employee onboarding workflow execution completed successfully"
    })
    
    print("✓ Stored execution data in hybrid memory")
    
    # Retrieve from memory
    results = await hybrid_memory.retrieve("onboarding workflow", limit=5)
    print(f"✓ Retrieved {len(results)} memory entries\n")
    
    # Show event history
    print("=" * 80)
    print("Event History")
    print("=" * 80)
    print()
    
    events = event_bus.get_history()
    print(f"Total events: {len(events)}")
    
    # Group events by type
    event_types = {}
    for event in events:
        if event.event_type not in event_types:
            event_types[event.event_type] = 0
        event_types[event.event_type] += 1
    
    print("Events by type:")
    for event_type, count in event_types.items():
        print(f"  • {event_type}: {count}")
    print()
    
    # Show platform statistics
    print("=" * 80)
    print("Platform Statistics")
    print("=" * 80)
    print()
    
    print(f"Total Agents: {len(workflow_engine.agents)}")
    print(f"Total Workflows: {len(workflow_engine.workflows)}")
    print(f"Total Executions: {len(workflow_engine.executions)}")
    print(f"Total Events: {len(event_bus.event_history)}")
    print()
    
    # Show sample API commands
    print("=" * 80)
    print("Sample API Calls")
    print("=" * 80)
    print()
    
    print("Run with: python main.py")
    print()
    print("Example API endpoints:")
    print("  • GET /health - Health check")
    print("  • GET /agents - List all agents")
    print("  • GET /workflows - List all workflows")
    print("  • POST /workflows/<id>/execute - Execute workflow")
    print("  • GET /executions/<id> - Get execution details")
    print("  • GET /events - Get event history")
    print("  • POST /memory/store - Store in memory")
    print("  • POST /agents/<id>/process - Process with agent")
    print()
    
    print("=" * 80)
    print("Example execution completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
