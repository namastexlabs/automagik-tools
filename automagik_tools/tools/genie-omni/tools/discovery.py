"""Discovery tools - Find and download information."""

import logging
from typing import Callable, Optional
from pathlib import Path
import base64
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable, get_config: Callable):
    """Register discovery tools with the MCP server."""
    @mcp.tool()
    async def download_media(
        message_id: str, instance_name: str = "genie", filename: Optional[str] = None
) -> str:
        """
        Download media from a WhatsApp message (image, video, audio, document).

        Use this when you need to:
        - Download images from messages
        - Save videos/audio files
        - Get documents sent via WhatsApp
        - Access media content locally

        Args:
            message_id: ID of the message containing media
            instance_name: Your WhatsApp instance (default: "genie")
            filename: Optional custom filename (auto-detected if not provided)

        Returns:
            Local file path where media was saved

        Example:
            download_media(message_id="3EB0ABC123...", filename="important_doc.pdf")
        """
        import base64
        import os
        from pathlib import Path

        config = get_config()
        client = get_client()

        try:
            # Get media as base64
            response = await client.evolution_get_base64_media(
                instance_name=instance_name, message_id=message_id
            )

            if not response or "base64" not in response:
                logger.warning(f"No base64 data in response for message {message_id}")
                return None

            # Decode base64
            media_data = base64.b64decode(response["base64"])

            # Determine media type and subdirectory from mimetype
            mimetype = response.get("mimetype", "")
            if mimetype.startswith("image/"):
                media_subdir = "media/images"
                ext = mimetype.split("/")[-1] if "/" in mimetype else "jpg"
            elif mimetype.startswith("video/"):
                media_subdir = "media/videos"
                ext = mimetype.split("/")[-1] if "/" in mimetype else "mp4"
            elif mimetype.startswith("audio/"):
                media_subdir = "media/audio"
                ext = mimetype.split("/")[-1] if "/" in mimetype else "mp3"
            elif "sticker" in mimetype.lower():
                media_subdir = "media/stickers"
                ext = "webp"
            elif mimetype.startswith("application/") or mimetype.startswith("text/"):
                media_subdir = "media/documents"
                ext = mimetype.split("/")[-1] if "/" in mimetype else "bin"
            else:
                media_subdir = "downloads"
                ext = "bin"

            # Ensure download folder exists with subdirectory
            download_folder = Path(config.media_download_folder) / media_subdir
            download_folder.mkdir(parents=True, exist_ok=True)

            # Generate filename
            if filename:
                final_filename = filename
            else:
                # Use message ID + extension
                final_filename = f"{message_id}.{ext}"

            # Save file
            file_path = download_folder / final_filename
            with open(file_path, "wb") as f:
                f.write(media_data)

            logger.info(f"Media downloaded: {file_path} ({len(media_data)} bytes)")

            # Format size for display
            size_mb = len(media_data) / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{len(media_data) / 1024:.2f} KB"

            return f"✅ Media downloaded successfully\nFile: {file_path}\nSize: {size_str}"

        except Exception as e:
            logger.error(f"Failed to download media for message {message_id}: {e}")
            return f"❌ Failed to download media: {str(e)}"


