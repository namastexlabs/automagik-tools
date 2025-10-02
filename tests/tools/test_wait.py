"""
Tests for Wait Utility
"""

import pytest
import asyncio
import subprocess
from unittest.mock import Mock, patch, AsyncMock
from fastmcp import Context

from automagik_tools.tools.wait import (
    create_server,
    get_metadata,
    get_config_class,
    wait_minutes,
)

# Extract actual function from FunctionTool wrapper
wait_minutes_fn = wait_minutes.fn if hasattr(wait_minutes, "fn") else wait_minutes
from automagik_tools.tools.wait.config import WaitConfig


@pytest.fixture
def mock_config(monkeypatch):
    """Create mock configuration"""
    monkeypatch.setenv("WAIT_MAX_DURATION", "300")  # 5 minutes
    monkeypatch.setenv("WAIT_DEFAULT_PROGRESS_INTERVAL", "0.5")
    return WaitConfig()


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
    """Create FastMCP server with mock config"""
    return create_server(mock_config)


@pytest.fixture(autouse=True)
def setup_config(mock_config):
    """Setup the global config for testing"""
    import automagik_tools.tools.wait as wait_module

    # Store original config
    original_config = wait_module.config

    # Set test config
    wait_module.config = mock_config

    yield

    # Restore original config
    wait_module.config = original_config


class TestWaitMetadata:
    """Test metadata functions"""

    def test_metadata_structure(self):
        """Test metadata has required fields"""
        metadata = get_metadata()

        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert metadata["name"] == "wait"
        assert metadata["version"] == "2.2.0"
        assert "Simple wait functionality" in metadata["description"]
        assert "author" in metadata
        assert "category" in metadata
        assert "tags" in metadata

    def test_config_class(self):
        """Test config class is returned"""
        config_class = get_config_class()
        assert config_class == WaitConfig


class TestWaitConfig:
    """Test configuration"""

    def test_default_config(self, monkeypatch):
        """Test default configuration values"""
        # Clear any env vars that might affect defaults
        monkeypatch.delenv("WAIT_MAX_DURATION", raising=False)
        monkeypatch.delenv("WAIT_DEFAULT_PROGRESS_INTERVAL", raising=False)

        config = WaitConfig()
        assert config.max_duration == 3600  # 60 minutes default
        assert config.default_progress_interval == 1.0

    def test_env_config(self, monkeypatch):
        """Test environment-based configuration"""
        monkeypatch.setenv("WAIT_MAX_DURATION", "120")
        monkeypatch.setenv("WAIT_DEFAULT_PROGRESS_INTERVAL", "0.5")

        config = WaitConfig()
        assert config.max_duration == 120
        assert config.default_progress_interval == 0.5


class TestWaitServer:
    """Test server creation and configuration"""

    def test_server_creation(self, mock_config):
        """Test server is created successfully"""
        server = create_server(mock_config)
        assert server is not None

    async def test_server_has_tools(self, server):
        """Test server has expected tools"""
        # Get available tools from the FastMCP server
        tools = await server.get_tools()
        tool_names = list(tools.keys())

        expected_tools = {"wait_minutes"}
        assert expected_tools.issubset(set(tool_names))

    def test_server_configuration(self, mock_config):
        """Test server is properly configured"""
        server = create_server(mock_config)
        assert server.name == "Wait Utility"


