"""
AutoMagik Workflows - Smart Claude Workflow Orchestration

This tool provides MCP integration for Claude Code workflow API with intelligent progress tracking.
Enables execution, monitoring, and management of Claude Code workflows with real-time progress reporting.
"""

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
    persistent: bool = True,
    session_name: Optional[str] = None,
    git_branch: Optional[str] = None,
    repository_url: Optional[str] = None,
    auto_merge: bool = False,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    🚀 Start a Claude Code workflow execution (returns immediately)

    Args:
        workflow_name: Workflow type (test, pr, fix, refactor, implement, review, document, architect)
        message: Task description for the workflow
        max_turns: Maximum conversation turns (1-100, default: 30)
        persistent: Use persistent workspace (default: True, set False for temporary workspace)
        session_name: Optional session identifier
        git_branch: Git branch for the workflow
        repository_url: Repository URL if applicable
        auto_merge: Automatically merge successful workflow results (default: False)
        ctx: MCP context for logging

    Returns:
        Dict containing initial workflow status and run_id for tracking
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
    if auto_merge:
        request_data["auto_merge"] = auto_merge

    try:
        # Start the workflow and return immediately
        start_response = await client.start_workflow(workflow_name, request_data, persistent)

        if "run_id" not in start_response:
            raise ValueError(f"Failed to start workflow: {start_response}")

        run_id = start_response["run_id"]

        if ctx:
            ctx.info(f"📋 Workflow started with run_id: {run_id}")
            ctx.info("💡 Use get_workflow_status() to track progress")

        # Return initial response immediately
        return {
            "status": start_response.get("status", "running"),
            "run_id": run_id,
            "workflow_name": workflow_name,
            "max_turns": max_turns,
            "started_at": start_response.get("started_at"),
            "session_id": start_response.get("session_id"),
            "message": f"Workflow '{workflow_name}' started successfully. Use get_workflow_status('{run_id}') to track progress.",
            "tracking_info": {
                "run_id": run_id,
                "polling_command": f"get_workflow_status('{run_id}')",
                "expected_duration": "Variable (depends on complexity)",
                "max_turns": max_turns
            }
        }

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Workflow execution error: {str(e)}")

        return {
            "status": "error",
            "workflow_name": workflow_name,
            "error": str(e),
            "message": f"Failed to start workflow '{workflow_name}': {str(e)}",
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
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "started_at",
    sort_order: str = "desc",
    detailed: bool = False,
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    📊 List recent workflow runs with optional filtering and pagination

    Args:
        workflow_name: Filter by specific workflow type
        status: Filter by status (pending, running, completed, failed)
        user_id: Filter by user ID
        page: Page number (starts from 1, default: 1)
        page_size: Number of runs per page (max 100, default: 20)
        sort_by: Sort field (started_at, completed_at, execution_time, total_cost)
        sort_order: Sort order (asc, desc)
        detailed: Include full orchestration data (workspace_path, git_branch, error_message, tools_used, session_name)
        ctx: MCP context for logging

    Returns:
        Paginated workflow runs with execution details and pagination info
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        filters = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order
        }

        if workflow_name:
            filters["workflow_name"] = workflow_name
        if status:
            filters["status"] = status
        if user_id:
            filters["user_id"] = user_id

        runs_response = await client.list_runs(filters)

        # Extract runs from paginated response
        runs = runs_response.get("runs", []) if isinstance(runs_response, dict) else []
        pagination_info = runs_response.get("pagination", {}) if isinstance(runs_response, dict) else {}

        if ctx:
            total_runs = pagination_info.get("total", len(runs))
            ctx.info(f"📊 Found {len(runs)} workflow runs (page {page}, total: {total_runs})")

        # Return concise or detailed summary of runs with pagination
        processed_runs = []
        for run in runs:
            if detailed:
                # Include full orchestration data for GENIE
                processed_run = {
                    "run_id": run.get("run_id", "unknown"),
                    "workflow_name": run.get("workflow_name", "unknown"),
                    "status": run.get("status", "unknown"),
                    "started_at": run.get("started_at", "unknown"),
                    "turns": run.get("turns", 0),
                    "execution_time": round(run.get("execution_time", 0), 1) if run.get("execution_time") else 0,
                    "cost": round(run.get("total_cost", 0), 4) if run.get("total_cost") else 0,
                    # Enhanced orchestration data
                    "workspace_path": run.get("workspace_path"),
                    "git_branch": run.get("git_branch"),
                    "error_message": run.get("error_message"),
                    "tools_used": run.get("tools_used", []),
                    "session_name": run.get("session_name"),
                    "repository_url": run.get("repository_url"),
                    "user_id": run.get("user_id"),
                    "tokens": run.get("tokens", 0)
                }
                if run.get("completed_at"):
                    processed_run["completed_at"] = run["completed_at"]
            else:
                # Backward compatible concise format
                processed_run = {
                    "run_id": run.get("run_id", "unknown"),
                    "workflow_name": run.get("workflow_name", "unknown"),
                    "status": run.get("status", "unknown"),
                    "started_at": run.get("started_at", "unknown"),
                    "turns": run.get("turns", 0),
                    "execution_time": round(run.get("execution_time", 0), 1) if run.get("execution_time") else 0,
                    "cost": round(run.get("total_cost", 0), 4) if run.get("total_cost") else 0
                }
                if run.get("completed_at"):
                    processed_run["completed_at"] = run["completed_at"]
            processed_runs.append(processed_run)

        return {
            "runs": processed_runs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": pagination_info.get("total", len(runs)),
                "total_pages": pagination_info.get("total_pages", 1),
                "has_next": pagination_info.get("has_next", False),
                "has_prev": pagination_info.get("has_prev", False)
            }
        }

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list runs: {str(e)}")

        return {
            "runs": [],
            "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0, "has_next": False, "has_prev": False},
            "error": str(e),
            "message": "Failed to retrieve workflow runs"
        }


