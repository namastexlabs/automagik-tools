"""
Tests for Wait Utility MCP tool
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from fastmcp import Context

from automagik_tools.tools.wait import (
    create_server,
    get_metadata,
    get_config_class,
    wait_seconds,
    wait_minutes,
    wait_until_timestamp,
    wait_with_progress,
)
from automagik_tools.tools.wait.config import WaitConfig


@pytest.fixture
def mock_config(monkeypatch):
    """Create mock configuration"""
    # Set environment variables to override defaults
    monkeypatch.setenv("WAIT_MAX_DURATION", "10")
    monkeypatch.setenv("WAIT_DEFAULT_PROGRESS_INTERVAL", "0.1")
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
    """Create test server instance"""
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
    """Test tool metadata and discovery"""

    def test_metadata_structure(self):
        """Test that metadata has required fields"""
        metadata = get_metadata()
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert metadata["name"] == "wait"
        assert metadata["version"] == "2.1.0"
        assert "Timing functions" in metadata["description"]
        assert "author" in metadata
        assert "category" in metadata
        assert "tags" in metadata

    def test_config_class(self):
        """Test config class is returned correctly"""
        config_class = get_config_class()
        assert config_class == WaitConfig


class TestWaitConfig:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration values"""
        # This test runs in isolation without the mock_config fixture
        # so it should get actual defaults
        import os

        # Temporarily clear any environment variables that might affect this test
        orig_max = os.environ.pop("WAIT_MAX_DURATION", None)
        orig_interval = os.environ.pop("WAIT_DEFAULT_PROGRESS_INTERVAL", None)

        try:
            config = WaitConfig()
            assert config.max_duration == 3600  # 1 hour
            assert config.default_progress_interval == 1.0
        finally:
            # Restore environment variables
            if orig_max:
                os.environ["WAIT_MAX_DURATION"] = orig_max
            if orig_interval:
                os.environ["WAIT_DEFAULT_PROGRESS_INTERVAL"] = orig_interval

    def test_env_config(self, monkeypatch):
        """Test configuration from environment"""
        monkeypatch.setenv("WAIT_MAX_DURATION", "7200")
        monkeypatch.setenv("WAIT_DEFAULT_PROGRESS_INTERVAL", "2.0")

        config = WaitConfig()
        assert config.max_duration == 7200
        assert config.default_progress_interval == 2.0


class TestWaitServer:
    """Test MCP server creation and tools"""

    def test_server_creation(self, server):
        """Test server is created with correct metadata"""
        assert server.name == "Wait Utility"

    @pytest.mark.asyncio
    async def test_server_has_tools(self, server):
        """Test server has expected tools registered"""
        # Get available tools from the FastMCP server
        tools = await server.get_tools()
        tool_names = list(tools.keys())

        expected_tools = {
            "wait_seconds", "wait_minutes", "wait_until_timestamp", "wait_with_progress"
        }
        assert expected_tools.issubset(set(tool_names))

    def test_server_configuration(self, mock_config):
        """Test server is properly configured"""
        server = create_server(mock_config)
        assert server is not None

        # Verify global config is set
        import automagik_tools.tools.wait as wait_module

        assert wait_module.config == mock_config


class TestWaitSeconds:
    """Test wait_seconds function"""

    @pytest.mark.asyncio
    async def test_wait_seconds_basic(self, mock_context):
        """Test basic wait_seconds functionality"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            result = await wait_seconds(2.5, mock_context)

            # Verify sleep was called with correct duration
            mock_sleep.assert_called_once_with(2.5)

            # Verify result structure
            assert result["status"] == "completed"
            assert "duration" in result
            assert "start_time" in result
            assert "start_iso" in result
            assert "end_time" in result
            assert "end_iso" in result

    @pytest.mark.asyncio
    async def test_wait_seconds_without_context(self):
        """Test wait_seconds without context"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            result = await wait_seconds(1.0)

            mock_sleep.assert_called_once_with(1.0)
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_wait_seconds_cancellation(self, mock_context):
        """Test wait_seconds cancellation handling"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()

            result = await wait_seconds(5.0, mock_context)

            assert result["status"] == "cancelled"
            assert "duration" in result
            assert "start_time" in result
            assert "start_iso" in result

    @pytest.mark.asyncio
    async def test_wait_seconds_negative_duration(self):
        """Test wait_seconds with negative duration"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await wait_seconds(-1.0)

    @pytest.mark.asyncio
    async def test_wait_seconds_exceeds_max(self):
        """Test wait_seconds exceeding max duration"""
        with pytest.raises(ValueError, match="exceeds max"):
            await wait_seconds(15.0)  # mock_config has max_duration=10

    @pytest.mark.asyncio
    async def test_wait_seconds_no_config(self):
        """Test wait_seconds without configuration"""
        import automagik_tools.tools.wait as wait_module

        original_config = wait_module.config
        wait_module.config = None

        try:
            with pytest.raises(ValueError, match="Tool not configured"):
                await wait_seconds(1.0)
        finally:
            wait_module.config = original_config


