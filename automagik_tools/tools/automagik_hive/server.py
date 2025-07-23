import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import AutomagikHiveConfig


class AutomagikHiveClient:
    """Client for interacting with the Automagik Hive API."""
    
    def __init__(self, config: AutomagikHiveConfig):
        self.config = config
        headers = {}
        if config.api_key:
            headers["x-api-key"] = config.api_key
        
        self.client = httpx.AsyncClient(
            base_url=config.api_base_url,
            timeout=config.timeout,
            headers=headers
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Automagik Hive API."""
        response = await self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def request_multipart(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a multipart form request to the Automagik Hive API."""
        files = {key: (None, str(value)) for key, value in data.items() if value is not None}
        response = await self.client.request(method, endpoint, files=files)
        response.raise_for_status()
        
        # Get the raw text and parse it with standard json module
        import json
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            # Return debug info for troubleshooting
            return {
                "error": "JSON parsing failed",
                "details": str(e),
                "raw_response": response.text[:1000],  # First 1000 chars
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
    
    async def request_form_urlencoded(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a form-urlencoded request to the Automagik Hive API."""
        # Filter out None values and convert to strings, handling booleans properly
        form_data = {}
        for key, value in data.items():
            if value is not None:
                if isinstance(value, bool):
                    form_data[key] = "true" if value else "false"
                else:
                    form_data[key] = str(value)
        
        response = await self.client.request(method, endpoint, data=form_data)
        response.raise_for_status()
        
        # Get the raw text and parse it with standard json module
        import json
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            # Return debug info for troubleshooting
            return {
                "error": "JSON parsing failed",
                "details": str(e),
                "raw_response": response.text[:1000],  # First 1000 chars
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }


def create_server(config: AutomagikHiveConfig = None) -> FastMCP:
    """Create and configure the Automagik Hive MCP server."""
    if config is None:
        config = AutomagikHiveConfig()
    mcp = FastMCP("Automagik Hive")
    
    # 🎮 Playground Status
    @mcp.tool()
    async def check_playground_status(app_id: Optional[str] = None) -> Dict[str, Any]:
        """Check the current status of the playground environment. Optionally specify an app ID to check a specific application."""
        params = {"app_id": app_id} if app_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", "/playground/status", params=params)
    
    # 🤖 Agent Operations
    @mcp.tool()
    async def list_available_agents() -> List[Dict[str, Any]]:
        """List all available agents in the playground that you can interact with."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", "/playground/agents")
    
    @mcp.tool()
    async def start_agent_conversation(
        agent_id: str,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a new conversation with an agent. Provide your message and the agent will respond."""
        # API expects multipart form data with message field and defaults
        data = {
            "message": message,
            "stream": "false",  # Convert to string for multipart
            "monitor": "false"  # Convert to string for multipart
        }
        if user_id:
            data["user_id"] = user_id
        if session_id:
            data["session_id"] = session_id
        
        async with AutomagikHiveClient(config) as client:
            return await client.request_multipart("POST", f"/playground/agents/{agent_id}/runs", data)
    
    @mcp.tool()
    async def continue_agent_conversation(
        agent_id: str,
        run_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Continue an ongoing conversation with an agent. Send your next message to keep the conversation going."""
        # API expects form-urlencoded data with "tools" field containing JSON array
        import json
        tools_json = json.dumps([{"type": "message", "content": message}])
        data = {
            "tools": tools_json,
            "stream": False
        }
        async with AutomagikHiveClient(config) as client:
            return await client.request_form_urlencoded("POST", f"/playground/agents/{agent_id}/runs/{run_id}/continue", data)
    
    @mcp.tool()
    async def view_agent_conversation_history(
        agent_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """View all your conversation sessions with a specific agent."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/agents/{agent_id}/sessions", params=params)
    
    @mcp.tool()
    async def get_specific_agent_conversation(
        agent_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get details of a specific conversation session with an agent."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/agents/{agent_id}/sessions/{session_id}", params=params)
    
    @mcp.tool()
    async def delete_agent_conversation(
        agent_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a conversation session with an agent. This cannot be undone."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("DELETE", f"/playground/agents/{agent_id}/sessions/{session_id}", params=params)
    
    @mcp.tool()
    async def rename_agent_conversation(
        agent_id: str,
        session_id: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Give a custom name to your conversation session with an agent for easier identification."""
        data = {"name": new_name}
        async with AutomagikHiveClient(config) as client:
            return await client.request("POST", f"/playground/agents/{agent_id}/sessions/{session_id}/rename", json=data)
    
    @mcp.tool()
    async def view_agent_memories(
        agent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """View what an agent remembers about your interactions and conversations."""
        params = {"user_id": user_id}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/agents/{agent_id}/memories", params=params)
    
    # 🔄 Workflow Operations
    @mcp.tool()
    async def list_available_workflows() -> List[Dict[str, Any]]:
        """List all available workflows in the playground that you can execute."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", "/playground/workflows")
    
    @mcp.tool()
    async def get_workflow_details(workflow_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific workflow including its steps and capabilities."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/workflows/{workflow_id}")
    
    @mcp.tool()
    async def execute_workflow(
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a workflow with your input data. The workflow will process your request through multiple steps."""
        data = {
            "input": input_data,
            "stream": False  # Disable streaming for better tool integration
        }
        if user_id:
            data["user_id"] = user_id
        async with AutomagikHiveClient(config) as client:
            return await client.request("POST", f"/playground/workflows/{workflow_id}/runs", json=data)
    
    @mcp.tool()
    async def view_workflow_execution_history(
        workflow_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """View all your execution sessions with a specific workflow."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/workflows/{workflow_id}/sessions", params=params)
    
    @mcp.tool()
    async def get_workflow_execution_details(
        workflow_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed results and logs from a specific workflow execution."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/workflows/{workflow_id}/sessions/{session_id}", params=params)
    
    @mcp.tool()
    async def delete_workflow_execution(
        workflow_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Delete a workflow execution session. This cannot be undone."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("DELETE", f"/playground/workflows/{workflow_id}/sessions/{session_id}")
    
    @mcp.tool()
    async def rename_workflow_execution(
        workflow_id: str,
        session_id: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Give a custom name to your workflow execution session for easier identification."""
        data = {"name": new_name}
        async with AutomagikHiveClient(config) as client:
            return await client.request("POST", f"/playground/workflows/{workflow_id}/sessions/{session_id}/rename", json=data)
    
    # 👥 Team Operations
    @mcp.tool()
    async def list_available_teams() -> Dict[str, Any]:
        """List all available agent teams in the playground that you can collaborate with."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", "/playground/teams")
    
    @mcp.tool()
    async def get_team_details(team_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific team including its members and capabilities."""
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/teams/{team_id}")
    
    @mcp.tool()
    async def start_team_collaboration(
        team_id: str,
        task_description: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a collaborative session with a team of agents. Describe your task and the team will work together."""
        # API expects multipart form data with message field and defaults
        data = {
            "message": task_description,
            "stream": "false",  # Convert to string for multipart
            "monitor": "false"  # Convert to string for multipart
        }
        if user_id:
            data["user_id"] = user_id
        
        async with AutomagikHiveClient(config) as client:
            return await client.request_multipart("POST", f"/playground/teams/{team_id}/runs", data)
    
    @mcp.tool()
    async def view_team_collaboration_history(
        team_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """View all your collaboration sessions with a specific team."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/teams/{team_id}/sessions", params=params)
    
    @mcp.tool()
    async def get_team_collaboration_details(
        team_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed results and communication logs from a specific team collaboration session."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/teams/{team_id}/sessions/{session_id}", params=params)
    
    @mcp.tool()
    async def delete_team_collaboration(
        team_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a team collaboration session. This cannot be undone."""
        params = {"user_id": user_id} if user_id else {}
        async with AutomagikHiveClient(config) as client:
            return await client.request("DELETE", f"/playground/teams/{team_id}/sessions/{session_id}", params=params)
    
    @mcp.tool()
    async def rename_team_collaboration(
        team_id: str,
        session_id: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Give a custom name to your team collaboration session for easier identification."""
        data = {"name": new_name}
        async with AutomagikHiveClient(config) as client:
            return await client.request("POST", f"/playground/teams/{team_id}/sessions/{session_id}/rename", json=data)
    
    @mcp.tool()
    async def view_team_memories(
        team_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """View what a team remembers about your collaborations and shared experiences."""
        params = {"user_id": user_id}
        async with AutomagikHiveClient(config) as client:
            return await client.request("GET", f"/playground/team/{team_id}/memories", params=params)
    
    # 🚀 Quick Actions - NOTE: This endpoint doesn't exist in the API, removing it
    # The /runs endpoint is not available according to the OpenAPI spec
    
    return mcp


def get_metadata() -> Dict[str, Any]:
    """Get metadata about the Automagik Hive tool."""
    return {
        "name": "automagik_hive",
        "description": "Comprehensive tool for testing all Automagik Hive API capabilities",
        "version": "1.0.0",
        "author": "Automagik Tools",
        "tags": ["agents", "ai", "monitoring", "playground", "api", "hive"],
        "capabilities": [
            "Agent management and conversations",
            "Workflow execution",
            "Team collaboration",
            "Memory and history management",
            "Playground monitoring"
        ]
    }


def get_config_class():
    """Get the configuration class for the Automagik Hive tool."""
    return AutomagikHiveConfig