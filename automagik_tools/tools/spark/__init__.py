"""
Spark - Workflow orchestration and AI agent management

This tool provides MCP integration for AutoMagik Spark API, enabling:
- Workflow management (agents, teams, structured workflows)
- Task execution and monitoring
- Schedule management (cron/interval)
- Source configuration for multiple AutoMagik instances
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP, Context
from .config import SparkConfig
from .client import SparkClient
from .models import (
    ScheduleType as ScheduleType,
    TaskStatus as TaskStatus,
    SourceType as SourceType,
)
import json

# Global config and client instances
config: Optional[SparkConfig] = None
client: Optional[SparkClient] = None

# Create FastMCP instance
mcp = FastMCP(
    "Spark",
    instructions="""
Spark - AutoMagik workflow orchestration and AI agent management

🤖 Execute AI workflows (agents, teams, structured processes)
📅 Schedule automated workflow runs (cron/interval)
🔄 Sync agents from remote AutoMagik instances
📊 Monitor task execution and status
🔌 Manage workflow sources (AutoMagik Agents, AutoMagik Hive)

Supports three workflow types:
- Agents: Single AI agent execution
- Teams: Multi-agent coordination
- Workflows: Structured multi-step processes
""",
)


def _get_config(ctx: Optional[Context] = None) -> SparkConfig:
    """Get configuration from context or global config."""
    if ctx:
        # Try to get cached config from context state (per-request cache)
        cached = ctx.get_state("spark_config")
        if cached:
            return cached

        # if ctx and hasattr(ctx, "tool_config") and ctx.tool_config:
        try:
            from automagik_tools.hub.config_injection import create_user_config_instance
            return create_user_config_instance(SparkConfig, ctx.tool_config)
        except Exception:
            pass

    global config
    if config is None:
        config = SparkConfig()
    return config


def _ensure_client(ctx: Optional[Context] = None) -> SparkClient:
    """Get client with user-specific or global config."""
    if ctx:
        # Try to get cached client from context state (per-request cache)
        cached = ctx.get_state("spark_client")
        if cached:
            return cached

    cfg = _get_config(ctx)

    # For multi-tenant with user config, create fresh client and cache it
    if ctx and hasattr(ctx, "tool_config") and ctx.tool_config:
        user_client = SparkClient(cfg)
        ctx.set_state("spark_client", user_client)
        return user_client

    # For single-tenant, use singleton
    global client
    if client is None:
        client = SparkClient(cfg)
    return client


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "spark",
        "version": "0.9.7",
        "description": "AutoMagik Spark workflow orchestration and AI agent management",
        "author": "Namastex Labs",
        "category": "workflow",
        "tags": ["ai", "workflow", "orchestration", "agents", "automation"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return SparkConfig


def create_server(tool_config: Optional[SparkConfig] = None):
    """Create FastMCP server instance"""
    global config, client
    config = tool_config or SparkConfig()
    client = SparkClient(config)
    return mcp


# Health and Status Tools
@mcp.tool()
async def get_health(ctx: Optional[Context] = None) -> str:
    """
    Get health status of Spark API and its services.

    Returns the status of API, worker, and Redis services.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.get_health()
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get health: {str(e)}")
        raise


