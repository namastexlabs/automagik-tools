"""
AutoMagik Workflows - Smart Claude Workflow Orchestration

This tool provides MCP integration for Claude Code workflow API with intelligent progress tracking.
Enables execution, monitoring, and management of Claude Code workflows with real-time progress reporting.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from .config import AutomagikWorkflowsConfig
from .client import ClaudeCodeClient

# Global config and client instances
config: Optional[AutomagikWorkflowsConfig] = None
client: Optional[ClaudeCodeClient] = None

# Create FastMCP instance
mcp = FastMCP(
    "AutoMagik Workflows",
    instructions="""
AutoMagik Workflows - Smart Claude workflow orchestration

🚀 Execute Claude Code workflows with real-time progress tracking
📋 Discover available workflows and their capabilities
📊 Monitor workflow execution status with detailed progress
📈 View execution history and performance metrics

Provides intelligent progress reporting using turns/max_turns ratio for optimal workflow monitoring.
""",
)


@mcp.tool()
async def run_workflow(
    workflow_name: str,
    message: str,
    max_turns: int = 30,
    session_name: Optional[str] = None,
    git_branch: Optional[str] = None,
    repository_url: Optional[str] = None,
    timeout: int = 7200,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    🚀 Execute a Claude Code workflow with intelligent progress tracking

    Args:
        workflow_name: Workflow type (test, pr, fix, refactor, implement, review, document, architect)
        message: Task description for the workflow
        max_turns: Maximum conversation turns (1-100, default: 30)
        session_name: Optional session identifier
        git_branch: Git branch for the workflow
        repository_url: Repository URL if applicable
        timeout: Workflow timeout in seconds (default: 2 hours)
        ctx: MCP context for progress reporting

    Returns:
        Dict containing workflow results, metrics, and execution details
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    if ctx:
        ctx.info(f"🚀 Starting '{workflow_name}' workflow with message: {message}")

    # Prepare request data
    request_data = {"message": message, "max_turns": max_turns}

    # Add optional parameters
    if session_name:
        request_data["session_name"] = session_name
    if git_branch:
        request_data["git_branch"] = git_branch
    if repository_url:
        request_data["repository_url"] = repository_url

    try:
        # Start the workflow
        start_response = await client.start_workflow(workflow_name, request_data)

        if "run_id" not in start_response:
            raise ValueError(f"Failed to start workflow: {start_response}")

        run_id = start_response["run_id"]

        if ctx:
            ctx.info(f"📋 Workflow started with run_id: {run_id}")

        # Monitor progress with polling
        start_time = time.time()
        current_turns = 0

        while time.time() - start_time < timeout:
            status_response = await client.get_workflow_status(run_id)

            # Extract progress information
            status = status_response.get("status", "unknown")
            current_turns = status_response.get("turns", current_turns)

            # Report progress using turns/max_turns ratio
            if ctx and max_turns > 0:
                progress_ratio = min(current_turns / max_turns, 1.0)
                await ctx.report_progress(progress=current_turns, total=max_turns)

                if ctx:
                    ctx.info(
                        f"📊 Progress: {current_turns}/{max_turns} turns ({progress_ratio:.1%})"
                    )

            # Check for completion
            if status == "completed":
                if ctx:
                    ctx.info("✅ Workflow completed successfully")
                    await ctx.report_progress(progress=max_turns, total=max_turns)

                # Return comprehensive results
                return {
                    "status": "completed",
                    "run_id": run_id,
                    "workflow_name": workflow_name,
                    "turns_used": current_turns,
                    "max_turns": max_turns,
                    "execution_time": time.time() - start_time,
                    "result": status_response.get("result", {}),
                    "metrics": status_response.get("metrics", {}),
                    "message": f"Workflow '{workflow_name}' completed in {current_turns} turns",
                }

            elif status == "failed":
                error_msg = status_response.get("error", "Unknown error")
                if ctx:
                    ctx.error(f"❌ Workflow failed: {error_msg}")

                return {
                    "status": "failed",
                    "run_id": run_id,
                    "workflow_name": workflow_name,
                    "turns_used": current_turns,
                    "max_turns": max_turns,
                    "execution_time": time.time() - start_time,
                    "error": error_msg,
                    "message": f"Workflow '{workflow_name}' failed after {current_turns} turns",
                }

            # Continue polling if still running
            elif status in ["pending", "running"]:
                await asyncio.sleep(config.polling_interval)
            else:
                if ctx:
                    ctx.warn(f"⚠️ Unknown status: {status}")
                await asyncio.sleep(config.polling_interval)

        # Timeout reached
        if ctx:
            ctx.error(f"⏰ Workflow timeout after {timeout} seconds")

        return {
            "status": "timeout",
            "run_id": run_id,
            "workflow_name": workflow_name,
            "turns_used": current_turns,
            "max_turns": max_turns,
            "execution_time": timeout,
            "message": f"Workflow '{workflow_name}' timed out after {timeout} seconds",
        }

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Workflow execution error: {str(e)}")

        return {
            "status": "error",
            "workflow_name": workflow_name,
            "error": str(e),
            "message": f"Failed to execute workflow '{workflow_name}': {str(e)}",
        }


@mcp.tool()
async def list_workflows(ctx: Optional[Context] = None) -> List[Dict[str, str]]:
    """
    📋 List all available Claude workflows with descriptions

    Returns:
        List of available workflows with their descriptions and capabilities
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        workflows = await client.list_workflows()

        if ctx:
            ctx.info(f"📋 Found {len(workflows)} available workflows")

        return workflows

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list workflows: {str(e)}")

        return [{"error": str(e), "message": "Failed to retrieve workflows"}]


