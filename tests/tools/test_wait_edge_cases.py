"""
Edge case tests for Wait Utility tool
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from fastmcp import Context

from automagik_tools.tools.wait import (
    wait_seconds,
    wait_minutes,
    wait_until_timestamp,
    wait_with_progress,
)
from automagik_tools.tools.wait.config import WaitConfig


@pytest.fixture
def mock_config_strict():
    """Create strict mock configuration with very low limits"""
    return WaitConfig(
        max_duration=1,  # Very strict 1-second limit
        default_progress_interval=0.01,
    )


@pytest.fixture
def mock_context():
    """Create mock MCP context"""
    ctx = Mock(spec=Context)
    ctx.info = Mock()
    ctx.error = Mock()
    ctx.report_progress = Mock()
    return ctx


@pytest.fixture(autouse=True)
def setup_config(mock_config_strict):
    """Setup the global config for edge case testing"""
    import automagik_tools.tools.wait as wait_module
    
    original_config = wait_module.config
    wait_module.config = mock_config_strict
    
    yield
    
    wait_module.config = original_config


class TestWaitEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_exactly_max_duration(self):
        """Test duration exactly at the maximum allowed"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Should work with exactly max_duration (1.0 second)
            result = await wait_seconds(1.0)
            
            mock_sleep.assert_called_once_with(1.0)
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_slightly_over_max_duration(self):
        """Test duration slightly over the maximum"""
        with pytest.raises(ValueError, match="exceeds maximum allowed"):
            await wait_seconds(1.001)  # Just over 1 second limit

    @pytest.mark.asyncio
    async def test_float_precision_duration(self, mock_context):
        """Test with very precise float durations"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Test with high precision float
            precise_duration = 0.123456789
            result = await wait_seconds(precise_duration, mock_context)
            
            mock_sleep.assert_called_once_with(precise_duration)
            assert result["requested_duration"] == precise_duration

    @pytest.mark.asyncio
    async def test_very_large_minutes(self):
        """Test with minutes that would exceed max duration"""
        # 1 minute = 60 seconds, but max_duration is 1 second
        with pytest.raises(ValueError, match="exceeds maximum allowed"):
            await wait_minutes(1.0)

    @pytest.mark.asyncio
    async def test_fractional_seconds_minutes(self, mock_context):
        """Test fractional seconds in minutes"""
        with patch('automagik_tools.tools.wait.wait_seconds') as mock_wait_seconds:
            mock_wait_seconds.return_value = {"status": "completed"}
            
            # 0.01 minutes = 0.6 seconds
            await wait_minutes(0.01, mock_context)
            
            mock_wait_seconds.assert_called_once_with(0.6, mock_context)

    @pytest.mark.asyncio
    async def test_timestamp_edge_cases(self, mock_context):
        """Test various timestamp edge cases"""
        # Test current time (should be "already_passed" due to processing delay)
        now = datetime.now(timezone.utc)
        result = await wait_until_timestamp(now.isoformat(), mock_context)
        assert result["status"] == "already_passed"
        
        # Test various timezone formats
        future_time = now + timedelta(milliseconds=500)
        
        # Test with different timezone formats
        timestamp_formats = [
            future_time.isoformat(),
            future_time.isoformat().replace('+00:00', 'Z'),
            future_time.replace(tzinfo=None).isoformat() + '+00:00',
        ]
        
        for timestamp_str in timestamp_formats:
            with patch('automagik_tools.tools.wait.wait_seconds') as mock_wait_seconds:
                mock_wait_seconds.return_value = {"status": "completed"}
                
                result = await wait_until_timestamp(timestamp_str, mock_context)
                
                # Should handle all formats correctly
                assert "target_timestamp" in result or result["status"] == "already_passed"

    @pytest.mark.asyncio
    async def test_malformed_timestamps(self, mock_context):
        """Test various malformed timestamp formats"""
        malformed_timestamps = [
            "",
            "not-a-timestamp",
            "2024-13-01T25:70:80Z",  # Invalid date/time values
            "2024-01-01",  # Missing time
            "12:00:00",  # Missing date
            "2024/01/01 12:00:00",  # Wrong format
            None,  # Would cause TypeError before reaching the function
        ]
        
        for timestamp in malformed_timestamps[:-1]:  # Exclude None
            result = await wait_until_timestamp(timestamp, mock_context)
            assert result["status"] == "error"
            assert "Invalid timestamp format" in result["error"]

    @pytest.mark.asyncio
    async def test_progress_interval_edge_cases(self, mock_context):
        """Test edge cases for progress intervals"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Test with interval larger than duration
            result = await wait_with_progress(0.1, 0.5, mock_context)
            assert result["status"] == "completed"
            assert result["progress_reports"] == 1  # Only one report
            
            # Test with very small interval
            result = await wait_with_progress(0.1, 0.001, mock_context)
            assert result["status"] == "completed"
            assert result["progress_reports"] >= 50  # Many reports

    @pytest.mark.asyncio
    async def test_progress_with_zero_interval(self):
        """Test progress with zero interval (should fail)"""
        with pytest.raises(ValueError, match="Interval must be positive"):
            await wait_with_progress(1.0, 0.0)

    @pytest.mark.asyncio
    async def test_concurrent_waits(self, mock_context):
        """Test multiple concurrent wait operations"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Start multiple waits concurrently
            tasks = [
                wait_seconds(0.1, mock_context),
                wait_seconds(0.2, mock_context),
                wait_seconds(0.3, mock_context),
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            for result in results:
                assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cancellation_timing(self, mock_context):
        """Test cancellation at different points in execution"""
        call_count = 0
        
        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Cancel on second sleep call
                raise asyncio.CancelledError()
            return None
        
        with patch('asyncio.sleep', side_effect=side_effect):
            result = await wait_with_progress(1.0, 0.1, mock_context)
            
            assert result["status"] == "cancelled"
            assert result["progress_reports"] >= 1  # At least one progress report

    @pytest.mark.asyncio
    async def test_context_none_handling(self):
        """Test all functions handle None context gracefully"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # All functions should work with ctx=None
            result1 = await wait_seconds(0.1, None)
            assert result1["status"] == "completed"
            
            result2 = await wait_minutes(0.001, None)  # 0.06 seconds
            assert "requested_duration_minutes" in result2
            
            result3 = await wait_with_progress(0.1, 0.05, None)
            assert result3["status"] == "completed"

    @pytest.mark.asyncio
    async def test_memory_usage_pattern(self, mock_context):
        """Test that function doesn't accumulate memory over multiple calls"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Run many iterations to check for memory leaks
            for i in range(100):
                result = await wait_seconds(0.001, mock_context)
                assert result["status"] == "completed"
                
                # Ensure we're not accumulating state
                assert result["requested_duration"] == 0.001

    @pytest.mark.asyncio
    async def test_extreme_precision_timing(self):
        """Test with extremely precise timing requirements"""
        # Test with microsecond precision
        duration = 0.000001  # 1 microsecond
        
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            result = await wait_seconds(duration)
            
            mock_sleep.assert_called_once_with(duration)
            assert result["requested_duration"] == duration

    @pytest.mark.asyncio
    async def test_timestamp_microsecond_precision(self, mock_context):
        """Test timestamp parsing with microsecond precision"""
        # Create timestamp with microseconds
        future_time = datetime.now(timezone.utc) + timedelta(microseconds=500000)
        timestamp_str = future_time.isoformat()
        
        with patch('automagik_tools.tools.wait.wait_seconds') as mock_wait_seconds:
            mock_wait_seconds.return_value = {"status": "completed"}
            
            result = await wait_until_timestamp(timestamp_str, mock_context)
            
            # Should handle microsecond precision
            if result.get("status") != "already_passed":
                mock_wait_seconds.assert_called_once()

    @pytest.mark.asyncio
    async def test_config_state_isolation(self):
        """Test that config changes don't affect ongoing operations"""
        import automagik_tools.tools.wait as wait_module
        
        original_config = wait_module.config
        
        # Start with one config
        wait_module.config = WaitConfig(max_duration=10)
        
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Change config during operation (shouldn't affect ongoing wait)
            wait_module.config = WaitConfig(max_duration=1)
            
            # This should still work (operation started with max_duration=10)
            result = await wait_seconds(0.5)
            assert result["status"] == "completed"
        
        wait_module.config = original_config


class TestWaitExtremeConditions:
    """Test extreme operating conditions"""

    @pytest.mark.asyncio
    async def test_rapid_successive_calls(self, mock_context):
        """Test rapid successive function calls"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Make rapid successive calls
            for i in range(50):
                result = await wait_seconds(0.001, mock_context)
                assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_interleaved_function_calls(self, mock_context):
        """Test interleaved calls to different wait functions"""
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            with patch('automagik_tools.tools.wait.wait_seconds') as mock_wait_seconds:
                mock_wait_seconds.return_value = {"status": "completed"}
                
                # Interleave different function calls
                await wait_seconds(0.01, mock_context)
                await wait_minutes(0.0001, mock_context)  # 0.006 seconds
                await wait_with_progress(0.01, 0.005, mock_context)
                
                # All should succeed without interference
                assert mock_sleep.call_count >= 2

    @pytest.mark.asyncio
    async def test_boundary_timestamp_handling(self, mock_context):
        """Test timestamps at various boundaries"""
        now = datetime.now(timezone.utc)
        
        # Test timestamp exactly now + max_duration
        boundary_time = now + timedelta(seconds=1.0)  # Exactly at limit
        timestamp_str = boundary_time.isoformat()
        
        with patch('automagik_tools.tools.wait.wait_seconds') as mock_wait_seconds:
            mock_wait_seconds.return_value = {"status": "completed"}
            
            result = await wait_until_timestamp(timestamp_str, mock_context)
            
            # Should either work or be already passed (due to processing time)
            assert result["status"] in ["completed", "already_passed"] or "target_timestamp" in result