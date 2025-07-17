"""
Edge case and error handling tests for Agent Connect
"""

import pytest
import asyncio
from unittest.mock import patch, Mock

from automagik_tools.tools.agent_connect import (
    create_server,
    listen_for_message,
    send_message,
    get_channel_history,
    clear_channel,
    send_reply,
)
from automagik_tools.tools.agent_connect.config import AgentConnectConfig
from automagik_tools.tools.agent_connect.models import Message
from automagik_tools.tools.agent_connect.manager import ChannelManager


class TestAgentConnectEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_empty_channel_id(self):
        """Test handling of empty channel ID"""
        # Empty string should still work as a valid channel
        result = await send_message("", "Test message")
        assert result["status"] == "sent"
        assert result["channel_id"] == ""
    
    @pytest.mark.asyncio
    async def test_very_long_message(self):
        """Test handling of very large messages"""
        # Create a 1MB message
        large_message = "x" * (1024 * 1024)
        
        result = await send_message("test-channel", large_message)
        assert result["status"] == "sent"
        
        # Should be able to retrieve it
        history = await get_channel_history("test-channel", limit=1)
        assert history["messages"][0]["content"] == large_message
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_chars(self):
        """Test handling of unicode and special characters"""
        special_message = "Hello 世界! 🚀 \n\t\r Special chars: < > & \" '"
        
        result = await send_message("test-channel", special_message)
        assert result["status"] == "sent"
        
        # Listen for it
        listen_task = asyncio.create_task(
            listen_for_message("test-channel", timeout=1.0)
        )
        await asyncio.sleep(0.1)
        received = await listen_task
        
        assert received["status"] == "received"
        assert received["message"]["content"] == special_message
    
    @pytest.mark.asyncio
    async def test_channel_name_edge_cases(self):
        """Test various channel name formats"""
        channel_names = [
            "simple",
            "with-dashes",
            "with_underscores",
            "with.dots",
            "with:colons:and:stuff",
            "with/slashes/path/like",
            "UPPERCASE",
            "MiXeDcAsE",
            "123numeric",
            "special!@#$%^&*()",
            " spaces at ends ",
            "very-long-channel-name-" + "x" * 200
        ]
        
        for channel in channel_names:
            result = await send_message(channel, f"Test for {channel}")
            assert result["status"] == "sent"
            assert result["channel_id"] == channel
    
    @pytest.mark.asyncio
    async def test_concurrent_listeners(self):
        """Test many concurrent listeners on same channel"""
        num_listeners = 50
        received_count = 0
        
        async def listener():
            nonlocal received_count
            result = await listen_for_message("concurrent-test", timeout=2.0)
            if result["status"] == "received":
                received_count += 1
        
        # Start many listeners
        listeners = [asyncio.create_task(listener()) for _ in range(num_listeners)]
        
        # Give them time to register
        await asyncio.sleep(0.1)
        
        # Send messages for all of them
        for i in range(num_listeners):
            await send_message("concurrent-test", f"Message {i}")
        
        # Wait for all listeners
        await asyncio.gather(*listeners)
        
        # All should have received a message
        assert received_count == num_listeners
    
    @pytest.mark.asyncio
    async def test_queue_overflow(self, monkeypatch):
        """Test behavior when queue is full"""
        # Create config with tiny queue
        monkeypatch.setenv("AGENT_CONNECT_MAX_QUEUE_SIZE", "2")
        config = AgentConnectConfig()
        manager = ChannelManager(config)
        
        import automagik_tools.tools.agent_connect as bridge_module
        original_manager = bridge_module.manager
        bridge_module.manager = manager
        
        try:
            # Fill the queue
            await send_message("full-queue", "Message 1")
            await send_message("full-queue", "Message 2")
            
            # This should block briefly then succeed when using put_nowait
            await send_message("full-queue", "Message 3")
            
            # Queue should handle overflow gracefully
            history = await get_channel_history("full-queue")
            assert history["message_count"] >= 2
            
        finally:
            bridge_module.manager = original_manager
    
    @pytest.mark.asyncio
    async def test_listener_timeout_precision(self):
        """Test timeout precision and edge cases"""
        # Test very short timeout
        start = asyncio.get_event_loop().time()
        result = await listen_for_message("empty", timeout=0.01)
        duration = asyncio.get_event_loop().time() - start
        
        assert result["status"] == "timeout"
        assert duration < 0.1  # Should timeout quickly
        
        # Test zero timeout
        result = await listen_for_message("empty", timeout=0)
        assert result["status"] == "timeout"
        
        # Test None timeout uses default
        import automagik_tools.tools.agent_connect as bridge_module
        config = bridge_module.config
        
        with patch.object(asyncio, 'wait_for', side_effect=asyncio.TimeoutError) as mock_wait:
            result = await listen_for_message("empty", timeout=None)
            assert result["status"] == "timeout"
            # Should use default timeout
            mock_wait.assert_called_once()
            call_args = mock_wait.call_args[1]
            assert call_args["timeout"] == config.default_timeout
    
    @pytest.mark.asyncio
    async def test_reply_to_nonexistent_message(self):
        """Test replying to a message that doesn't have a listener"""
        result = await send_reply(
            original_message_id="fake-msg-id",
            reply_channel_id="test",
            reply_content="Reply to nothing"
        )
        
        assert result["status"] == "reply_sent"
        # Reply is sent even if no one is listening
        assert result["original_message_id"] == "fake-msg-id"
    
    @pytest.mark.asyncio
    async def test_clear_nonexistent_channel(self):
        """Test clearing a channel that doesn't exist"""
        result = await clear_channel("nonexistent-channel")
        assert result["status"] == "not_found"
        assert "not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_history_with_no_messages(self):
        """Test getting history of empty channel"""
        # Create channel but don't send messages
        from automagik_tools.tools.agent_connect import list_active_channels
        
        # Force channel creation
        listen_task = asyncio.create_task(
            listen_for_message("empty-history", timeout=0.01)
        )
        await listen_task
        
        history = await get_channel_history("empty-history")
        assert history["message_count"] == 0
        assert history["messages"] == []
        assert history["listener_count"] == 0
    
    @pytest.mark.asyncio
    async def test_metadata_edge_cases(self):
        """Test metadata handling"""
        # Test with None metadata
        result = await send_message("test", "Message", metadata=None)
        assert result["status"] == "sent"
        
        # Test with complex metadata
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "null": None,
            "bool": True,
            "number": 42.5
        }
        
        result = await send_message("test", "Message", metadata=complex_metadata)
        assert result["status"] == "sent"
        
        # Retrieve and verify
        msg = await listen_for_message("test", timeout=1.0)
        assert msg["message"]["metadata"] == complex_metadata
    
    @pytest.mark.asyncio
    async def test_rapid_send_receive(self):
        """Test rapid fire sending and receiving"""
        num_messages = 100
        
        async def sender():
            for i in range(num_messages):
                await send_message("rapid", f"Message {i}")
        
        async def receiver():
            received = []
            for _ in range(num_messages):
                msg = await listen_for_message("rapid", timeout=2.0)
                if msg["status"] == "received":
                    received.append(msg["message"]["content"])
            return received
        
        # Run sender and receiver concurrently
        sender_task = asyncio.create_task(sender())
        receiver_task = asyncio.create_task(receiver())
        
        await sender_task
        received = await receiver_task
        
        # Should receive all messages in order
        assert len(received) == num_messages
        for i, content in enumerate(received):
            assert content == f"Message {i}"


