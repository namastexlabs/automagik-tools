"""
Spark - Workflow orchestration and AI agent management

This tool provides MCP integration for AutoMagik Spark API, enabling:
- Workflow management (agents, teams, structured workflows)
- Task execution and monitoring
- Schedule management (cron/interval)
- Source configuration for multiple AutoMagik instances
"""

from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from .config import SparkConfig
from .client import SparkClient
from .models import ScheduleType, TaskStatus, SourceType
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


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "spark",
        "version": "1.0.0",
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.get_health()
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        workflows = await client.list_workflows(source, limit)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        workflow = await client.get_workflow(workflow_id)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.run_workflow(workflow_id, input_text)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.delete_workflow(workflow_id)
        return json.dumps({"success": True, "deleted": workflow_id})
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete workflow: {str(e)}")
        raise


# Remote Workflow Discovery Tools
@mcp.tool()
async def list_remote_workflows(
    source_url: str, ctx: Optional[Context] = None
) -> str:
    """
    List available workflows from a remote AutoMagik instance.
    
    Args:
        source_url: The URL of the remote AutoMagik instance (e.g., http://localhost:8881)
    
    Returns a list of available workflows that can be synced.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        workflows = await client.list_remote_workflows(source_url)
        return json.dumps(workflows, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list remote workflows: {str(e)}")
        raise


@mcp.tool()
async def sync_workflow(
    workflow_id: str,
    input_component: str = "input",
    output_component: str = "output",
    ctx: Optional[Context] = None,
) -> str:
    """
    Sync a workflow from a remote source to local Spark instance.
    
    Args:
        workflow_id: The ID of the workflow to sync
        input_component: Input component name (default: "input")
        output_component: Output component name (default: "output")
    
    Returns the synced workflow details.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.sync_workflow(workflow_id, input_component, output_component)
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
    ctx: Optional[Context] = None,
) -> str:
    """
    List task executions with optional filtering.
    
    Args:
        workflow_id: Filter by specific workflow (optional)
        status: Filter by status - pending, running, completed, failed (optional)
        limit: Maximum number of tasks to return (default: 50)
    
    Returns a list of task executions with their details.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        tasks = await client.list_tasks(workflow_id, status, limit)
        return json.dumps(tasks, indent=2)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        task = await client.get_task(task_id)
        return json.dumps(task, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get task: {str(e)}")
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        schedules = await client.list_schedules(workflow_id)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        schedule = await client.create_schedule(
            workflow_id, schedule_type, schedule_expr, input_value
        )
        return json.dumps(schedule, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to create schedule: {str(e)}")
        raise


@mcp.tool()
async def delete_schedule(schedule_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a schedule.
    
    Args:
        schedule_id: The UUID of the schedule to delete
    
    Returns confirmation of deletion.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.delete_schedule(schedule_id)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.enable_schedule(schedule_id)
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.disable_schedule(schedule_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to disable schedule: {str(e)}")
        raise


# Source Management Tools
@mcp.tool()
async def list_sources(ctx: Optional[Context] = None) -> str:
    """
    List all configured workflow sources.
    
    Returns a list of sources (AutoMagik Agents, AutoMagik Hive instances).
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        sources = await client.list_sources()
        return json.dumps(sources, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list sources: {str(e)}")
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
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        source = await client.add_source(name, source_type, url, api_key)
        return json.dumps(source, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to add source: {str(e)}")
        raise


@mcp.tool()
async def delete_source(source_id: str, ctx: Optional[Context] = None) -> str:
    """
    Delete a workflow source.
    
    Args:
        source_id: The UUID of the source to delete
    
    Returns confirmation of deletion.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.delete_source(source_id)
        return json.dumps({"success": True, "deleted": source_id})
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to delete source: {str(e)}")
        raise