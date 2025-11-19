"""Reading tools - What messages have I received?"""

import logging
from typing import Callable, Dict, List, Any
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable):
    """Register message reading tools with the MCP server."""

    @mcp.tool()
    async def read_messages(
        from_phone: str, instance_name: str = "genie", limit: int = 50
    ) -> str:
        """
        Read messages from a specific person or conversation.

        Use this when you need to:
        - See what someone said to me
        - Get context for a conversation
        - Check message history

        Args:
            from_phone: Phone number (e.g., "5511999999999") or group ID (e.g., "120363xxx")
                       Auto-detects format - no need for @s.whatsapp.net or @g.us
            instance_name: Your WhatsApp instance (default: "genie")
            limit: Maximum messages to return (default: 50)

        Returns:
            Recent messages from that person, newest first
        """
        client = get_client()

        try:
            # Use Evolution API directly for message history (Omni traces don't support groups)
            response = await client.evolution_find_messages(instance_name, from_phone, limit=limit)

            messages_data = response.get("messages", {})
            records = messages_data.get("records", [])
            # Apply limit client-side since Evolution API ignores it
            records = records[:limit]
            total = messages_data.get("total", 0)

            if not records:
                return f"📱 No messages found from {from_phone}"

            result = [f"📱 MESSAGES FROM {from_phone} ({total} total, showing {len(records)})"]
            result.append("")

            for msg in records:
                # Extract message details
                key = msg.get("key", {})
                sender_name = msg.get("pushName", "Unknown")
                from_me = key.get("fromMe", False)

                # Get timestamp
                timestamp = msg.get("messageTimestamp", 0)
                if timestamp:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                else:
                    time_str = "Unknown"

                # Get message content
                msg_type = msg.get("messageType", "unknown")
                message_content = msg.get("message", {})

                # Extract text content
                text = ""
                if "conversation" in message_content:
                    text = message_content["conversation"]
                elif "extendedTextMessage" in message_content:
                    text = message_content["extendedTextMessage"].get("text", "")

                # Format sender
                sender_label = "You" if from_me else sender_name

                # Get message ID
                message_id = key.get("id", "Unknown")

                result.append(f"[{time_str}] {sender_label}")
                result.append(f"  ID: {message_id}")
                result.append(f"  Type: {msg_type}")
                if text:
                    # Truncate long messages
                    display_text = text[:100] + "..." if len(text) > 100 else text
                    result.append(f"  Message: {display_text}")
                result.append("")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error reading messages: {e}")
            return f"❌ Failed to read messages: {str(e)}"

    @mcp.tool()
    async def check_new_messages(
        instance_name: str = "genie", hours: int = 24, limit: int = 50
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
            # Import models from parent package
            from ..models import TraceFilter

            start_time = datetime.utcnow() - timedelta(hours=hours)

            filters = TraceFilter(
                instance_name=instance_name, start_date=start_time, limit=limit
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
                    timestamp = (
                        msg.received_at.strftime("%H:%M") if msg.received_at else "??"
                    )
                    result.append(f"  [{timestamp}] {msg.message_type or 'unknown'}")
                if len(msgs) > 3:
                    result.append(f"  ... and {len(msgs) - 3} more")
                result.append("")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error checking new messages: {e}")
            return f"❌ Failed to check new messages: {str(e)}"