class TestWaitMinutes:
    """Test wait_minutes function"""

    @pytest.mark.asyncio
    async def test_wait_minutes_basic(self, mock_context):
        """Test basic wait_minutes functionality"""
        # Use small duration for fast test
        result = await wait_minutes_fn(0.1, mock_context)

        assert result["status"] == "completed"
        assert result["duration_minutes"] == 0.1
        assert "duration_seconds" in result
        assert result["duration_seconds"] > 5.5  # ~6 seconds for 0.1 minutes
        assert "start_time" in result
        assert "start_iso" in result
        assert "end_time" in result
        assert "end_iso" in result

    @pytest.mark.asyncio
    async def test_wait_minutes_without_context(self):
        """Test wait_minutes without context"""
        result = await wait_minutes_fn(0.05)  # 3 seconds

        assert result["status"] == "completed"
        assert result["duration_minutes"] == 0.05
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_wait_minutes_cancellation(self, mock_context):
        """Test wait_minutes cancellation behavior"""
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
            result = await wait_minutes_fn(2.0, mock_context)

            assert result["status"] == "cancelled"
            assert result["duration_minutes"] == 2.0
            assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_wait_minutes_negative_duration(self):
        """Test wait_minutes with negative duration"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await wait_minutes_fn(-1.0)

    @pytest.mark.asyncio
    async def test_wait_minutes_exceeds_max(self):
        """Test wait_minutes exceeding max duration"""
        with pytest.raises(ValueError, match="exceeds max"):
            await wait_minutes_fn(10.0)  # 600 seconds, exceeds 300s limit

    @pytest.mark.asyncio
    async def test_wait_minutes_no_config(self):
        """Test wait_minutes without configuration"""
        import automagik_tools.tools.wait as wait_module

        original_config = wait_module.config
        wait_module.config = None

        try:
            with pytest.raises(ValueError, match="Tool not configured"):
                await wait_minutes_fn(1.0)
        finally:
            wait_module.config = original_config


class TestWaitIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_hub_discovery(self):
        """Test tool can be discovered through hub"""
        from automagik_tools.hub import create_hub_server

        hub_server = create_hub_server()
        tools = await hub_server.get_tools()

        # Should have wait_minutes from wait tool
        wait_tools = [name for name in tools.keys() if "wait" in name]
        assert len(wait_tools) > 0

    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, server):
        """Test MCP protocol compliance"""
        # Test server has tools
        tools = await server.get_tools()
        assert len(tools) == 1  # Single wait_minutes function

        # Test each tool has required properties
        for tool_name, tool_info in tools.items():
            assert tool_name is not None
            assert hasattr(tool_info, "name")
            assert hasattr(tool_info, "description")

    def test_tool_serving(self):
        """Test tool can be served via CLI"""
        # Test that the wait tool can be started (will timeout, which is expected)
        result = subprocess.run(
            ["timeout", "2s", "uv", "run", "automagik-tools", "tool", "wait"],
            capture_output=True,
            text=True,
        )
        # Should timeout (exit code 124) as the server would run indefinitely
        assert result.returncode in [0, 124]  # 0 = clean exit, 124 = timeout


class TestWaitErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_zero_duration(self):
        """Test zero duration is rejected"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await wait_minutes_fn(0)

    @pytest.mark.asyncio
    async def test_very_small_duration(self, mock_context):
        """Test very small durations work"""
        result = await wait_minutes_fn(0.01, mock_context)  # 0.6 seconds

        assert result["status"] == "completed"
        assert result["duration_minutes"] == 0.01


class TestWaitPerformance:
    """Performance and timing tests"""

    @pytest.mark.asyncio
    async def test_function_call_overhead(self, mock_context):
        """Test function call overhead is minimal"""
        import time

        start = time.time()
        # Very short wait to measure overhead
        await wait_minutes_fn(0.01, mock_context)
        end = time.time()

        # Should complete in reasonable time (allowing some overhead)
        assert end - start < 2.0  # Should be ~0.6s + overhead

    @pytest.mark.asyncio
    async def test_real_timing_accuracy(self, mock_context):
        """Test timing accuracy within reasonable bounds"""
        import time

        expected_duration = 0.05  # 3 seconds
        start = time.time()
        result = await wait_minutes_fn(expected_duration, mock_context)
        end = time.time()

        actual_wall_time = end - start
        reported_duration = result["duration_seconds"]

        # Allow 100% tolerance for timing accuracy due to progress updates
        tolerance = expected_duration * 60
        assert abs(actual_wall_time - expected_duration * 60) < tolerance
        assert abs(reported_duration - expected_duration * 60) < tolerance