@mcp.tool()
async def get_workflow_status(
    run_id: str, detailed: bool = True, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    📈 Get detailed status of specific workflow run with progress tracking

    Args:
        run_id: Unique identifier for the workflow run
        detailed: Get enhanced detailed information (default: True)
        ctx: MCP context for progress reporting

    Returns:
        Detailed status information including progress, metrics, and results
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        status_response = await client.get_workflow_status(run_id, detailed=detailed)

        # Extract key information for context reporting
        status = status_response.get("status", "unknown")
        turns = status_response.get("turns", 0) or status_response.get("current_turns", 0) or 0
        workflow_name = status_response.get("workflow_name", "unknown")
        
        # Calculate progress if we have turn information
        if ctx and turns > 0:
            # Try to get max_turns from the response, otherwise use default
            max_turns = status_response.get("max_turns", 30)
            progress_ratio = min(turns / max_turns, 1.0) if max_turns > 0 else 0
            
            try:
                await ctx.report_progress(progress=turns, total=max_turns)
            except Exception:
                # Context reporting might not be available, continue without it
                pass

            ctx.info(f"📈 Workflow {workflow_name} ({run_id}): {status}")
            ctx.info(f"📊 Progress: {turns} turns completed ({progress_ratio:.1%})")
            
            # Report current phase if available
            current_phase = status_response.get("current_phase")
            if current_phase:
                ctx.info(f"🔄 Current phase: {current_phase}")
            
            # Report cache efficiency if available
            cache_efficiency = status_response.get("cache_efficiency")
            if cache_efficiency:
                ctx.info(f"💾 Cache efficiency: {cache_efficiency}%")
            
            # Report tools being used if available
            tools_used = status_response.get("tools_used", [])
            if tools_used:
                ctx.info(f"🔧 Tools used: {', '.join(tools_used)}")
            
            if status == "completed":
                ctx.info("✅ Workflow completed successfully")
            elif status == "running":
                ctx.info("⏳ Workflow is still running...")
            elif status == "failed":
                ctx.error(f"❌ Workflow failed: {status_response.get('error', 'Unknown error')}")

        # Return the full comprehensive response from the API
        # Make a copy to avoid modifying the original
        comprehensive_response = dict(status_response)
        
        # Ensure we have the run_id in the response
        comprehensive_response["run_id"] = run_id
        
        # Add backward compatibility fields if they're missing
        if "current_turns" not in comprehensive_response and turns > 0:
            comprehensive_response["current_turns"] = turns
        
        # Normalize turns field for backward compatibility
        if "turns" not in comprehensive_response and "current_turns" in comprehensive_response:
            comprehensive_response["turns"] = comprehensive_response["current_turns"]
        elif "current_turns" not in comprehensive_response and "turns" in comprehensive_response:
            comprehensive_response["current_turns"] = comprehensive_response["turns"]

        return comprehensive_response

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to get status for run {run_id}: {str(e)}")

        return {
            "error": str(e),
            "run_id": run_id,
            "message": f"Failed to retrieve status for run {run_id}",
        }


@mcp.tool()
async def kill_workflow(
    run_id: str, force: bool = False, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    ⚡ Emergency termination of a running Claude Code workflow

    Args:
        run_id: Unique identifier for the workflow run to terminate
        force: If True, force kill immediately. If False, graceful shutdown (default: False)
        ctx: MCP context for logging

    Returns:
        Kill confirmation with cleanup status and audit information
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    if ctx:
        kill_type = "force kill" if force else "graceful shutdown"
        ctx.info(f"⚡ Initiating {kill_type} for workflow run: {run_id}")

    try:
        kill_response = await client.kill_workflow(run_id, force)

        if ctx:
            status = kill_response.get("status", "unknown")
            if status == "killed":
                ctx.info(f"✅ Workflow {run_id} terminated successfully")
            elif status == "not_found":
                ctx.warning(f"⚠️ Workflow {run_id} not found or already completed")
            else:
                ctx.info(f"📋 Kill request processed: {status}")

        return {
            "status": kill_response.get("status", "processed"),
            "run_id": run_id,
            "force": force,
            "killed_at": kill_response.get("killed_at"),
            "cleanup_status": kill_response.get("cleanup_status", "completed"),
            "message": kill_response.get("message", f"Kill request processed for run {run_id}"),
            "audit_info": kill_response.get("audit_info", {}),
        }

    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to kill workflow {run_id}: {str(e)}")

        return {
            "status": "error",
            "run_id": run_id,
            "force": force,
            "error": str(e),
            "message": f"Failed to kill workflow {run_id}: {str(e)}",
        }


@mcp.tool()
async def get_health_status(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    🩺 Check health status of the Automagik Agents Platform
    
    Returns comprehensive system health information for orchestration planning:
    - System status (healthy/degraded/error)
    - Active workflow count and resource usage
    - Service availability and performance metrics
    - Last error information if any
    
    Args:
        ctx: MCP context for logging
        
    Returns:
        System health data with status, metrics, and availability info
    """
    global client
    if not client:
        raise ValueError("Tool not configured")
    
    if ctx:
        ctx.info("🩺 Checking Automagik Agents Platform health status")
    
    try:
        health_response = await client.get_health_status()
        
        # Extract key health metrics for context reporting
        status = health_response.get("status", "unknown")
        active_workflows = health_response.get("workflows", {}).get("active_count", 0)
        
        if ctx:
            ctx.info(f"🩺 System status: {status}")
            if active_workflows > 0:
                ctx.info(f"⚡ Active workflows: {active_workflows}")
            
            # Report any concerning metrics
            system_info = health_response.get("system", {})
            cpu_usage = system_info.get("cpu_usage", 0)
            memory_usage = system_info.get("memory_usage", 0)
            
            if cpu_usage > 80:
                ctx.warning(f"⚠️ High CPU usage: {cpu_usage}%")
            if memory_usage > 80:
                ctx.warning(f"⚠️ High memory usage: {memory_usage}%")
            
            if status == "healthy":
                ctx.info("✅ System is healthy and ready for orchestration")
            elif status == "degraded":
                ctx.warning("⚠️ System is degraded - proceed with caution")
            elif status == "error":
                ctx.error("❌ System has errors - investigate before orchestration")
        
        # Ensure we have the timestamp in the response
        if "timestamp" not in health_response:
            from datetime import datetime
            health_response["timestamp"] = datetime.now().isoformat() + "Z"
        
        return health_response
        
    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to check health status: {str(e)}")
        
        # Return error status with graceful degradation
        from datetime import datetime
        return {
            "status": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat() + "Z",
            "message": f"Health check failed: {str(e)}",
            "recommendation": "Proceed with caution or retry health check",
            "system": {"available": False},
            "workflows": {"active_count": 0, "accessible": False},
            "services": {"health_endpoint": "unavailable"}
        }


@mcp.tool()
async def list_runs_by_status(
    status: str, 
    limit: int = 10, 
    ctx: Optional[Context] = None
) -> List[Dict[str, Any]]:
    """
    🔍 Query workflow runs by status for orchestration decisions
    
    Filters workflow runs by their execution status, useful for:
    - Finding running workflows to coordinate resources
    - Analyzing failed workflows for retry strategies
    - Checking completed workflows for success patterns
    
    Args:
        status: Status to filter by (running, completed, failed, pending)
        limit: Maximum number of runs to return (default: 10)
        ctx: MCP context for logging
    
    Returns:
        List of workflow runs matching the status with enhanced orchestration data
    """
    global client
    if not client:
        raise ValueError("Tool not configured")
    
    try:
        # Get runs with enhanced data and filter by status
        all_runs_response = await client.list_runs({
            "page_size": limit * 3,  # Get more to filter from
            "detailed": True,  # Include full orchestration data
            "sort_by": "started_at",
            "sort_order": "desc"
        })
        
        all_runs = all_runs_response.get("runs", []) if isinstance(all_runs_response, dict) else []
        
        # Filter by status
        filtered_runs = [
            run for run in all_runs 
            if run.get("status", "").lower() == status.lower()
        ][:limit]
        
        if ctx:
            ctx.info(f"🔍 Found {len(filtered_runs)} workflows with status '{status}'")
            
            # Provide insights for orchestration
            if status.lower() == "running" and len(filtered_runs) > 2:
                ctx.warning(f"⚠️ {len(filtered_runs)} workflows running - consider resource coordination")
            elif status.lower() == "failed" and len(filtered_runs) > 0:
                ctx.info(f"📊 {len(filtered_runs)} failed workflows available for analysis")
            elif status.lower() == "completed":
                ctx.info(f"✅ {len(filtered_runs)} completed workflows for pattern analysis")
        
        return filtered_runs
        
    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list runs by status '{status}': {str(e)}")
        
        return [{
            "error": str(e),
            "status": status,
            "message": f"Failed to retrieve runs with status '{status}'"
        }]


@mcp.tool()
async def list_runs_by_workflow(
    workflow_name: str, 
    limit: int = 10, 
    ctx: Optional[Context] = None
) -> List[Dict[str, Any]]:
    """
    🔍 Query workflow runs by workflow type for performance analysis
    
    Filters workflow runs by their workflow type, useful for:
    - Analyzing performance patterns for specific workflows
    - Checking success rates before starting similar workflows
    - Identifying workflow-specific issues or bottlenecks
    
    Args:
        workflow_name: Workflow type to filter by (builder, tester, analyzer, etc.)
        limit: Maximum number of runs to return (default: 10)
        ctx: MCP context for logging
    
    Returns:
        List of runs for the specified workflow with performance metrics
    """
    global client
    if not client:
        raise ValueError("Tool not configured")
    
    try:
        # Use API filtering if available
        runs_response = await client.list_runs({
            "workflow_name": workflow_name,  # API-level filter
            "page_size": limit,
            "detailed": True,  # Include orchestration data
            "sort_by": "started_at",
            "sort_order": "desc"
        })
        
        runs = runs_response.get("runs", []) if isinstance(runs_response, dict) else []
        
        if ctx:
            ctx.info(f"🔍 Found {len(runs)} recent '{workflow_name}' workflow runs")
            
            if runs:
                # Calculate performance insights
                completed_runs = [r for r in runs if r.get("status") == "completed"]
                failed_runs = [r for r in runs if r.get("status") == "failed"]
                running_runs = [r for r in runs if r.get("status") == "running"]
                
                if completed_runs:
                    success_rate = (len(completed_runs) / len(runs)) * 100
                    ctx.info(f"📊 Success rate: {success_rate:.1f}% ({len(completed_runs)}/{len(runs)})")
                    
                    # Average execution time for completed runs
                    avg_time = sum(r.get("execution_time", 0) for r in completed_runs) / len(completed_runs)
                    if avg_time > 0:
                        ctx.info(f"⏱️ Average execution time: {avg_time:.1f} seconds")
                
                if failed_runs:
                    ctx.warning(f"⚠️ {len(failed_runs)} recent failures - investigate patterns")
                
                if running_runs:
                    ctx.info(f"⚡ {len(running_runs)} currently running")
        
        return runs
        
    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list runs for workflow '{workflow_name}': {str(e)}")
        
        return [{
            "error": str(e),
            "workflow_name": workflow_name,
            "message": f"Failed to retrieve runs for workflow '{workflow_name}'"
        }]


@mcp.tool()
async def list_runs_by_time_range(
    start_time: str, 
    end_time: str, 
    limit: int = 50, 
    ctx: Optional[Context] = None
) -> List[Dict[str, Any]]:
    """
    🔍 Query workflow runs within time range for historical analysis
    
    Filters workflow runs by execution time range, useful for:
    - Analyzing activity patterns and system load
    - Historical performance review and trend analysis
    - Identifying peak usage periods and resource optimization
    
    Args:
        start_time: Start time in ISO format (2025-01-20T00:00:00Z)
        end_time: End time in ISO format (2025-01-20T23:59:59Z)
        limit: Maximum number of runs to return (default: 50)
        ctx: MCP context for logging
    
    Returns:
        List of workflow runs within time range with activity patterns
    """
    from datetime import datetime
    
    global client
    if not client:
        raise ValueError("Tool not configured")
    
    try:
        # Parse time range
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Get runs from API (may need to fetch more and filter)
        all_runs_response = await client.list_runs({
            "page_size": limit * 2,  # Get extra to filter by time
            "detailed": True,  # Include orchestration data
            "sort_by": "started_at",
            "sort_order": "desc"
        })
        
        all_runs = all_runs_response.get("runs", []) if isinstance(all_runs_response, dict) else []
        
        # Filter by time range
        filtered_runs = []
        for run in all_runs:
            run_time_str = run.get("started_at", "")
            if run_time_str:
                try:
                    run_time = datetime.fromisoformat(run_time_str.replace('Z', '+00:00'))
                    if start_dt <= run_time <= end_dt:
                        filtered_runs.append(run)
                except ValueError:
                    # Skip runs with invalid timestamps
                    continue
        
        # Limit results
        filtered_runs = filtered_runs[:limit]
        
        if ctx:
            duration = end_dt - start_dt
            ctx.info(f"🔍 Found {len(filtered_runs)} workflow runs in {duration.days} day(s)")
            
            if filtered_runs:
                # Activity analysis for orchestration insights
                workflow_types = {}
                status_counts = {}
                total_cost = 0
                total_execution_time = 0
                
                for run in filtered_runs:
                    # Workflow type distribution
                    wf_type = run.get("workflow_name", "unknown")
                    workflow_types[wf_type] = workflow_types.get(wf_type, 0) + 1
                    
                    # Status distribution
                    status = run.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Cost and time aggregation
                    total_cost += run.get("total_cost", 0)
                    total_execution_time += run.get("execution_time", 0)
                
                if total_cost > 0:
                    ctx.info(f"💰 Total cost: ${total_cost:.2f}")
                
                if total_execution_time > 0:
                    avg_time = total_execution_time / len(filtered_runs)
                    ctx.info(f"⏱️ Average execution time: {avg_time:.1f} seconds")
                
                ctx.info(f"📊 Workflow types: {dict(workflow_types)}")
                ctx.info(f"📈 Status distribution: {dict(status_counts)}")
                
                # Peak activity detection
                if len(filtered_runs) / max(duration.days, 1) > 10:
                    ctx.warning("⚠️ High activity period detected - monitor system resources")
        
        return filtered_runs
        
    except ValueError as ve:
        if ctx:
            ctx.error(f"💥 Invalid time format: {str(ve)}")
        
        return [{
            "error": str(ve),
            "start_time": start_time,
            "end_time": end_time,
            "message": "Invalid time format - use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
        }]
        
    except Exception as e:
        if ctx:
            ctx.error(f"💥 Failed to list runs by time range: {str(e)}")
        
        return [{
            "error": str(e),
            "start_time": start_time,
            "end_time": end_time,
            "message": f"Failed to retrieve runs for time range: {str(e)}"
        }]


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "automagik-workflows",
        "version": "1.2.0",
        "description": "Smart Claude workflow orchestration with GENIE orchestration features, health monitoring, advanced filtering, and enhanced status tracking",
        "author": "Namastex Labs",
        "category": "workflow",
        "tags": ["claude", "workflow", "automation", "orchestration", "genie", "health", "filtering", "monitoring"],
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
