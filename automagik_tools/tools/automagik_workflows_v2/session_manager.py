"""
Session management for Automagik Workflows V2
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .client import AutomagikWorkflowsClient
from .models import WorkflowRun, WorkflowStatus

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages workflow sessions with ID-based continuation and epic name tracking."""
    
    def __init__(self, client: AutomagikWorkflowsClient):
        self.client = client
        self._session_cache: Dict[str, WorkflowRun] = {}
        self._epic_cache: Dict[str, List[str]] = {}  # epic_name -> [session_ids]
        self._last_refresh = None
    
    async def refresh_sessions(self, force: bool = False) -> None:
        """Refresh session cache from API."""
        now = datetime.now()
        
        # Refresh every 30 seconds or on force
        if (force or 
            self._last_refresh is None or 
            (now - self._last_refresh).seconds > 30):
            
            try:
                runs_response = await self.client.list_workflow_runs()
                self._session_cache.clear()
                self._epic_cache.clear()
                
                for run in runs_response.runs:
                    self._session_cache[run.session_id] = run
                    
                    # Track epic name associations
                    if run.session_name:  # session_name contains epic_name
                        if run.session_name not in self._epic_cache:
                            self._epic_cache[run.session_name] = []
                        self._epic_cache[run.session_name].append(run.session_id)
                
                self._last_refresh = now
                logger.info(f"Refreshed {len(self._session_cache)} sessions")
                
            except Exception as e:
                logger.error(f"Failed to refresh sessions: {e}")
                raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[WorkflowRun]:
        """Get session information by session ID."""
        await self.refresh_sessions()
        return self._session_cache.get(session_id)
    
    async def find_sessions_by_epic(self, epic_name: str) -> List[WorkflowRun]:
        """Find all sessions associated with an epic name."""
        await self.refresh_sessions()
        
        session_ids = self._epic_cache.get(epic_name, [])
        return [
            self._session_cache[session_id] 
            for session_id in session_ids 
            if session_id in self._session_cache
        ]
    
    async def get_active_sessions(self) -> List[WorkflowRun]:
        """Get all currently active (running) sessions."""
        await self.refresh_sessions()
        
        return [
            run for run in self._session_cache.values()
            if run.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]
        ]
    
    async def get_recent_sessions(self, limit: int = 10) -> List[WorkflowRun]:
        """Get most recent sessions."""
        await self.refresh_sessions()
        
        sessions = list(self._session_cache.values())
        sessions.sort(key=lambda x: x.started_at, reverse=True)
        return sessions[:limit]
    
    async def get_sessions_by_user(self, user_id: str) -> List[WorkflowRun]:
        """Get sessions for a specific user."""
        await self.refresh_sessions()
        
        return [
            run for run in self._session_cache.values()
            if run.user_id == user_id
        ]
    
    async def validate_session_for_continuation(self, session_id: str) -> bool:
        """Validate if a session can be continued."""
        session = await self.get_session_by_id(session_id)
        if not session:
            return False
        
        # Can continue if session is completed or failed (for retry)
        return session.status in [
            WorkflowStatus.COMPLETED, 
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED
        ]
    
    async def get_session_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session context for display/debugging."""
        session = await self.get_session_by_id(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Get detailed status from API
        try:
            status = await self.client.get_workflow_status(session_id, detailed=True)
            
            return {
                "session_id": session_id,
                "epic_name": session.session_name,
                "workflow_name": session.workflow_name,
                "status": session.status.value,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "current_turn": status.current_turn,
                "max_turns": status.max_turns,
                "current_action": status.current_action,
                "workspace_path": status.workspace_path,
                "git_info": status.git_info,
                "original_message": session.message
            }
            
        except Exception as e:
            logger.error(f"Failed to get detailed session context: {e}")
            return {
                "session_id": session_id,
                "epic_name": session.session_name,
                "workflow_name": session.workflow_name,
                "status": session.status.value,
                "error": str(e)
            }
    
    async def clear_session_cache(self) -> None:
        """Clear the session cache (force refresh on next access)."""
        self._session_cache.clear()
        self._epic_cache.clear()
        self._last_refresh = None
        logger.info("Session cache cleared")
    
    def get_epic_names(self) -> List[str]:
        """Get list of known epic names."""
        return list(self._epic_cache.keys())
    
    def get_session_count(self) -> Dict[str, int]:
        """Get session count statistics."""
        if not self._session_cache:
            return {"total": 0}
        
        status_counts = {}
        for run in self._session_cache.values():
            status = run.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total": len(self._session_cache),
            "by_status": status_counts,
            "epic_count": len(self._epic_cache)
        }