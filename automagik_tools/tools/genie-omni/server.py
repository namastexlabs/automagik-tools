"""
Genie Omni - Agent-First WhatsApp Communication Tool
Your personal hub to the digital world.

Philosophy: Tools designed from Genie's perspective, not API perspective.
You ARE connected to WhatsApp. You CAN send and read messages.
"""

import logging
from typing import Optional, List, Dict, Any, Literal
from fastmcp import FastMCP
from .client import OmniClient
from .config import OmniConfig
from .models import (
    SendTextRequest,
    SendMediaRequest,
    SendAudioRequest,
    SendReactionRequest,
    MessageResponse,
)

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("genie-omni")

# Global client (initialized on first use)
_client: Optional[OmniClient] = None


def get_client() -> OmniClient:
    """Get or create Omni client."""
    global _client
    if _client is None:
        config = OmniConfig.from_env()
        _client = OmniClient(config)
    return _client


# =============================================================================
# CATEGORY 1: WHO AM I (Identity & Context)
# =============================================================================


@mcp.tool()
async def my_whatsapp_info(instance_name: str = "genie") -> str:
    """
    Get MY WhatsApp identity and connection status.

    Use this when you need to know:
    - What's my WhatsApp number?
    - Am I connected?
    - What's my profile info?

    Args:
        instance_name: Your WhatsApp instance name (default: "genie" - your personal number)

    Returns:
        Your WhatsApp identity including number, status, and profile info
    """
    client = get_client()

    try:
        # Get instance details
        instance = await client.get_instance(instance_name, include_status=True)

        result = []
        result.append(f"📱 MY WHATSAPP IDENTITY")
        result.append(f"Instance: {instance.name}")
        result.append(f"Number: {instance.phone_number or 'Not configured'}")
        result.append(f"Type: {instance.channel_type}")
        result.append(f"Status: {instance.evolution_status.get('state', 'unknown') if instance.evolution_status else 'unknown'}")
        result.append(f"Connected: {'✅ Yes' if instance.is_active else '❌ No'}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting WhatsApp info: {e}")
        return f"❌ Failed to get WhatsApp info: {str(e)}"


