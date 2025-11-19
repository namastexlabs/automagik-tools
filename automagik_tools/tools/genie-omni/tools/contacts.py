"""Contact and conversation tools - Who do I know? Who am I talking to?"""

import logging
from typing import Callable, Optional, Literal
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable):
    """Register contact and conversation tools with the MCP server."""

    @mcp.tool()
    async def my_contacts(
        instance_name: str = "genie", search: Optional[str] = None, limit: int = 50
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
                instance_name=instance_name, page=1, page_size=limit, search_query=search
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
        limit: int = 20,
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
                chat_type_filter=chat_filter,
            )

            if not chats.chats:
                return "💬 No conversations found" + (
                    f" (type: {conversation_type})" if conversation_type != "all" else ""
                )

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
