"""
Tests for Enhanced AutoMagik Workflows MCP tool - GENIE Orchestration Features
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastmcp import Context

from automagik_tools.tools.automagik_workflows import (
    create_server,
    get_metadata,
    run_workflow,
    list_recent_runs,
    get_health_status,
    list_runs_by_status,
    list_runs_by_workflow,
    list_runs_by_time_range,
)
from automagik_tools.tools.automagik_workflows.config import AutomagikWorkflowsConfig
from automagik_tools.tools.automagik_workflows.client import ClaudeCodeClient


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = AutomagikWorkflowsConfig()
    # Set fields directly to bypass environment variable lookup
    config.api_key = "test-api-key"
    config.base_url = "https://api.test.com"
    config.timeout = 30
    config.polling_interval = 1
    config.max_retries = 2
    return config


@pytest.fixture
def mock_context():
    """Create mock MCP context"""
    ctx = Mock(spec=Context)
    ctx.info = Mock()
    ctx.error = Mock()
    ctx.warning = Mock()
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture(autouse=True)
def setup_client(mock_config):
    """Setup the global client for testing"""
    import automagik_tools.tools.automagik_workflows as workflow_module

    # Store original values
    original_config = workflow_module.config
    original_client = workflow_module.client

    # Set test config and client
    workflow_module.config = mock_config
    workflow_module.client = ClaudeCodeClient(mock_config)

    yield

    # Restore original values
    workflow_module.config = original_config
    workflow_module.client = original_client


class TestEnhancedMetadata:
    """Test enhanced tool metadata"""

    def test_enhanced_metadata_structure(self):
        """Test that enhanced metadata has correct version and features"""
        metadata = get_metadata()
        assert metadata["name"] == "automagik-workflows"
        assert metadata["version"] == "1.2.0"  # Enhanced version
        assert "GENIE orchestration features" in metadata["description"]
        assert "health monitoring" in metadata["description"]
        assert "advanced filtering" in metadata["description"]
        assert "orchestration" in metadata["tags"]
        assert "genie" in metadata["tags"]
        assert "health" in metadata["tags"]
        assert "filtering" in metadata["tags"]


class TestEnhancedListRecentRuns:
    """Test enhanced list_recent_runs with detailed parameter"""

    @pytest.mark.asyncio
    async def test_list_recent_runs_detailed_true(self, mock_context):
        """Test list_recent_runs with detailed=True includes orchestration data"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {
                        "run_id": "run-1",
                        "workflow_name": "builder",
                        "status": "completed",
                        "started_at": "2025-01-20T10:00:00Z",
                        "completed_at": "2025-01-20T10:30:00Z",
                        "turns": 15,
                        "execution_time": 1800,
                        "total_cost": 0.0234,
                        # Enhanced orchestration data
                        "workspace_path": "/workspaces/builder-123",
                        "git_branch": "feature/new-tool",
                        "error_message": None,
                        "tools_used": ["bash", "edit", "read"],
                        "session_name": "build-session-1",
                        "repository_url": "https://github.com/test/repo",
                        "user_id": "user-123",
                        "tokens": 12450
                    }
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_recent_runs(detailed=True, page_size=5, ctx=mock_context)

            # Verify detailed orchestration data is included
            assert "runs" in result
            run = result["runs"][0]
            
            # Basic fields
            assert run["run_id"] == "run-1"
            assert run["workflow_name"] == "builder"
            assert run["status"] == "completed"
            
            # Enhanced orchestration fields
            assert run["workspace_path"] == "/workspaces/builder-123"
            assert run["git_branch"] == "feature/new-tool"
            assert run["error_message"] is None
            assert run["tools_used"] == ["bash", "edit", "read"]
            assert run["session_name"] == "build-session-1"
            assert run["repository_url"] == "https://github.com/test/repo"
            assert run["user_id"] == "user-123"
            assert run["tokens"] == 12450

    @pytest.mark.asyncio
    async def test_list_recent_runs_detailed_false_backward_compatibility(self, mock_context):
        """Test list_recent_runs with detailed=False maintains backward compatibility"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {
                        "run_id": "run-1",
                        "workflow_name": "builder",
                        "status": "completed",
                        "started_at": "2025-01-20T10:00:00Z",
                        "completed_at": "2025-01-20T10:30:00Z",
                        "turns": 15,
                        "execution_time": 1800,
                        "total_cost": 0.0234,
                        # These should NOT be included when detailed=False
                        "workspace_path": "/workspaces/builder-123",
                        "git_branch": "feature/new-tool",
                        "tools_used": ["bash", "edit", "read"],
                    }
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_recent_runs(detailed=False, page_size=5, ctx=mock_context)

            # Verify only basic fields are included (backward compatibility)
            run = result["runs"][0]
            assert run["run_id"] == "run-1"
            assert run["workflow_name"] == "builder"
            assert run["status"] == "completed"
            assert run["turns"] == 15
            assert run["execution_time"] == 1800
            assert run["cost"] == 0.0234
            
            # Enhanced fields should NOT be present
            assert "workspace_path" not in run
            assert "git_branch" not in run
            assert "tools_used" not in run

    @pytest.mark.asyncio
    async def test_list_recent_runs_default_detailed_false(self, mock_context):
        """Test that detailed defaults to False for backward compatibility"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {"runs": [{"run_id": "run-1", "status": "completed"}]}
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            # Call without detailed parameter
            result = await list_recent_runs(page_size=5, ctx=mock_context)

            # Should use concise format (backward compatible)
            run = result["runs"][0]
            assert "run_id" in run
            assert "workspace_path" not in run  # Enhanced field not included by default