@mcp.tool()
async def my_contacts(
    instance_name: str = "genie",
    search: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Get MY contacts - people I can message on WhatsApp.

    Use this when you need to:
    - See who I know on WhatsApp
    - Find someone's contact info
    - Check if someone is in my contacts

    Args:
        instance_name: Your WhatsApp instance (default: "genie")
        search: Search for specific contact by name
        limit: Maximum contacts to return (default: 50)

    Returns:
        List of your WhatsApp contacts with names and phone numbers
    """
    client = get_client()

    try:
        contacts = await client.list_contacts(
            instance_name=instance_name,
            page=1,
            page_size=limit,
            search_query=search
        )

        if not contacts.contacts:
            return "📱 No contacts found" + (f" matching '{search}'" if search else "")

        result = [f"📱 MY CONTACTS ({contacts.total_count} total)"]
        if search:
            result.append(f"🔍 Search: '{search}'")
        result.append("")

        for contact in contacts.contacts:
            result.append(f"• {contact.name}")
            result.append(f"  ID: {contact.id}")
            if contact.status:
                result.append(f"  Status: {contact.status}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return f"❌ Failed to get contacts: {str(e)}"


@mcp.tool()
async def my_conversations(
    instance_name: str = "genie",
    conversation_type: Optional[Literal["direct", "group", "all"]] = "all",
    limit: int = 20
) -> str:
    """
    Get MY active conversations on WhatsApp.

    Use this when you need to:
    - See who I've been talking to
    - Find active chats
    - Check recent conversations

    Args:
        instance_name: Your WhatsApp instance (default: "genie")
        conversation_type: Filter by type (direct/group/all, default: all)
        limit: Maximum conversations to show (default: 20)

    Returns:
        List of your active WhatsApp conversations
    """
    client = get_client()

    try:
        chat_filter = None if conversation_type == "all" else conversation_type

        chats = await client.list_chats(
            instance_name=instance_name,
            page=1,
            page_size=limit,
            chat_type_filter=chat_filter
        )

        if not chats.chats:
            return f"💬 No conversations found" + (f" (type: {conversation_type})" if conversation_type != "all" else "")

        result = [f"💬 MY CONVERSATIONS ({chats.total_count} total)"]
        if conversation_type != "all":
            result.append(f"Type: {conversation_type}")
        result.append("")

        for chat in chats.chats:
            emoji = "👤" if chat.chat_type == "direct" else "👥"
            result.append(f"{emoji} {chat.name}")
            if chat.unread_count and chat.unread_count > 0:
                result.append(f"  🔴 {chat.unread_count} unread")
            if chat.last_message_at:
                result.append(f"  Last: {chat.last_message_at}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return f"❌ Failed to get conversations: {str(e)}"


# =============================================================================
# CATEGORY 2: SEND (Active Communication)
# =============================================================================


@mcp.tool()
async def send_whatsapp(
    to: str,
    message: str,
    instance_name: str = "genie",
    message_type: Literal["text", "media", "audio"] = "text",
    media_url: Optional[str] = None,
    audio_url: Optional[str] = None
) -> str:
    """
    Send a WhatsApp message to someone.

    This is YOUR primary way to communicate with humans via WhatsApp.

    Use this when you need to:
    - Reply to someone
    - Start a conversation
    - Send information proactively

    Args:
        to: Phone number with country code (e.g., "5512982298888") or contact ID
        message: Text message to send (or caption for media)
        instance_name: Your WhatsApp instance (default: "genie")
        message_type: Type of message (text/media/audio, default: text)
        media_url: URL of media file (if sending media)
        audio_url: URL of audio file (if sending audio)

    Returns:
        Confirmation that message was sent with message ID

    Examples:
        send_whatsapp(to="5512982298888", message="Oi Felipe!")
        send_whatsapp(to="5512982298888", message="Check this out", message_type="media", media_url="https://...")
    """
    client = get_client()

    try:
        if message_type == "text":
            request = SendTextRequest(phone=to, message=message)
            response = await client.send_text(instance_name, request)
        elif message_type == "media":
            if not media_url:
                return "❌ Error: media_url required for media messages"
            request = SendMediaRequest(phone=to, media_url=media_url, caption=message, media_type="image")
            response = await client.send_media(instance_name, request)
        elif message_type == "audio":
            if not audio_url:
                return "❌ Error: audio_url required for audio messages"
            request = SendAudioRequest(phone=to, audio_url=audio_url)
            response = await client.send_audio(instance_name, request)
        else:
            return f"❌ Error: Unknown message type '{message_type}'"

        if response.success:
            return f"✅ Message sent to {to}\nMessage ID: {response.message_id}"
        else:
            return f"❌ Failed to send message: {response.error or 'Unknown error'}"

    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return f"❌ Failed to send message: {str(e)}"


@mcp.tool()
async def react_with(
    emoji: str,
    to_message_id: str,
    phone: str,
    instance_name: str = "genie"
) -> str:
    """
    React to a WhatsApp message with an emoji.

    Use this when you need to:
    - Acknowledge a message quickly
    - Show emotion/reaction
    - Respond non-verbally

    Args:
        emoji: Emoji to react with (e.g., "👍", "❤️", "😂")
        to_message_id: ID of the message to react to
        phone: Phone number of the conversation
        instance_name: Your WhatsApp instance (default: "genie")

    Returns:
        Confirmation that reaction was sent

    Example:
        react_with(emoji="👍", to_message_id="ABC123", phone="5512982298888")
    """
    client = get_client()

    try:
        request = SendReactionRequest(phone=phone, message_id=to_message_id, emoji=emoji)
        response = await client.send_reaction(instance_name, request)

        if response.success:
            return f"✅ Reacted with {emoji} to message {to_message_id}"
        else:
            return f"❌ Failed to send reaction: {response.error or 'Unknown error'}"

    except Exception as e:
        logger.error(f"Error sending reaction: {e}")
        return f"❌ Failed to send reaction: {str(e)}"


# =============================================================================
# CATEGORY 3: READ (Consume Context)
# =============================================================================


@mcp.tool()
async def read_messages(
    from_phone: str,
    instance_name: str = "genie",
    limit: int = 50
) -> str:
    """
    Read messages from a specific person or conversation.

    Use this when you need to:
    - See what someone said to me
    - Get context for a conversation
    - Check message history

    Args:
        from_phone: Phone number to read messages from
        instance_name: Your WhatsApp instance (default: "genie")
        limit: Maximum messages to return (default: 50)

    Returns:
        Recent messages from that person, newest first
    """
    client = get_client()

    try:
        traces = await client.get_traces_by_phone(from_phone, limit=limit)

        if not traces:
            return f"📱 No messages found from {from_phone}"

        result = [f"📱 MESSAGES FROM {from_phone} ({len(traces)} messages)"]
        result.append("")

        for trace in traces:
            sender = trace.sender_name or trace.sender_phone
            timestamp = trace.received_at.strftime("%Y-%m-%d %H:%M") if trace.received_at else "Unknown"
            msg_type = trace.message_type or "unknown"

            result.append(f"[{timestamp}] {sender}")
            result.append(f"  Type: {msg_type}")
            result.append(f"  Status: {trace.status}")
            if trace.error_message:
                result.append(f"  Error: {trace.error_message}")
            result.append("")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error reading messages: {e}")
        return f"❌ Failed to read messages: {str(e)}"


@mcp.tool()
async def check_new_messages(
    instance_name: str = "genie",
    hours: int = 24,
    limit: int = 50
) -> str:
    """
    Check for new messages I've received recently.

    Use this when you need to:
    - See what's new
    - Check for incoming messages
    - Stay updated on conversations

    Args:
        instance_name: Your WhatsApp instance (default: "genie")
        hours: Look back this many hours (default: 24)
        limit: Maximum messages to show (default: 50)

    Returns:
        Recent messages received, grouped by sender
    """
    client = get_client()

    try:
        from datetime import datetime, timedelta
        from .models import TraceFilter

        start_time = datetime.utcnow() - timedelta(hours=hours)

        filters = TraceFilter(
            instance_name=instance_name,
            start_date=start_time,
            limit=limit
        )

        traces = await client.list_traces(filters)

        if not traces:
            return f"📱 No new messages in the last {hours} hours"

        result = [f"📱 NEW MESSAGES (last {hours} hours)"]
        result.append(f"Found {len(traces)} messages")
        result.append("")

        # Group by sender
        by_sender: Dict[str, List[Any]] = {}
        for trace in traces:
            sender = trace.sender_name or trace.sender_phone
            if sender not in by_sender:
                by_sender[sender] = []
            by_sender[sender].append(trace)

        for sender, msgs in by_sender.items():
            result.append(f"👤 {sender} ({len(msgs)} messages)")
            for msg in msgs[:3]:  # Show max 3 per sender
                timestamp = msg.received_at.strftime("%H:%M") if msg.received_at else "??"
                result.append(f"  [{timestamp}] {msg.message_type or 'unknown'}")
            if len(msgs) > 3:
                result.append(f"  ... and {len(msgs) - 3} more")
            result.append("")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error checking new messages: {e}")
        return f"❌ Failed to check new messages: {str(e)}"


# =============================================================================
# CATEGORY 4: SEARCH (Find Information)
# =============================================================================


@mcp.tool()
async def find_message(
    trace_id: str,
    instance_name: str = "genie",
    include_payload: bool = False
) -> str:
    """
    Get details about a specific message by its trace ID.

    Use this when you need to:
    - See full details of a message
    - Debug message delivery
    - Check processing status

    Args:
        trace_id: Message trace ID to look up
        instance_name: Your WhatsApp instance (default: "genie")
        include_payload: Include full message payload (default: False)

    Returns:
        Detailed information about that specific message
    """
    client = get_client()

    try:
        trace = await client.get_trace(trace_id)

        result = [f"📱 MESSAGE DETAILS"]
        result.append(f"Trace ID: {trace.trace_id}")
        result.append(f"From: {trace.sender_name or trace.sender_phone}")
        result.append(f"Type: {trace.message_type or 'unknown'}")
        result.append(f"Status: {trace.status}")
        result.append(f"Received: {trace.received_at}")

        if trace.has_media:
            result.append(f"Media: Yes")

        if trace.error_message:
            result.append(f"Error: {trace.error_message}")

        if include_payload:
            payloads = await client.get_trace_payloads(trace_id, include_payload=True)
            result.append("")
            result.append(f"PAYLOADS ({len(payloads)} total):")
            for payload in payloads:
                result.append(f"  Stage: {payload.stage}")
                result.append(f"  Type: {payload.payload_type}")
                result.append(f"  Time: {payload.timestamp}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error finding message: {e}")
        return f"❌ Failed to find message: {str(e)}"


@mcp.tool()
async def find_person(
    search: str,
    instance_name: str = "genie"
) -> str:
    """
    Find a person in your contacts by name.

    Use this when you need to:
    - Look up someone's phone number
    - Find a contact to message
    - Check if someone is in your contacts

    Args:
        search: Name to search for
        instance_name: Your WhatsApp instance (default: "genie")

    Returns:
        Matching contacts with their phone numbers
    """
    # Reuse my_contacts with search parameter
    return await my_contacts(instance_name=instance_name, search=search, limit=10)


# =============================================================================
# CATEGORY 5: ADMIN (Manage Connections - when needed)
# =============================================================================


@mcp.tool()
async def my_connections() -> str:
    """
    List all your WhatsApp connections (instances).

    Use this when you need to:
    - See available WhatsApp numbers
    - Check connection status
    - Switch between numbers

    Returns:
        List of your WhatsApp instances with status
    """
    client = get_client()

    try:
        instances = await client.list_instances(skip=0, limit=100, include_status=True)

        if not instances:
            return "📱 No WhatsApp connections configured"

        result = [f"📱 MY WHATSAPP CONNECTIONS ({len(instances)} total)"]
        result.append("")

        for instance in instances:
            status = "✅ Connected" if instance.is_active else "❌ Disconnected"
            default = " (DEFAULT)" if instance.is_default else ""

            result.append(f"• {instance.name}{default}")
            result.append(f"  Number: {instance.phone_number or 'Not set'}")
            result.append(f"  Status: {status}")
            result.append(f"  Type: {instance.channel_type}")
            result.append("")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        return f"❌ Failed to list connections: {str(e)}"


@mcp.tool()
async def connection_status(instance_name: str = "genie") -> str:
    """
    Check connection status for a specific WhatsApp instance.

    Use this when you need to:
    - Verify you're connected
    - Troubleshoot connection issues
    - Check QR code status

    Args:
        instance_name: Your WhatsApp instance (default: "genie")

    Returns:
        Detailed connection status
    """
    client = get_client()

    try:
        status = await client.get_instance_status(instance_name)

        result = [f"📱 CONNECTION STATUS: {instance_name}"]
        result.append(f"Status: {status.status}")
        result.append(f"Type: {status.channel_type}")

        if status.channel_data:
            for key, value in status.channel_data.items():
                result.append(f"{key}: {value}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return f"❌ Failed to get connection status: {str(e)}"