# Workflow Management Tools
@mcp.tool()
async def list_workflows(
    source: Optional[str] = None,
    limit: int = 100,
    ctx: Optional[Context] = None,
) -> str:
    """
    List all synchronized workflows (agents, teams, structured workflows).

    Args:
        source: Filter by source URL (optional)
        limit: Maximum number of workflows to return (default: 100)

    Returns a list of workflows with their details including type, status, and run statistics.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        workflows = await api_client.list_workflows(source, limit)
        return json.dumps(workflows, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list workflows: {str(e)}")
        raise


@mcp.tool()
async def get_workflow(workflow_id: str, ctx: Optional[Context] = None) -> str:
    """
    Get detailed information about a specific workflow.

    Args:
        workflow_id: The UUID of the workflow

    Returns workflow details including configuration, components, and execution history.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        workflow = await api_client.get_workflow(workflow_id)
        return json.dumps(workflow, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get workflow: {str(e)}")
        raise


@mcp.tool()
async def run_workflow(
    workflow_id: str, input_text: str, ctx: Optional[Context] = None
) -> str:
    """
    Execute a workflow with the provided input.

    Args:
        workflow_id: The UUID of the workflow to execute
        input_text: Input text for the workflow (e.g., question, task description)

    Returns task execution details including output and status.

    Examples:
        - For agents: "What is the capital of France?"
        - For teams: "Create a REST API with authentication"
        - For workflows: Task-specific input based on workflow type
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.run_workflow(workflow_id, input_text)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to run workflow: {str(e)}")
        raise


@mcp.tool()
async def delete_workflow(workflow_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a synchronized workflow.

    Args:
        workflow_id: The UUID of the workflow to delete

    Returns confirmation of deletion.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        await api_client.delete_workflow(workflow_id)
        return json.dumps({"success": True, "deleted": workflow_id})
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete workflow: {str(e)}")
        raise


# Remote Workflow Discovery Tools
@mcp.tool()
async def list_remote_workflows(
    source_url: str, simplified: bool = True, ctx: Optional[Context] = None
) -> str:
    """
    List available workflows from a remote AutoMagik instance.

    Args:
        source_url: The URL of the remote AutoMagik instance (e.g., http://localhost:8881)
        simplified: Return only essential flow information (default: True)

    Returns a list of available workflows that can be synced.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        workflows = await api_client.list_remote_workflows(source_url, simplified)
        return json.dumps(workflows, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list remote workflows: {str(e)}")
        raise


@mcp.tool()
async def get_remote_workflow(
    workflow_id: str, source_url: str, ctx: Optional[Context] = None
) -> str:
    """
    Get detailed information about a specific remote workflow.

    Args:
        workflow_id: The ID of the remote workflow
        source_url: The URL of the remote AutoMagik instance (e.g., http://localhost:8881)

    Returns detailed remote workflow information.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        workflow = await api_client.get_remote_workflow(workflow_id, source_url)
        return json.dumps(workflow, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get remote workflow: {str(e)}")
        raise


@mcp.tool()
async def sync_workflow(
    workflow_id: str,
    source_url: str,
    input_component: str = "input",
    output_component: str = "output",
    ctx: Optional[Context] = None,
) -> str:
    """
    Sync a workflow from a remote source to local Spark instance.

    Args:
        workflow_id: The ID of the workflow to sync
        source_url: The URL of the remote source (e.g., http://localhost:8881)
        input_component: Input component name (default: "input")
        output_component: Output component name (default: "output")

    Returns the synced workflow details.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.sync_workflow(
            workflow_id, source_url, input_component, output_component
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to sync workflow: {str(e)}")
        raise


# Task Management Tools
@mcp.tool()
async def list_tasks(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    List task executions with pagination support.

    Args:
        workflow_id: Filter by specific workflow (optional)
        status: Filter by status - pending, running, completed, failed (optional)
        limit: Maximum number of tasks to return (default: 50, max: 100)
        offset: Number of tasks to skip for pagination (default: 0)

    Returns a paginated response with:
        - items: List of task executions
        - total: Total number of tasks matching filters
        - limit: Items per page
        - offset: Current offset
        - has_more: Whether more tasks are available

    Pagination examples:
        # Get first 50 tasks
        list_tasks(limit=50, offset=0)

        # Get next 50 tasks
        list_tasks(limit=50, offset=50)

        # Get specific workflow's tasks, paginated
        list_tasks(workflow_id="workflow-id", limit=20, offset=0)

        # Get only completed tasks, paginated
        list_tasks(status="completed", limit=25, offset=0)
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.list_tasks(workflow_id, status, limit, offset)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list tasks: {str(e)}")
        raise


@mcp.tool()
async def get_task(task_id: str, ctx: Optional[Context] = None) -> str:
    """
    Get detailed information about a specific task execution.

    Args:
        task_id: The UUID of the task

    Returns task details including input, output, status, and timing.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        task = await api_client.get_task(task_id)
        return json.dumps(task, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get task: {str(e)}")
        raise


@mcp.tool()
async def delete_task(task_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a task execution.

    Args:
        task_id: The UUID of the task to delete

    Returns confirmation of deletion.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.delete_task(task_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete task: {str(e)}")
        raise


# Schedule Management Tools
@mcp.tool()
async def list_schedules(
    workflow_id: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    List all active schedules.

    Args:
        workflow_id: Filter by specific workflow (optional)

    Returns a list of schedules with their configuration and next run times.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        schedules = await api_client.list_schedules(workflow_id)
        return json.dumps(schedules, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list schedules: {str(e)}")
        raise


@mcp.tool()
async def create_schedule(
    workflow_id: str,
    schedule_type: str,
    schedule_expr: str,
    input_value: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Create a new schedule for automated workflow execution.

    Args:
        workflow_id: The UUID of the workflow to schedule
        schedule_type: Type of schedule - "interval" or "cron"
        schedule_expr: Schedule expression
            - For interval: "5m", "1h", "30s", "2d"
            - For cron: "0 9 * * *" (daily at 9 AM), "*/15 * * * *" (every 15 minutes)
        input_value: Optional default input for scheduled runs

    Returns the created schedule details.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        schedule = await api_client.create_schedule(
            workflow_id, schedule_type, schedule_expr, input_value
        )
        return json.dumps(schedule, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to create schedule: {str(e)}")
        raise


@mcp.tool()
async def get_schedule(schedule_id: str, ctx: Optional[Context] = None) -> str:
    """
    Get detailed information about a specific schedule.

    Args:
        schedule_id: The UUID of the schedule

    Returns schedule details including configuration and next run time.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        schedule = await api_client.get_schedule(schedule_id)
        return json.dumps(schedule, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get schedule: {str(e)}")
        raise


@mcp.tool()
async def update_schedule(
    schedule_id: str,
    workflow_id: str,
    schedule_type: str,
    schedule_expr: str,
    input_value: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Update an existing schedule.

    Args:
        schedule_id: The UUID of the schedule to update
        workflow_id: The UUID of the workflow (required)
        schedule_type: Type of schedule - "interval" or "cron" (required)
        schedule_expr: Schedule expression (required)
            - For interval: "5m", "1h", "30s", "2d"
            - For cron: "0 9 * * *" (daily at 9 AM), "*/15 * * * *" (every 15 minutes)
        input_value: Default input for scheduled runs (optional)

    Returns the updated schedule details.

    Note: The Spark API requires all schedule fields to be provided.
          Use get_schedule() first to retrieve current values if you only want to change one field.

    Example workflow:
        1. schedule = get_schedule(schedule_id)
        2. update_schedule(
               schedule_id=schedule_id,
               workflow_id=schedule["workflow_id"],
               schedule_type=schedule["schedule_type"],
               schedule_expr="0 10 * * *",  # Change only this
               input_value=schedule.get("input_value")
           )
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.update_schedule(
            schedule_id, workflow_id, schedule_type, schedule_expr, input_value
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to update schedule: {str(e)}")
        raise


@mcp.tool()
async def delete_schedule(schedule_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a schedule.

    Args:
        schedule_id: The UUID of the schedule to delete

    Returns confirmation of deletion.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        await api_client.delete_schedule(schedule_id)
        return json.dumps({"success": True, "deleted": schedule_id})
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete schedule: {str(e)}")
        raise


@mcp.tool()
async def enable_schedule(schedule_id: str, ctx: Optional[Context] = None) -> str:
    """
    Enable a disabled schedule.

    Args:
        schedule_id: The UUID of the schedule to enable

    Returns the updated schedule details.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.enable_schedule(schedule_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to enable schedule: {str(e)}")
        raise


@mcp.tool()
async def disable_schedule(schedule_id: str, ctx: Optional[Context] = None) -> str:
    """
    Disable an active schedule.

    Args:
        schedule_id: The UUID of the schedule to disable

    Returns the updated schedule details.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        result = await api_client.disable_schedule(schedule_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to disable schedule: {str(e)}")
        raise


# Source Management Tools
@mcp.tool()
async def list_sources(
    status: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    List all configured workflow sources.

    Args:
        status: Filter by status - "active" or "inactive" (optional)

    Returns a list of sources (AutoMagik Agents, AutoMagik Hive instances).
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        sources = await api_client.list_sources(status)
        return json.dumps(sources, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list sources: {str(e)}")
        raise


@mcp.tool()
async def get_source(source_id: str, ctx: Optional[Context] = None) -> str:
    """
    Get detailed information about a specific workflow source.

    Args:
        source_id: The UUID of the source

    Returns source details including configuration and status.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        source = await api_client.get_source(source_id)
        return json.dumps(source, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get source: {str(e)}")
        raise


@mcp.tool()
async def add_source(
    name: str,
    source_type: str,
    url: str,
    api_key: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Add a new workflow source.

    Args:
        name: Display name for the source
        source_type: Type of source - "automagik-agents", "automagik-hive", or "langflow"
        url: Base URL of the source (e.g., http://localhost:8881)
        api_key: Optional API key for authentication

    Returns the created source details.

    Example:
        add_source("Local Agents", "automagik-agents", "http://localhost:8881", "namastex888")
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        source = await api_client.add_source(name, source_type, url, api_key)
        return json.dumps(source, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to add source: {str(e)}")
        raise


@mcp.tool()
async def update_source(
    source_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Update a workflow source configuration.

    Args:
        source_id: The UUID of the source to update
        name: New display name (optional)
        url: New base URL (optional)
        api_key: New API key (optional)

    Returns the updated source details.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        source = await api_client.update_source(source_id, name, url, api_key)
        return json.dumps(source, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to update source: {str(e)}")
        raise


@mcp.tool()
async def delete_source(source_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a workflow source.

    Args:
        source_id: The UUID of the source to delete

    Returns confirmation of deletion.
    """
    api_client = _ensure_client(ctx)
    if not api_client:
        raise ValueError("Tool not configured")

    try:
        await api_client.delete_source(source_id)
        return json.dumps({"success": True, "deleted": source_id})
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete source: {str(e)}")
        raise
