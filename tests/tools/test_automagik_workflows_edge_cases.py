"""
Edge case tests for Enhanced AutoMagik Workflows MCP tool
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastmcp import Context

from automagik_tools.tools.automagik_workflows import (
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

    original_config = workflow_module.config
    original_client = workflow_module.client

    workflow_module.config = mock_config
    workflow_module.client = ClaudeCodeClient(mock_config)

    yield

    workflow_module.config = original_config
    workflow_module.client = original_client


class TestEnhancedRunWorkflowEdgeCases:
    """Test edge cases for enhanced run_workflow"""

    @pytest.mark.asyncio
    async def test_run_workflow_empty_workflow_name(self):
        """Test handling of empty workflow name"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(side_effect=ValueError("Empty workflow name"))

            result = await run_workflow(
                workflow_name="",
                message="Test message"
            )

            assert result["status"] == "error"
            assert "Empty workflow name" in result["error"]

    @pytest.mark.asyncio
    async def test_run_workflow_empty_message(self):
        """Test handling of empty message"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(side_effect=ValueError("Empty message"))

            result = await run_workflow(
                workflow_name="test",
                message=""
            )

            assert result["status"] == "error"
            assert "Empty message" in result["error"]

    @pytest.mark.asyncio
    async def test_run_workflow_very_long_message(self, mock_context):
        """Test handling of very long messages"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "long-msg-123",
                "status": "running"
            })

            long_message = "x" * 10000  # 10KB message
            result = await run_workflow(
                workflow_name="test",
                message=long_message,
                ctx=mock_context
            )

            # Should handle large payloads gracefully
            assert result["status"] == "running"
            assert result["run_id"] == "long-msg-123"

    @pytest.mark.asyncio
    async def test_run_workflow_max_turns_edge_values(self, mock_context):
        """Test edge values for max_turns parameter"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "edge-turns-123",
                "status": "running"
            })

            # Test with max_turns = 1 (minimum)
            result = await run_workflow(
                workflow_name="test",
                message="Test",
                max_turns=1,
                ctx=mock_context
            )
            assert result["max_turns"] == 1

            # Test with max_turns = 100 (maximum)
            result = await run_workflow(
                workflow_name="test",
                message="Test", 
                max_turns=100,
                ctx=mock_context
            )
            assert result["max_turns"] == 100

    @pytest.mark.asyncio
    async def test_run_workflow_all_optional_parameters(self, mock_context):
        """Test with all optional parameters provided"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "full-params-123",
                "status": "running"
            })

            result = await run_workflow(
                workflow_name="test",
                message="Test message",
                max_turns=50,
                persistent=True,
                session_name="edge-test-session",
                git_branch="feature/edge-test",
                repository_url="https://github.com/test/edge-repo",
                auto_merge=True,
                ctx=mock_context
            )

            # Verify all parameters were processed
            call_args = mock_client.start_workflow.call_args[0][1]
            assert call_args["message"] == "Test message"
            assert call_args["max_turns"] == 50
            assert call_args["session_name"] == "edge-test-session"
            assert call_args["git_branch"] == "feature/edge-test"
            assert call_args["repository_url"] == "https://github.com/test/edge-repo"
            assert call_args["auto_merge"] is True


class TestEnhancedListRecentRunsEdgeCases:
    """Test edge cases for enhanced list_recent_runs"""

    @pytest.mark.asyncio
    async def test_list_recent_runs_empty_response(self, mock_context):
        """Test handling of empty runs response"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(return_value={"runs": []})

            result = await list_recent_runs(detailed=True, ctx=mock_context)

            assert result["runs"] == []
            assert result["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_recent_runs_malformed_response(self, mock_context):
        """Test handling of malformed API response"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Response without 'runs' key
            mock_client.list_runs = AsyncMock(return_value={"unexpected": "data"})

            result = await list_recent_runs(detailed=True, ctx=mock_context)

            assert result["runs"] == []

    @pytest.mark.asyncio
    async def test_list_recent_runs_missing_orchestration_fields(self, mock_context):
        """Test handling of runs missing orchestration fields"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {
                        "run_id": "incomplete-1",
                        "status": "completed",
                        # Missing: workspace_path, git_branch, tools_used, etc.
                    }
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_recent_runs(detailed=True, ctx=mock_context)

            run = result["runs"][0]
            # Should handle missing fields gracefully with None values
            assert run["workspace_path"] is None
            assert run["git_branch"] is None
            assert run["error_message"] is None
            assert run["tools_used"] == []
            assert run["session_name"] is None

    @pytest.mark.asyncio
    async def test_list_recent_runs_large_page_size(self, mock_context):
        """Test with very large page size"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(return_value={"runs": []})

            result = await list_recent_runs(page_size=1000, ctx=mock_context)

            # Should pass large page size to API
            call_args = mock_client.list_runs.call_args[0][0]
            assert call_args["page_size"] == 1000


