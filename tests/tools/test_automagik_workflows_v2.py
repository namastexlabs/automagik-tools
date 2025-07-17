"""
Comprehensive test suite for automagik-workflows-v2 tool
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from typing import Dict, Any

from automagik_tools.tools.automagik_workflows_v2.config import AutomagikWorkflowsV2Config
from automagik_tools.tools.automagik_workflows_v2.client import AutomagikWorkflowsClient
from automagik_tools.tools.automagik_workflows_v2.session_manager import SessionManager
from automagik_tools.tools.automagik_workflows_v2.progress_tracker import ProgressTracker
from automagik_tools.tools.automagik_workflows_v2.models import (
    WorkflowName, WorkflowMode, WorkflowStatus, WorkflowRequest, WorkflowResponse,
    WorkflowStatusResponse, WorkflowRun, HealthResponse
)
from automagik_tools.tools.automagik_workflows_v2 import create_server, get_metadata, get_config_class


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    return AutomagikWorkflowsV2Config(
        api_base_url="http://localhost:28881",
        api_key="test-api-key",
        user_id="test-user",
        timeout=14400,
        polling_interval=2
    )


@pytest.fixture
def mock_client(mock_config):
    """Create mock client for testing."""
    client = AsyncMock(spec=AutomagikWorkflowsClient)
    client.config = mock_config
    client.is_healthy = True
    return client


@pytest.fixture
def mock_session_manager(mock_client):
    """Create mock session manager for testing."""
    return AsyncMock(spec=SessionManager)


@pytest.fixture
def mock_progress_tracker(mock_client, mock_config):
    """Create mock progress tracker for testing."""
    return AsyncMock(spec=ProgressTracker)


@pytest.fixture
def mock_context():
    """Create mock FastMCP Context for testing."""
    context = AsyncMock()
    context.report_progress = AsyncMock()
    context.elicit = AsyncMock()
    return context


class TestAutomagikWorkflowsV2Config:
    """Test configuration management."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = AutomagikWorkflowsV2Config(
            api_key="test-key",
            user_id="test-user"
        )
        
        assert config.api_base_url == "http://localhost:28881"
        assert config.api_key == "test-key"
        assert config.user_id == "test-user"
        assert config.timeout == 14400
        assert config.polling_interval == 8
    
    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_V2_API_KEY", "env-key")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_V2_USER_ID", "env-user")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_V2_BASE_URL", "http://localhost:9999")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_V2_TIMEOUT", "7200")
        
        config = AutomagikWorkflowsV2Config()
        
        assert config.api_key == "env-key"
        assert config.user_id == "env-user"
        assert config.api_base_url == "http://localhost:9999"
        assert config.timeout == 7200