class TestWaitMinutes:
    """Test wait_minutes function"""

    @pytest.mark.asyncio
    async def test_wait_minutes_conversion(self, mock_context):
        """Test wait_minutes converts to seconds correctly"""
        with patch("automagik_tools.tools.wait.wait_seconds") as mock_wait_seconds:
            mock_wait_seconds.return_value = {
                "status": "completed",
                "duration": 120.0,
                "start_time": 1234567890.0,
                "start_iso": "2024-01-01T00:00:00Z",
                "end_time": 1234568010.0,
                "end_iso": "2024-01-01T00:02:00Z"
            }

            result = await wait_minutes(2.0, mock_context)

            # Verify wait_seconds was called with converted duration
            mock_wait_seconds.assert_called_once_with(120.0, mock_context)

            # Verify result includes minutes information
            assert "duration_minutes" in result
            assert result["duration_minutes"] == 2.0

    @pytest.mark.asyncio
    async def test_wait_minutes_fractional(self, mock_context):
        """Test wait_minutes with fractional minutes"""
        with patch("automagik_tools.tools.wait.wait_seconds") as mock_wait_seconds:
            mock_wait_seconds.return_value = {
                "status": "completed",
                "duration": 90.0,
                "start_time": 1234567890.0,
                "start_iso": "2024-01-01T00:00:00Z",
                "end_time": 1234567980.0,
                "end_iso": "2024-01-01T00:01:30Z"
            }

            await wait_minutes(1.5, mock_context)

            # 1.5 minutes = 90 seconds
            mock_wait_seconds.assert_called_once_with(90.0, mock_context)


class TestWaitUntilTimestamp:
    """Test wait_until_timestamp function"""

    @pytest.mark.asyncio
    async def test_wait_until_timestamp_future(self, mock_context):
        """Test waiting until future timestamp"""
        # Create a timestamp 2 seconds in the future
        future_time = datetime.now(timezone.utc) + timedelta(seconds=2)
        timestamp_str = future_time.isoformat()

        with patch("automagik_tools.tools.wait.wait_seconds") as mock_wait_seconds:
            mock_wait_seconds.return_value = {
                "status": "completed",
                "duration": 2.0,
                "start_time": 1234567890.0,
                "start_iso": "2024-01-01T00:00:00Z",
                "end_time": 1234567892.0,
                "end_iso": "2024-01-01T00:00:02Z"
            }

            result = await wait_until_timestamp(timestamp_str, mock_context)

            # Should call wait_seconds with approximately 2 seconds
            args, kwargs = mock_wait_seconds.call_args
            assert 1.8 <= args[0] <= 2.2  # Allow some tolerance for execution time

            assert "target_iso" in result

    @pytest.mark.asyncio
    async def test_wait_until_timestamp_past(self, mock_context):
        """Test waiting until past timestamp"""
        # Create a timestamp in the past
        past_time = datetime.now(timezone.utc) - timedelta(seconds=5)
        timestamp_str = past_time.isoformat()

        result = await wait_until_timestamp(timestamp_str, mock_context)

        assert result["status"] == "already_passed"
        assert result["target_iso"] == timestamp_str
        assert result["time_diff"] < 0

    @pytest.mark.asyncio
    async def test_wait_until_timestamp_invalid_format(self, mock_context):
        """Test invalid timestamp format"""
        result = await wait_until_timestamp("invalid-timestamp", mock_context)

        assert result["status"] == "error"
        assert "Invalid ISO 8601 format" in result["error"]

    @pytest.mark.asyncio
    async def test_wait_until_timestamp_exceeds_max(self, mock_context):
        """Test timestamp that exceeds max duration"""
        # Create a timestamp far in the future (more than max_duration)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=20)
        timestamp_str = future_time.isoformat()

        with pytest.raises(ValueError, match="exceeds max"):
            await wait_until_timestamp(timestamp_str, mock_context)

    @pytest.mark.asyncio
    async def test_wait_until_timestamp_with_z_suffix(self, mock_context):
        """Test timestamp with Z suffix"""
        future_time = datetime.now(timezone.utc) + timedelta(seconds=2)
        timestamp_str = future_time.isoformat().replace("+00:00", "Z")

        with patch("automagik_tools.tools.wait.wait_seconds") as mock_wait_seconds:
            mock_wait_seconds.return_value = {"status": "completed"}

            await wait_until_timestamp(timestamp_str, mock_context)

            # Should successfully parse and call wait_seconds
            mock_wait_seconds.assert_called_once()