class TestGetHealthStatusEdgeCases:
    """Test edge cases for get_health_status"""

    @pytest.mark.asyncio
    async def test_get_health_status_partial_response(self, mock_context):
        """Test handling of partial health response"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Minimal health response
            mock_health_response = {"status": "healthy"}
            mock_client.get_health_status = AsyncMock(return_value=mock_health_response)

            result = await get_health_status(ctx=mock_context)

            assert result["status"] == "healthy"
            # Timestamp should be added
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_health_status_extreme_resource_values(self, mock_context):
        """Test handling of extreme resource usage values"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_health_response = {
                "status": "degraded",
                "system": {
                    "cpu_usage": 99.9,  # Very high
                    "memory_usage": 100.0,  # Maximum
                    "disk_usage": 0.1  # Very low
                }
            }
            mock_client.get_health_status = AsyncMock(return_value=mock_health_response)

            result = await get_health_status(ctx=mock_context)

            assert result["system"]["cpu_usage"] == 99.9
            assert result["system"]["memory_usage"] == 100.0
            
            # Should warn about extreme values
            warning_calls = [call.args[0] for call in mock_context.warning.call_args_list]
            assert any("High CPU usage: 99.9%" in call for call in warning_calls)
            assert any("High memory usage: 100.0%" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_get_health_status_timeout_error(self, mock_context):
        """Test handling of timeout errors"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            import asyncio
            mock_client.get_health_status = AsyncMock(side_effect=asyncio.TimeoutError("Health check timeout"))

            result = await get_health_status(ctx=mock_context)

            assert result["status"] == "unknown"
            assert "Health check timeout" in result["error"]
            assert result["recommendation"] == "Proceed with caution or retry health check"


class TestListRunsByStatusEdgeCases:
    """Test edge cases for list_runs_by_status"""

    @pytest.mark.asyncio
    async def test_list_runs_by_status_unknown_status(self, mock_context):
        """Test filtering by unknown status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "unknown", "workflow_name": "test"},
                    {"run_id": "run-2", "status": "completed", "workflow_name": "test"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("unknown", ctx=mock_context)

            assert len(result) == 1
            assert result[0]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_list_runs_by_status_mixed_case(self, mock_context):
        """Test case insensitive status matching"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "RUNNING", "workflow_name": "test"},
                    {"run_id": "run-2", "status": "Running", "workflow_name": "test"},
                    {"run_id": "run-3", "status": "running", "workflow_name": "test"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("running", ctx=mock_context)

            # All three should match regardless of case
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_runs_by_status_no_matches(self, mock_context):
        """Test when no runs match the status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "completed", "workflow_name": "test"},
                    {"run_id": "run-2", "status": "failed", "workflow_name": "test"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_status("running", ctx=mock_context)

            assert len(result) == 0
            # Context should still log that 0 were found
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("Found 0 workflows with status 'running'" in call for call in info_calls)


class TestListRunsByWorkflowEdgeCases:
    """Test edge cases for list_runs_by_workflow"""

    @pytest.mark.asyncio
    async def test_list_runs_by_workflow_no_completed_runs(self, mock_context):
        """Test workflow analysis with no completed runs"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "running", "workflow_name": "builder"},
                    {"run_id": "run-2", "status": "failed", "workflow_name": "builder"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_workflow("builder", ctx=mock_context)

            assert len(result) == 2
            
            # Should calculate 0% success rate
            assert mock_context.info.called

    @pytest.mark.asyncio
    async def test_list_runs_by_workflow_zero_execution_time(self, mock_context):
        """Test workflow analysis with zero execution times"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "completed", "workflow_name": "builder", "execution_time": 0},
                    {"run_id": "run-2", "status": "completed", "workflow_name": "builder", "execution_time": 0},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_workflow("builder", ctx=mock_context)

            # Should handle zero execution times without crashing
            assert len(result) == 2
            # Average execution time should be 0
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            # Should not log average execution time if it's 0
            assert not any("Average execution time" in call for call in info_calls)

    @pytest.mark.asyncio 
    async def test_list_runs_by_workflow_empty_workflow_name(self, mock_context):
        """Test with empty workflow name"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(return_value={"runs": []})

            result = await list_runs_by_workflow("", ctx=mock_context)

            # Should pass empty string to API
            call_args = mock_client.list_runs.call_args[0][0]
            assert call_args["workflow_name"] == ""


class TestListRunsByTimeRangeEdgeCases:
    """Test edge cases for list_runs_by_time_range"""

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_same_start_end_time(self, mock_context):
        """Test with identical start and end times"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "started_at": "2025-01-20T10:00:00Z", "workflow_name": "test"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T10:00:00Z",
                end_time="2025-01-20T10:00:00Z",
                ctx=mock_context
            )

            # Should include runs that match exactly
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_reverse_time_order(self, mock_context):
        """Test with end time before start time"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {"runs": []}
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T23:59:59Z",
                end_time="2025-01-20T00:00:00Z",  # Earlier than start
                ctx=mock_context
            )

            # Should return empty result
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_malformed_timestamps(self, mock_context):
        """Test with runs having malformed timestamps"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "started_at": "invalid-timestamp", "workflow_name": "test"},
                    {"run_id": "run-2", "started_at": "2025-01-20T10:00:00Z", "workflow_name": "test"},
                    {"run_id": "run-3", "started_at": "", "workflow_name": "test"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00Z",
                end_time="2025-01-20T23:59:59Z",
                ctx=mock_context
            )

            # Should only include runs with valid timestamps
            assert len(result) == 1
            assert result[0]["run_id"] == "run-2"

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_missing_cost_and_time(self, mock_context):
        """Test activity analysis with missing cost and execution time data"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {
                        "run_id": "run-1",
                        "started_at": "2025-01-20T10:00:00Z",
                        "workflow_name": "test",
                        "status": "completed"
                        # Missing: total_cost, execution_time
                    }
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00Z", 
                end_time="2025-01-20T23:59:59Z",
                ctx=mock_context
            )

            assert len(result) == 1
            
            # Should handle missing cost/time gracefully
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            # Should not log cost or time if they're 0/missing
            assert not any("Total cost:" in call for call in info_calls)
            assert not any("Average execution time:" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_list_runs_by_time_range_timezone_variations(self, mock_context):
        """Test time parsing with different timezone formats"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {"runs": []}
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            # Test various valid ISO formats
            result = await list_runs_by_time_range(
                start_time="2025-01-20T00:00:00+00:00",  # Explicit timezone
                end_time="2025-01-20T23:59:59Z",          # Z timezone
                ctx=mock_context
            )

            # Should parse both formats correctly
            assert isinstance(result, list)