class TestEnhancedRunWorkflow:
    """Test enhanced run_workflow with auto_merge parameter"""

    @pytest.mark.asyncio
    async def test_run_workflow_with_auto_merge_true(self, mock_context):
        """Test run_workflow with auto_merge=True parameter"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "auto-merge-123",
                "status": "running",
                "started_at": "2025-01-20T10:00:00Z"
            })

            result = await run_workflow(
                workflow_name="builder",
                message="Create new tool",
                auto_merge=True,
                ctx=mock_context
            )

            # Verify auto_merge parameter was passed to client
            call_args = mock_client.start_workflow.call_args
            request_data = call_args[0][1]  # Second argument is request_data
            assert request_data["auto_merge"] is True
            
            # Verify response
            assert result["run_id"] == "auto-merge-123"
            assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_run_workflow_auto_merge_false_default(self, mock_context):
        """Test that auto_merge defaults to False for backward compatibility"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "no-merge-123",
                "status": "running"
            })

            result = await run_workflow(
                workflow_name="builder",
                message="Create new tool",
                ctx=mock_context
            )

            # Verify auto_merge is not passed when False (default)
            call_args = mock_client.start_workflow.call_args
            request_data = call_args[0][1]
            assert "auto_merge" not in request_data  # Should not be included when False