@mcp.tool()
async def list_recent_runs(
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    sort_by: str = "started_at",
    sort_order: str = "desc",
    ctx: Optional[Context] = None,
) -> List[Dict[str, Any]]:
    """
    📊 List recent workflow runs with optional filtering

    Args:
        workflow_name: Filter by specific workflow type
        status: Filter by status (pending, running, completed, failed)
        limit: Maximum number of runs to return (default: 10)
        sort_by: Sort field (started_at, workflow_name, status)
        sort_order: Sort order (asc, desc)
        ctx: MCP context for logging

    Returns:
        List of recent workflow runs with execution details
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        filters = {"limit": limit, "sort_by": sort_by, "sort_order": sort_order}

        if workflow_name:
            filters["workflow_name"] = workflow_name
        if status:
            filters["status"] = status

        runs_response = await client.list_runs(filters)

        # Extract runs from response
        runs = runs_response.get("runs", []) if isinstance(runs_response, dict) else []

        if ctx:
            ctx.info(f"📊 Found {len(runs)} workflow runs")

        return runs

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list runs: {str(e)}")

        return [{"error": str(e), "message": "Failed to retrieve workflow runs"}]


@mcp.tool()
async def get_workflow_status(
    run_id: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    📈 Get detailed status of specific workflow run

    Args:
        run_id: Unique identifier for the workflow run
        ctx: MCP context for logging

    Returns:
        Detailed status information including progress, metrics, and results
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        status_response = await client.get_workflow_status(run_id)

        # Add human-readable status information
        status = status_response.get("status", "unknown")
        turns = status_response.get("turns", 0)

        if ctx:
            ctx.info(f"📈 Workflow {run_id} status: {status} ({turns} turns)")

        return status_response

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to get status for run {run_id}: {str(e)}")

        return {
            "error": str(e),
            "run_id": run_id,
            "message": f"Failed to retrieve status for run {run_id}",
        }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "automagik-workflows",
        "version": "1.0.0",
        "description": "Smart Claude workflow orchestration with real-time progress tracking",
        "author": "Namastex Labs",
        "category": "workflow",
        "tags": ["claude", "workflow", "automation", "progress", "monitoring"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return AutomagikWorkflowsConfig


def create_server(tool_config: Optional[AutomagikWorkflowsConfig] = None):
    """Create FastMCP server instance"""
    global config, client
    config = tool_config or AutomagikWorkflowsConfig()
    client = ClaudeCodeClient(config)
    return mcp
