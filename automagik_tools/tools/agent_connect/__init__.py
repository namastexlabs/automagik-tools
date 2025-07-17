"""
Agent Connect - Seamless inter-agent communication for MCP

Agent Connect enables true agent coordination through blocking message channels.
Perfect for multi-agent workflows where agents need to synchronize and communicate.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone

from fastmcp import FastMCP, Context

from .config import AgentConnectConfig
from .models import Message
from .manager import ChannelManager

# Global instances
config: Optional[AgentConnectConfig] = None
manager: Optional[ChannelManager] = None

# Create FastMCP instance
mcp = FastMCP(
    "Agent Connect",
    instructions="""🤖 Agent Connect - Seamless multi-agent coordination
    
    Connect your agents through blocking message channels for perfect synchronization:
    • 📡 Listen on channels and block until messages arrive
    • 📨 Send messages with optional reply waiting
    • 📚 Browse message history across channels
    • 🔍 Discover active channels and listeners
    • 💾 Persistent storage across agent instances
    """,
)


@mcp.tool()
async def listen_for_message(
    channel_id: str, 
    timeout: Optional[Union[int, float, str]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    🎧 Listen for incoming messages on a channel (blocking)
    
    This powerful function blocks execution until a message arrives, enabling
    perfect agent synchronization. Great for waiting for approvals, responses,
    or coordination signals from other agents.
    
    Args:
        channel_id: The channel name to listen on (e.g., "approvals", "coordination")
        timeout: Maximum seconds to wait (None = wait forever)
        ctx: MCP context (optional)
    
    Returns:
        Dict with message data and status, or timeout info if no message arrives
    """
    global manager, config
    if not manager or not config:
        raise ValueError("Tool not configured")
    
    # Handle timeout parameter conversion and default
    if timeout is None:
        timeout = config.default_timeout
    elif isinstance(timeout, str):
        try:
            timeout = float(timeout)
        except (ValueError, TypeError):
            timeout = config.default_timeout
    
    try:
        # Register as active listener
        await manager.increment_listeners(channel_id)
        
        # Wait for message using file-based polling
        message = await manager.wait_for_message(channel_id, timeout)
        
        if message:
            return {
                "status": "received",
                "message": message.model_dump(),
                "channel_id": channel_id,
                "listener_count": await manager.get_listener_count(channel_id) - 1
            }
        else:
            return {
                "status": "timeout",
                "channel_id": channel_id,
                "timeout_seconds": timeout,
                "message": f"No message received within {timeout} seconds"
            }
        
    finally:
        await manager.decrement_listeners(channel_id)