class TestGetHealthStatus:
    """Test new get_health_status function"""

    @pytest.mark.asyncio
    async def test_get_health_status_success(self, mock_context):
        """Test successful health status check"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_health_response = {
                "status": "healthy",
                "timestamp": "2025-01-20T10:30:00Z",
                "system": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "disk_usage": 23.1
                },
                "workflows": {
                    "active_count": 3,
                    "queued_count": 1,
                    "failed_count": 0
                },
                "services": {
                    "claude_code": "healthy",
                    "git_service": "healthy",
                    "file_system": "healthy"
                },
                "last_error": None
            }
            mock_client.get_health_status = AsyncMock(return_value=mock_health_response)

            result = await get_health_status(ctx=mock_context)

            # Verify complete health data is returned
            assert result["status"] == "healthy"
            assert result["system"]["cpu_usage"] == 45.2
            assert result["workflows"]["active_count"] == 3
            assert result["services"]["claude_code"] == "healthy"
            assert "timestamp" in result
            
            # Verify context logging
            mock_context.info.assert_called()
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("System status: healthy" in call for call in info_calls)
            assert any("Active workflows: 3" in call for call in info_calls)
            assert any("System is healthy and ready for orchestration" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_get_health_status_degraded_warnings(self, mock_context):
        """Test health status with warnings for high resource usage"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_health_response = {
                "status": "degraded",
                "system": {
                    "cpu_usage": 85.5,  # High CPU
                    "memory_usage": 92.3,  # High memory
                    "disk_usage": 45.0
                },
                "workflows": {"active_count": 0}
            }
            mock_client.get_health_status = AsyncMock(return_value=mock_health_response)

            result = await get_health_status(ctx=mock_context)

            assert result["status"] == "degraded"
            
            # Verify warnings for high resource usage
            mock_context.warning.assert_called()
            warning_calls = [call.args[0] for call in mock_context.warning.call_args_list]
            assert any("High CPU usage: 85.5%" in call for call in warning_calls)
            assert any("High memory usage: 92.3%" in call for call in warning_calls)
            assert any("System is degraded - proceed with caution" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_get_health_status_error_fallback(self, mock_context):
        """Test graceful error handling when health check fails"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.get_health_status = AsyncMock(side_effect=Exception("Health API unavailable"))

            result = await get_health_status(ctx=mock_context)

            # Verify graceful fallback response
            assert result["status"] == "unknown"
            assert "Health API unavailable" in result["error"]
            assert "timestamp" in result
            assert result["recommendation"] == "Proceed with caution or retry health check"
            assert result["system"]["available"] is False
            assert result["workflows"]["accessible"] is False
            
            # Verify error logging
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_get_health_status_adds_timestamp(self, mock_context):
        """Test that timestamp is added if missing from API response"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Response without timestamp
            mock_health_response = {
                "status": "healthy",
                "system": {"cpu_usage": 30.0}
            }
            mock_client.get_health_status = AsyncMock(return_value=mock_health_response)

            result = await get_health_status(ctx=mock_context)

            # Verify timestamp was added
            assert "timestamp" in result
            # Verify it's a valid ISO timestamp
            timestamp = result["timestamp"]
            assert timestamp.endswith("Z")
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))  # Should not raise


