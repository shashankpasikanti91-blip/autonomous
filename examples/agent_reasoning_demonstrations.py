"""
Comprehensive examples demonstrating Pydantic AI reasoning chains in agents.

This module showcases:
1. Reasoning chain execution with memory integration
2. Tool selection based on context and reasoning
3. Multi-agent orchestration with reasoning
4. Memory-based decision making
5. Logging of reasoning steps for transparency
"""
import asyncio
from datetime import datetime
from core.agents.concrete import (
    CoordinatorAgent, ExecutorAgent, AnalyzerAgent, PlannerAgent
)
from core.tools.implementations import (
    EmailSenderTool, CalendarSchedulerTool, InvoiceGeneratorTool, N8NWebhookTool
)
from core.memory.implementations import VectorMemory, FirestoreMemory, HybridMemory
from core.workflows.engine import WorkflowEngine, EventBus
from core.models import (
    ExecutionStatus, AgentRole, ReasoningStep, ReasoningChain
)
from examples.enhanced_workflows_with_reasoning import (
    create_enhanced_employee_onboarding_workflow,
    create_enhanced_meeting_scheduling_workflow,
    create_enhanced_invoice_processing_workflow,
    ENHANCED_WORKFLOW_EXECUTION_CONTEXTS
)
from utils.logger import get_logger


logger = get_logger(__name__)


async def demonstrate_coordinator_reasoning() -> None:
    """
    Demonstrate Coordinator Agent reasoning for workflow orchestration.
    
    Shows:
    - Analyzing workflow complexity
    - Planning agent delegation
    - Resource allocation reasoning
    - Dependency identification
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Coordinator Agent Reasoning")
    logger.info("="*80)
    
    # Create memory backend
    memory = HybridMemory(
        vector_memory=VectorMemory(),
        firestore_memory=FirestoreMemory()
    )
    
    # Create coordinator agent
    coordinator = CoordinatorAgent(
        agent_id="coordinator_demo_1",
        tools=[],  # Coordinators don't execute tools directly
        memory=memory
    )
    
    # Coordinator reasoning context
    onboarding_context = {
        "workflow_id": "employee_onboarding_001",
        "agents": ["executor_1", "analyzer_1"],
        "steps_count": 6,
        "required_capabilities": ["email_send", "calendar_schedule", "invoice_generate"],
        "dependencies": [
            "step_1 -> step_2",  # Planning before execution
            "step_2 -> step_3",  # Email before calendar
            "step_3 -> step_4",  # Calendar before invoice
        ],
        "risk_factors": ["email_delivery", "calendar_conflict"]
    }
    
    # Run coordinator reasoning
    logger.info("\n[COORDINATOR] Analyzing workflow structure...")
    reasoning_chain = await coordinator._coordinate_reasoning(
        task="Orchestrate employee onboarding workflow",
        context=onboarding_context
    )
    
    # Display reasoning output
    logger.info(f"\n[COORDINATOR] Reasoning Analysis:")
    logger.info(f"  Initial Analysis: {reasoning_chain.initial_analysis}")
    logger.info(f"  Reasoning Steps: {len(reasoning_chain.steps)}")
    
    for step in reasoning_chain.steps:
        logger.info(f"\n  Step {step.step_number}:")
        logger.info(f"    Thinking: {step.thinking}")
        logger.info(f"    Observation: {step.observation}")
        logger.info(f"    Conclusion: {step.conclusion}")
        logger.info(f"    Confidence: {step.confidence:.2f}")
    
    logger.info(f"\n  Final Decision: {reasoning_chain.final_decision}")
    logger.info(f"  Reasoning Time: {reasoning_chain.reasoning_time_ms}ms")


async def demonstrate_executor_reasoning() -> None:
    """
    Demonstrate Executor Agent reasoning for task execution.
    
    Shows:
    - Tool capability evaluation
    - Execution strategy planning
    - Success criteria definition
    - Ready state assessment
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Executor Agent Reasoning")
    logger.info("="*80)
    
    # Create memory backend
    memory = VectorMemory()
    
    # Create executor with tools
    executor = ExecutorAgent(
        agent_id="executor_demo_1",
        tools=[
            EmailSenderTool("email_sender", "Email Sender", "Send emails"),
            CalendarSchedulerTool("calendar_scheduler", "Calendar Scheduler", "Schedule meetings"),
            InvoiceGeneratorTool("invoice_generator", "Invoice Generator", "Generate invoices")
        ],
        memory=memory
    )
    
    # Execution reasoning context
    task_context = {
        "task": "Send welcome email and schedule orientation",
        "requirements": ["email_send", "calendar_schedule"],
        "available_tools": {
            "email_sender": "Sends emails to recipients",
            "calendar_scheduler": "Schedules meetings"
        },
        "success_criteria": ["email_delivered", "calendar_event_created"],
        "constraints": ["timezone_aware", "no_conflicts"]
    }
    
    # Run executor reasoning
    logger.info("\n[EXECUTOR] Analyzing execution requirements...")
    reasoning_chain = await executor._execution_reasoning(
        task="Process employee onboarding tasks",
        context=task_context
    )
    
    # Display reasoning output
    logger.info(f"\n[EXECUTOR] Execution Analysis:")
    logger.info(f"  Initial Analysis: {reasoning_chain.initial_analysis}")
    logger.info(f"  Reasoning Steps: {len(reasoning_chain.steps)}")
    
    for step in reasoning_chain.steps:
        logger.info(f"\n  Step {step.step_number}:")
        logger.info(f"    Thinking: {step.thinking}")
        logger.info(f"    Observation: {step.observation}")
        logger.info(f"    Conclusion: {step.conclusion}")
        logger.info(f"    Confidence: {step.confidence:.2f}")
    
    logger.info(f"\n  Final Decision: {reasoning_chain.final_decision}")
    logger.info(f"  Reasoning Time: {reasoning_chain.reasoning_time_ms}ms")
    
    # Demonstrate tool selection
    logger.info("\n[EXECUTOR] Tool Selection Process:")
    selections = await executor._select_tools(
        task="Send welcome email",
        context=task_context
    )
    
    for i, selection in enumerate(selections, 1):
        logger.info(f"\n  Selection {i}:")
        logger.info(f"    Tool ID: {selection.selected_tool_id}")
        logger.info(f"    Action Type: {selection.action_type}")
        logger.info(f"    Priority: {selection.priority}")
        logger.info(f"    Rationale: {selection.rationale}")


