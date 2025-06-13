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
)
from automagik_tools.tools.automagik_workflows.config import AutomagikWorkflowsConfig
from automagik_tools.tools.automagik_workflows.client import ClaudeCodeClient


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    return AutomagikWorkflowsConfig(
        api_key="test-api-key",
        base_url="https://api.test.com",
        timeout=30,
        polling_interval=1,
        max_retries=2,
    )


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
        assert metadata["version"] == "1.0.0"
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
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names


class TestRunWorkflow:
    """Test run_workflow function"""

    @pytest.mark.asyncio
    async def test_run_workflow_success(self, mock_context):
        """Test successful workflow execution"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow.return_value = {"run_id": "test-123"}
            mock_client.get_workflow_status.side_effect = [
                {"status": "running", "turns": 5},
                {"status": "completed", "turns": 10, "result": {"success": True}},
            ]

            result = await run_workflow(
                workflow_name="test",
                message="Test workflow",
                max_turns=20,
                ctx=mock_context,
            )

            assert result["status"] == "completed"
            assert result["run_id"] == "test-123"
            assert result["workflow_name"] == "test"
            assert result["turns_used"] == 10
            assert result["max_turns"] == 20
            assert "execution_time" in result

            mock_context.info.assert_called()
            mock_context.report_progress.assert_called()

    @pytest.mark.asyncio
    async def test_run_workflow_failure(self, mock_context):
        """Test workflow execution failure"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow.return_value = {"run_id": "test-456"}
            mock_client.get_workflow_status.return_value = {
                "status": "failed",
                "turns": 3,
                "error": "Workflow failed due to timeout",
            }

            result = await run_workflow(
                workflow_name="test",
                message="Test workflow",
                max_turns=10,
                ctx=mock_context,
            )

            assert result["status"] == "failed"
            assert result["error"] == "Workflow failed due to timeout"
            assert result["turns_used"] == 3
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_run_workflow_timeout(self, mock_context):
        """Test workflow execution timeout"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow.return_value = {"run_id": "test-789"}
            mock_client.get_workflow_status.return_value = {
                "status": "running",
                "turns": 2,
            }

            # Use very short timeout to trigger timeout condition
            result = await run_workflow(
                workflow_name="test",
                message="Test workflow",
                max_turns=10,
                timeout=1,  # 1 second timeout
                ctx=mock_context,
            )

            assert result["status"] == "timeout"
            assert result["run_id"] == "test-789"
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
            mock_client.start_workflow.side_effect = Exception("API Error")

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
            mock_client.list_workflows.return_value = mock_workflows

            result = await list_workflows(ctx=mock_context)

            assert len(result) == 2
            assert result[0]["name"] == "test"
            assert result[1]["name"] == "fix"
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_context):
        """Test error handling in list_workflows"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.list_workflows.side_effect = Exception("Connection failed")

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
            mock_client.list_runs.return_value = mock_runs_response

            result = await list_recent_runs(
                workflow_name="test", status="completed", limit=5, ctx=mock_context
            )

            assert len(result) == 2
            assert result[0]["run_id"] == "run-1"
            mock_context.info.assert_called()


class TestGetWorkflowStatus:
    """Test get_workflow_status function"""

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, mock_context):
        """Test getting workflow status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_status = {
                "status": "running",
                "turns": 7,
                "progress": "Processing files",
            }
            mock_client.get_workflow_status.return_value = mock_status

            result = await get_workflow_status(run_id="test-123", ctx=mock_context)

            assert result["status"] == "running"
            assert result["turns"] == 7
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_status_error(self, mock_context):
        """Test error handling in get_workflow_status"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.get_workflow_status.side_effect = Exception("Status error")

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

            call_kwargs = mock_client.request.call_args[1]
            assert "X-API-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-API-Key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_client_retry_logic(self, client):
        """Test client retry logic on failures"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First two calls fail, third succeeds
            mock_client.request.side_effect = [
                Exception("Connection error"),
                Exception("Connection error"),
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
            mock_client.request.side_effect = Exception("Persistent error")

            with patch("asyncio.sleep"):  # Speed up the test
                with pytest.raises(Exception, match="Persistent error"):
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
        assert len(tools_dict) == 4

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
            mock_client.start_workflow.return_value = {"run_id": "perf-test"}
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
        """Test that progress reporting works correctly"""
        with patch("automagik_tools.tools.automagik_workflows.client") as mock_client:
            mock_client.start_workflow.return_value = {"run_id": "progress-test"}
            mock_client.get_workflow_status.side_effect = [
                {"status": "running", "turns": 2},
                {"status": "running", "turns": 5},
                {"status": "completed", "turns": 8, "result": {}},
            ]

            await run_workflow(
                workflow_name="test",
                message="Progress test",
                max_turns=10,
                ctx=mock_context,
            )

            # Verify progress was reported multiple times
            assert mock_context.report_progress.call_count >= 2

            # Check that final progress shows completion
            final_call = mock_context.report_progress.call_args_list[-1]
            args, kwargs = final_call
            assert kwargs["progress"] == 10  # max_turns
            assert kwargs["total"] == 10