class TestListRunsByStatus:
    """Test new list_runs_by_status function"""

    @pytest.mark.asyncio
    async def test_list_runs_by_status_running(self, mock_context):
        """Test filtering runs by running status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "running", "workflow_name": "builder"},
                    {"run_id": "run-2", "status": "completed", "workflow_name": "tester"},
                    {"run_id": "run-3", "status": "running", "workflow_name": "analyzer"},
                    {"run_id": "run-4", "status": "running", "workflow_name": "validator"},  # Added third running
                    {"run_id": "run-5", "status": "failed", "workflow_name": "builder"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("running", limit=10, ctx=mock_context)

            # Verify only running workflows are returned
            assert len(result) == 3
            assert all(run["status"] == "running" for run in result)
            assert result[0]["run_id"] == "run-1"
            assert result[1]["run_id"] == "run-3"
            assert result[2]["run_id"] == "run-4"
            
            # Verify context insights
            assert mock_context.info.called
            # Check if warning was called for multiple running workflows
            warning_calls = [call.args[0] for call in mock_context.warning.call_args_list]
            assert any("workflows running - consider resource coordination" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_list_runs_by_status_failed_insights(self, mock_context):
        """Test filtering runs by failed status with insights"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "fail-1", "status": "failed", "workflow_name": "builder"},
                    {"run_id": "fail-2", "status": "failed", "workflow_name": "tester"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("failed", limit=5, ctx=mock_context)

            assert len(result) == 2
            assert all(run["status"] == "failed" for run in result)
            
            # Verify context provides failure analysis insights
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("failed workflows available for analysis" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_list_runs_by_status_case_insensitive(self, mock_context):
        """Test that status filtering is case insensitive"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "COMPLETED", "workflow_name": "builder"},
                    {"run_id": "run-2", "status": "completed", "workflow_name": "tester"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("completed", limit=5, ctx=mock_context)

            # Both COMPLETED and completed should match
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_runs_by_status_error_handling(self, mock_context):
        """Test error handling in list_runs_by_status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(side_effect=Exception("API error"))

            result = await list_runs_by_status("running", ctx=mock_context)

            assert len(result) == 1
            assert "error" in result[0]
            assert "API error" in result[0]["error"]
            mock_context.error.assert_called()


class TestListRunsByWorkflow:
    """Test new list_runs_by_workflow function"""

    @pytest.mark.asyncio
    async def test_list_runs_by_workflow_performance_analysis(self, mock_context):
        """Test workflow performance analysis insights"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "builder-1", "status": "completed", "workflow_name": "builder", "execution_time": 1200},
                    {"run_id": "builder-2", "status": "completed", "workflow_name": "builder", "execution_time": 1800},
                    {"run_id": "builder-3", "status": "failed", "workflow_name": "builder", "execution_time": 600},
                    {"run_id": "builder-4", "status": "running", "workflow_name": "builder", "execution_time": 0},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_workflow("builder", limit=10, ctx=mock_context)

            assert len(result) == 4
            assert all(run["workflow_name"] == "builder" for run in result)
            
            # Verify performance insights in context
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("Success rate: 50.0% (2/4)" in call for call in info_calls)
            assert any("Average execution time: 1500.0 seconds" in call for call in info_calls)
            
            # Should warn about failures
            warning_calls = [call.args[0] for call in mock_context.warning.call_args_list]
            assert any("1 recent failures - investigate patterns" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_list_runs_by_workflow_api_filtering(self, mock_context):
        """Test that workflow filtering uses API-level filtering"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {"runs": []}
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            await list_runs_by_workflow("analyzer", limit=5, ctx=mock_context)

            # Verify API was called with workflow filter
            call_args = mock_client.list_runs.call_args[0][0]
            assert call_args["workflow_name"] == "analyzer"
            assert call_args["detailed"] is True
            assert call_args["page_size"] == 5


class TestListRunsByTimeRange:
    """Test new list_runs_by_time_range function"""

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_filtering(self, mock_context):
        """Test time range filtering logic"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "started_at": "2025-01-20T10:00:00Z", "workflow_name": "builder"},
                    {"run_id": "run-2", "started_at": "2025-01-20T14:00:00Z", "workflow_name": "tester"},
                    {"run_id": "run-3", "started_at": "2025-01-21T10:00:00Z", "workflow_name": "analyzer"},  # Outside range
                    {"run_id": "run-4", "started_at": "2025-01-19T10:00:00Z", "workflow_name": "builder"},  # Outside range
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00Z",
                end_time="2025-01-20T23:59:59Z",
                limit=10,
                ctx=mock_context
            )

            # Only runs within the specified day should be returned
            assert len(result) == 2
            assert result[0]["run_id"] == "run-1"
            assert result[1]["run_id"] == "run-2"

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_activity_analysis(self, mock_context):
        """Test activity pattern analysis"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {
                        "run_id": "run-1", 
                        "started_at": "2025-01-20T10:00:00Z", 
                        "workflow_name": "builder",
                        "status": "completed",
                        "total_cost": 0.05,
                        "execution_time": 1200
                    },
                    {
                        "run_id": "run-2", 
                        "started_at": "2025-01-20T14:00:00Z", 
                        "workflow_name": "builder",
                        "status": "failed",
                        "total_cost": 0.02,
                        "execution_time": 600
                    },
                    {
                        "run_id": "run-3", 
                        "started_at": "2025-01-20T16:00:00Z", 
                        "workflow_name": "tester",
                        "status": "completed",
                        "total_cost": 0.03,
                        "execution_time": 900
                    }
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00Z",
                end_time="2025-01-20T23:59:59Z",
                ctx=mock_context
            )

            assert len(result) == 3
            
            # Verify activity analysis in context
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("Total cost: $0.10" in call for call in info_calls)
            assert any("Average execution time: 900.0 seconds" in call for call in info_calls)
            assert any("Workflow types: {'builder': 2, 'tester': 1}" in call for call in info_calls)
            assert any("Status distribution: {'completed': 2, 'failed': 1}" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_invalid_time_format(self, mock_context):
        """Test error handling for invalid time format"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            result = await list_runs_by_time_range(
                start_time="invalid-time",
                end_time="2025-01-20T23:59:59Z",
                ctx=mock_context
            )

            assert len(result) == 1
            assert "error" in result[0]
            assert "Invalid time format" in result[0]["message"]
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_high_activity_warning(self, mock_context):
        """Test warning for high activity periods"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Create 15 runs in one day (high activity)
            mock_runs = [
                {
                    "run_id": f"run-{i}",
                    "started_at": "2025-01-20T10:00:00Z",
                    "workflow_name": "builder",
                    "status": "completed"
                } for i in range(15)
            ]
            mock_client.list_runs = AsyncMock(return_value={"runs": mock_runs})

            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00Z",
                end_time="2025-01-20T23:59:59Z",
                ctx=mock_context
            )

            assert len(result) == 15
            
            # Should warn about high activity
            warning_calls = [call.args[0] for call in mock_context.warning.call_args_list]
            assert any("High activity period detected" in call for call in warning_calls)


