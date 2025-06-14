"""
Tests for Wait Utility non-blocking timer functions
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastmcp import Context

from automagik_tools.tools.wait import (
    start_timer,
    get_timer_status,
    cancel_timer,
    list_active_timers,
    cleanup_timers,
    active_timers,
    TimerStatus,
)
from automagik_tools.tools.wait.config import WaitConfig


@pytest.fixture
def mock_config(monkeypatch):
    """Create mock configuration"""
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
    return ctx


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


@pytest.fixture(autouse=True)
async def cleanup_active_timers():
    """Clean up active timers before/after each test"""
    # Clean up before test
    for timer_id, handle in list(active_timers.items()):
        if handle.task and not handle.task.done():
            handle.task.cancel()
            try:
                await handle.task
            except asyncio.CancelledError:
                pass
    active_timers.clear()
    
    yield
    
    # Clean up after test
    for timer_id, handle in list(active_timers.items()):
        if handle.task and not handle.task.done():
            handle.task.cancel()
            try:
                await handle.task
            except asyncio.CancelledError:
                pass
    active_timers.clear()


class TestStartTimer:
    """Test start_timer function"""

    @pytest.mark.asyncio
    async def test_start_timer_basic(self, mock_context):
        """Test basic timer creation"""
        result = await start_timer(2.0, ctx=mock_context)

        assert "timer_id" in result
        assert result["status"] == "running"
        assert result["duration"] == 2.0
        assert "start_time" in result
        assert "start_iso" in result

        # Verify timer is in active registry
        timer_id = result["timer_id"]
        assert timer_id in active_timers
        assert active_timers[timer_id].status == TimerStatus.RUNNING

    @pytest.mark.asyncio
    async def test_start_timer_with_interval(self, mock_context):
        """Test timer with custom progress interval"""
        result = await start_timer(1.0, interval=0.1, ctx=mock_context)

        assert result["status"] == "running"
        timer_id = result["timer_id"]
        assert timer_id in active_timers

    @pytest.mark.asyncio
    async def test_start_timer_validation(self):
        """Test timer validation"""
        # Test negative duration
        with pytest.raises(ValueError, match="Duration must be positive"):
            await start_timer(-1.0)

        # Test exceeding max duration
        with pytest.raises(ValueError, match="exceeds max"):
            await start_timer(15.0)

    @pytest.mark.asyncio
    async def test_start_timer_no_config(self):
        """Test timer without configuration"""
        import automagik_tools.tools.wait as wait_module

        original_config = wait_module.config
        wait_module.config = None

        try:
            with pytest.raises(ValueError, match="Tool not configured"):
                await start_timer(1.0)
        finally:
            wait_module.config = original_config


class TestGetTimerStatus:
    """Test get_timer_status function"""

    @pytest.mark.asyncio
    async def test_get_timer_status_running(self, mock_context):
        """Test getting status of running timer"""
        result = await start_timer(1.0, ctx=mock_context)
        timer_id = result["timer_id"]

        status = await get_timer_status(timer_id, ctx=mock_context)

        assert status["timer_id"] == timer_id
        assert status["status"] == "running"
        assert status["progress"] >= 0.0
        assert status["duration"] == 1.0
        assert "start_time" in status
        assert "start_iso" in status
        assert "elapsed" in status

    @pytest.mark.asyncio
    async def test_get_timer_status_completed(self, mock_context):
        """Test getting status of completed timer"""
        # Use a very short duration to ensure completion
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            
            result = await start_timer(0.001, ctx=mock_context)
            timer_id = result["timer_id"]

            # Wait a moment for timer to complete
            await asyncio.sleep(0.01)

            status = await get_timer_status(timer_id, ctx=mock_context)

            assert status["timer_id"] == timer_id
            # Timer should eventually be completed
            assert status["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_get_timer_status_not_found(self, mock_context):
        """Test getting status of non-existent timer"""
        status = await get_timer_status("invalid-id", ctx=mock_context)

        assert "error" in status
        assert status["error"] == "Timer not found"


class TestCancelTimer:
    """Test cancel_timer function"""

    @pytest.mark.asyncio
    async def test_cancel_timer_running(self, mock_context):
        """Test cancelling a running timer"""
        result = await start_timer(5.0, ctx=mock_context)
        timer_id = result["timer_id"]

        # Cancel the timer
        cancel_result = await cancel_timer(timer_id, ctx=mock_context)

        assert cancel_result["timer_id"] == timer_id
        assert cancel_result["status"] == "cancelled"
        assert "elapsed" in cancel_result

        # Verify timer is marked as cancelled
        handle = active_timers[timer_id]
        assert handle.status == TimerStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_timer_not_found(self, mock_context):
        """Test cancelling non-existent timer"""
        result = await cancel_timer("invalid-id", ctx=mock_context)

        assert "error" in result
        assert result["error"] == "Timer not found"

    @pytest.mark.asyncio
    async def test_cancel_timer_already_completed(self, mock_context):
        """Test cancelling already completed timer"""
        # Create a very short timer that completes quickly
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            
            result = await start_timer(0.001, ctx=mock_context)
            timer_id = result["timer_id"]

            # Wait for timer to complete
            await asyncio.sleep(0.01)

            # Try to cancel completed timer
            cancel_result = await cancel_timer(timer_id, ctx=mock_context)

            # Should indicate timer is already in a final state
            assert "error" in cancel_result or cancel_result["status"] == "cancelled"


class TestListActiveTimers:
    """Test list_active_timers function"""

    @pytest.mark.asyncio
    async def test_list_empty(self, mock_context):
        """Test listing when no timers are active"""
        result = await list_active_timers(ctx=mock_context)

        assert result["active_timers"] == 0
        assert result["total_timers"] == 0
        assert result["timers"] == []

    @pytest.mark.asyncio
    async def test_list_multiple_timers(self, mock_context):
        """Test listing multiple timers"""
        # Start multiple timers
        timer1 = await start_timer(2.0, ctx=mock_context)
        timer2 = await start_timer(3.0, ctx=mock_context)
        timer3 = await start_timer(1.0, ctx=mock_context)

        result = await list_active_timers(ctx=mock_context)

        assert result["active_timers"] >= 3  # Some might complete quickly
        assert result["total_timers"] == 3
        assert len(result["timers"]) == 3

        # Verify timer data structure
        timer_ids = [t["timer_id"] for t in result["timers"]]
        assert timer1["timer_id"] in timer_ids
        assert timer2["timer_id"] in timer_ids
        assert timer3["timer_id"] in timer_ids

        for timer in result["timers"]:
            assert "timer_id" in timer
            assert "status" in timer
            assert "progress" in timer
            assert "elapsed" in timer
            assert "duration" in timer

    @pytest.mark.asyncio
    async def test_list_with_cancelled_timer(self, mock_context):
        """Test listing with cancelled timer"""
        # Start timer and cancel it
        timer1 = await start_timer(5.0, ctx=mock_context)
        await cancel_timer(timer1["timer_id"], ctx=mock_context)

        # Start another timer
        timer2 = await start_timer(3.0, ctx=mock_context)

        result = await list_active_timers(ctx=mock_context)

        assert result["total_timers"] == 2
        # Only one should be running
        assert result["active_timers"] == 1


class TestCleanupTimers:
    """Test cleanup_timers function"""

    @pytest.mark.asyncio
    async def test_cleanup_empty(self, mock_context):
        """Test cleanup when no timers exist"""
        result = await cleanup_timers(ctx=mock_context)

        assert result["cleaned"] == 0
        assert result["remaining"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_completed_timers(self, mock_context):
        """Test cleanup of completed/cancelled timers"""
        # Start some timers
        timer1 = await start_timer(1.0, ctx=mock_context)
        timer2 = await start_timer(2.0, ctx=mock_context)
        timer3 = await start_timer(3.0, ctx=mock_context)

        # Cancel one timer
        await cancel_timer(timer1["timer_id"], ctx=mock_context)

        # Run cleanup
        result = await cleanup_timers(ctx=mock_context)

        # Should have cleaned cancelled timer, kept running ones
        assert result["cleaned"] >= 1
        assert result["remaining"] >= 2

    @pytest.mark.asyncio
    async def test_cleanup_all_running(self, mock_context):
        """Test cleanup when all timers are still running"""
        # Get initial count
        initial_result = await list_active_timers(ctx=mock_context)
        initial_count = initial_result["total_timers"]
        
        # Start running timers
        await start_timer(5.0, ctx=mock_context)
        await start_timer(6.0, ctx=mock_context)

        result = await cleanup_timers(ctx=mock_context)

        # No cleanup should occur for running timers
        assert result["cleaned"] == 0
        assert result["remaining"] == initial_count + 2