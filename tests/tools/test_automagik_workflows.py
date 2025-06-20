"""
Tests for AutoMagik Workflows MCP tool
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from fastmcp import Context

from automagik_tools.tools.automagik_workflows import (
    create_server,
    get_metadata,
    get_config_class,
    run_workflow,
    list_workflows,
    list_recent_runs,
    get_workflow_status,
    kill_workflow,
    # Enhanced functions
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
    ctx.warn = Mock()
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture
def server(mock_config):
    """Create test server instance"""
    return create_server(mock_config)


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


class TestAutomagikWorkflowsMetadata:
    """Test tool metadata and discovery"""

    def test_metadata_structure(self):
        """Test that metadata has required fields"""
        metadata = get_metadata()
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert metadata["name"] == "automagik-workflows"
        assert metadata["version"] == "1.2.0"
        assert "Smart Claude workflow orchestration" in metadata["description"]

    def test_config_class(self):
        """Test config class is returned correctly"""
        config_class = get_config_class()
        assert config_class == AutomagikWorkflowsConfig


class TestAutomagikWorkflowsConfig:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AutomagikWorkflowsConfig()
        assert config.base_url == "http://localhost:28881"
        assert config.timeout == 7200
        assert config.polling_interval == 8
        assert config.max_retries == 3

    def test_env_config(self, monkeypatch):
        """Test configuration from environment"""
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_API_KEY", "test-key")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_BASE_URL", "https://test.com")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_TIMEOUT", "1800")
        monkeypatch.setenv("AUTOMAGIK_WORKFLOWS_POLLING_INTERVAL", "5")

        config = AutomagikWorkflowsConfig()
        assert config.api_key == "test-key"
        assert config.base_url == "https://test.com"
        assert config.timeout == 1800
        assert config.polling_interval == 5


class TestAutomagikWorkflowsServer:
    """Test MCP server creation and tools"""

    def test_server_creation(self, server):
        """Test server is created with correct metadata"""
        assert server.name == "AutoMagik Workflows"
        assert "workflow orchestration" in server.instructions

    @pytest.mark.asyncio
    async def test_server_has_tools(self, server):
        """Test server has expected tools registered"""
        tools_dict = await server.get_tools()
        tool_names = list(tools_dict.keys())

        expected_tools = [
            "run_workflow",
            "list_workflows",
            "list_recent_runs",
            "get_workflow_status",
            "kill_workflow",
            # Enhanced/new tools
            "get_health_status",
            "list_runs_by_status",
            "list_runs_by_workflow",
            "list_runs_by_time_range"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names
            
        # Verify we have all 9 enhanced tools
        assert len(tools_dict) >= 9


class TestRunWorkflow:
    """Test run_workflow function"""

    @pytest.mark.asyncio
    async def test_run_workflow_success(self, mock_context):
        """Test successful workflow execution (returns immediately)"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={
                "run_id": "test-123",
                "status": "running",
                "started_at": "2024-01-15T10:00:00Z",
                "session_id": "session-456"
            })

            result = await run_workflow(
                workflow_name="test",
                message="Test workflow",
                max_turns=20,
                ctx=mock_context,
            )

            # Verify immediate return response (not completion data)
            assert result["status"] == "running"  # Initial status
            assert result["run_id"] == "test-123"
            assert result["workflow_name"] == "test"
            assert result["max_turns"] == 20
            assert result["started_at"] == "2024-01-15T10:00:00Z"
            assert result["session_id"] == "session-456"
            assert "tracking_info" in result
            assert result["tracking_info"]["run_id"] == "test-123"

            mock_context.info.assert_called()
            # run_workflow doesn't call report_progress since it returns immediately
            mock_context.report_progress.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_workflow_start_failure(self, mock_context):
        """Test workflow start failure (API error during initialization)"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Simulate API error during workflow start
            mock_client.start_workflow = AsyncMock(side_effect=Exception("API Error: Invalid workflow type"))

            result = await run_workflow(
                workflow_name="invalid_workflow",
                message="Test workflow", 
                max_turns=10,
                ctx=mock_context,
            )

            assert result["status"] == "error"
            assert "API Error: Invalid workflow type" in result["error"]
            assert result["workflow_name"] == "invalid_workflow"
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_run_workflow_missing_run_id(self, mock_context):
        """Test workflow start when API doesn't return run_id"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Simulate API response without run_id
            mock_client.start_workflow = AsyncMock(return_value={"status": "error", "message": "Invalid request"})

            result = await run_workflow(
                workflow_name="test",
                message="Test workflow",
                max_turns=10,
                ctx=mock_context,
            )

            assert result["status"] == "error"
            assert "Failed to start workflow" in result["error"]
            assert result["workflow_name"] == "test"
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_run_workflow_client_not_configured(self):
        """Test behavior when client is not configured"""
        # Reset global client
        import automagik_tools.tools.automagik_workflows as workflow_module

        original_client = workflow_module.client
        workflow_module.client = None

        try:
            with pytest.raises(ValueError, match="Tool not configured"):
                await run_workflow(workflow_name="test", message="Test workflow")
        finally:
            workflow_module.client = original_client

    @pytest.mark.asyncio
    async def test_run_workflow_api_error(self, mock_context):
        """Test handling of API errors"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(side_effect=Exception("API Error"))

            result = await run_workflow(
                workflow_name="test", message="Test workflow", ctx=mock_context
            )

            assert result["status"] == "error"
            assert "API Error" in result["error"]
            mock_context.error.assert_called()


class TestListWorkflows:
    """Test list_workflows function"""

    @pytest.mark.asyncio
    async def test_list_workflows(self, mock_context):
        """Test listing available workflows"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_workflows = [
                {"name": "test", "description": "Test workflow"},
                {"name": "fix", "description": "Bug fix workflow"},
            ]
            mock_client.list_workflows = AsyncMock(return_value=mock_workflows)

            result = await list_workflows(ctx=mock_context)

            assert len(result) == 2
            assert result[0]["name"] == "test"
            assert result[1]["name"] == "fix"
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_context):
        """Test error handling in list_workflows"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_workflows = AsyncMock(side_effect=Exception("Connection failed"))

            result = await list_workflows(ctx=mock_context)

            assert len(result) == 1
            assert "error" in result[0]
            assert "Connection failed" in result[0]["error"]
            mock_context.error.assert_called()


class TestListRecentRuns:
    """Test list_recent_runs function"""

    @pytest.mark.asyncio
    async def test_list_recent_runs(self, mock_context):
        """Test listing recent workflow runs"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_runs_response = {
                "runs": [
                    {"run_id": "run-1", "status": "completed", "workflow_name": "test"},
                    {"run_id": "run-2", "status": "running", "workflow_name": "fix"},
                ]
            }
            mock_client.list_runs = AsyncMock(return_value=mock_runs_response)

            result = await list_recent_runs(
                workflow_name="test", status="completed", page_size=5, ctx=mock_context
            )

            assert len(result["runs"]) == 2
            assert result["runs"][0]["run_id"] == "run-1"
            mock_context.info.assert_called()


