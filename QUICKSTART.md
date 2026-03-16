"""
Quick Start Guide for the Autonomous HR & Business Operations Intelligence Platform

This file provides a quick reference for getting started with the platform.
"""

# ============================================================================
# QUICK START
# ============================================================================

# 1. INSTALLATION
# ============================================================================
"""
pip install -r requirements.txt
cp .env.example .env

# For Pydantic AI reasoning features:
pip install anthropic pydantic-ai (optional)
"""

# 2. RUNNING THE APPLICATION
# ============================================================================
"""
# Start the server
python main.py

# Then visit:
# API Documentation: http://localhost:8000/docs
# Alternative Docs: http://localhost:8000/redoc
"""

# 3. RUN EXAMPLE
# ============================================================================
"""
# Run basic example
python examples/run_example.py

# Run Pydantic AI reasoning demonstrations (NEW)
python examples/agent_reasoning_demonstrations.py

# Show enhanced workflows with reasoning (NEW)
python -c "from examples.enhanced_workflows_with_reasoning import create_enhanced_workflows_map; workflows = create_enhanced_workflows_map(); print(f'Available workflows: {list(workflows.keys())}')"
"""

# ============================================================================
# BASIC USAGE PATTERNS
# ============================================================================

# NEW FEATURE: Pydantic AI Reasoning Chains
# ============================================================================
# Agents now automatically generate reasoning chains during execution:
#
# ReasoningChain includes:
#   - Multiple reasoning steps with confidence scores
#   - Observation and conclusion for each step
#   - Final decision and reasoning time
#
# ActionSelection provides:
#   - Selected tools and their priority
#   - Rationale for selection
#   - Fallback options
#
# ExecutionPlan offers:
#   - Detailed step-by-step plan
#   - Task prioritization
#   - Risk assessment and mitigation
#
# All reasoning is logged and stored in memory for transparency and learning.
# ============================================================================

# Connect to AsyncIO for workflow scripts
import asyncio
import sys
from pathlib import Path

# Add app to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from core.workflows.engine import WorkflowEngine
from core.agents.concrete import ExecutorAgent
from core.memory.implementations import HybridMemory
from core.models import WorkflowDefinition, WorkflowStepDefinition

async def example_basic_usage():
    """Basic usage example."""
    
    # 1. Create memory
    memory = HybridMemory()
    
    # 2. Create agents
    executor = ExecutorAgent(agent_id="executor_1", memory=memory)
    
    # 3. Create workflow engine
    engine = WorkflowEngine()
    engine.register_agent(executor)
    
    # 4. Create a simple workflow
    step = WorkflowStepDefinition(
        id="step_1",
        name="First Step",
        description="Initial step",
        agent_id="executor_1",
        next_steps=[]
    )
    
    workflow = WorkflowDefinition(
        id="workflow_simple",
        name="Simple Workflow",
        description="A simple test workflow",
        steps=[step],
        entry_point="step_1",
        agents=["executor_1"]
    )
    
    engine.register_workflow(workflow)
    
    # 5. Execute workflow
    execution = await engine.execute_workflow(
        "workflow_simple",
        {"task": "Test task"}
    )
    
    print(f"Execution completed: {execution.status.value}")

# ============================================================================
# API USAGE PATTERNS
# ============================================================================

"""
# Using Python requests library:

import requests

BASE_URL = "http://localhost:8000"

# Get all agents
response = requests.get(f"{BASE_URL}/agents")
agents = response.json()

# Get agent state
response = requests.get(f"{BASE_URL}/agents/executor_1")
agent_state = response.json()

# Execute workflow
response = requests.post(
    f"{BASE_URL}/workflows/workflow_employee_onboarding/execute",
    json={"task": "Onboard new employee"}
)
execution = response.json()

# Get execution details
response = requests.get(f"{BASE_URL}/executions/{execution['execution_id']}")
details = response.json()

# Get agent tools
response = requests.get(f"{BASE_URL}/agents/executor_1/tools")
tools = response.json()

# Store in memory
response = requests.post(
    f"{BASE_URL}/memory/store",
    json={"content": "Important data", "metadata": {"type": "note"}}
)
memory_id = response.json()["memory_id"]

# Retrieve from memory
response = requests.get(f"{BASE_URL}/memory/retrieve?query=important&limit=5")
results = response.json()

# Get event history
response = requests.get(f"{BASE_URL}/events")
events = response.json()

# Platform stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()

# Get info
response = requests.get(f"{BASE_URL}/info")
info = response.json()
"""

