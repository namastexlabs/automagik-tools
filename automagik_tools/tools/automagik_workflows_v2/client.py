"""
HTTP client for Automagik Workflows V2 API
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import uuid
from datetime import datetime

from .config import AutomagikWorkflowsV2Config
from .models import (
    WorkflowRequest, WorkflowResponse, WorkflowStatusResponse, 
    WorkflowRunsResponse, HealthResponse, WorkflowName
)

logger = logging.getLogger(__name__)


class AutomagikWorkflowsClient:
    """HTTP client for Automagik Workflows API with self-healing capabilities."""
    
    def __init__(self, config: AutomagikWorkflowsV2Config):
        self.config = config
        self.base_url = config.api_base_url.rstrip("/")
        self.session: Optional[httpx.AsyncClient] = None
        self._healthy = False
        self._last_health_check = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _ensure_session(self):
        """Ensure HTTP session is initialized."""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "x-api-key": self.config.api_key,
                    "Content-Type": "application/json"
                }
            )
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling."""
        await self._ensure_session()
        
        if retries is None:
            retries = self.config.max_retries
            
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                if method.upper() == "GET":
                    response = await self.session.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.session.post(url, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.ConnectError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == retries:
                    self._healthy = False
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                if e.response.status_code >= 500 and attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == retries:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> HealthResponse:
        """Check API health status."""
        try:
            response_data = await self._make_request("GET", "/api/v1/workflows/claude-code/health")
            health = HealthResponse(**response_data)
            self._healthy = (health.status == "healthy")
            self._last_health_check = datetime.now()
            return health
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._healthy = False
            raise
    
    def _get_user_id(self) -> str:
        """Get or generate a valid UUID for user_id."""
        # Try to use configured user_id if it's a valid UUID
        try:
            if self.config.user_id:
                # Validate that it's a valid UUID
                uuid.UUID(self.config.user_id)
                return self.config.user_id
        except (ValueError, AttributeError):
            pass
        
        # Generate a new UUID if config user_id is not valid
        return str(uuid.uuid4())
    
    async def discover_workflows(self) -> Dict[str, Any]:
        """Discover available workflows and capabilities."""
        health = await self.health_check()
        
        # Extract available workflows from health response
        available_workflows = []
        if health.workflows:
            available_workflows = [
                name for name, available in health.workflows.items() 
                if available
            ]
        
        # Fallback to known workflows if none discovered
        if not available_workflows:
            available_workflows = [w.value for w in WorkflowName]
        
        return {
            "available_workflows": available_workflows,
            "health_status": health.status,
            "api_version": health.version,
            "capabilities": ["dynamic_discovery", "session_management", "progress_tracking"]
        }
    
    async def run_workflow(self, request: WorkflowRequest) -> WorkflowResponse:
        """Execute a workflow."""
        # Build request payload
        payload = {
            "message": request.message,
            "input_format": "text",  # Not using stream-json currently
            "timeout": request.timeout or self.config.timeout,
            "user_id": request.user_id or self._get_user_id()
        }
        
        # Add optional parameters
        if request.session_id:
            payload["session_id"] = request.session_id
        if request.epic_name:
            payload["session_name"] = request.epic_name
        if request.max_turns:
            payload["max_turns"] = request.max_turns
        if request.repository_url:
            payload["repository_url"] = request.repository_url
        if request.git_branch:
            payload["git_branch"] = request.git_branch
        if request.persistent is not None:
            payload["persistent"] = request.persistent
        if request.auto_merge is not None:
            payload["auto_merge"] = request.auto_merge
        if request.temp_workspace is not None:
            payload["temp_workspace"] = request.temp_workspace
        
        endpoint = f"/api/v1/workflows/claude-code/run/{request.workflow_name.value}"
        response_data = await self._make_request("POST", endpoint, data=payload)
        
        return WorkflowResponse(**response_data)
    
    async def get_workflow_status(self, run_id: str, detailed: bool = True) -> WorkflowStatusResponse:
        """Get workflow status."""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/status"
        params = {"debug": detailed} if detailed else None
        
        response_data = await self._make_request("GET", endpoint, params=params)
        return WorkflowStatusResponse(**response_data)
    
    async def list_workflow_runs(self) -> WorkflowRunsResponse:
        """List all workflow runs."""
        endpoint = "/api/v1/workflows/claude-code/runs"
        response_data = await self._make_request("GET", endpoint)
        
        return WorkflowRunsResponse(**response_data)
    
    async def clear_session(self, run_id: str) -> Dict[str, Any]:
        """Clear/cleanup a workflow session."""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/cleanup"
        return await self._make_request("POST", endpoint)
    
    async def kill_workflow(self, run_id: str) -> Dict[str, Any]:
        """Force stop a running workflow."""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/kill"
        return await self._make_request("POST", endpoint)
    
    async def add_feedback(self, run_id: str, message: str, message_type: str = "user") -> Dict[str, Any]:
        """Add real-time feedback to running workflow."""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/add-message"
        payload = {
            "message_type": message_type,
            "content": message
        }
        return await self._make_request("POST", endpoint, data=payload)
    
    @property
    def is_healthy(self) -> bool:
        """Check if API is healthy."""
        return self._healthy
    
    async def ensure_healthy(self, force_check: bool = False) -> bool:
        """Ensure API is healthy, perform health check if needed."""
        now = datetime.now()
        
        # Force health check if requested or if we haven't checked recently
        if (force_check or 
            self._last_health_check is None or 
            (now - self._last_health_check).seconds > self.config.health_check_interval):
            
            try:
                await self.health_check()
            except Exception:
                self._healthy = False
        
        return self._healthy