class TestEnhancedToolsServerIntegration:
    """Test integration of all enhanced tools with server"""

    @pytest.fixture
    def enhanced_server(self, mock_config):
        """Create server with enhanced functions"""
        return create_server(mock_config)

    @pytest.mark.asyncio
    async def test_server_has_all_enhanced_tools(self, enhanced_server):
        """Test server has all enhanced tools registered"""
        tools_dict = await enhanced_server.get_tools()
        tool_names = list(tools_dict.keys())

        expected_tools = [
            "run_workflow",
            "list_workflows", 
            "list_recent_runs",
            "get_workflow_status",
            "kill_workflow",
            # New enhanced tools
            "get_health_status",
            "list_runs_by_status",
            "list_runs_by_workflow", 
            "list_runs_by_time_range"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Missing tool: {tool_name}"

        # Verify we have exactly the expected number of tools
        assert len(tools_dict) == 9, f"Expected 9 tools, got {len(tools_dict)}"

    @pytest.mark.asyncio
    async def test_all_enhanced_tools_have_descriptions(self, enhanced_server):
        """Test all enhanced tools have proper descriptions"""
        tools_dict = await enhanced_server.get_tools()

        for tool_name, tool in tools_dict.items():
            assert tool.description is not None
            assert len(tool.description.strip()) > 0
            # Enhanced tools should have emoji indicators
            if tool_name in ["get_health_status", "list_runs_by_status", "list_runs_by_workflow", "list_runs_by_time_range"]:
                assert "🔍" in tool.description or "🩺" in tool.description

    @pytest.mark.asyncio
    async def test_enhanced_tools_client_not_configured_error(self):
        """Test all enhanced tools handle missing client configuration"""
        import automagik_tools.tools.automagik_workflows as workflow_module

        original_client = workflow_module.client
        workflow_module.client = None

        try:
            # Test all new enhanced functions
            with pytest.raises(ValueError, match="Tool not configured"):
                await get_health_status()
            
            with pytest.raises(ValueError, match="Tool not configured"):
                await list_runs_by_status("running")
            
            with pytest.raises(ValueError, match="Tool not configured"):
                await list_runs_by_workflow("builder")
                
            with pytest.raises(ValueError, match="Tool not configured"):
                await list_runs_by_time_range("2025-01-20T00:00:00Z", "2025-01-20T23:59:59Z")

        finally:
            workflow_module.client = original_client


class TestClientHealthEndpoint:
    """Test the new health endpoint in the HTTP client"""

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return ClaudeCodeClient(mock_config)

    @pytest.mark.asyncio
    async def test_client_get_health_status_request(self, client):
        """Test health status HTTP request"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "system": {"cpu_usage": 30.0}
            }
            mock_client.request.return_value = mock_response

            result = await client.get_health_status()

            assert result["status"] == "healthy"
            
            # Verify correct endpoint was called
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert call_args[1]["url"].endswith("/api/v1/workflows/claude-code/health")

    @pytest.mark.asyncio
    async def test_client_health_endpoint_authentication(self, client):
        """Test health endpoint includes authentication"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_client.request.return_value = mock_response

            await client.get_health_status()

            # Verify the request was called with authentication
            mock_client.request.assert_called_once()
            # Check that headers parameter was passed with API key
            call_kwargs = mock_client.request.call_args.kwargs
            headers = call_kwargs.get("headers", {})
            assert "X-API-Key" in headers
            assert headers["X-API-Key"] == "test-api-key"