# ============================================================================
# CREATING CUSTOM WORKFLOWS
# ============================================================================

"""
from core.models import WorkflowDefinition, WorkflowStepDefinition, ToolExecutionRequest

# Define workflow steps
steps = [
    WorkflowStepDefinition(
        id="step_1",
        name="Send Email",
        description="Send notification email",
        agent_id="executor_1",
        tool_calls=[
            ToolExecutionRequest(
                tool_id="email_sender",
                inputs={
                    "to": "user@example.com",
                    "subject": "Hello",
                    "body": "Your task is ready"
                }
            )
        ],
        next_steps=["step_2"]
    ),
    WorkflowStepDefinition(
        id="step_2",
        name="Update Status",
        description="Update status",
        agent_id="executor_1",
        next_steps=[]
    )
]

# Create workflow
workflow = WorkflowDefinition(
    id="custom_workflow",
    name="My Custom Workflow",
    description="A custom workflow",
    steps=steps,
    entry_point="step_1",
    agents=["executor_1"]
)

# Register and execute
engine.register_workflow(workflow)
execution = await engine.execute_workflow("custom_workflow")
"""

# ============================================================================
# CREATING CUSTOM TOOLS
# ============================================================================

"""
from core.agents.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            tool_id="my_tool",
            name="My Tool",
            description="My custom tool"
        )
    
    async def execute(self, inputs):
        # Your implementation
        return {"result": "success"}
    
    def get_schema(self):
        return {
            "id": self.tool_id,
            "name": self.name,
            "inputs": [
                {"name": "param1", "type": "string", "required": True}
            ]
        }

# Add to agent
agent.add_tool(MyCustomTool())
"""

# ============================================================================
# WORKING WITH MEMORY
# ============================================================================

"""
from core.memory.implementations import HybridMemory

# Create memory
memory = HybridMemory()

# Store data
mem_id = await memory.store({
    "content": "Important information",
    "metadata": {"category": "notes", "priority": "high"}
})

# Retrieve data
results = await memory.retrieve("important information", limit=5)

# Update data
await memory.update(mem_id, {
    "content": "Updated information",
    "metadata": {"status": "updated"}
})

# Delete data
await memory.delete(mem_id)

# Clear all
await memory.clear()
"""

# ============================================================================
# EVENT-DRIVEN PATTERNS
# ============================================================================

"""
from core.workflows.engine import EventBus
from core.models import Event

event_bus = EventBus()

# Subscribe to events
async def on_workflow_completed(event):
    print(f"Workflow completed: {event.data}")

await event_bus.subscribe("workflow_completed", on_workflow_completed)

# Get event history
events = event_bus.get_history()
workflow_events = event_bus.get_history("workflow_completed")
"""

# ============================================================================
# FIREBASE OPERATIONS
# ============================================================================

"""
from integrations.firebase import FirestoreManager, AuthenticationManager

# Authentication
auth = AuthenticationManager()
token = await auth.authenticate_user("user@example.com", "password")

# Firestore
firestore = FirestoreManager()
await firestore.set_document("users", "user_1", {"name": "John"})
doc = await firestore.get_document("users", "user_1")
docs = await firestore.query_collection("users", limit=10)
await firestore.delete_document("users", "user_1")
"""

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

"""
Required environment variables (.env):

# Server
ENV=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Firebase
FIREBASE_PROJECT_ID=your-project
FIREBASE_PRIVATE_KEY=your-key
... (see .env.example)

# AI Model
ANTHROPIC_API_KEY=your-key

# Memory
USE_VECTOR_MEMORY=True
USE_FIRESTORE_MEMORY=True
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
1. Module not found errors:
   - Ensure you're running from project root
   - Check that app directory is in Python path
   - Verify installation: pip install -r requirements.txt

2. API connection errors:
   - Check that server is running: python main.py
   - Verify API_PORT in .env (default: 8000)
   - Check http://localhost:8000/docs

3. Firebase errors:
   - Provide valid credentials in .env
   - Or run in mock mode (default)

4. Asyncio errors:
   - Use 'await' for async functions
   - Run with asyncio.run(main_function())
"""

# ============================================================================
# NEXT STEPS
# ============================================================================

"""
1. Run the example:
   python examples/run_example.py

2. Start the server:
   python main.py

3. Visit the API docs:
   http://localhost:8000/docs

4. Create your first workflow:
   See examples/sample_workflows.py

5. Integrate with your services:
   See examples/integrations.py

6. Deploy to production:
   See Docker support (TODO)
"""

if __name__ == "__main__":
    asyncio.run(example_basic_usage())
