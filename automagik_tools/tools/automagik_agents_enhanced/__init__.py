"""
Enhanced Automagik Agents MCP Tool with AI-powered JSON-to-Markdown processing

This tool wraps the standard automagik functionality with intelligent
response processing that converts noisy JSON outputs into clean, structured
Markdown for better human readability.
"""

import os
from typing import Dict, Any, Optional, List
from contextlib import suppress
import httpx
from pydantic import BaseModel, Field

from fastmcp import FastMCP, Context
from .config import AutomagikAgentsEnhancedConfig
from ...ai_processors.json_markdown_processor import get_processor
from ...ai_processors.enhanced_response import EnhancedResponse, enhance_existing_response

# Global config instance
config: Optional[AutomagikAgentsEnhancedConfig] = None

# Create FastMCP instance
mcp = FastMCP(
    "Automagik Agents Enhanced",
    instructions="""
Enhanced Automagik Agents API with AI-powered response processing.

This tool provides access to all 47 automagik endpoints with intelligent
JSON-to-Markdown conversion for better human readability.

Features:
- Clean, structured Markdown outputs
- AI-powered response interpretation
- Context-aware formatting
- Error explanations and solutions
- Progress tracking for async operations

Base URL: Dynamic based on configuration
Authentication: API key based
AI Processing: GPT-4o-mini for response enhancement
"""
)


# Enhanced API request function
async def make_enhanced_api_request(
    method: str,
    endpoint: str,
    tool_name: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
    extra_headers: Optional[Dict[str, str]] = None
) -> EnhancedResponse:
    """Make HTTP request to the API and enhance the response with AI processing"""
    global config
    if not config:
        error_data = {"error": "Tool not configured", "tool": tool_name}
        return EnhancedResponse(error_data, tool_name=tool_name)
    
    url = f"{config.base_url}{endpoint}"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    # Add API key authentication if configured
    if config.api_key:
        headers["x-api-key"] = config.api_key
    
    # Add any extra headers (e.g., override X-API-Key)
    if extra_headers:
        headers.update(extra_headers)
    
    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            
            # Handle different response types
            if response.status_code >= 400:
                # Error response
                try:
                    response_data = response.json()
                except:
                    response_data = {"error": f"HTTP {response.status_code}: {response.text}", "status_code": response.status_code}
            else:
                # Success response
                if "application/json" in response.headers.get("content-type", ""):
                    response_data = response.json()
                else:
                    response_data = {"result": response.text, "content_type": response.headers.get("content-type")}
            
            # Enhance with AI processing
            if config.enable_ai_processing:
                return await enhance_existing_response(response_data, tool_name)
            else:
                return EnhancedResponse(response_data, tool_name=tool_name)
                
    except httpx.HTTPStatusError as e:
        error_data = {"error": f"HTTP {e.response.status_code}: {str(e)}", "url": url}
        if ctx:
            ctx.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        
        if config.enable_ai_processing:
            return await enhance_existing_response(error_data, tool_name)
        else:
            return EnhancedResponse(error_data, tool_name=tool_name)
    except Exception as e:
        error_data = {"error": str(e), "url": url}
        if ctx:
            ctx.error(f"Request failed: {str(e)}")
        
        if config.enable_ai_processing:
            return await enhance_existing_response(error_data, tool_name)
        else:
            return EnhancedResponse(error_data, tool_name=tool_name)


