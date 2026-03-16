"""
API Client example for interacting with the platform via HTTP.
This demonstrates how to use the FastAPI endpoints programmatically.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add app to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: pip install httpx")
    sys.exit(1)

from utils.logger import get_logger


logger = get_logger(__name__)


class HRPlatformClient:
    """HTTP client for interacting with the HR Platform API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token: Optional[str] = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check platform health."""
        response = await self.client.get("/health")
        return response.json()
    
    async def login(self, email: str, password: str) -> str:
        """Authenticate user and get token."""
        response = await self.client.post(
            "/auth/login",
            params={"email": email, "password": password}
        )
        data = response.json()
        self.token = data.get("token")
        return self.token
    
    async def list_agents(self) -> Dict[str, Any]:
        """List all agents."""
        response = await self.client.get("/agents")
        return response.json()
    
    async def get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Get agent state."""
        response = await self.client.get(f"/agents/{agent_id}")
        return response.json()
    
    async def get_agent_tools(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's available tools."""
        response = await self.client.get(f"/agents/{agent_id}/tools")
        return response.json()
    
    async def process_with_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process input with an agent."""
        response = await self.client.post(
            f"/agents/{agent_id}/process",
            json=input_data
        )
        return response.json()
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List all workflows."""
        response = await self.client.get("/workflows")
        return response.json()
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details."""
        response = await self.client.get(f"/workflows/{workflow_id}")
        return response.json()
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        response = await self.client.post("/workflows", json=workflow_data)
        return response.json()
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        response = await self.client.post(
            f"/workflows/{workflow_id}/execute",
            json=input_data or {}
        )
        return response.json()
    
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution details."""
        response = await self.client.get(f"/executions/{execution_id}")
        return response.json()
    
    async def list_workflow_executions(self, workflow_id: str) -> Dict[str, Any]:
        """List executions for a workflow."""
        response = await self.client.get(f"/workflows/{workflow_id}/executions")
        return response.json()
    
    async def get_events(
        self,
        event_type: Optional[str] = None,
        execution_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get event history."""
        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        if execution_id:
            params["execution_id"] = execution_id
        
        response = await self.client.get("/events", params=params)
        return response.json()
    
    async def store_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store data in memory."""
        response = await self.client.post("/memory/store", json=data)
        return response.json()
    
    async def retrieve_memory(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Retrieve from memory."""
        response = await self.client.get(
            "/memory/retrieve",
            params={"query": query, "limit": limit}
        )
        return response.json()
    
    async def set_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store document in Firestore."""
        response = await self.client.post(
            f"/data/{collection}/{document_id}",
            json=data
        )
        return response.json()
    
    async def get_document(
        self,
        collection: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Get document from Firestore."""
        response = await self.client.get(f"/data/{collection}/{document_id}")
        return response.json()
    
    async def query_collection(
        self,
        collection: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Query collection."""
        response = await self.client.get(
            f"/data/{collection}",
            params={"limit": limit}
        )
        return response.json()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get platform statistics."""
        response = await self.client.get("/stats")
        return response.json()
    
    async def get_info(self) -> Dict[str, Any]:
        """Get platform information."""
        response = await self.client.get("/info")
        return response.json()
    
    async def close(self):
        """Close the client connection."""
        await self.client.aclose()


async def main():
    """Example client usage."""
    client = HRPlatformClient()
    
    try:
        # Check health
        print("Checking platform health...")
        health = await client.health_check()
        print(f"✓ Platform is healthy: {health}\n")
        
        # Get platform info
        print("Getting platform information...")
        info = await client.get_info()
        print(f"✓ Platform: {info['name']} v{info['version']}\n")
        
        # List agents
        print("Listing agents...")
        agents = await client.list_agents()
        print(f"✓ Found {agents['total']} agents:")
        for agent in agents['agents']:
            print(f"  - {agent['name']} ({agent['agent_id']})")
        print()
        
        # Get agent tools
        if agents['agents']:
            agent_id = agents['agents'][0]['agent_id']
            print(f"Getting tools for {agent_id}...")
            tools = await client.get_agent_tools(agent_id)
            print(f"✓ Agent has {tools['total']} tools:")
            for tool in tools['tools']:
                print(f"  - {tool['name']} ({tool['tool_id']})")
            print()
        
        # List workflows
        print("Listing workflows...")
        workflows = await client.list_workflows()
        print(f"✓ Found {workflows['total']} workflows:")
        for wf in workflows['workflows']:
            print(f"  - {wf['name']} ({wf['workflow_id']})")
        print()
        
        # Execute a workflow
        if workflows['workflows']:
            workflow_id = workflows['workflows'][0]['workflow_id']
            print(f"Executing workflow {workflow_id}...")
            
            execution = await client.execute_workflow(
                workflow_id,
                {"task": "Test execution via client"}
            )
            execution_id = execution['execution_id']
            print(f"✓ Execution started: {execution_id}\n")
            
            # Get execution details
            print("Getting execution details...")
            details = await client.get_execution(execution_id)
            print(f"✓ Execution status: {details['status']}")
            print(f"  Steps executed: {len(details['steps_executed'])}")
            print(f"  Tool calls: {details['tool_calls_count']}\n")
        
        # Store in memory
        print("Storing data in memory...")
        mem = await client.store_memory({
            "content": "Test data from API client",
            "metadata": {"source": "api_client", "type": "test"}
        })
        print(f"✓ Stored in memory: {mem['memory_id']}\n")
        
        # Retrieve from memory
        print("Retrieving from memory...")
        results = await client.retrieve_memory("test data", limit=5)
        print(f"✓ Retrieved {results['count']} memory entries\n")
        
        # Get statistics
        print("Getting platform statistics...")
        stats = await client.get_statistics()
        print(f"✓ Platform Statistics:")
        print(f"  Agents: {stats['agents_count']}")
        print(f"  Workflows: {stats['workflows_count']}")
        print(f"  Executions: {stats['executions_count']}")
        print(f"  Completed: {stats['completed_executions']}")
        print(f"  Failed: {stats['failed_executions']}")
        print(f"  Events: {stats['events_count']}\n")
        
        print("=" * 60)
        print("Client example completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"✗ Error: {str(e)}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
