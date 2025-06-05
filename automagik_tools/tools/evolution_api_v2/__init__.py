"""
WhatsApp integration via Evolution API v2

This tool provides MCP integration for Evolution API v2 API using FastMCP's native OpenAPI support.
"""

import httpx
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType

from .config import EvolutionApiV2Config

# Global config instance
config: Optional[EvolutionApiV2Config] = None

# Global MCP instance
mcp: Optional[FastMCP] = None


def create_mcp_from_openapi(tool_config: EvolutionApiV2Config) -> FastMCP:
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
        openapi_url = tool_config.openapi_url or "https://raw.githubusercontent.com/EvolutionAPI/docs-evolution/refs/heads/main/openapi/openapi-v2.json"
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
    except Exception as e:
        # Fallback to a minimal spec if we can't fetch
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Evolution API v2",
                "description": "WhatsApp integration via Evolution API v2",
                "version": "1.0.0"
            },
            "servers": [{"url": tool_config.base_url}],
            "paths": {}
        }
    
    # Create MCP server from OpenAPI spec
    mcp_server = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="Evolution API v2",
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
def create_tool(tool_config: Optional[EvolutionApiV2Config] = None) -> FastMCP:
    """Create the MCP tool instance"""
    global config, mcp
    config = tool_config or EvolutionApiV2Config()
    
    if mcp is None:
        mcp = create_mcp_from_openapi(config)
    
    return mcp


def create_server(tool_config: Optional[EvolutionApiV2Config] = None):
    """Create FastMCP server instance"""
    tool = create_tool(tool_config)
    return tool


def get_tool_name() -> str:
    """Get the tool name"""
    return "evolution-api-v2"


def get_config_class():
    """Get the config class for this tool"""
    return EvolutionApiV2Config


def get_config_schema() -> Dict[str, Any]:
    """Get the JSON schema for the config"""
    return EvolutionApiV2Config.model_json_schema()


def get_required_env_vars() -> Dict[str, str]:
    """Get required environment variables"""
    return {
        "EVOLUTION_API_V2_API_KEY": "API key for authentication",
        "EVOLUTION_API_V2_BASE_URL": "Base URL for the API",
        "EVOLUTION_API_V2_OPENAPI_URL": "URL to fetch OpenAPI spec (optional)",
    }


def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {
        "name": "evolution-api-v2",
        "version": "1.0.0",
        "description": "WhatsApp integration via Evolution API v2",
        "author": "Automagik Team",
        "category": "api",
        "tags": ["api", "integration", "openapi"],
        "config_env_prefix": "EVOLUTION_API_V2_"
    }


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the tool as a standalone service"""
    import uvicorn
    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)