# =============================================================================
# CATEGORY 1: WHO AM I (Identity & Context)
# =============================================================================


    @mcp.tool()
    async def find_message(
        trace_id: str, instance_name: str = "genie", include_payload: bool = False
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

            result = ["📱 MESSAGE DETAILS"]
            result.append(f"Trace ID: {trace.trace_id}")
            result.append(f"From: {trace.sender_name or trace.sender_phone}")
            result.append(f"Type: {trace.message_type or 'unknown'}")
            result.append(f"Status: {trace.status}")
            result.append(f"Received: {trace.received_at}")

            if trace.has_media:
                result.append("Media: Yes")

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
    async def find_person(search: str, instance_name: str = "genie") -> str:
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
        client = get_client()

        try:
            contacts = await client.list_contacts(
                instance_name=instance_name, page=1, page_size=10, search_query=search
            )

            if not contacts.contacts:
                return f"📱 No contacts found matching '{search}'"

            # Filter out group IDs (ending in @g.us) - only show individual contacts
            individual_contacts = [c for c in contacts.contacts if not c.id.endswith("@g.us")]

            if not individual_contacts:
                return f"📱 No individual contacts found matching '{search}' (found only groups)"

            result = [f"📱 CONTACTS MATCHING '{search}' ({len(individual_contacts)} total)"]
            result.append("")

            for contact in individual_contacts:
                result.append(f"👤 {contact.name}")
                result.append(f"  Phone: {contact.id}")
                result.append("")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error finding person: {e}")
            return f"❌ Failed to find person: {str(e)}"


    @mcp.tool()
    async def find_chats(instance_name: str = "genie") -> str:
        """
        Find all chat conversations in your WhatsApp.

        Use this when you need to:
        - See all active conversations
        - Discover chats you've had
        - Get chat IDs for messaging

        Args:
            instance_name: Your WhatsApp instance (default: "genie")

        Returns:
            List of all chats with their details
        """
        client = get_client()

        try:
            response = await client.evolution_find_chats(instance_name=instance_name)

            # Evolution API returns different structures, handle both
            chats = response if isinstance(response, list) else response.get("chats", [])

            if not chats:
                return "💬 No chats found"

            result = [f"💬 ALL CHATS ({len(chats)} total)"]
            result.append("")

            for chat in chats[:50]:  # Limit to first 50 for readability
                # Extract chat info from various possible structures
                chat_id = chat.get("id") or chat.get("remoteJid") or "Unknown"
                chat_name = chat.get("name") or chat.get("pushName") or chat_id
                unread = chat.get("unreadCount") or 0
                is_group = "@g.us" in str(chat_id)

                icon = "👥" if is_group else "👤"
                result.append(f"{icon} {chat_name}")
                result.append(f"  ID: {chat_id}")
                if unread and unread > 0:
                    result.append(f"  Unread: {unread}")
                result.append("")

            if len(chats) > 50:
                result.append(f"... and {len(chats) - 50} more chats")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error finding chats: {e}")
            return f"❌ Failed to find chats: {str(e)}"


    @mcp.tool()
    async def list_all_groups(instance_name: str = "genie") -> str:
        """
        List all WhatsApp groups you're a member of.

        Use this when you need to:
        - See all groups you belong to
        - Get group IDs for messaging
        - Check group membership

        Args:
            instance_name: Your WhatsApp instance (default: "genie")

        Returns:
            List of all groups with member counts
        """
        client = get_client()

        try:
            response = await client.evolution_fetch_all_groups(
                instance_name=instance_name, get_participants=True
            )

            # Evolution API returns different structures
            groups = response if isinstance(response, list) else response.get("groups", [])

            if not groups:
                return "👥 No groups found"

            result = [f"👥 ALL GROUPS ({len(groups)} total)"]
            result.append("")

            for group in groups:
                # Extract group info
                group_id = group.get("id") or group.get("remoteJid") or "Unknown"
                group_name = group.get("subject") or group.get("name") or "Unnamed Group"
                participants = group.get("participants", [])
                participant_count = len(participants) if isinstance(participants, list) else group.get("size", 0)

                result.append(f"👥 {group_name}")
                result.append(f"  ID: {group_id}")
                result.append(f"  Members: {participant_count}")

                # Show creator if available
                owner = group.get("owner") or group.get("creator")
                if owner:
                    result.append(f"  Creator: {owner}")

                result.append("")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            return f"❌ Failed to list groups: {str(e)}"


    @mcp.tool()
    async def get_group_members(group_jid: str, instance_name: str = "genie") -> str:
        """
        Get members of a specific WhatsApp group.

        Use this when you need to:
        - See who's in a group
        - Check admin status
        - Get member phone numbers

        Args:
            group_jid: Group ID (JID) - get from list_all_groups
            instance_name: Your WhatsApp instance (default: "genie")

        Returns:
            List of group members with their roles
        """
        client = get_client()

        try:
            response = await client.evolution_find_group_members(
                instance_name=instance_name, group_jid=group_jid
            )

            # Evolution API returns different structures
            participants = response if isinstance(response, list) else response.get("participants", [])

            if not participants:
                return f"👥 No members found in group {group_jid}"

            result = [f"👥 GROUP MEMBERS ({len(participants)} total)"]
            result.append(f"Group: {group_jid}")
            result.append("")

            for participant in participants:
                # Extract participant info
                user_id = participant.get("id") or participant.get("jid") or "Unknown"
                is_admin = participant.get("admin") or participant.get("isAdmin", False)
                is_super_admin = participant.get("isSuperAdmin", False)

                # Determine role
                if is_super_admin:
                    role = "👑 Super Admin"
                elif is_admin:
                    role = "⭐ Admin"
                else:
                    role = "👤 Member"

                result.append(f"{role} {user_id}")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error getting group members: {e}")
            return f"❌ Failed to get group members: {str(e)}"
