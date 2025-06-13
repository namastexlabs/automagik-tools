"""
Automagik - AI-powered agents and workflows

This tool provides MCP integration for Automagik Agents API with enhanced AI processing.
All responses are processed by GPT-4.1-mini for optimal human readability.
"""

from typing import Dict, Any, Optional, List
import httpx

from fastmcp import FastMCP, Context
from .config import AutomagikConfig
from ...ai_processors.enhanced_response import enhance_existing_response

# Global config instance
config: Optional[AutomagikConfig] = None

# Create FastMCP instance
mcp = FastMCP(
    "Automagik",
    instructions="""
Automagik - AI-powered agents and workflows

🤖 Execute AI agents for various tasks (coding, analysis, conversations)
📝 Manage prompts and memories for agent customization  
🔧 Control MCP servers and Claude-Code workflows
💬 Track sessions and manage users

All responses are enhanced with AI processing for better readability.
""",
)


# Pydantic models for request/response validation


async def make_api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    tool_name: str = "api_request",
) -> str:
    """Make HTTP request to the API and return AI-enhanced response"""
    import time

    global config
    if not config:
        raise ValueError("Tool not configured")

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

    # Start timing for API call
    api_start_time = time.time()
    raw_response = None

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.request(
                method=method, url=url, headers=headers, params=params, json=json_data
            )
            response.raise_for_status()

            # Get raw JSON response
            if "application/json" in response.headers.get("content-type", ""):
                raw_response = response.json()
            else:
                raw_response = {"result": response.text}

    except httpx.HTTPStatusError as e:
        if ctx:
            ctx.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raw_response = {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except Exception as e:
        if ctx:
            ctx.error(f"Request failed: {str(e)}")
        raw_response = {"error": str(e)}

    # Calculate API timing
    api_time = time.time() - api_start_time
    api_time_ms = int(api_time * 1000)

    # Check if markdown enhancement is enabled
    if not config.enable_markdown:
        # Return raw JSON response without AI enhancement
        import json

        return f"```json\n{json.dumps(raw_response, indent=2)}\n```\n\n---\n*API response time: {api_time_ms}ms*"

    # Enhance response with AI processing
    try:
        ai_start_time = time.time()
        enhanced = await enhance_existing_response(raw_response, tool_name)
        ai_time = time.time() - ai_start_time
        ai_time_ms = int(ai_time * 1000)

        # Update the markdown to include both API and AI timing
        # Replace the AI timing footer with comprehensive timing
        if (
            enhanced.processing_result
            and enhanced.processing_result.processing_time is not None
        ):
            timing_pattern = f"*Generated in {int(enhanced.processing_result.processing_time * 1000)}ms*"
            new_timing = f"*API: {api_time_ms}ms • AI: {ai_time_ms}ms • Total: {api_time_ms + ai_time_ms}ms*"

            if timing_pattern in enhanced.markdown:
                enhanced_markdown = enhanced.markdown.replace(
                    timing_pattern, new_timing
                )
            else:
                # If pattern not found, append timing at the end
                enhanced_markdown = enhanced.markdown + f"\n\n---\n{new_timing}"
        else:
            # If no processing result or processing time, just append new timing
            new_timing = f"*API: {api_time_ms}ms • AI: {ai_time_ms}ms • Total: {api_time_ms + ai_time_ms}ms*"
            enhanced_markdown = enhanced.markdown + f"\n\n---\n{new_timing}"

        return enhanced_markdown
    except Exception as e:
        # Fallback to raw JSON if enhancement fails
        import json

        return f"```json\n{json.dumps(raw_response, indent=2)}\n```\n\n*Note: AI enhancement failed: {str(e)}*\n\n---\n*API: {api_time_ms}ms*"


# System Operations


@mcp.tool()
async def get_service_info(ctx: Optional[Context] = None) -> str:
    """
    Retrieve service information and status for Automagik Agents

    Endpoint: GET /
    """
    if ctx:
        ctx.info("Calling GET /")

    endpoint = "/"
    params = None
    json_data = None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="get_service_info",
    )


@mcp.tool()
async def get_health_status(ctx: Optional[Context] = None) -> str:
    """
    Check health and operational status of Automagik service

    Endpoint: GET /health
    """
    if ctx:
        ctx.info("Calling GET /health")

    endpoint = "/health"
    params = None
    json_data = None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="get_health_status",
    )