async def demonstrate_analyzer_reasoning() -> None:
    """
    Demonstrate Analyzer Agent reasoning for data analysis.
    
    Shows:
    - Data structure understanding
    - Pattern identification
    - Correlation analysis
    - Insight generation
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Analyzer Agent Reasoning")
    logger.info("="*80)
    
    # Create memory backend
    memory = VectorMemory()
    
    # Create analyzer agent
    analyzer = AnalyzerAgent(
        agent_id="analyzer_demo_1",
        tools=[],
        memory=memory
    )
    
    # Analysis reasoning context
    analysis_context = {
        "data_structure": {
            "invoice_data": {},
            "payment_history": {},
            "client_profile": {}
        },
        "analysis_type": "invoice_validation",
        "patterns": ["payment_delays", "amount_patterns", "client_behavior"],
        "data_size": 1500
    }
    
    # Run analyzer reasoning
    logger.info("\n[ANALYZER] Starting data analysis...")
    reasoning_chain = await analyzer._analysis_reasoning(
        task="Analyze invoice data for quality and patterns",
        context=analysis_context
    )
    
    # Display reasoning output
    logger.info(f"\n[ANALYZER] Analysis Results:")
    logger.info(f"  Initial Analysis: {reasoning_chain.initial_analysis}")
    logger.info(f"  Reasoning Steps: {len(reasoning_chain.steps)}")
    
    for step in reasoning_chain.steps:
        logger.info(f"\n  Step {step.step_number}:")
        logger.info(f"    Thinking: {step.thinking}")
        logger.info(f"    Observation: {step.observation}")
        logger.info(f"    Conclusion: {step.conclusion}")
        logger.info(f"    Confidence: {step.confidence:.2f}")
    
    logger.info(f"\n  Final Decision: {reasoning_chain.final_decision}")
    logger.info(f"  Reasoning Time: {reasoning_chain.reasoning_time_ms}ms")


async def demonstrate_planner_reasoning() -> None:
    """
    Demonstrate Planner Agent reasoning for strategic planning.
    
    Shows:
    - Objective decomposition
    - Resource allocation strategy
    - Timeline estimation
    - Risk-aware scheduling
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Planner Agent Reasoning")
    logger.info("="*80)
    
    # Create memory backend
    memory = VectorMemory()
    
    # Create planner agent
    planner = PlannerAgent(
        agent_id="planner_demo_1",
        tools=[],
        memory=memory
    )
    
    # Planning reasoning context
    planning_context = {
        "objective": "Schedule optimal meeting across timezones",
        "resources": {
            "calendar_system": "Active",
            "notification_system": "Active",
            "room_booking": "Available"
        },
        "estimated_duration": 4,  # 4 hours total
        "risks": [
            "timezone_conflict",
            "room_unavailable",
            "attendee_conflict"
        ]
    }
    
    # Run planner reasoning
    logger.info("\n[PLANNER] Creating strategic plan...")
    reasoning_chain = await planner._planning_reasoning(
        task="Plan optimal meeting schedule",
        context=planning_context
    )
    
    # Display reasoning output
    logger.info(f"\n[PLANNER] Planning Analysis:")
    logger.info(f"  Initial Analysis: {reasoning_chain.initial_analysis}")
    logger.info(f"  Reasoning Steps: {len(reasoning_chain.steps)}")
    
    for step in reasoning_chain.steps:
        logger.info(f"\n  Step {step.step_number}:")
        logger.info(f"    Thinking: {step.thinking}")
        logger.info(f"    Observation: {step.observation}")
        logger.info(f"    Conclusion: {step.conclusion}")
        logger.info(f"    Confidence: {step.confidence:.2f}")
    
    logger.info(f"\n  Final Decision: {reasoning_chain.final_decision}")
    logger.info(f"  Reasoning Time: {reasoning_chain.reasoning_time_ms}ms")


