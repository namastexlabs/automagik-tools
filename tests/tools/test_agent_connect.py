"""
Tests for Agent Connect MCP tool
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import uuid

from automagik_tools.tools.agent_connect import (
    create_server,
    get_metadata,
    get_config_class,
)
from automagik_tools.tools.agent_connect.config import AgentConnectConfig
from automagik_tools.tools.agent_connect.models import Message, ChannelInfo
from automagik_tools.tools.agent_connect.manager import ChannelManager


@pytest.fixture
def mock_config(monkeypatch):
    """Create mock configuration"""
    monkeypatch.setenv("AGENT_CONNECT_MAX_QUEUE_SIZE", "100")
    monkeypatch.setenv("AGENT_CONNECT_MAX_HISTORY_SIZE", "50")
    monkeypatch.setenv("AGENT_CONNECT_DEFAULT_TIMEOUT", "60")
    return AgentConnectConfig()


@pytest.fixture
def manager(mock_config):
    """Create channel manager instance"""
    # Clean up storage directory before each test
    import shutil
    import os
    storage_dir = "/tmp/agent_connect"
    if os.path.exists(storage_dir):
        shutil.rmtree(storage_dir)
    return ChannelManager(mock_config)


@pytest.fixture
def server(mock_config):
    """Create FastMCP server with mock config"""
    return create_server(mock_config)


@pytest.fixture(autouse=True)
def setup_globals(mock_config, manager):
    """Setup global config and manager for testing"""
    import automagik_tools.tools.agent_connect as bridge_module
    
    # Store originals
    original_config = bridge_module.config
    original_manager = bridge_module.manager
    
    # Set test instances
    bridge_module.config = mock_config
    bridge_module.manager = manager
    
    yield
    
    # Restore originals
    bridge_module.config = original_config
    bridge_module.manager = original_manager


class TestAgentConnectMetadata:
    """Test metadata functions"""
    
    def test_metadata_structure(self):
        """Test metadata has required fields"""
        metadata = get_metadata()
        
        assert isinstance(metadata, dict)
        assert metadata["name"] == "agent-connect"
        assert metadata["version"] == "1.0.0"
        assert "multi-agent coordination" in metadata["description"]
        assert metadata["author"] == "Namastex Labs"
        assert metadata["category"] == "coordination"
        assert "agents" in metadata["tags"]
        assert "coordination" in metadata["tags"]
    
    def test_config_class(self):
        """Test config class is returned correctly"""
        config_class = get_config_class()
        assert config_class == AgentConnectConfig


class TestAgentConnectConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        # Create config without environment variables
        import os
        old_env = {}
        for key in list(os.environ.keys()):
            if key.startswith("AGENT_CONNECT_"):
                old_env[key] = os.environ.pop(key)
        
        try:
            config = AgentConnectConfig()
            assert config.max_queue_size == 1000
            assert config.max_history_size == 100
            assert config.default_timeout == 300.0
            assert config.cleanup_interval == 3600
            assert config.inactive_channel_hours == 24
            assert config.reply_timeout_default == 30.0
        finally:
            # Restore environment
            os.environ.update(old_env)
    
    def test_env_config(self, monkeypatch):
        """Test configuration from environment"""
        monkeypatch.setenv("AGENT_CONNECT_MAX_QUEUE_SIZE", "500")
        monkeypatch.setenv("AGENT_CONNECT_DEFAULT_TIMEOUT", "120")
        
        config = AgentConnectConfig()
        assert config.max_queue_size == 500
        assert config.default_timeout == 120.0


class TestMessageModels:
    """Test data models"""
    
    def test_message_creation(self):
        """Test Message model creation"""
        msg = Message(
            channel_id="test-channel",
            content="Hello world",
            sender_id="agent-1"
        )
        
        assert msg.channel_id == "test-channel"
        assert msg.content == "Hello world"
        assert msg.sender_id == "agent-1"
        assert msg.id is not None
        assert msg.timestamp is not None
        assert msg.in_reply_to is None
        assert msg.metadata == {}
    
    def test_message_dict_conversion(self):
        """Test Message dict conversion with ISO timestamp"""
        msg = Message(
            channel_id="test-channel",
            content="Test",
            sender_id="agent-1"
        )
        
        msg_dict = msg.dict()
        assert msg_dict["channel_id"] == "test-channel"
        assert msg_dict["content"] == "Test"
        assert isinstance(msg_dict["timestamp"], str)
        assert "T" in msg_dict["timestamp"]  # ISO format
    
    def test_channel_info_creation(self):
        """Test ChannelInfo model"""
        info = ChannelInfo(channel_id="test-channel")
        
        assert info.channel_id == "test-channel"
        assert info.active_listeners == 0
        assert info.pending_messages == 0
        assert info.total_messages_sent == 0
        assert info.created_at is not None
        assert info.last_activity is not None


class TestChannelManager:
    """Test ChannelManager functionality"""
    
    @pytest.mark.asyncio
    async def test_send_to_channel(self, manager):
        """Test sending message to channel"""
        msg = Message(
            channel_id="test-channel",
            content="Test message",
            sender_id="test-sender"
        )
        
        await manager.send_to_channel("test-channel", msg)
        
        # Check message was added to storage
        channels_data = manager.storage.get_channels_data()
        assert "test-channel" in channels_data
        assert len(channels_data["test-channel"]["messages"]) == 1
        assert channels_data["test-channel"]["messages"][0]["content"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_wait_for_message(self, manager):
        """Test waiting for messages"""
        # Send a message
        msg = Message(
            channel_id="wait-test",
            content="Test message",
            sender_id="test-sender"
        )
        await manager.send_to_channel("wait-test", msg)
        
        # Wait for the message (should return immediately)
        received_msg = await manager.wait_for_message("wait-test", timeout=1.0)
        
        assert received_msg is not None
        assert received_msg.content == "Test message"
        assert received_msg.channel_id == "wait-test"
    
    @pytest.mark.asyncio
    async def test_listener_management(self, manager):
        """Test listener increment/decrement"""
        await manager.increment_listeners("listener-test")
        assert await manager.get_listener_count("listener-test") == 1
        
        await manager.increment_listeners("listener-test")
        assert await manager.get_listener_count("listener-test") == 2
        
        await manager.decrement_listeners("listener-test")
        assert await manager.get_listener_count("listener-test") == 1
    
    @pytest.mark.asyncio
    async def test_history_limits(self, manager, mock_config):
        """Test history retrieval with limit"""
        # Send more messages than requested limit
        for i in range(10):
            msg = Message(
                channel_id="test-channel",
                content=f"Message {i}",
                sender_id="test-sender"
            )
            await manager.send_to_channel("test-channel", msg)
        
        # Request history with limit smaller than total messages
        limit = 5
        history = await manager.get_channel_history("test-channel", limit=limit)
        assert len(history) == limit
        
        # Should have kept the most recent messages
        assert history[-1].content == "Message 9"
    
    @pytest.mark.asyncio
    async def test_clear_channel(self, manager):
        """Test clearing a channel"""
        # Create channel and add messages
        msg = Message(
            channel_id="test-channel",
            content="Test",
            sender_id="test-sender"
        )
        await manager.send_to_channel("test-channel", msg)
        
        # Clear channel
        result = await manager.clear_channel("test-channel")
        assert result is True
        
        # Check cleared - verify no pending messages and empty history
        channels_data = manager.storage.get_channels_data()
        history_data = manager.storage.get_history_data()
        
        assert len(channels_data["test-channel"]["messages"]) == 0
        assert len(history_data["test-channel"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_active_channels(self, manager):
        """Test getting active channels"""
        # Create multiple channels by sending messages
        msg1 = Message(channel_id="channel-1", content="Test 1", sender_id="test")
        msg2 = Message(channel_id="channel-2", content="Test 2", sender_id="test")
        
        await manager.send_to_channel("channel-1", msg1)
        await manager.send_to_channel("channel-2", msg2)
        
        channels = await manager.get_active_channels()
        assert len(channels) == 2
        assert any(c.channel_id == "channel-1" for c in channels)
        assert any(c.channel_id == "channel-2" for c in channels)


class TestAgentConnectTools:
    """Test MCP tool functions"""
    
    @pytest.mark.asyncio
    async def test_listen_for_message_success(self, server, manager):
        """Test successful message reception"""
        # Get tool function from server
        tools = await server.get_tools()
        listen_tool = tools["listen_for_message"]
        send_tool = tools["send_message"]
        
        # Start listening in a task
        async def listen_for_msg():
            return await listen_tool.fn(channel_id="test-channel", timeout=2.0)
        
        listen_task = asyncio.create_task(listen_for_msg())
        
        # Give listener time to start
        await asyncio.sleep(0.1)
        
        # Send a message
        await send_tool.fn(
            channel_id="test-channel",
            message="Hello agent"
        )
        
        # Wait for the listener to receive
        result = await listen_task
        
        assert result["status"] == "received"
        assert result["message"]["content"] == "Hello agent"
        assert result["channel_id"] == "test-channel"
    
    @pytest.mark.asyncio
    async def test_listen_for_message_timeout(self, server):
        """Test message reception timeout"""
        tools = await server.get_tools()
        listen_tool = tools["listen_for_message"]
        
        result = await listen_tool.fn(channel_id="empty-channel", timeout=0.1)
        
        assert result["status"] == "timeout"
        assert result["channel_id"] == "empty-channel"
        assert result["timeout_seconds"] == 0.1
    
    @pytest.mark.asyncio
    async def test_send_message_simple(self, server):
        """Test simple message sending"""
        tools = await server.get_tools()
        send_tool = tools["send_message"]
        list_tool = tools["list_active_channels"]
        
        result = await send_tool.fn(
            channel_id="test-channel",
            message="Test message",
            metadata={"key": "value"}
        )
        
        assert result["status"] == "sent"
        assert result["channel_id"] == "test-channel"
        assert "message_id" in result
        assert "timestamp" in result
        assert "sender_id" in result
        
        # Verify channel was created by checking active channels
        channels_result = await list_tool.fn()
        assert channels_result["channel_count"] >= 1
        channel_ids = [ch["channel_id"] for ch in channels_result["channels"]]
        assert "test-channel" in channel_ids
    
    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, server):
        """Test sending message and waiting for reply"""
        tools = await server.get_tools()
        send_tool = tools["send_message"]
        listen_tool = tools["listen_for_message"]
        reply_tool = tools["send_reply"]
        
        # Create a task to send the reply
        async def send_delayed_reply():
            await asyncio.sleep(0.1)
            # Listen for the original message first
            original = await listen_tool.fn(channel_id="test-channel", timeout=1.0)
            if original["status"] == "received":
                # Send reply
                await reply_tool.fn(
                    original_message_id=original["message"]["id"],
                    reply_channel_id="test-channel",
                    reply_content="Reply received"
                )
        
        # Start reply task
        reply_task = asyncio.create_task(send_delayed_reply())
        
        # Send message and wait for reply
        result = await send_tool.fn(
            channel_id="test-channel",
            message="Need reply",
            wait_for_reply=True,
            reply_timeout=2.0
        )
        
        await reply_task
        
        assert result["status"] == "sent"
        assert result["reply_status"] == "received"
        assert result["reply"]["content"] == "Reply received"
    
    @pytest.mark.asyncio
    async def test_send_reply(self, server, manager):
        """Test reply functionality"""
        tools = await server.get_tools()
        reply_tool = tools["send_reply"]
        
        result = await reply_tool.fn(
            original_message_id="msg-123",
            reply_channel_id="test-channel",
            reply_content="This is a reply"
        )
        
        assert result["status"] == "reply_sent"
        assert result["original_message_id"] == "msg-123"
        assert "reply_message_id" in result
        assert result["reply_channel"] == "test-channel:reply:msg-123"
    
    @pytest.mark.asyncio
    async def test_get_channel_history(self, server, manager):
        """Test getting channel history"""
        # Add some messages
        for i in range(5):
            msg = Message(
                channel_id="test-channel",
                content=f"Message {i}",
                sender_id="test-sender"
            )
            await manager.send_to_channel("test-channel", msg)
        
        tools = await server.get_tools()
        history_tool = tools["get_channel_history"]
        result = await history_tool.fn(channel_id="test-channel", limit=3)
        
        assert result["channel_id"] == "test-channel"
        assert result["message_count"] == 3
        assert len(result["messages"]) == 3
        assert result["messages"][-1]["content"] == "Message 4"
    
    @pytest.mark.asyncio
    async def test_clear_channel_tool(self, server, manager):
        """Test clear channel tool"""
        # Create channel with messages
        await manager.send_to_channel("test-channel", Message(
            channel_id="test-channel",
            content="Test",
            sender_id="test"
        ))
        
        tools = await server.get_tools()
        clear_tool = tools["clear_channel"]
        result = await clear_tool.fn(channel_id="test-channel")
        
        assert result["status"] == "cleared"
        assert result["channel_id"] == "test-channel"
        assert "cleared" in result["message"]
    
    @pytest.mark.asyncio
    async def test_list_active_channels_tool(self, server, manager):
        """Test listing active channels"""
        # Create channels by sending messages
        msg1 = Message(channel_id="channel-1", content="Test 1", sender_id="test")
        msg2 = Message(channel_id="channel-2", content="Test 2", sender_id="test")
        
        await manager.send_to_channel("channel-1", msg1)
        await manager.send_to_channel("channel-2", msg2)
        
        # Add a listener
        await manager.increment_listeners("channel-1")
        
        tools = await server.get_tools()
        list_tool = tools["list_active_channels"]
        result = await list_tool.fn()
        
        assert result["channel_count"] == 2
        assert len(result["channels"]) == 2
        
        # Find channel-1
        channel_1 = next(c for c in result["channels"] if c["channel_id"] == "channel-1")
        assert channel_1["active_listeners"] == 1


class TestAgentConnectServer:
    """Test server creation and MCP compliance"""
    
    def test_server_creation(self, server):
        """Test server is created correctly"""
        assert server is not None
        assert server.name == "Agent Connect"
    
    @pytest.mark.asyncio
    async def test_server_tools(self, server):
        """Test server has all expected tools"""
        # FastMCP provides tools via get_tools()
        tools = await server.get_tools()
        tool_names = list(tools.keys())
        
        expected_tools = [
            "listen_for_message",
            "send_message",
            "get_channel_history",
            "clear_channel",
            "list_active_channels",
            "send_reply"
        ]
        
        for tool in expected_tools:
            assert tool in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_not_configured_error(self, server):
        """Test error when tool not configured"""
        import automagik_tools.tools.agent_connect as bridge_module
        
        # Temporarily clear config
        original_config = bridge_module.config
        bridge_module.config = None
        
        try:
            tools = await server.get_tools()
            listen_tool = tools["listen_for_message"]
            
            with pytest.raises(ValueError, match="Tool not configured"):
                await listen_tool.fn(channel_id="test")
        finally:
            # Restore
            bridge_module.config = original_config