# Agents Operations


@mcp.tool()
async def list_agents(ctx: Optional[Context] = None) -> str:
    """
    Get a list of all available AI agents and their capabilities.

    Use this first to discover what agents are available before running them.
    Each agent has different specializations and purposes.

    Endpoint: GET /api/v1/agent/list

    Returns:
        List of agents with 'id', 'name', 'description' for each agent

    Common agents you'll find:
        - 'simple': General purpose conversational agent
        - 'claude_code': Advanced code analysis and development
        - 'genie': Orchestrator for complex multi-step workflows
        - 'discord': Discord bot interactions
        - 'stan': Customer management specialist
    """
    if ctx:
        ctx.info("Calling GET /api/v1/agent/list")

    endpoint = "/api/v1/agent/list"
    params = None
    json_data = None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="list_agents",
    )


@mcp.tool()
async def run_agent(
    agent_name: str,
    message_content: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    memory_enabled: Optional[bool] = None,
    tools_enabled: Optional[bool] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Execute an AI agent synchronously with a message and get immediate response.

    This runs an agent and waits for completion. Use this when you need an immediate response.
    For long-running tasks, use run_agent_async instead.

    Common agent names: simple, claude_code, genie, discord, stan

    Endpoint: POST /api/v1/agent/{agent_name}/run

    Args:
        agent_name: Name of the agent to execute (e.g., 'simple', 'claude_code', 'genie')
        message_content: The message/prompt to send to the agent (be specific and clear)
        context: Optional additional context for the agent
        session_id: Optional session ID to continue conversation
        memory_enabled: Optional flag to enable/disable agent memory
        tools_enabled: Optional flag to enable/disable agent tools

    Returns:
        Dict with 'message' (agent response), 'session_id', 'success', 'tool_calls', 'tool_outputs'

    Example:
        run_agent('simple', 'Hello, how can you help me with Python coding?')
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/agent/{agent_name}/run")

    endpoint = f"/api/v1/agent/{agent_name}/run"
    params = None
    json_data = {"message_content": message_content}

    # Add optional orchestration parameters
    if context:
        json_data["context"] = context
    if session_id:
        json_data["session_id"] = session_id
    if memory_enabled is not None:
        json_data["memory_enabled"] = memory_enabled
    if tools_enabled is not None:
        json_data["tools_enabled"] = tools_enabled

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="run_agent",
    )


@mcp.tool()
async def run_agent_async(
    agent_name: str, message_content: str, ctx: Optional[Context] = None
) -> str:
    """
    Start an AI agent asynchronously for long-running tasks and get a run_id to check status later.

    Use this for complex tasks that might take time. You can check progress with get_run_status().

    Endpoint: POST /api/v1/agent/{agent_name}/run/async

    Args:
        agent_name: Name of the agent to execute (e.g., 'claude_code', 'genie')
        message_content: The message/prompt to send to the agent

    Returns:
        Dict with 'run_id' (use with get_run_status), 'status', 'message', 'agent_name'

    Example:
        result = run_agent_async('claude_code', 'Review my Python code for bugs')
        run_id = result['run_id']
        # Later: get_run_status(run_id)
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/agent/{agent_name}/run/async")

    endpoint = f"/api/v1/agent/{agent_name}/run/async"
    params = None
    json_data = {"message_content": message_content}

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="run_agent_async",
    )


@mcp.tool()
async def get_run_status(run_id: str, ctx: Optional[Context] = None) -> str:
    """
    Check the status and results of an asynchronous agent run.

    Use this to monitor progress of agents started with run_agent_async().

    Endpoint: GET /api/v1/run/{run_id}/status

    Args:
        run_id: The run ID returned by run_agent_async()

    Returns:
        Enhanced status information with 'status' (pending/running/completed), 'result', 'error', 'progress'

    Status values:
        - 'pending': Not started yet
        - 'running': Currently executing
        - 'completed': Finished (check 'result' field)
        - 'failed': Error occurred (check 'error' field)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/run/{run_id}/status")

    endpoint = f"/api/v1/run/{run_id}/status"
    params = None
    json_data = None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        tool_name="get_run_status",
    )


