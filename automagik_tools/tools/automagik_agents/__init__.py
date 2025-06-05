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


def get_custom_mcp_names() -> Dict[str, str]:
    """
    Create custom MCP names for long operationIds to respect the 56-character limit.
    Maps operationId -> friendly_name with natural, user-friendly names.
    """
    return {
        # Claude Code agent operations
        "run_claude_code_workflow_api_v1_agent_claude_code__workflow_name__run_post": "run_workflow",
        "get_claude_code_run_status_api_v1_agent_claude_code_run__run_id__status_get": "get_run_status",
        "list_claude_code_workflows_api_v1_agent_claude_code_workflows_get": "list_workflows",
        
        # Genie agent operations
        "approve_epic_step_api_v1_agent_genie_approve__epic_id___approval_id__post": "approve_step",
        
        # Agent prompt management
        "get_prompt_api_v1_agent__agent_id__prompt__prompt_id__get": "get_prompt",
        "update_prompt_api_v1_agent__agent_id__prompt__prompt_id__put": "update_prompt",
        "delete_prompt_api_v1_agent__agent_id__prompt__prompt_id__delete": "delete_prompt",
        "activate_prompt_api_v1_agent__agent_id__prompt__prompt_id__activate_post": "activate_prompt",
        "deactivate_prompt_api_v1_agent__agent_id__prompt__prompt_id__deactivate_post": "deactivate_prompt",
        
        # Session management
        "get_session_route_api_v1_sessions__session_id_or_name__get": "get_session",
        "delete_session_route_api_v1_sessions__session_id_or_name__delete": "delete_session",
        
        # Memory management
        "delete_memory_endpoint_api_v1_memories__memory_id__delete": "delete_memory",
        
        # MCP Server management (more specific names to avoid conflicts)
        "delete_mcp_server_api_v1_mcp_servers__server_name__delete": "delete_server",
        "start_mcp_server_api_v1_mcp_servers__server_name__start_post": "start_server",
        "stop_mcp_server_api_v1_mcp_servers__server_name__stop_post": "stop_server",
        "restart_mcp_server_api_v1_mcp_servers__server_name__restart_post": "restart_server",
        "list_mcp_server_tools_api_v1_mcp_servers__server_name__tools_get": "list_server_tools",
        "list_mcp_server_resources_api_v1_mcp_servers__server_name__resources_get": "list_server_resources",
        
        # Agent tools
        "list_agent_mcp_tools_api_v1_mcp_agents__agent_name__tools_get": "list_agent_tools",
    }


def create_custom_route_maps(config: AutomagikAgentsConfig):
    """
    Create custom route maps for better organization and naming.
    """
    route_maps = [
        # Admin/Management endpoints as tools
        RouteMap(
            methods=["POST", "PUT", "DELETE"], 
            pattern=r"^/api/v1/mcp/.*", 
            mcp_type=MCPType.TOOL
        ),
        
        # Agent management endpoints as tools
        RouteMap(
            methods=["POST", "PUT", "DELETE"], 
            pattern=r"^/api/v1/agent/.*/prompt/.*", 
            mcp_type=MCPType.TOOL
        ),
        
        # Make workflow runs tools (even though they're GET with params)
        RouteMap(
            methods=["GET"], 
            pattern=r"^/api/v1/agent/.*/run/.*", 
            mcp_type=MCPType.TOOL
        ),
    ]
    
    # Conditionally exclude health endpoints
    if config.exclude_health_endpoints:
        route_maps.append(
            RouteMap(
                pattern=r".*/health$", 
                mcp_type=MCPType.EXCLUDE
            )
        )
    
    return route_maps


def clean_operation_name(operation_id: str) -> str:
    """
    Clean an operationId to make it more natural and user-friendly.
    
    Args:
        operation_id: The original operationId from OpenAPI spec
        
    Returns:
        Cleaned, more natural name
    """
    name = operation_id
    
    # Remove common API prefixes and suffixes
    prefixes_to_remove = [
        "api_v1_", "api_v2_", "api_", 
        "endpoint_", "route_", "_endpoint", "_route"
    ]
    
    suffixes_to_remove = [
        "_get", "_post", "_put", "_delete", "_patch", "_head", "_options"
    ]
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Remove suffixes
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # Extract meaningful part before first double underscore (path parameters)
    name = name.split("__")[0]
    
    # Clean up common patterns
    replacements = {
        "_api_v1_": "_",
        "_api_": "_",
        "mcp_servers": "server",
        "mcp_agents": "agent", 
        "claude_code": "workflow",
        "session_route": "session",
        "memory_endpoint": "memory",
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove duplicate underscores
    while "__" in name:
        name = name.replace("__", "_")
    
    # Remove leading/trailing underscores
    name = name.strip("_")
    
    return name


def validate_component_names(openapi_spec: Dict[str, Any], mcp_names: Dict[str, str], config: AutomagikAgentsConfig) -> Dict[str, str]:
    """
    Validate and ensure all component names are within limits.
    Returns the validated mcp_names dict.
    """
    validated_names = {}
    max_length = config.max_component_name_length
    
    for path, path_item in openapi_spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                operation_id = operation.get("operationId")
                if operation_id:
                    # Use custom name if provided, otherwise clean the operationId
                    if operation_id in mcp_names:
                        name = mcp_names[operation_id]
                    else:
                        name = clean_operation_name(operation_id)
                    
                    # Ensure name is within configured character limit
                    if config.auto_truncate_names and len(name) > max_length:
                        name = name[:max_length]
                    elif len(name) > max_length:
                        # Log warning but don't truncate if auto_truncate is disabled
                        print(f"Warning: Component name '{name}' ({len(name)} chars) exceeds limit ({max_length} chars)")
                    
                    validated_names[operation_id] = name
    
    return validated_names


def create_mcp_from_openapi(tool_config: AutomagikAgentsConfig) -> FastMCP:
    """Create MCP server from OpenAPI specification"""

    # Create HTTP client with authentication
    headers = {}
    if tool_config.api_key:
        headers["X-API-Key"] = tool_config.api_key
        # Also support Authorization header
        headers["Authorization"] = f"Bearer {tool_config.api_key}"

    client = httpx.AsyncClient(
        base_url=tool_config.base_url, headers=headers, timeout=tool_config.timeout
    )

    # Fetch OpenAPI spec
    try:
        # Try the configured OpenAPI URL first
        openapi_url = (
            tool_config.openapi_url or "http://192.168.112.148:8881/api/v1/openapi.json"
        )
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
    except Exception:
        # Fallback to a minimal spec if we can't fetch
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Automagik Agents",
                "description": "Automagik agents templates and API",
                "version": "1.0.0",
            },
            "servers": [{"url": tool_config.base_url}],
            "paths": {},
        }

    # Get custom names and validate them
    custom_names = get_custom_mcp_names()
    validated_names = validate_component_names(openapi_spec, custom_names, tool_config)

    # Create MCP server from OpenAPI spec
    mcp_server = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="automagik_agents",  # Shorter server name
        timeout=tool_config.timeout,
        mcp_names=validated_names,  # Custom component names
        route_maps=create_custom_route_maps(tool_config),  # Custom route mapping
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
        "config_env_prefix": "AUTOMAGIK_AGENTS_",
    }


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the tool as a standalone service"""
    import uvicorn

    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)
