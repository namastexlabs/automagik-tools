"""
Pydantic models for Automagik Workflows V2 API
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowMode(str, Enum):
    """Available workflow execution modes."""
    RESEARCH = "research"  # temp_workspace: true
    CODE = "code"         # repository_url + git_branch  
    BUDDY = "buddy"       # persistent: true + auto_merge: true
    THROWAWAY = "throwaway"  # persistent: false


class WorkflowName(str, Enum):
    """Available workflow types."""
    BRAIN = "brain"
    BUILDER = "builder"
    GENIE = "genie"
    SHIPPER = "shipper"
    SURGEON = "surgeon"
    GUARDIAN = "guardian"
    LINA = "lina"
    FLASHINHO_THINKER = "flashinho_thinker"
    CLAUDE = "claude"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowRequest(BaseModel):
    """Request payload for workflow execution."""
    message: str = Field(description="Task description for Claude")
    workflow_name: WorkflowName = Field(description="Type of workflow to execute")
    epic_name: Optional[str] = Field(None, description="Epic name for orchestration (stored as session_name)")
    session_id: Optional[str] = Field(None, description="Continue previous session by ID")
    max_turns: Optional[int] = Field(None, description="Maximum conversation turns (1-200)")
    
    # Mode-specific parameters
    repository_url: Optional[str] = Field(None, description="External repository URL for code mode")
    git_branch: Optional[str] = Field(None, description="Git branch for code mode")
    persistent: Optional[bool] = Field(True, description="Keep workspace after completion")
    auto_merge: Optional[bool] = Field(False, description="Auto-merge to main branch")
    temp_workspace: Optional[bool] = Field(False, description="Use temporary isolated workspace")
    
    # Fixed parameters (set by tool)
    user_id: Optional[str] = Field(None, description="User identifier (set from config)")
    timeout: Optional[int] = Field(14400, description="Execution timeout in seconds")


class WorkflowResponse(BaseModel):
    """Response from workflow execution API."""
    run_id: str = Field(description="Unique workflow run identifier")
    session_id: str = Field(description="Session identifier for continuation")
    status: WorkflowStatus = Field(description="Current workflow status")
    started_at: datetime = Field(description="Workflow start timestamp")
    message: str = Field(description="Status or confirmation message")


class WorkflowStatusResponse(BaseModel):
    """Response from workflow status check."""
    run_id: str = Field(description="Workflow run identifier")
    session_id: str = Field(description="Session identifier")
    status: WorkflowStatus = Field(description="Current status")
    current_turn: Optional[int] = Field(None, description="Current conversation turn")
    max_turns: Optional[int] = Field(None, description="Maximum turns configured")
    current_action: Optional[str] = Field(None, description="Current workflow action description")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    workspace_path: Optional[str] = Field(None, description="Workspace directory path")
    git_info: Optional[Dict[str, Any]] = Field(None, description="Git repository information")


class WorkflowRun(BaseModel):
    """Individual workflow run information."""
    run_id: str = Field(description="Unique run identifier")
    session_id: str = Field(description="Session identifier")
    session_name: Optional[str] = Field(None, description="Human-readable session name (epic_name)")
    workflow_name: str = Field(description="Type of workflow")
    status: WorkflowStatus = Field(description="Current status")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    message: str = Field(description="Original task message")
    user_id: Optional[str] = Field(None, description="User identifier")


class WorkflowRunsResponse(BaseModel):
    """Response from list runs API."""
    runs: List[WorkflowRun] = Field(description="List of workflow runs")
    total: int = Field(description="Total number of runs")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")


class HealthResponse(BaseModel):
    """Response from health check API."""
    status: str = Field(description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(description="Health check timestamp")
    version: Optional[str] = Field(None, description="API version")
    environment: Optional[str] = Field(None, description="Environment name")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")
    workflows: Optional[Dict[str, bool]] = Field(None, description="Available workflows status")


class WorkflowDiscovery(BaseModel):
    """Discovered workflow capabilities."""
    available_workflows: List[WorkflowName] = Field(description="Available workflow types")
    health_status: str = Field(description="API health status")
    api_version: Optional[str] = Field(None, description="API version")
    capabilities: List[str] = Field(default_factory=list, description="API capabilities")


class ElicitationRequest(BaseModel):
    """Request for parameter elicitation."""
    workflow_name: WorkflowName = Field(description="Selected workflow type")
    message: str = Field(description="Task description")
    mode: Optional[WorkflowMode] = Field(None, description="Detected workflow mode")
    missing_parameters: List[str] = Field(description="Parameters that need elicitation")


class ElicitationResponse(BaseModel):
    """Response with elicited parameters."""
    repository_url: Optional[str] = Field(None, description="Selected repository URL")
    git_branch: Optional[str] = Field(None, description="Selected git branch") 
    epic_name: Optional[str] = Field(None, description="Epic name for tracking")
    max_turns: Optional[int] = Field(None, description="Turn limit preference")
    workflow_mode: WorkflowMode = Field(description="Confirmed workflow mode")
    auto_merge: Optional[bool] = Field(None, description="Auto-merge preference")
    persistent: Optional[bool] = Field(None, description="Workspace persistence preference")