class TestGetWorkflowStatus:
    """Test get_workflow_status function"""

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, mock_context):
        """Test getting workflow status with comprehensive API response"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Create a comprehensive mock response that includes all the fields
            # mentioned in the bug report
            mock_status = {
                "status": "running",
                "turns": 7,
                "current_turns": 7,
                "max_turns": 30,
                "workflow_name": "test",
                "progress": "Processing files",
                "current_phase": "execution",
                "cache_efficiency": 85.5,
                "tools_used": ["bash", "edit", "read"],
                "performance_score": 92.3,
                "execution_time": 145.2,
                "total_cost": 0.0234,
                "total_tokens": 12450,
                "token_breakdown": {
                    "input_tokens": 8900,
                    "output_tokens": 3550,
                    "cached_tokens": 2100
                },
                "started_at": "2024-01-15T10:00:00Z",
                "error": None
            }
            # Use AsyncMock to properly handle await
            mock_client.get_workflow_status = AsyncMock(return_value=mock_status)

            result = await get_workflow_status(run_id="test-123", ctx=mock_context)

            # Verify that ALL comprehensive data is preserved
            assert result["status"] == "running"
            assert result["turns"] == 7
            assert result["current_turns"] == 7
            assert result["max_turns"] == 30
            assert result["current_phase"] == "execution"
            assert result["cache_efficiency"] == 85.5
            assert result["tools_used"] == ["bash", "edit", "read"]
            assert result["performance_score"] == 92.3
            assert result["token_breakdown"]["input_tokens"] == 8900
            assert result["run_id"] == "test-123"  # Added by the function
            
            # Verify context logging includes comprehensive data
            mock_context.info.assert_called()
            
            # Check that context reported cache efficiency and tools used
            info_calls = [call.args[0] for call in mock_context.info.call_args_list]
            assert any("Cache efficiency: 85.5%" in call for call in info_calls)
            assert any("Tools used: bash, edit, read" in call for call in info_calls)
            assert any("Current phase: execution" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_comprehensive_data_parity(self, mock_context):
        """Test that MCP tool returns same comprehensive data as direct API"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            # Simulate a comprehensive API response with all expected fields
            direct_api_response = {
                "run_id": "test-run-123",
                "status": "running",
                "workflow_name": "implement",
                "turns": 15,
                "max_turns": 30,
                "current_phase": "initialization",
                "cache_efficiency": 92.8,
                "tools_used": ["bash", "edit", "read", "write"],
                "performance_score": 88.5,
                "execution_time": 245.7,
                "total_cost": 0.0456,
                "total_tokens": 18720,
                "token_breakdown": {
                    "input_tokens": 12400,
                    "output_tokens": 6320,
                    "cached_tokens": 3890
                },
                "started_at": "2024-01-15T14:30:00Z",
                "completed_at": None,
                "error": None,
                "logs": "Processing user request...",
                "session_id": "session-789",
                # Additional comprehensive fields
                "memory_usage": 85.2,
                "average_response_time": 1.8,
                "success_rate": 0.95
            }
            
            mock_client.get_workflow_status = AsyncMock(return_value=direct_api_response)

            # Call the MCP tool function
            mcp_result = await get_workflow_status(run_id="test-run-123", ctx=mock_context)

            # Verify that ALL fields from the direct API are preserved in MCP response
            for key, expected_value in direct_api_response.items():
                assert key in mcp_result, f"Missing field '{key}' in MCP response"
                assert mcp_result[key] == expected_value, f"Field '{key}' value mismatch: expected {expected_value}, got {mcp_result[key]}"
            
            # Verify run_id is properly added even if not in original response
            assert mcp_result["run_id"] == "test-run-123"
            
            # Verify comprehensive fields that were mentioned in the bug report
            assert "current_phase" in mcp_result
            assert "cache_efficiency" in mcp_result  
            assert "tools_used" in mcp_result
            assert "performance_score" in mcp_result
            assert "token_breakdown" in mcp_result
            assert isinstance(mcp_result["token_breakdown"], dict)
            assert "input_tokens" in mcp_result["token_breakdown"]

    @pytest.mark.asyncio
    async def test_get_status_error(self, mock_context):
        """Test error handling in get_workflow_status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.get_workflow_status = AsyncMock(side_effect=Exception("Status error"))

            result = await get_workflow_status(run_id="test-123", ctx=mock_context)

            assert "error" in result
            assert "Status error" in result["error"]
            assert result["run_id"] == "test-123"
            mock_context.error.assert_called()


class TestClaudeCodeClient:
    """Test the HTTP client functionality"""

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return ClaudeCodeClient(mock_config)

    @pytest.mark.asyncio
    async def test_start_workflow_request(self, client):
        """Test start workflow HTTP request"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"run_id": "test-123"}
            mock_client.request.return_value = mock_response

            result = await client.start_workflow("test", {"message": "test"})

            assert result["run_id"] == "test-123"
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_authentication(self, client):
        """Test client includes authentication headers"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_client.request.return_value = mock_response

            await client._make_request("GET", "/test")

            call_kwargs = mock_client.request.call_args.kwargs
            assert "X-API-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-API-Key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_client_retry_logic(self, client):
        """Test client retry logic on failures"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First two calls fail with connection error, third succeeds
            import httpx
            mock_client.request.side_effect = [
                httpx.ConnectError("Connection error"),
                httpx.ConnectError("Connection error"),
                Mock(status_code=200, json=lambda: {"success": True}),
            ]

            with patch("asyncio.sleep"):  # Speed up the test
                result = await client._make_request("GET", "/test")

            assert result["success"] is True
            assert mock_client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_client_max_retries_exceeded(self, client):
        """Test client when max retries are exceeded"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            import httpx
            mock_client.request.side_effect = httpx.ConnectError("Persistent error")

            with patch("asyncio.sleep"):  # Speed up the test
                with pytest.raises(ConnectionError, match="Failed to connect"):
                    await client._make_request("GET", "/test")

            # Should try max_retries + 1 times (initial + 2 retries = 3 total)
            assert mock_client.request.call_count == 3


class TestAutomagikWorkflowsIntegration:
    """Test integration with automagik hub"""

    def test_hub_mounting(self):
        """Test tool can be mounted in hub"""
        import subprocess

        result = subprocess.run(
            ["uvx", "automagik-tools", "list"],
            capture_output=True,
            text=True,
            cwd="/home/namastex/workspace/automagik-tools",
        )

        # Tool should be discoverable (but may not be listed if not registered yet)
        # This test mainly verifies the CLI doesn't crash
        assert result.returncode == 0

    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, server):
        """Test MCP protocol compliance"""
        # Test tool listing
        tools_dict = await server.get_tools()
        assert len(tools_dict) == 9  # Enhanced from 4 to 9 tools

        # Test each tool has required properties
        for tool_name, tool in tools_dict.items():
            assert tool_name is not None
            assert hasattr(tool, "fn")  # FastMCP Tool has fn attribute
            assert tool.description is not None
            assert len(tool.description.strip()) > 0


class TestAutomagikWorkflowsPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    async def test_run_workflow_response_time(self, mock_context):
        """Test workflow execution response time"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow = AsyncMock(return_value={"run_id": "perf-test"})
            mock_client.get_workflow_status.return_value = {
                "status": "completed",
                "turns": 1,
                "result": {"success": True},
            }

            start = time.time()
            await run_workflow(
                workflow_name="test",
                message="Performance test",
                max_turns=5,
                ctx=mock_context,
            )
            duration = time.time() - start

            # Should respond quickly with mocked API
            assert duration < 1.0  # 1 second threshold

    @pytest.mark.asyncio
    async def test_context_progress_reporting(self, mock_context):
        """Test that progress reporting works correctly in get_workflow_status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.get_workflow_status = AsyncMock(return_value={
                "status": "running", 
                "turns": 8,
                "max_turns": 10,
                "workflow_name": "test",
                "current_phase": "execution"
            })

            await get_workflow_status(run_id="progress-test", ctx=mock_context)

            # Verify progress was reported
            mock_context.report_progress.assert_called_once()

            # Check that progress reporting shows correct values
            call_args = mock_context.report_progress.call_args
            args, kwargs = call_args
            assert kwargs["progress"] == 8  # current turns
            assert kwargs["total"] == 10  # max turns