@mcp.tool()
async def send_message(
    channel_id: str,
    message: str,
    wait_for_reply: bool = False,
    reply_timeout: Optional[Union[int, float, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    📨 Send a message to other agents on a channel
    
    Broadcast messages to other agents instantly! Perfect for notifications,
    status updates, or triggering actions. Can optionally wait for a reply
    to create request-response patterns between agents.
    
    Args:
        channel_id: Channel name to send to (e.g., "notifications", "tasks")
        message: Your message content
        wait_for_reply: Block and wait for a response (creates request-response pattern)
        reply_timeout: Max seconds to wait for reply (None = use default)
        metadata: Optional extra data to attach (JSON-serializable dict)
        ctx: MCP context (optional)
    
    Returns:
        Dict with send confirmation and optional reply if wait_for_reply=True
    """
    global manager, config
    if not manager or not config:
        raise ValueError("Tool not configured")
    
    # Handle reply timeout parameter conversion and default
    if wait_for_reply and reply_timeout is None:
        reply_timeout = config.reply_timeout_default
    elif isinstance(reply_timeout, str):
        try:
            reply_timeout = float(reply_timeout)
        except (ValueError, TypeError):
            reply_timeout = config.reply_timeout_default if wait_for_reply else None
    
    # Create message
    msg = Message(
        channel_id=channel_id,
        content=message,
        sender_id=manager.get_instance_id(),
        metadata=metadata or {}
    )
    
    # Send to channel
    await manager.send_to_channel(channel_id, msg)
    
    result = {
        "status": "sent",
        "message_id": msg.id,
        "channel_id": channel_id,
        "timestamp": msg.timestamp.isoformat(),
        "sender_id": msg.sender_id
    }
    
    if wait_for_reply:
        # Create reply channel based on message ID
        reply_channel = f"{channel_id}:reply:{msg.id}"
        
        # Wait for reply on dedicated channel using manager directly
        try:
            await manager.increment_listeners(reply_channel)
            reply_msg = await manager.wait_for_message(reply_channel, reply_timeout)
            
            if reply_msg:
                result["reply"] = reply_msg.model_dump()
                result["reply_status"] = "received"
            else:
                result["reply_status"] = "timeout"
                result["reply_timeout_seconds"] = reply_timeout
        finally:
            await manager.decrement_listeners(reply_channel)
    
    return result


@mcp.tool()
async def get_channel_history(
    channel_id: str,
    limit: int = 100,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    📚 Browse message history for a channel
    
    Perfect for catching up on conversations or analyzing past interactions.
    Returns the most recent messages with full metadata and context.
    
    Args:
        channel_id: Channel name to browse (e.g., "project-updates", "alerts")
        limit: Max messages to return (most recent first)
        ctx: MCP context (optional)
    
    Returns:
        Dict with message history, count, and current listener info
    """
    global manager
    if not manager:
        raise ValueError("Tool not configured")
    
    history = await manager.get_channel_history(channel_id, limit)
    
    return {
        "channel_id": channel_id,
        "message_count": len(history),
        "messages": [msg.dict() for msg in history],
        "listener_count": await manager.get_listener_count(channel_id)
    }


@mcp.tool()
async def clear_channel(
    channel_id: str,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    🧹 Clear all messages in a channel and reset it
    
    Perfect for cleaning up old conversations or starting fresh.
    Removes all pending messages and history but keeps the channel active.
    
    Args:
        channel_id: Channel name to clear (e.g., "temp-data", "debug-logs")
        ctx: MCP context (optional)
    
    Returns:
        Dict with clear status and confirmation message
    """
    global manager
    if not manager:
        raise ValueError("Tool not configured")
    
    success = await manager.clear_channel(channel_id)
    
    return {
        "status": "cleared" if success else "not_found",
        "channel_id": channel_id,
        "message": f"Channel {channel_id} {'cleared' if success else 'not found'}"
    }


@mcp.tool()
async def list_active_channels(
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    🔍 Discover all active channels and their status
    
    Perfect for monitoring agent activity and finding busy channels.
    Shows listener counts, pending messages, and channel metadata.
    
    Args:
        ctx: MCP context (optional)
    
    Returns:
        Dict with channel list, counts, and activity information
    """
    global manager
    if not manager:
        raise ValueError("Tool not configured")
    
    channels = await manager.get_active_channels()
    
    return {
        "channel_count": len(channels),
        "channels": [
            {
                "channel_id": ch.channel_id,
                "active_listeners": ch.active_listeners,
                "pending_messages": ch.pending_messages,
                "total_messages_sent": ch.total_messages_sent,
                "created_at": ch.created_at.isoformat(),
                "last_activity": ch.last_activity.isoformat()
            }
            for ch in channels
        ]
    }


@mcp.tool()
async def send_reply(
    original_message_id: str,
    reply_channel_id: str,
    reply_content: str,
    metadata: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    ↩️ Send a reply to a specific message
    
    Perfect for request-response patterns! This creates a dedicated reply
    channel for the original message, enabling clean conversation threads.
    
    Args:
        original_message_id: ID of the message you're replying to
        reply_channel_id: Original channel where the message was sent
        reply_content: Your reply message
        metadata: Optional extra data for the reply
        ctx: MCP context (optional)
    
    Returns:
        Dict with reply status and dedicated reply channel info
    """
    global manager
    if not manager:
        raise ValueError("Tool not configured")
    
    # Send to the reply channel
    reply_channel = f"{reply_channel_id}:reply:{original_message_id}"
    
    msg = Message(
        channel_id=reply_channel,
        content=reply_content,
        sender_id=manager.get_instance_id(),
        in_reply_to=original_message_id,
        metadata=metadata or {}
    )
    
    await manager.send_to_channel(reply_channel, msg)
    
    return {
        "status": "reply_sent",
        "reply_message_id": msg.id,
        "original_message_id": original_message_id,
        "reply_channel": reply_channel,
        "timestamp": msg.timestamp.isoformat()
    }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "agent-connect",
        "version": "1.0.0",
        "description": "🤖 Seamless multi-agent coordination through blocking message channels",
        "author": "Namastex Labs",
        "category": "coordination",
        "tags": ["agents", "coordination", "blocking", "communication", "sync"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return AgentConnectConfig


def create_server(tool_config: Optional[AgentConnectConfig] = None):
    """Create FastMCP server instance"""
    global config, manager
    config = tool_config or AgentConnectConfig()
    manager = ChannelManager(config)
    
    # Note: Cleanup task will be started when the event loop is running
    # We can't create tasks here as the event loop might not be running yet
    
    return mcp