class TestAutomagikWorkflowsClient:
    """Test HTTP client functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_config):
        """Test successful health check."""
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "environment": "test",
                "uptime": 3600
            }
            mock_response.raise_for_status = Mock()
            
            mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
            
            client = AutomagikWorkflowsClient(mock_config)
            health = await client.health_check()
            
            assert health.status == "healthy"
            assert health.version == "1.0.0"
            assert client.is_healthy
    
    @pytest.mark.asyncio
    async def test_discover_workflows(self, mock_config):
        """Test workflow discovery."""
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_response = Mock()
            mock_response.json.return_value = {
                "available_workflows": ["implement", "research", "buddy", "throwaway"],
                "capabilities": ["elicitation", "progress_tracking"]
            }
            mock_response.raise_for_status = Mock()
            
            mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
            
            client = AutomagikWorkflowsClient(mock_config)
            discovery = await client.discover_workflows()
            
            assert "implement" in discovery["available_workflows"]
            assert "progress_tracking" in discovery["capabilities"]
    
    @pytest.mark.asyncio
    async def test_run_workflow(self, mock_config):
        """Test workflow execution."""
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_response = Mock()
            mock_response.json.return_value = {
                "run_id": "test-run-123",
                "session_id": "test-session-456", 
                "status": "running",
                "started_at": "2024-01-01T00:00:00Z"
            }
            mock_response.raise_for_status = Mock()
            
            mock_httpx.return_value.__aenter__.return_value.post.return_value = mock_response
            
            client = AutomagikWorkflowsClient(mock_config)
            
            request = WorkflowRequest(
                message="Test workflow",
                workflow_name=WorkflowName.IMPLEMENT,
                user_id="test-user"
            )
            
            response = await client.run_workflow(request)
            
            assert response.run_id == "test-run-123"
            assert response.session_id == "test-session-456"


class TestSessionManager:
    """Test session management functionality."""
    
    @pytest.mark.asyncio
    async def test_refresh_sessions(self, mock_client):
        """Test session cache refresh."""
        mock_runs_response = Mock()
        mock_runs_response.runs = [
            WorkflowRun(
                run_id="run-1",
                session_id="session-1",
                session_name="test-epic",
                workflow_name="implement",
                status=WorkflowStatus.COMPLETED,
                started_at=datetime.now(),
                user_id="test-user",
                message="Test message"
            )
        ]
        
        mock_client.list_workflow_runs.return_value = mock_runs_response
        
        session_manager = SessionManager(mock_client)
        await session_manager.refresh_sessions()
        
        assert "session-1" in session_manager._session_cache
        assert "test-epic" in session_manager._epic_cache
        assert "session-1" in session_manager._epic_cache["test-epic"]
    
    @pytest.mark.asyncio
    async def test_find_sessions_by_epic(self, mock_client):
        """Test finding sessions by epic name."""
        mock_runs_response = Mock()
        mock_runs_response.runs = [
            WorkflowRun(
                run_id="run-1",
                session_id="session-1", 
                session_name="auth-epic",
                workflow_name="implement",
                status=WorkflowStatus.COMPLETED,
                started_at=datetime.now(),
                user_id="test-user",
                message="Auth feature"
            ),
            WorkflowRun(
                run_id="run-2",
                session_id="session-2",
                session_name="auth-epic", 
                workflow_name="research",
                status=WorkflowStatus.RUNNING,
                started_at=datetime.now(),
                user_id="test-user",
                message="Auth research"
            )
        ]
        
        mock_client.list_workflow_runs.return_value = mock_runs_response
        
        session_manager = SessionManager(mock_client)
        sessions = await session_manager.find_sessions_by_epic("auth-epic")
        
        assert len(sessions) == 2
        assert all(s.session_name == "auth-epic" for s in sessions)


class TestProgressTracker:
    """Test progress tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_track_workflow_progress_completion(self, mock_client, mock_context):
        """Test progress tracking until completion."""
        # Mock status responses
        status_responses = [
            WorkflowStatusResponse(
                run_id="test-run",
                status=WorkflowStatus.RUNNING,
                current_turn=1,
                max_turns=3,
                current_action="Starting",
                started_at=datetime.now()
            ),
            WorkflowStatusResponse(
                run_id="test-run",
                status=WorkflowStatus.RUNNING, 
                current_turn=2,
                max_turns=3,
                current_action="Processing",
                started_at=datetime.now()
            ),
            WorkflowStatusResponse(
                run_id="test-run",
                status=WorkflowStatus.COMPLETED,
                current_turn=3,
                max_turns=3,
                current_action="Finished",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        ]
        
        mock_client.get_workflow_status.side_effect = status_responses
        
        tracker = ProgressTracker(mock_client, polling_interval=0.1)
        
        final_status = await tracker.track_workflow_progress("test-run", mock_context)
        
        assert final_status.status == WorkflowStatus.COMPLETED
        assert mock_context.report_progress.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_track_workflow_progress_failure(self, mock_client, mock_context):
        """Test progress tracking with workflow failure."""
        failed_status = WorkflowStatusResponse(
            run_id="test-run",
            status=WorkflowStatus.FAILED,
            current_turn=1,
            max_turns=3,
            current_action="Failed",
            error_message="Test error",
            started_at=datetime.now()
        )
        
        mock_client.get_workflow_status.return_value = failed_status
        
        tracker = ProgressTracker(mock_client, polling_interval=0.1)
        
        final_status = await tracker.track_workflow_progress("test-run", mock_context)
        
        assert final_status.status == WorkflowStatus.FAILED
        assert final_status.error_message == "Test error"


class TestWorkflowOrchestration:
    """Test main workflow orchestration functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrate_workflow_with_discovery(self, mock_client, mock_context):
        """Test workflow orchestration with dynamic discovery."""
        # Mock discovery response
        mock_client.discover_workflows.return_value = {
            "available_workflows": ["implement", "research", "buddy", "throwaway"]
        }
        
        # Mock elicitation response
        mock_context.elicit.return_value = {"workflow_name": "implement"}
        
        # Mock workflow execution
        mock_response = WorkflowResponse(
            run_id="test-run-123",
            session_id="test-session-456",
            status="running",
            started_at=datetime.now()
        )
        mock_client.run_workflow.return_value = mock_response
        
        # Mock progress tracking
        final_status = WorkflowStatusResponse(
            run_id="test-run-123",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        with patch('automagik_tools.tools.automagik_workflows_v2.server.progress_tracker') as mock_tracker:
            mock_tracker.track_workflow_progress.return_value = final_status
            
            from automagik_tools.tools.automagik_workflows_v2.server import orchestrate_workflow
            
            result = await orchestrate_workflow(
                message="Build a login system",
                ctx=mock_context
            )
            
            assert result["status"] == "started"
            assert result["run_id"] == "test-run-123"
            assert result["workflow_name"] == "implement"
    
    @pytest.mark.asyncio
    async def test_orchestrate_workflow_with_session_continuation(self, mock_client, mock_context):
        """Test workflow orchestration with session continuation."""
        # Mock session validation
        with patch('automagik_tools.tools.automagik_workflows_v2.server.session_manager') as mock_session_mgr:
            mock_session_mgr.validate_session_for_continuation.return_value = True
            
            # Mock workflow execution
            mock_response = WorkflowResponse(
                run_id="test-run-123",
                session_id="existing-session-456",
                status="running", 
                started_at=datetime.now()
            )
            mock_client.run_workflow.return_value = mock_response
            
            from automagik_tools.tools.automagik_workflows_v2.server import orchestrate_workflow
            
            result = await orchestrate_workflow(
                message="Continue the login system",
                session_id="existing-session-456",
                workflow_name=WorkflowName.IMPLEMENT,
                ctx=mock_context
            )
            
            assert result["session_id"] == "existing-session-456"


class TestToolIntegration:
    """Test tool integration and registration."""
    
    def test_get_metadata(self):
        """Test tool metadata."""
        metadata = get_metadata()
        
        assert metadata["name"] == "automagik-workflows-v2"
        assert metadata["version"] == "2.0.0"
        assert "dynamic_workflow_discovery" in metadata["capabilities"]
        assert "real_time_progress_streaming" in metadata["capabilities"]
    
    def test_get_config_class(self):
        """Test configuration class export."""
        config_class = get_config_class()
        assert config_class == AutomagikWorkflowsV2Config
    
    def test_create_server(self):
        """Test server creation."""
        server = create_server()
        assert server is not None
        assert server.name == "automagik-workflows-v2"


class TestElicitationWorkflow:
    """Test elicitation functionality."""
    
    @pytest.mark.asyncio
    async def test_parameter_elicitation(self, mock_context):
        """Test parameter elicitation for missing values."""
        mock_context.elicit.return_value = {
            "repository_url": "https://github.com/test/repo.git",
            "git_branch": "feature/auth",
            "epic_name": "authentication-system"
        }
        
        from automagik_tools.tools.automagik_workflows_v2.server import _elicit_parameters
        from automagik_tools.tools.automagik_workflows_v2.models import ElicitationRequest
        
        request = ElicitationRequest(
            workflow_name=WorkflowName.IMPLEMENT,
            message="Build authentication",
            mode=WorkflowMode.CODE,
            missing_parameters=["repository_url", "git_branch", "epic_name"]
        )
        
        response = await _elicit_parameters(mock_context, request)
        
        assert response.repository_url == "https://github.com/test/repo.git"
        assert response.git_branch == "feature/auth"
        assert response.epic_name == "authentication-system"


# Integration test markers
pytestmark = pytest.mark.asyncio