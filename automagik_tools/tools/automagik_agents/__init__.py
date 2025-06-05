"""
Automagik agents templates and API

This tool provides MCP integration for Automagik Agents API using FastMCP's native OpenAPI support.
"""

import httpx
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType

from .config import AutomagikAgentsConfig

# Global config instance
config: Optional[AutomagikAgentsConfig] = None

# Global MCP instance
mcp: Optional[FastMCP] = None


def create_mcp_from_openapi(tool_config: AutomagikAgentsConfig) -> FastMCP:
    """Create MCP server from OpenAPI specification"""
    
    # Create HTTP client with authentication
    headers = {}
    if tool_config.api_key:
        headers["X-API-Key"] = tool_config.api_key
        # Also support Authorization header
        headers["Authorization"] = f"Bearer {tool_config.api_key}"
    
    client = httpx.AsyncClient(
        base_url=tool_config.base_url,
        headers=headers,
        timeout=tool_config.timeout
    )
    
    # Fetch OpenAPI spec
    try:
        # Try the configured OpenAPI URL first
        openapi_url = tool_config.openapi_url or "http://192.168.112.148:8881/api/v1/openapi.json"
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
    except Exception as e:
        # Fallback to a minimal spec if we can't fetch
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Automagik Agents",
                "description": "Automagik agents templates and API",
                "version": "1.0.0"
            },
            "servers": [{"url": tool_config.base_url}],
            "paths": {}
        }
    
    # Create MCP server from OpenAPI spec
    mcp_server = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="Automagik Agents",
        timeout=tool_config.timeout,
        route_maps=[
            # You can customize route mapping here
            # Example: Make all analytics endpoints tools
            # RouteMap(methods=["GET"], pattern=r"^/analytics/.*", mcp_type=MCPType.TOOL),
            
            # Example: Exclude admin endpoints
            # RouteMap(pattern=r"^/admin/.*", mcp_type=MCPType.EXCLUDE),
        ]
    )
    
    return mcp_server


# Tool creation functions (required by automagik-tools)
def create_tool(tool_config: Optional[AutomagikAgentsConfig] = None) -> FastMCP:
    """Create the MCP tool instance"""
    global config, mcp
    config = tool_config or AutomagikAgentsConfig()
    
    if mcp is None:
        mcp = create_mcp_from_openapi(config)
    
    return mcp


def create_server(tool_config: Optional[AutomagikAgentsConfig] = None):
    """Create FastMCP server instance"""
    tool = create_tool(tool_config)
    return tool


def get_tool_name() -> str:
    """Get the tool name"""
    return "automagik-agents"


def get_config_class():
    """Get the config class for this tool"""
    return AutomagikAgentsConfig


def get_config_schema() -> Dict[str, Any]:
    """Get the JSON schema for the config"""
    return AutomagikAgentsConfig.model_json_schema()


def get_required_env_vars() -> Dict[str, str]:
    """Get required environment variables"""
    return {
        "AUTOMAGIK_AGENTS_API_KEY": "API key for authentication",
        "AUTOMAGIK_AGENTS_BASE_URL": "Base URL for the API",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "URL to fetch OpenAPI spec (optional)",
    }


def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {
        "name": "automagik-agents",
        "version": "1.0.0",
        "description": "Automagik agents templates and API",
        "author": "Automagik Team",
        "category": "api",
        "tags": ["api", "integration", "openapi"],
        "config_env_prefix": "AUTOMAGIK_AGENTS_"
    }


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the tool as a standalone service"""
    import uvicorn
    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)