class TestAgentConnectErrorRecovery:
    """Test error recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_manager_not_initialized(self):
        """Test when manager is not initialized"""
        import automagik_tools.tools.agent_connect as bridge_module
        
        original_manager = bridge_module.manager
        bridge_module.manager = None
        
        try:
            with pytest.raises(ValueError, match="Tool not configured"):
                await send_message("test", "message")
        finally:
            bridge_module.manager = original_manager
    
    @pytest.mark.asyncio
    async def test_listener_cleanup_on_error(self):
        """Test listener count is cleaned up on errors"""
        from automagik_tools.tools.agent_connect import list_active_channels
        
        # Start a listener that will timeout
        try:
            await listen_for_message("cleanup-test", timeout=0.01)
        except:
            pass
        
        # Check listener was cleaned up
        channels = await list_active_channels()
        cleanup_channel = next(
            (c for c in channels["channels"] if c["channel_id"] == "cleanup-test"),
            None
        )
        
        if cleanup_channel:
            assert cleanup_channel["active_listeners"] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_modifications(self):
        """Test concurrent access to same channel"""
        channel = "concurrent-test"
        num_operations = 20
        
        async def random_operation(op_id):
            """Perform random operations"""
            import random
            
            op = random.choice(["send", "listen", "history", "clear"])
            
            if op == "send":
                await send_message(channel, f"Op {op_id}")
            elif op == "listen":
                await listen_for_message(channel, timeout=0.1)
            elif op == "history":
                await get_channel_history(channel)
            elif op == "clear":
                await clear_channel(channel)
        
        # Run many operations concurrently
        tasks = [
            asyncio.create_task(random_operation(i))
            for i in range(num_operations)
        ]
        
        # Should not deadlock or crash
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most operations should succeed
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count > num_operations * 0.8  # At least 80% success