async def demonstrate_full_workflow_with_reasoning() -> None:
    """
    Demonstrate complete workflow execution with agent reasoning.
    
    Shows:
    - Multi-agent orchestration
    - Reasoning chain logging throughout workflow
    - Memory integration across agents
    - Event-driven architecture with reasoning events
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Full Workflow with Agent Reasoning")
    logger.info("="*80)
    
    # Create shared memory
    memory = HybridMemory(
        vector_memory=VectorMemory(),
        firestore_memory=FirestoreMemory()
    )
    
    # Create event bus for monitoring
    event_bus = EventBus()
    
    # Create workflow engine
    workflow_engine = WorkflowEngine(event_bus=event_bus)
    
    # Create agents with tools
    coordinator = CoordinatorAgent(
        agent_id="coordinator_1",
        memory=memory
    )
    
    executor = ExecutorAgent(
        agent_id="executor_1",
        tools=[
            EmailSenderTool("email_sender", "Email Sender", "Send emails"),
            CalendarSchedulerTool("calendar_scheduler", "Calendar", "Schedule meetings"),
            InvoiceGeneratorTool("invoice_generator", "Invoice", "Generate invoices"),
            N8NWebhookTool("n8n_webhook", "N8N", "Trigger workflows")
        ],
        memory=memory
    )
    
    analyzer = AnalyzerAgent(
        agent_id="analyzer_1",
        memory=memory
    )
    
    # Register agents and workflow
    workflow_engine.register_agent(coordinator)
    workflow_engine.register_agent(executor)
    workflow_engine.register_agent(analyzer)
    
    workflow_definition = create_enhanced_employee_onboarding_workflow()
    workflow_engine.register_workflow(workflow_definition)
    
    # Get execution context
    exec_context = ENHANCED_WORKFLOW_EXECUTION_CONTEXTS["enhanced_employee_onboarding"]
    
    # Execute workflow
    logger.info(f"\n[WORKFLOW] Starting: {workflow_definition.name}")
    logger.info(f"[WORKFLOW] Agents: {', '.join(workflow_definition.agents)}")
    logger.info(f"[WORKFLOW] Steps: {len(workflow_definition.steps)}")
    
    try:
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow_definition.id,
            input_data=exec_context["context"]
        )
        
        logger.info(f"\n[WORKFLOW] Execution Status: {execution.status.value}")
        logger.info(f"[WORKFLOW] Steps Executed: {len(execution.steps_executed)}")
        logger.info(f"[WORKFLOW] Agents Involved: {', '.join(execution.agents_involved)}")
        
        if execution.errors:
            logger.warning(f"[WORKFLOW] Errors: {len(execution.errors)}")
            for error in execution.errors:
                logger.warning(f"  - {error}")
        
        # Display reasoning chains from results
        if execution.results:
            logger.info(f"\n[WORKFLOW] Results with Reasoning:")
            for step_id, result in execution.results.items():
                if isinstance(result, dict) and "reasoning_chain" in result:
                    reasoning = result["reasoning_chain"]
                    logger.info(f"\n  Step: {step_id}")
                    logger.info(f"    Reasoning Time: {reasoning.get('reasoning_time_ms', 'N/A')}ms")
                    logger.info(f"    Final Decision: {reasoning.get('final_decision', 'N/A')}")
        
        # Display event history with reasoning events
        events = event_bus.get_history()
        logger.info(f"\n[WORKFLOW] Event History ({len(events)} events):")
        for event in events[-10:]:  # Last 10 events
            logger.info(f"  - {event.event_type}: {event.data}")
    
    except Exception as e:
        logger.error(f"[WORKFLOW] Execution failed: {str(e)}")


async def demonstrate_memory_based_reasoning() -> None:
    """
    Demonstrate how agents use memory for contextual reasoning.
    
    Shows:
    - Storing reasoning chains in memory
    - Retrieving historical patterns
    - Memory-based decision enhancement
    - Cross-agent memory sharing
    """
    logger.info("\n" + "="*80)
    logger.info("DEMONSTRATION: Memory-Based Agent Reasoning")
    logger.info("="*80)
    
    # Create memory backend
    vector_memory = VectorMemory()
    firestore_memory = FirestoreMemory()
    memory = HybridMemory(vector_memory, firestore_memory)
    
    # Create agent
    executor = ExecutorAgent(
        agent_id="executor_memory_demo",
        tools=[EmailSenderTool("email", "Email", "Send emails")],
        memory=memory
    )
    
    # Store some example memories
    logger.info("\n[MEMORY] Storing execution history...")
    
    memories_to_store = [
        {
            "type": "execution",
            "task": "Send welcome email",
            "success": True,
            "duration_ms": 250,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "type": "execution",
            "task": "Schedule meeting",
            "success": True,
            "duration_ms": 180,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "type": "reasoning",
            "confidence_avg": 0.82,
            "steps_count": 4,
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    for mem in memories_to_store:
        try:
            await memory.store(mem)
            logger.info(f"  Stored: {mem['type']} - {mem.get('task', 'general')}")
        except Exception as e:
            logger.warning(f"  Failed to store: {str(e)}")
    
    # Retrieve memories for reasoning enhancement
    logger.info("\n[MEMORY] Retrieving execution patterns...")
    
    try:
        retrieved = await memory.retrieve({"type": "execution"})
        logger.info(f"  Retrieved {len(retrieved)} execution records")
        
        for rec in retrieved:
            logger.info(f"    - {rec.get('task', 'unknown')}: {rec.get('success', 'unknown')}")
    except Exception as e:
        logger.warning(f"  Retrieval failed: {str(e)}")
    
    # Process with reasoning chain enhanced by memory
    logger.info("\n[MEMORY] Processing task with memory-enhanced reasoning...")
    
    input_data = {
        "task": "Send onboarding email",
        "objective": "Send welcome email to new employee",
        "context": {
            "requirements": ["email_send"],
            "tool_inputs": {
                "email_sender": {
                    "to": "newemployee@example.com",
                    "subject": "Welcome!",
                    "body": "Welcome to the team!"
                }
            }
        }
    }
    
    response = await executor.process(input_data)
    
    logger.info(f"\n[MEMORY] Execution completed:")
    logger.info(f"  Status: {response.status.value}")
    logger.info(f"  Memory Accessed: {response.memory_accessed}")
    
    if response.reasoning_chain:
        logger.info(f"  Reasoning Steps: {len(response.reasoning_chain.steps)}")
        logger.info(f"  Reasoning Time: {response.reasoning_chain.reasoning_time_ms}ms")


async def run_all_demonstrations() -> None:
    """Run all agent reasoning demonstrations."""
    logger.info("\n\n")
    logger.info("#"*80)
    logger.info("# PYDANTIC AI AGENT REASONING DEMONSTRATIONS")
    logger.info("#"*80)
    
    try:
        # Coordinator reasoning
        await demonstrate_coordinator_reasoning()
        
        # Executor reasoning
        await demonstrate_executor_reasoning()
        
        # Analyzer reasoning
        await demonstrate_analyzer_reasoning()
        
        # Planner reasoning
        await demonstrate_planner_reasoning()
        
        # Full workflow with reasoning
        await demonstrate_full_workflow_with_reasoning()
        
        # Memory-based reasoning
        await demonstrate_memory_based_reasoning()
        
        logger.info("\n" + "#"*80)
        logger.info("# ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        logger.info("#"*80 + "\n")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # Run demonstrations
    asyncio.run(run_all_demonstrations())