class TestClientEdgeCases:
    """Test edge cases for the HTTP client"""

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return ClaudeCodeClient(mock_config)

    @pytest.mark.asyncio
    async def test_client_empty_api_key(self):
        """Test client with empty API key"""
        config = AutomagikWorkflowsConfig()  # Uses default empty api_key
        client = ClaudeCodeClient(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_client.request.return_value = mock_response

            await client.get_health_status()

            # Should not include X-API-Key header when empty
            call_kwargs = mock_client.request.call_args.kwargs
            assert "X-API-Key" not in call_kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_client_malformed_json_response(self, client):
        """Test client handling of malformed JSON response"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            import json
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.text = "Not JSON response"
            mock_client.request.return_value = mock_response

            result = await client.get_health_status()

            # Should return text fallback
            assert result["message"] == "Not JSON response"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_client_network_errors(self, client):
        """Test client handling of various network errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test different error types
            errors = [
                ConnectionError("Network unreachable"),
                TimeoutError("Request timeout"),
                Exception("Generic network error")
            ]

            for error in errors:
                mock_client.request.side_effect = error
                
                with patch("asyncio.sleep"):  # Speed up retry tests
                    with pytest.raises(type(error)):
                        await client._make_request("GET", "/test")


class TestParameterValidation:
    """Test parameter validation edge cases"""

    @pytest.mark.asyncio
    async def test_list_runs_by_status_special_characters(self, mock_context):
        """Test status filtering with special characters"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(return_value={"runs": []})

            # Test with special characters in status
            result = await list_runs_by_status("running-test", ctx=mock_context)
            assert isinstance(result, list)

            result = await list_runs_by_status("status_with_underscore", ctx=mock_context)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_runs_by_workflow_unicode_names(self, mock_context):
        """Test workflow filtering with Unicode characters"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_runs = AsyncMock(return_value={"runs": []})

            # Test with Unicode workflow name
            result = await list_runs_by_workflow("测试工作流", ctx=mock_context)
            assert isinstance(result, list)

            # Verify Unicode was passed correctly
            call_args = mock_client.list_runs.call_args[0][0]
            assert call_args["workflow_name"] == "测试工作流"