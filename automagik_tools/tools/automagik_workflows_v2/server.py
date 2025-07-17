"""
FastMCP server for Automagik Workflows V2
Single super-tool with dynamic discovery, elicitation, and real-time coordination
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from datetime import datetime

from fastmcp import FastMCP, Context

from .config import AutomagikWorkflowsV2Config
from .client import AutomagikWorkflowsClient
from .session_manager import SessionManager
from .progress_tracker import ProgressTracker
from .models import (
    WorkflowName, WorkflowMode, WorkflowRequest, WorkflowStatus,
    ElicitationRequest, ElicitationResponse
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
server = FastMCP(
    "automagik-workflows-v2",
    instructions="""
Revolutionary streaming workflow orchestration with dynamic discovery and elicitation.

🚀 Single super-tool approach with intelligent parameter collection
📊 Real-time progress streaming via FastMCP Context
🔍 Dynamic workflow discovery with enum-based selection
💾 Session management with ID-based continuation and epic tracking
🔄 Self-healing connectivity with automatic retry logic
⚡ Elicitation-powered interaction for seamless UX

Supports all workflow modes: implement, research, buddy, throwaway
"""
)

# Global instances (initialized in create_server)
client: Optional[AutomagikWorkflowsClient] = None
session_manager: Optional[SessionManager] = None
progress_tracker: Optional[ProgressTracker] = None
config: Optional[AutomagikWorkflowsV2Config] = None

@dataclass
class ElicitParametersData:
    """Dataclass for eliciting workflow parameters"""
    repository_url: Optional[str] = None
    git_branch: Optional[str] = None
    epic_name: Optional[str] = None
    max_turns: Optional[int] = None
    auto_merge: Optional[bool] = None
    persistent: Optional[bool] = None


@server.tool()
async def orchestrate_workflow(
    ctx: Context,
    message: str,
    workflow_name: Optional[WorkflowName] = None,
    epic_name: Optional[str] = None,
    session_id: Optional[str] = None,
    repository_url: Optional[str] = None,
    git_branch: Optional[str] = None,
    max_turns: Optional[int] = None,
    mode: Optional[WorkflowMode] = None,
    auto_merge: Optional[bool] = None,
    persistent: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Orchestrate workflows with intelligent parameter discovery and elicitation.
    
    This is the primary tool for workflow orchestration with:
    - Dynamic workflow discovery and enum-based selection
    - Elicitation-powered parameter collection
    - Real-time progress streaming
    - Session management with epic name tracking
    - Self-healing connectivity
    """
    
    try:
        # Ensure client is healthy
        await client.ensure_healthy(force_check=True)
        if not client.is_healthy:
            return {
                "status": "error",
                "error": "Automagik Workflows API is not accessible. Check connectivity and API key.",
                "health_check": False
            }
        
        await ctx.report_progress(0, 4, "Initializing workflow orchestration...")
        
        # Step 1: Discover available workflows if not specified
        if workflow_name is None:
            await ctx.report_progress(1, 4, "Discovering available workflows...")
            
            discovery = await client.discover_workflows()
            available_workflows = discovery.get("available_workflows", [])
            
            if not available_workflows:
                return {
                    "status": "error",
                    "error": "No workflows available. Check API connectivity.",
                    "discovery": discovery
                }
            
            # Use elicitation to get workflow selection  
            workflow_selection = await ctx.elicit(
                message=f"Select a workflow type for the task: '{message}'",
                response_type=available_workflows  # list[str] format
            )
            
            if workflow_selection.action == "accept":
                selected_workflow = workflow_selection.data
                workflow_name = WorkflowName(selected_workflow)
            else:
                return {
                    "status": "cancelled",
                    "message": "Workflow selection was cancelled or declined",
                    "action": workflow_selection.action
                }
        
        await ctx.report_progress(2, 4, f"Selected workflow: {workflow_name.value}")
        
        # Step 2: Intelligent mode detection and parameter elicitation
        detected_mode = _detect_workflow_mode(message, repository_url, mode)
        
        # Collect missing parameters via elicitation
        elicitation_request = ElicitationRequest(
            workflow_name=workflow_name,
            message=message,
            mode=detected_mode,
            missing_parameters=_identify_missing_parameters(
                detected_mode, repository_url, git_branch, epic_name, max_turns
            )
        )
        
        if elicitation_request.missing_parameters:
            await ctx.report_progress(2, 4, "Collecting additional parameters...")
            
            elicited_params = await _elicit_parameters(ctx, elicitation_request)
            
            # Apply elicited parameters
            repository_url = repository_url or elicited_params.repository_url
            git_branch = git_branch or elicited_params.git_branch
            epic_name = epic_name or elicited_params.epic_name
            max_turns = max_turns or elicited_params.max_turns
            auto_merge = auto_merge if auto_merge is not None else elicited_params.auto_merge
            persistent = persistent if persistent is not None else elicited_params.persistent
            mode = elicited_params.workflow_mode
        
        # Step 3: Handle session continuation
        final_session_id = session_id
        if session_id:
            await ctx.report_progress(3, 4, f"Validating session continuation: {session_id}")
            
            if not await session_manager.validate_session_for_continuation(session_id):
                return {
                    "status": "error", 
                    "error": f"Session {session_id} cannot be continued",
                    "session_validation": False
                }
        
        # Step 4: Build and execute workflow request
        await ctx.report_progress(3, 4, "Executing workflow...")
        
        workflow_request = WorkflowRequest(
            message=message,
            workflow_name=workflow_name,
            epic_name=epic_name,
            session_id=final_session_id,
            max_turns=max_turns,
            repository_url=repository_url,
            git_branch=git_branch,
            persistent=_determine_persistence(mode, persistent),
            auto_merge=_determine_auto_merge(mode, auto_merge),
            temp_workspace=_determine_temp_workspace(mode),
            user_id=config.user_id,
            timeout=config.timeout
        )
        
        # Execute workflow
        response = await client.run_workflow(workflow_request)
        
        await ctx.report_progress(4, 4, f"Workflow started: {response.run_id}")
        
        # Start real-time progress tracking
        progress_task = asyncio.create_task(
            progress_tracker.track_workflow_progress(
                response.run_id,
                ctx,
                timeout_minutes=config.timeout // 60
            )
        )
        
        # Return immediate response with tracking promise
        result = {
            "status": "started",
            "run_id": response.run_id,
            "session_id": response.session_id,
            "workflow_name": workflow_name.value,
            "epic_name": epic_name,
            "mode": mode.value if mode else "auto",
            "started_at": response.started_at.isoformat(),
            "tracking": "enabled",
            "progress_monitoring": True
        }
        
        # Wait for completion and get final status
        try:
            final_status = await progress_task
            result.update({
                "final_status": final_status.status.value,
                "completed_at": final_status.completed_at.isoformat() if final_status.completed_at else None,
                "workspace_path": final_status.workspace_path,
                "error_message": final_status.error_message
            })
        except Exception as e:
            logger.error(f"Progress tracking failed: {e}")
            result.update({
                "tracking_error": str(e),
                "progress_monitoring": False
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow orchestration failed: {e}")
        await ctx.report_progress(0, 1, f"Error: {str(e)[:100]}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@server.tool()
async def continue_session(
    ctx: Context,
    session_id: str,
    message: str,
    workflow_name: Optional[WorkflowName] = None
) -> Dict[str, Any]:
    """Continue an existing workflow session by ID."""
    
    try:
        await ctx.report_progress(0, 2, f"Continuing session: {session_id}")
        
        # Validate session
        if not await session_manager.validate_session_for_continuation(session_id):
            return {
                "status": "error",
                "error": f"Session {session_id} cannot be continued"
            }
        
        # Get session context
        session_context = await session_manager.get_session_context_summary(session_id)
        
        # Use orchestrate_workflow with session_id
        result = await orchestrate_workflow(
            message=message,
            workflow_name=workflow_name or WorkflowName(session_context.get("workflow_name", "implement")),
            session_id=session_id,
            ctx=ctx
        )
        
        await ctx.report_progress(2, 2, "Session continuation initiated")
        
        return {
            **result,
            "continued_from": session_id,
            "previous_context": session_context
        }
        
    except Exception as e:
        logger.error(f"Session continuation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "session_id": session_id
        }


@server.tool()
async def send_workflow_feedback(
    ctx: Context,
    run_id: str,
    feedback: str,
    message_type: Literal["user", "system"] = "user"
) -> Dict[str, Any]:
    """Send real-time feedback to a running workflow."""
    
    try:
        await ctx.report_progress(0, 1, f"Sending feedback to workflow: {run_id}")
        
        result = await client.add_feedback(run_id, feedback, message_type)
        
        await ctx.report_progress(1, 1, f"Feedback sent: {feedback[:50]}...")
        
        return {
            "status": "success",
            "run_id": run_id,
            "feedback_sent": feedback,
            "message_type": message_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send feedback: {e}")
        return {
            "status": "error",
            "error": str(e),
            "run_id": run_id
        }


@server.tool()
async def get_session_info(
    ctx: Context,
    session_id: Optional[str] = None,
    epic_name: Optional[str] = None,
    show_recent: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """Get session information, epic tracking, or recent sessions."""
    
    try:
        await ctx.report_progress(0, 1, "Retrieving session information...")
        
        if session_id:
            # Get specific session
            context = await session_manager.get_session_context_summary(session_id)
            return {
                "type": "single_session",
                "session": context
            }
        
        elif epic_name:
            # Get sessions for epic
            sessions = await session_manager.find_sessions_by_epic(epic_name)
            return {
                "type": "epic_sessions",
                "epic_name": epic_name,
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "workflow_name": s.workflow_name,
                        "status": s.status.value,
                        "started_at": s.started_at.isoformat()
                    } for s in sessions
                ],
                "count": len(sessions)
            }
        
        elif show_recent:
            # Get recent sessions
            sessions = await session_manager.get_recent_sessions(limit)
            return {
                "type": "recent_sessions",
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "epic_name": s.session_name,
                        "workflow_name": s.workflow_name,
                        "status": s.status.value,
                        "started_at": s.started_at.isoformat()
                    } for s in sessions
                ],
                "count": len(sessions)
            }
        
        else:
            # Get summary statistics
            stats = session_manager.get_session_count()
            epic_names = session_manager.get_epic_names()
            active_sessions = await session_manager.get_active_sessions()
            
            return {
                "type": "summary",
                "statistics": stats,
                "epic_names": epic_names,
                "active_sessions": [
                    {
                        "session_id": s.session_id,
                        "epic_name": s.session_name,
                        "workflow_name": s.workflow_name,
                        "status": s.status.value
                    } for s in active_sessions
                ],
                "tracking_count": progress_tracker.get_active_tracking_count()
            }
        
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@server.tool()
async def clear_workflow_session(
    ctx: Context,
    run_id: str
) -> Dict[str, Any]:
    """Clear/cleanup a workflow session."""
    
    try:
        await ctx.report_progress(0, 1, f"Clearing session: {run_id}")
        
        result = await client.clear_session(run_id)
        
        # Clear from session cache
        await session_manager.clear_session_cache()
        
        await ctx.report_progress(1, 1, "Session cleared successfully")
        
        return {
            "status": "success",
            "run_id": run_id,
            "cleared": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        return {
            "status": "error",
            "error": str(e),
            "run_id": run_id
        }


@server.tool()
async def get_workflow_health(ctx: Context) -> Dict[str, Any]:
    """Check workflow system health and connectivity."""
    
    try:
        await ctx.report_progress(0, 1, "Checking system health...")
        
        health = await client.health_check()
        discovery = await client.discover_workflows()
        
        await ctx.report_progress(1, 1, f"Health check complete: {health.status}")
        
        return {
            "status": "success",
            "health": {
                "api_status": health.status,
                "timestamp": health.timestamp.isoformat(),
                "version": health.version,
                "environment": health.environment,
                "uptime": health.uptime
            },
            "capabilities": discovery,
            "client_healthy": client.is_healthy,
            "tracking_active": progress_tracker.get_active_tracking_count(),
            "session_cache_size": session_manager.get_session_count()["total"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "client_healthy": False,
            "timestamp": datetime.now().isoformat()
        }


# Helper functions

def _detect_workflow_mode(message: str, repository_url: Optional[str], mode: Optional[WorkflowMode]) -> WorkflowMode:
    """Detect workflow mode based on message and parameters."""
    if mode:
        return mode
    
    if repository_url:
        return WorkflowMode.CODE
    
    # Simple heuristics
    message_lower = message.lower()
    if any(word in message_lower for word in ["research", "analyze", "study", "investigate", "review"]):
        return WorkflowMode.RESEARCH
    elif any(word in message_lower for word in ["implement", "build", "create", "develop", "code"]):
        return WorkflowMode.CODE
    else:
        return WorkflowMode.RESEARCH  # Default to research for analysis tasks


def _identify_missing_parameters(
    mode: WorkflowMode,
    repository_url: Optional[str],
    git_branch: Optional[str], 
    epic_name: Optional[str],
    max_turns: Optional[int]
) -> List[str]:
    """Identify parameters that need elicitation."""
    missing = []
    
    if mode == WorkflowMode.CODE and not repository_url:
        missing.append("repository_url")
    
    if mode == WorkflowMode.CODE and repository_url and not git_branch:
        missing.append("git_branch")
    
    if not epic_name:
        missing.append("epic_name")
    
    return missing


async def _elicit_parameters(ctx: Context, request: ElicitationRequest) -> ElicitationResponse:
    """Elicit missing parameters from user."""
    
    # Build elicitation schema based on missing parameters
    schema_properties = {}
    required_fields = []
    
    if "repository_url" in request.missing_parameters:
        schema_properties["repository_url"] = {
            "type": "string",
            "description": "GitHub repository URL (e.g., https://github.com/user/repo.git)"
        }
        required_fields.append("repository_url")
    
    if "git_branch" in request.missing_parameters:
        schema_properties["git_branch"] = {
            "type": "string", 
            "description": "Git branch to work on (e.g., main, feature/auth, develop)"
        }
        required_fields.append("git_branch")
    
    if "epic_name" in request.missing_parameters:
        schema_properties["epic_name"] = {
            "type": "string",
            "description": "Epic name for tracking this workflow (e.g., auth-system, user-dashboard)"
        }
        required_fields.append("epic_name")
    
    # Optional parameters
    schema_properties.update({
        "max_turns": {
            "type": "integer",
            "description": "Maximum conversation turns (optional, 1-200)",
            "minimum": 1,
            "maximum": 200
        },
        "auto_merge": {
            "type": "boolean",
            "description": "Automatically merge changes to main branch"
        },
        "persistent": {
            "type": "boolean", 
            "description": "Keep workspace after completion"
        }
    })
    
    schema = {
        "type": "object",
        "properties": schema_properties,
        "required": required_fields
    }
    
    prompt = f"Please provide additional parameters for {request.workflow_name.value} workflow: '{request.message}'"
    if request.mode:
        prompt += f" (Mode: {request.mode.value})"
    
    result = await ctx.elicit(
        message=prompt,
        response_type=ElicitParametersData
    )
    
    if result.action == "accept":
        data = result.data
        return ElicitationResponse(
            repository_url=data.repository_url,
            git_branch=data.git_branch,
            epic_name=data.epic_name,
            max_turns=data.max_turns,
            workflow_mode=request.mode or WorkflowMode.RESEARCH,
            auto_merge=data.auto_merge,
            persistent=data.persistent
        )
    else:
        # Return empty response if user cancels
        return ElicitationResponse(
            workflow_mode=request.mode or WorkflowMode.RESEARCH
        )


def _determine_persistence(mode: Optional[WorkflowMode], persistent: Optional[bool]) -> bool:
    """Determine workspace persistence based on mode."""
    if persistent is not None:
        return persistent
    
    if mode == WorkflowMode.THROWAWAY:
        return False
    elif mode in [WorkflowMode.CODE, WorkflowMode.BUDDY]:
        return True
    else:
        return True  # Default to persistent


def _determine_auto_merge(mode: Optional[WorkflowMode], auto_merge: Optional[bool]) -> bool:
    """Determine auto-merge based on mode."""
    if auto_merge is not None:
        return auto_merge
    
    return mode == WorkflowMode.BUDDY


def _determine_temp_workspace(mode: Optional[WorkflowMode]) -> bool:
    """Determine if temporary workspace should be used."""
    return mode == WorkflowMode.RESEARCH


def create_server(tool_config: Optional[AutomagikWorkflowsV2Config] = None) -> FastMCP:
    """Create and configure the FastMCP server."""
    global client, session_manager, progress_tracker, config
    
    # Initialize configuration
    config = tool_config or AutomagikWorkflowsV2Config()
    
    # Initialize components
    client = AutomagikWorkflowsClient(config)
    session_manager = SessionManager(client)
    progress_tracker = ProgressTracker(client, config.polling_interval)
    
    logger.info("Automagik Workflows V2 server initialized")
    
    return server