# Enhanced tool functions with AI processing
@mcp.tool()
async def list_agents_enhanced(ctx: Optional[Context] = None) -> str:
    """
    Get a list of all available AI agents with enhanced, human-readable formatting.
    
    This returns a clean, structured overview of available agents, their capabilities,
    and recommended use cases - much more readable than raw JSON.
    
    Returns:
        Markdown-formatted table of agents with descriptions and use cases
    """
    if ctx:
        ctx.info("Getting enhanced list of available agents")
    
    response = await make_enhanced_api_request(
        method="GET",
        endpoint="/api/v1/agent/list",
        tool_name="list_agents",
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def run_agent_enhanced(agent_name: str, message_content: str, ctx: Optional[Context] = None) -> str:
    """
    Execute an AI agent with enhanced response formatting.
    
    This provides a clean, conversational view of the agent's response,
    highlighting the key message and any additional context.
    
    Args:
        agent_name: Name of the agent (e.g., 'simple', 'claude_code', 'genie')
        message_content: Your message/prompt to send to the agent
        
    Returns:
        Clean, formatted response from the agent with context
    """
    if ctx:
        ctx.info(f"Running agent '{agent_name}' with enhanced formatting")
    
    response = await make_enhanced_api_request(
        method="POST",
        endpoint=f"/api/v1/agent/{agent_name}/run",
        tool_name="run_agent",
        json_data={"message_content": message_content},
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def run_agent_async_enhanced(agent_name: str, message_content: str, ctx: Optional[Context] = None) -> str:
    """
    Start an AI agent asynchronously with enhanced progress tracking.
    
    This provides clear information about the started task and how to monitor
    its progress, including the run ID and next steps.
    
    Args:
        agent_name: Name of the agent to execute
        message_content: Your message/prompt to send to the agent
        
    Returns:
        Enhanced response with run ID and monitoring instructions
    """
    if ctx:
        ctx.info(f"Starting async agent '{agent_name}' with enhanced tracking")
    
    response = await make_enhanced_api_request(
        method="POST",
        endpoint=f"/api/v1/agent/{agent_name}/run/async",
        tool_name="run_agent_async",
        json_data={"message_content": message_content},
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def get_run_status_enhanced(run_id: str, ctx: Optional[Context] = None) -> str:
    """
    Check the status of an asynchronous agent run with enhanced progress display.
    
    This provides a clear, visual representation of the current status,
    progress information, and results if completed.
    
    Args:
        run_id: The run ID returned by run_agent_async_enhanced
        
    Returns:
        Enhanced status display with progress indicators and results
    """
    if ctx:
        ctx.info(f"Checking enhanced status for run {run_id}")
    
    response = await make_enhanced_api_request(
        method="GET",
        endpoint=f"/api/v1/run/{run_id}/status",
        tool_name="get_run_status",
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def create_prompt_enhanced(agent_id: int, prompt_text: str, name: str, ctx: Optional[Context] = None) -> str:
    """
    Create a new system prompt with enhanced confirmation and management info.
    
    This provides clear confirmation of the prompt creation with guidance
    on how to activate and manage the new prompt.
    
    Args:
        agent_id: ID of the agent (get from list_agents_enhanced)
        prompt_text: The system prompt content
        name: Descriptive name for the prompt
        
    Returns:
        Enhanced confirmation with prompt management instructions
    """
    if ctx:
        ctx.info(f"Creating enhanced prompt '{name}' for agent {agent_id}")
    
    response = await make_enhanced_api_request(
        method="POST",
        endpoint=f"/api/v1/agent/{agent_id}/prompt",
        tool_name="create_prompt",
        json_data={"prompt_text": prompt_text, "name": name},
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def create_memories_batch_enhanced(memories: List[Dict[str, Any]], ctx: Optional[Context] = None) -> str:
    """
    Create multiple memory records with enhanced batch summary.
    
    This provides a clear overview of the created memories with
    organization by type and easy reference information.
    
    Args:
        memories: List of memory objects to create
        
    Returns:
        Enhanced summary of created memories with organization
    """
    if ctx:
        ctx.info(f"Creating enhanced batch of {len(memories)} memories")
    
    response = await make_enhanced_api_request(
        method="POST",
        endpoint="/api/v1/memories/batch",
        tool_name="create_memories_batch",
        json_data=memories,
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def run_claude_code_workflow_enhanced(workflow_name: str, data: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None) -> str:
    """
    Execute a Claude-Code workflow with enhanced progress tracking.
    
    This provides clear information about the started workflow and
    how to monitor its progress through completion.
    
    Available workflows: fix, refactor, review, test, architect, pr, document, implement
    
    Args:
        workflow_name: Type of workflow to execute
        data: Workflow-specific data (usually contains 'message' field)
        
    Returns:
        Enhanced workflow status with monitoring instructions
    """
    if ctx:
        ctx.info(f"Starting enhanced Claude-Code workflow '{workflow_name}'")
    
    response = await make_enhanced_api_request(
        method="POST",
        endpoint=f"/api/v1/agent/claude-code/{workflow_name}/run",
        tool_name="run_claude_code_workflow",
        json_data=data,
        ctx=ctx
    )
    
    return response.markdown


@mcp.tool()
async def get_claude_code_run_status_enhanced(run_id: str, ctx: Optional[Context] = None) -> str:
    """
    Check Claude-Code workflow status with enhanced progress visualization.
    
    This provides a detailed view of the workflow progress, including
    any generated artifacts, git commits, and completion status.
    
    Args:
        run_id: The run ID returned by run_claude_code_workflow_enhanced
        
    Returns:
        Enhanced workflow status with detailed progress information
    """
    if ctx:
        ctx.info(f"Checking enhanced Claude-Code status for run {run_id}")
    
    response = await make_enhanced_api_request(
        method="GET",
        endpoint=f"/api/v1/agent/claude-code/run/{run_id}/status",
        tool_name="get_claude_code_run_status",
        ctx=ctx
    )
    
    return response.markdown


# Raw access functions (for when you need the original JSON)
@mcp.tool()
async def get_raw_response(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Get raw JSON response from any automagik endpoint.
    
    Use this when you need the original JSON data without AI processing.
    
    Args:
        endpoint: API endpoint path (e.g., '/api/v1/agent/list')
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data for POST/PUT requests
        
    Returns:
        Raw JSON response from the API
    """
    if ctx:
        ctx.info(f"Getting raw response from {method} {endpoint}")
    
    # Temporarily disable AI processing
    old_setting = config.enable_ai_processing if config else True
    if config:
        config.enable_ai_processing = False
    
    try:
        response = await make_enhanced_api_request(
            method=method,
            endpoint=endpoint,
            tool_name="raw_request",
            json_data=data,
            ctx=ctx
        )
        return response.raw_data
    finally:
        # Restore AI processing setting
        if config:
            config.enable_ai_processing = old_setting


# Configuration and metadata functions
def create_tool(tool_config: Optional[AutomagikAgentsEnhancedConfig] = None) -> FastMCP:
    """Create the enhanced MCP tool instance"""
    global config
    config = tool_config or AutomagikAgentsEnhancedConfig()
    return mcp


def create_server(tool_config: Optional[AutomagikAgentsEnhancedConfig] = None):
    """Create FastMCP server instance"""
    tool = create_tool(tool_config)
    return tool


def get_tool_name() -> str:
    """Get the tool name"""
    return "automagik-enhanced"


def get_config_class():
    """Get the config class for this tool"""
    return AutomagikAgentsEnhancedConfig


def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {
        "name": "automagik-enhanced",
        "version": "1.0.0",
        "description": "Enhanced Automagik Agents API with AI-powered response processing",
        "author": "Automagik Team",
        "category": "ai-enhanced",
        "tags": ["api", "ai", "markdown", "enhanced", "openapi"],
        "features": [
            "AI-powered JSON-to-Markdown conversion",
            "Clean, structured response formatting",
            "Context-aware error explanations",
            "Progress tracking for async operations",
            "Human-readable agent interactions"
        ],
        "config_env_prefix": "AUTOMAGIK_AGENTS_"
    }


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the enhanced tool as a standalone service"""
    import uvicorn
    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)