class TestWaitWithProgress:
    """Test wait_with_progress function"""

    @pytest.mark.asyncio
    async def test_wait_with_progress_basic(self, mock_context):
        """Test basic progress reporting functionality"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            result = await wait_with_progress(0.3, 0.1, mock_context)

            # Should call sleep multiple times for progress intervals
            assert mock_sleep.call_count >= 3

            # Verify result structure
            assert result["status"] == "completed"
            assert result["duration"] >= 0.3
            assert result["interval"] == 0.1
            assert result["reports"] >= 3

    @pytest.mark.asyncio
    async def test_wait_with_progress_context_reporting(self, mock_context):
        """Test progress reporting to context"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            await wait_with_progress(0.2, 0.1, mock_context)

            # Verify context methods were called for progress reporting
            assert mock_context.report_progress.call_count >= 2

    @pytest.mark.asyncio
    async def test_wait_with_progress_cancellation(self, mock_context):
        """Test cancellation during progress wait"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()

            result = await wait_with_progress(2.0, 0.5, mock_context)

            assert result["status"] == "cancelled"
            assert "reports" in result

    @pytest.mark.asyncio
    async def test_wait_with_progress_default_interval(self, mock_context):
        """Test using default progress interval from config"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            # Call without specifying interval to get default behavior
            result = await wait_with_progress(0.2, ctx=mock_context)

            # Should use config.default_progress_interval (0.1 in mock_config) since it's different from 1.0
            assert result["interval"] == 0.1

    @pytest.mark.asyncio
    async def test_wait_with_progress_negative_duration(self):
        """Test negative duration validation"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await wait_with_progress(-1.0, 0.5)

    @pytest.mark.asyncio
    async def test_wait_with_progress_negative_interval(self):
        """Test negative interval validation"""
        with pytest.raises(ValueError, match="Interval must be positive"):
            await wait_with_progress(2.0, -0.5)

    @pytest.mark.asyncio
    async def test_wait_with_progress_exceeds_max(self):
        """Test duration exceeding max"""
        with pytest.raises(ValueError, match="exceeds max"):
            await wait_with_progress(15.0, 1.0)


class TestWaitIntegration:
    """Test integration with automagik hub"""

    def test_hub_discovery(self):
        """Test tool can be discovered by hub"""
        import subprocess

        # Test tool discovery using actual CLI
        result = subprocess.run(
            ["uv", "run", "automagik-tools", "list"],
            capture_output=True,
            text=True,
            cwd="/home/namastex/workspace/automagik-tools",
        )

        # Tool should be discoverable
        assert "wait" in result.stdout
        assert result.returncode == 0

    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, server):
        """Test MCP protocol compliance"""
        # Test server has tools
        tools = await server.get_tools()
        assert len(tools) == 4  # Four blocking wait functions

        # Test each tool has required properties
        for tool_name, tool_info in tools.items():
            assert tool_name is not None
            # FastMCP returns tool objects with description and parameters
            assert hasattr(tool_info, "description") or isinstance(tool_info, dict)
            if hasattr(tool_info, "description"):
                assert len(tool_info.description.strip()) > 0
            elif isinstance(tool_info, dict) and "description" in tool_info:
                assert len(tool_info["description"].strip()) > 0

    def test_tool_serving(self):
        """Test tool can be served standalone"""
        import subprocess

        # Test that tool can start (will timeout, but that's expected)
        result = subprocess.run(
            ["timeout", "2s", "uv", "run", "automagik-tools", "tool", "wait"],
            capture_output=True,
            text=True,
            cwd="/home/namastex/workspace/automagik-tools",
        )

        # Should start successfully (timeout is expected)
        assert result.returncode == 124  # timeout exit code


class TestWaitErrorHandling:
    """Test error scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_zero_duration(self):
        """Test zero duration handling"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await wait_seconds(0.0)

    @pytest.mark.asyncio
    async def test_very_small_duration(self, mock_context):
        """Test very small duration (should work)"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            result = await wait_seconds(0.001, mock_context)

            mock_sleep.assert_called_once_with(0.001)
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_context_error_in_progress_reporting(self, mock_context):
        """Test handling of context errors during progress reporting"""
        # Make report_progress raise an exception
        mock_context.report_progress.side_effect = Exception("Context error")

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            # Progress reporting errors should propagate for real-time streaming
            with pytest.raises(Exception, match="Context error"):
                await wait_with_progress(0.2, 0.1, mock_context)


class TestWaitPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    async def test_function_call_overhead(self, server, mock_context):
        """Test function call overhead is minimal"""
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None

            start = time.time()
            await wait_seconds(1.0, mock_context)
            duration = time.time() - start

            # Function call overhead should be minimal (not actual wait time)
            assert duration < 0.1  # 100ms threshold

    @pytest.mark.asyncio
    async def test_real_timing_accuracy(self):
        """Test real timing accuracy with very short waits"""
        start = time.time()
        result = await wait_seconds(0.05)  # 50ms wait
        actual_duration = time.time() - start

        # Should be reasonably accurate (±20ms tolerance)
        assert 0.03 <= actual_duration <= 0.07
        assert result["status"] == "completed"

        # Result should also track timing accurately
        assert 0.04 <= result["duration"] <= 0.06