# Prompts Operations


@mcp.tool()
async def list_prompts(
    agent_id: int, status_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List prompts for a specified agent, filtered by status key

    Endpoint: GET /api/v1/agent/{agent_id}/prompt

    Args:
        agent_id: ID of the agent to list prompts for (integer, required)
        status_key: Optional status key filter (string, e.g., 'active', default: None)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/agent/{agent_id}/prompt")

    endpoint = f"/api/v1/agent/{agent_id}/prompt"

    params = {}
    if status_key is not None:
        params["status_key"] = status_key

    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def create_prompt(
    agent_id: int, prompt_text: str, name: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Create a new system prompt for an AI agent to customize its behavior.

    System prompts define how an agent behaves, its personality, and capabilities.
    Use this to create specialized agent behaviors.

    Endpoint: POST /api/v1/agent/{agent_id}/prompt

    Args:
        agent_id: ID of the agent (get from list_agents())
        prompt_text: The system prompt content - be detailed about desired behavior
        name: Descriptive name for this prompt (e.g., 'code-reviewer', 'creative-writer')

    Returns:
        Dict with 'id' (use for activate_prompt), 'agent_id', 'prompt_text', 'name'

    Example:
        create_prompt(8, 'You are a helpful Python code reviewer. Focus on bugs and best practices.', 'python-reviewer')
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/agent/{agent_id}/prompt")

    endpoint = f"/api/v1/agent/{agent_id}/prompt"
    params = None
    json_data = {"prompt_text": prompt_text, "name": name}

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def get_prompt(
    agent_id: int, prompt_id: int, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Retrieve details for a specific prompt by prompt and agent ID

    Endpoint: GET /api/v1/agent/{agent_id}/prompt/{prompt_id}

    Args:
        agent_id: ID of the agent (integer, required)
        prompt_id: ID of the prompt to retrieve (integer, required)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/agent/{agent_id}/prompt/{prompt_id}")

    endpoint = f"/api/v1/agent/{agent_id}/prompt/{prompt_id}"
    params = None
    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def update_prompt(
    agent_id: int,
    prompt_id: int,
    prompt_text: Optional[str] = None,
    name: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Update the content or status of an existing prompt

    Endpoint: PUT /api/v1/agent/{agent_id}/prompt/{prompt_id}

    Args:
        agent_id: Agent's unique ID (integer, required)
        prompt_id: Prompt's unique ID to update (integer, required)
        prompt_text: Updated prompt text (string, optional)
        name: Updated name (string, optional)
    """
    if ctx:
        ctx.info(f"Calling PUT /api/v1/agent/{agent_id}/prompt/{prompt_id}")

    endpoint = f"/api/v1/agent/{agent_id}/prompt/{prompt_id}"
    params = None
    json_data = {}

    if prompt_text is not None:
        json_data["prompt_text"] = prompt_text
    if name is not None:
        json_data["name"] = name

    return await make_api_request(
        method="PUT", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def delete_prompt(
    agent_id: int, prompt_id: int, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete a prompt from an agent by prompt ID

    Endpoint: DELETE /api/v1/agent/{agent_id}/prompt/{prompt_id}

    Args:
        agent_id: ID of the agent (integer, required)
        prompt_id: ID of the prompt to delete (integer, required)
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/agent/{agent_id}/prompt/{prompt_id}")

    endpoint = f"/api/v1/agent/{agent_id}/prompt/{prompt_id}"
    params = None
    json_data = None

    return await make_api_request(
        method="DELETE", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def activate_prompt(
    agent_id: int, prompt_id: int, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Activate a prompt for an agent and deactivate other prompts

    Endpoint: POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/activate

    Args:
        agent_id: ID of the agent (integer, required)
        prompt_id: ID of the prompt to activate (integer, required)
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/activate")

    endpoint = f"/api/v1/agent/{agent_id}/prompt/{prompt_id}/activate"
    params = None
    json_data = None

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def deactivate_prompt(
    agent_id: int, prompt_id: int, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Deactivate a prompt for an agent, making it inactive

    Endpoint: POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/deactivate

    Args:
        agent_id: ID of the agent (integer, required)
        prompt_id: ID of the prompt to deactivate (integer, required)
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/agent/{agent_id}/prompt/{prompt_id}/deactivate")

    endpoint = f"/api/v1/agent/{agent_id}/prompt/{prompt_id}/deactivate"
    params = None
    json_data = None

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


# Sessions Operations


@mcp.tool()
async def list_sessions(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_desc: Optional[bool] = False,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    List all sessions with pagination and sorting options

    Endpoint: GET /api/v1/sessions

    Args:
        page: Results page number (integer, min: 1, default: 1)
        page_size: Number of sessions per page (integer, 1-100, default: 50)
        sort_desc: Sort by most recent first (boolean, default: True)
    """
    if ctx:
        ctx.info("Calling GET /api/v1/sessions")

    endpoint = "/api/v1/sessions"

    params = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    if sort_desc is not None:
        params["sort_desc"] = sort_desc

    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def get_session_history(
    session_id_or_name: str,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_desc: Optional[bool] = False,
    hide_tools: Optional[bool] = False,
    show_system_prompt: Optional[bool] = False,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Retrieve a session's message history by ID or name

    Endpoint: GET /api/v1/sessions/{session_id_or_name}

    Args:
        session_id_or_name: Identifier of session (UUID or string, required)
        page: Results page number (integer, min: 1, default: 1)
        page_size: Messages per page (integer, 1-100, default: 50)
        sort_desc: Sort by most recent first (boolean, default: True)
        hide_tools: Exclude tool calls/outputs (boolean, default: False)
        show_system_prompt: Include system prompt in details (boolean, default: False)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/sessions/{session_id_or_name}")

    endpoint = f"/api/v1/sessions/{session_id_or_name}"

    params = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    if sort_desc is not None:
        params["sort_desc"] = sort_desc
    if hide_tools is not None:
        params["hide_tools"] = hide_tools
    if show_system_prompt is not None:
        params["show_system_prompt"] = show_system_prompt

    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def delete_session(
    session_id_or_name: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete a session and all its message history by ID or name

    Endpoint: DELETE /api/v1/sessions/{session_id_or_name}

    Args:
        session_id_or_name: Identifier (UUID or string) of the session to delete (required)
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/sessions/{session_id_or_name}")

    endpoint = f"/api/v1/sessions/{session_id_or_name}"
    params = None
    json_data = None

    return await make_api_request(
        method="DELETE", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


# Users Operations


@mcp.tool()
async def list_users(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Return paginated list of users with profile metadata

    Endpoint: GET /api/v1/users

    Args:
        page: Results page number (integer, min: 1, default: 1)
        page_size: Number of users per page (integer, 1-100, default: 20)
    """
    if ctx:
        ctx.info("Calling GET /api/v1/users")

    endpoint = "/api/v1/users"

    params = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size

    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def create_user(
    data: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Create a new user with optional email, phone, and custom data

    Endpoint: POST /api/v1/users

    Args:
        data: Request body data
    """
    if ctx:
        ctx.info("Calling POST /api/v1/users")

    endpoint = "/api/v1/users"
    params = None
    json_data = data

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def get_user(
    user_identifier: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Retrieve user details by ID, email, or phone number

    Endpoint: GET /api/v1/users/{user_identifier}

    Args:
        user_identifier: Unique user identifier (ID, email, or phone number, required)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/users/{user_identifier}")

    endpoint = f"/api/v1/users/{user_identifier}"
    params = None
    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def update_user(
    user_identifier: str,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Update an existing user's details or metadata

    Endpoint: PUT /api/v1/users/{user_identifier}

    Args:
        user_identifier: ID, email, or phone number for lookup (string, required)
        data: Request body data
    """
    if ctx:
        ctx.info(f"Calling PUT /api/v1/users/{user_identifier}")

    endpoint = f"/api/v1/users/{user_identifier}"
    params = None
    json_data = data

    return await make_api_request(
        method="PUT", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def delete_user(
    user_identifier: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete a user account by ID, email, or phone number

    Endpoint: DELETE /api/v1/users/{user_identifier}

    Args:
        user_identifier: ID, email, or phone number of user to delete (string, required)
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/users/{user_identifier}")

    endpoint = f"/api/v1/users/{user_identifier}"
    params = None
    json_data = None

    return await make_api_request(
        method="DELETE", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


# Memories Operations


@mcp.tool()
async def list_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_desc: Optional[bool] = False,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    List all memories with filtering, pagination, and sorting options

    Endpoint: GET /api/v1/memories

    Args:
        user_id: User ID (UUID, optional) to filter (e.g., '123e4567-e89b-12d3-a456-426614174000')
        agent_id: Agent ID to filter (integer, optional)
        session_id: Session ID to filter (string, optional)
        page: Page number for paging (integer, default: 1)
        page_size: Items per results page (integer, default: 50)
        sort_desc: Sort order, most recent first if True (boolean, default: True)
    """
    if ctx:
        ctx.info("Calling GET /api/v1/memories")

    endpoint = "/api/v1/memories"

    params = {}
    if user_id is not None:
        params["user_id"] = user_id
    if agent_id is not None:
        params["agent_id"] = agent_id
    if session_id is not None:
        params["session_id"] = session_id
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    if sort_desc is not None:
        params["sort_desc"] = sort_desc

    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def create_memory(
    data: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Create a new memory with the provided details

    Endpoint: POST /api/v1/memories

    Args:
        data: Request body data
    """
    if ctx:
        ctx.info("Calling POST /api/v1/memories")

    endpoint = "/api/v1/memories"
    params = None
    json_data = data

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def create_memories_batch(
    memories: List[Dict[str, Any]], ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Create multiple memory records in a single batch operation

    Endpoint: POST /api/v1/memories/batch

    Args:
        memories: List of memory objects to create. Each memory should contain fields like:
                 - name: Name of the memory (required)
                 - content: Content of the memory (required)
                 - agent_id: Agent ID to associate with (required if user_id not provided)
                 - user_id: User ID to associate with (required if agent_id not provided)
                 - session_id: Optional session ID
                 - metadata: Optional metadata object
    """
    if ctx:
        ctx.info("Calling POST /api/v1/memories/batch")

    endpoint = "/api/v1/memories/batch"
    params = None
    json_data = memories  # Send the list directly, not wrapped in a data object

    return await make_api_request(
        method="POST", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def get_memory(memory_id: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Retrieve a specific memory record by memory ID

    Endpoint: GET /api/v1/memories/{memory_id}

    Args:
        memory_id: Unique ID of memory to retrieve (string, required)
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/memories/{memory_id}")

    endpoint = f"/api/v1/memories/{memory_id}"
    params = None
    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def update_memory(
    memory_id: str, data: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Update an existing memory record's details by memory ID

    Endpoint: PUT /api/v1/memories/{memory_id}

    Args:
        memory_id: ID of the memory to update (string, required)
        data: Request body data
    """
    if ctx:
        ctx.info(f"Calling PUT /api/v1/memories/{memory_id}")

    endpoint = f"/api/v1/memories/{memory_id}"
    params = None
    json_data = data

    return await make_api_request(
        method="PUT", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def delete_memory(
    memory_id: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete a memory from the database by memory ID

    Endpoint: DELETE /api/v1/memories/{memory_id}

    Args:
        memory_id: Memory ID to delete (string, required)
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/memories/{memory_id}")

    endpoint = f"/api/v1/memories/{memory_id}"
    params = None
    json_data = None

    return await make_api_request(
        method="DELETE", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


# Messages Operations


@mcp.tool()
async def delete_message(
    message_id: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete a message by its unique ID from Automagik system

    Endpoint: DELETE /api/v1/messages/{message_id}

    Args:
        message_id: Unique identifier of the message to delete (UUID string, required)
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/messages/{message_id}")

    endpoint = f"/api/v1/messages/{message_id}"
    params = None
    json_data = None

    return await make_api_request(
        method="DELETE", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


# Mcp Operations


@mcp.tool()
async def configure_mcp_servers(
    x_api_key: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Configure multiple MCP servers using server config format

    Endpoint: POST /api/v1/mcp/configure

    Args:
        x_api_key:
        data: Request body data
    """
    if ctx:
        ctx.info("Calling POST /api/v1/mcp/configure")

    endpoint = "/api/v1/mcp/configure"
    params = None
    json_data = data

    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def get_mcp_health(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Get health status of the MCP system and components

    Endpoint: GET /api/v1/mcp/health
    """
    if ctx:
        ctx.info("Calling GET /api/v1/mcp/health")

    endpoint = "/api/v1/mcp/health"
    params = None
    json_data = None

    return await make_api_request(
        method="GET", endpoint=endpoint, params=params, json_data=json_data, ctx=ctx
    )


@mcp.tool()
async def list_mcp_servers(
    x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List all MCP servers and their runtime states

    Endpoint: GET /api/v1/mcp/servers

    Args:
        x_api_key:
    """
    if ctx:
        ctx.info("Calling GET /api/v1/mcp/servers")

    endpoint = "/api/v1/mcp/servers"
    params = None
    json_data = None

    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def create_mcp_server(
    name: str,
    command: List[str],
    server_type: str = "stdio",
    x_api_key: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Create a new MCP server configuration

    Endpoint: POST /api/v1/mcp/servers

    Args:
        name: Name of the MCP server (string, required)
        command: Command to run the server as a list (e.g., ["python", "server.py"])
        server_type: Type of server - 'stdio' or 'http' (string, default: 'stdio')
        x_api_key: Optional API key override
    """
    if ctx:
        ctx.info("Calling POST /api/v1/mcp/servers")

    endpoint = "/api/v1/mcp/servers"
    params = None
    json_data = {"name": name, "command": command, "server_type": server_type}
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def get_mcp_server(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Get full details for a specific MCP server by name

    Endpoint: GET /api/v1/mcp/servers/{server_name}

    Args:
        server_name: Name of the server to retrieve (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/mcp/servers/{server_name}")

    endpoint = f"/api/v1/mcp/servers/{server_name}"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def update_mcp_server(
    server_name: str,
    x_api_key: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Update MCP server configuration by server name

    Endpoint: PUT /api/v1/mcp/servers/{server_name}

    Args:
        server_name: MCP server's name to update (string, required)
        x_api_key:
        data: Request body data
    """
    if ctx:
        ctx.info(f"Calling PUT /api/v1/mcp/servers/{server_name}")

    endpoint = f"/api/v1/mcp/servers/{server_name}"
    params = None
    json_data = data
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="PUT",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def delete_mcp_server(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete an MCP server from configuration by server name

    Endpoint: DELETE /api/v1/mcp/servers/{server_name}

    Args:
        server_name: Server name to delete from registry (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling DELETE /api/v1/mcp/servers/{server_name}")

    endpoint = f"/api/v1/mcp/servers/{server_name}"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="DELETE",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def start_mcp_server(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Start a managed MCP server by server name

    Endpoint: POST /api/v1/mcp/servers/{server_name}/start

    Args:
        server_name: Name of the server to start (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/mcp/servers/{server_name}/start")

    endpoint = f"/api/v1/mcp/servers/{server_name}/start"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def stop_mcp_server(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Stop a running MCP server by its server name

    Endpoint: POST /api/v1/mcp/servers/{server_name}/stop

    Args:
        server_name: MCP server to stop (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/mcp/servers/{server_name}/stop")

    endpoint = f"/api/v1/mcp/servers/{server_name}/stop"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def restart_mcp_server(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Restart a managed MCP server by server name

    Endpoint: POST /api/v1/mcp/servers/{server_name}/restart

    Args:
        server_name: Name of MCP server to restart (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/mcp/servers/{server_name}/restart")

    endpoint = f"/api/v1/mcp/servers/{server_name}/restart"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    x_api_key: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Call a specific tool on an MCP server

    Endpoint: POST /api/v1/mcp/tools/call

    Args:
        server_name: Name of the MCP server (string, required)
        tool_name: Name of the tool to call (string, required)
        arguments: Arguments to pass to the tool (dict, optional)
        x_api_key: Optional API key override
    """
    if ctx:
        ctx.info("Calling POST /api/v1/mcp/tools/call")

    endpoint = "/api/v1/mcp/tools/call"
    params = None
    json_data = {
        "server_name": server_name,
        "tool_name": tool_name,
        "arguments": arguments or {},
    }
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def access_mcp_resource(
    server_name: str,
    uri: str,
    x_api_key: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Access a managed resource on an MCP server

    Endpoint: POST /api/v1/mcp/resources/access

    Args:
        server_name: Name of the MCP server (string, required)
        uri: URI of the resource to access (string, required)
        x_api_key: Optional API key override
    """
    if ctx:
        ctx.info("Calling POST /api/v1/mcp/resources/access")

    endpoint = "/api/v1/mcp/resources/access"
    params = None
    json_data = {"server_name": server_name, "uri": uri}
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def list_mcp_server_tools(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List all tools available on a specific MCP server

    Endpoint: GET /api/v1/mcp/servers/{server_name}/tools

    Args:
        server_name: Name of the MCP server (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/mcp/servers/{server_name}/tools")

    endpoint = f"/api/v1/mcp/servers/{server_name}/tools"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def list_mcp_server_resources(
    server_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List all resources managed by a specific MCP server

    Endpoint: GET /api/v1/mcp/servers/{server_name}/resources

    Args:
        server_name: Name of MCP server (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/mcp/servers/{server_name}/resources")

    endpoint = f"/api/v1/mcp/servers/{server_name}/resources"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


@mcp.tool()
async def list_agent_mcp_tools(
    agent_name: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List all MCP tools available to a specific agent

    Endpoint: GET /api/v1/mcp/agents/{agent_name}/tools

    Args:
        agent_name: Agent name (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/mcp/agents/{agent_name}/tools")

    endpoint = f"/api/v1/mcp/agents/{agent_name}/tools"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
    )


# Claude-Code Operations


@mcp.tool()
async def run_claude_code_workflow(
    workflow_name: str,
    x_api_key: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Start a Claude-Code workflow asynchronously and return run ID

    Endpoint: POST /api/v1/workflows/claude-code/run/{workflow_name}

    Args:
        workflow_name: Claude-Code workflow to run (string, required, e.g., 'bug-fixer')
        x_api_key:
        data: Request body data
    """
    if ctx:
        ctx.info(f"Calling POST /api/v1/workflows/claude-code/run/{workflow_name}")

    endpoint = f"/api/v1/workflows/claude-code/run/{workflow_name}"
    params = None
    json_data = data
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="POST",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
        tool_name="run_claude_code_workflow",
    )


@mcp.tool()
async def get_claude_code_run_status(
    run_id: str, x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    Get status and results of a specific Claude-Code workflow run

    Endpoint: GET /api/v1/workflows/claude-code/run/{run_id}/status

    Args:
        run_id: Run ID for Claude-Code workflow (string, required)
        x_api_key:
    """
    if ctx:
        ctx.info(f"Calling GET /api/v1/workflows/claude-code/run/{run_id}/status")

    endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/status"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
        tool_name="get_claude_code_run_status",
    )


@mcp.tool()
async def list_claude_code_workflows(
    x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    List all available Claude-Code workflows and status

    Endpoint: GET /api/v1/workflows/claude-code/workflows

    Args:
        x_api_key:
    """
    if ctx:
        ctx.info("Calling GET /api/v1/workflows/claude-code/workflows")

    endpoint = "/api/v1/workflows/claude-code/workflows"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
        tool_name="list_claude_code_workflows",
    )


@mcp.tool()
async def get_claude_code_health(
    x_api_key: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    Check health and status of Claude-Code agent and workflows

    Endpoint: GET /api/v1/workflows/claude-code/health

    Args:
        x_api_key:
    """
    if ctx:
        ctx.info("Calling GET /api/v1/workflows/claude-code/health")

    endpoint = "/api/v1/workflows/claude-code/health"
    params = None
    json_data = None
    # Use x_api_key if provided
    extra_headers = {"x-api-key": x_api_key} if x_api_key else None

    return await make_api_request(
        method="GET",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx,
        extra_headers=extra_headers,
        tool_name="get_claude_code_health",
    )


# ========================================
# Convenience Functions for Enhanced UX
# ========================================


@mcp.tool()
async def chat_agent(
    agent_name: str, message: str, ctx: Optional[Context] = None
) -> str:
    """
    Simple chat interface for agents - wrapper around run_agent for ease of use.

    This is a convenience function that provides a simpler interface to the run_agent functionality.

    Args:
        agent_name: Name of the agent to chat with (e.g., 'simple', 'claude_code', 'genie')
        message: Your message to the agent

    Returns:
        The agent's response as a string

    Example:
        chat_agent('simple', 'Hello, how are you?')
    """
    if ctx:
        ctx.info(f"Starting chat with agent: {agent_name}")

    return await run_agent(agent_name, message, ctx=ctx)


@mcp.tool()
async def run_workflow(
    workflow_name: str,
    data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Start a Claude-Code workflow with optional parameters.

    This is a convenience function that wraps the run_claude_code_workflow function
    with a simpler interface.

    Args:
        workflow_name: Name of the workflow to run
        data: Optional parameters to pass to the workflow

    Returns:
        Workflow execution result including run_id for status tracking

    Example:
        run_workflow('bug-fixer', {'file_path': 'src/main.py'})
    """
    if ctx:
        ctx.info(f"Starting workflow: {workflow_name}")

    return await run_claude_code_workflow(workflow_name, data=data, ctx=ctx)


@mcp.tool()
async def list_workflows(ctx: Optional[Context] = None) -> str:
    """
    List all available Claude-Code workflows.

    This is a convenience function that wraps the list_claude_code_workflows function
    for easier discovery of available workflows.

    Returns:
        List of available workflows with descriptions

    Example:
        list_workflows()
    """
    if ctx:
        ctx.info("Fetching available workflows")

    return await list_claude_code_workflows(ctx=ctx)


@mcp.tool()
async def check_workflow_progress(run_id: str, ctx: Optional[Context] = None) -> str:
    """
    Check the progress and status of a running workflow.

    This is a convenience function that wraps the get_claude_code_run_status function
    for easier status tracking.

    Args:
        run_id: The run ID returned from run_workflow or run_claude_code_workflow

    Returns:
        Current status and results of the workflow run

    Example:
        check_workflow_progress('abc123-def456-789')
    """
    if ctx:
        ctx.info(f"Checking progress for run: {run_id}")

    return await get_claude_code_run_status(run_id, ctx=ctx)


# Resources
# Temporarily disabled due to FastMCP URI validation issues
# @mcp.resource("file:///config")
# async def get_api_config_v2(ctx: Optional[Context] = None) -> str:
#     """Get the API configuration and available endpoints"""
#     return """
# This tool was auto-generated from an OpenAPI specification.
# Base URL: https://api.example.com
# Total endpoints: 47
# Use the tool functions to interact with the API.
# """


# Prompts
@mcp.prompt()
def api_explorer(endpoint: str = "") -> str:
    """Generate a prompt for exploring Automagik API endpoints"""
    if endpoint:
        return f"""
Help me explore the {endpoint} endpoint of Automagik API.
What parameters does it accept and what does it return?
"""
    else:
        return """
What endpoints are available in the Automagik API?
List the main operations I can perform with AI agents and workflows.
"""


# Tool creation functions (required by automagik-tools)
def create_tool(tool_config: Optional[AutomagikConfig] = None) -> FastMCP:
    """Create the MCP tool instance"""
    global config
    config = tool_config or AutomagikConfig()
    return mcp


def create_server(tool_config: Optional[AutomagikConfig] = None):
    """Create FastMCP server instance"""
    tool = create_tool(tool_config)
    return tool


def get_tool_name() -> str:
    """Get the tool name"""
    return "automagik"


def get_config_class():
    """Get the config class for this tool"""
    return AutomagikConfig


def get_config_schema() -> Dict[str, Any]:
    """Get the JSON schema for the config"""
    return AutomagikConfig.model_json_schema()


def get_required_env_vars() -> Dict[str, str]:
    """Get required environment variables"""
    return {
        "AUTOMAGIK_API_KEY": "API key for authentication",
        "AUTOMAGIK_BASE_URL": "Base URL for the API (optional)",
    }


def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {
        "name": "automagik",
        "version": "2.0.0",
        "description": "Automagik - AI-powered agents and workflows with enhanced responses",
        "author": "Automagik Team",
        "category": "ai-agents",
        "tags": ["ai", "agents", "workflows", "ai-enhanced"],
        "config_env_prefix": "AUTOMAGIK_",
    }


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the tool as a standalone service"""
    import uvicorn

    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)
