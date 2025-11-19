"""Messaging tools - Send and manage WhatsApp messages."""

import logging
from typing import Callable, Optional, Literal, Dict, List, Any
from pathlib import Path
from fastmcp import FastMCP
from ..models import SendMediaRequest, SendAudioRequest

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable, get_config: Callable):
    """Register messaging tools with the MCP server."""
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
        media_type: Optional[Literal["image", "video", "document"]] = None,
        mime_type: Optional[str] = None,
        audio_url: Optional[str] = None,
        quoted_message_id: Optional[str] = None,
        delay: Optional[int] = None,
        split_message: Optional[bool] = None,
) -> str:
        """
        Send a WhatsApp message to someone.

        This is YOUR primary way to communicate with humans via WhatsApp.

        Use this when you need to:
        - Reply to someone
        - Start a conversation
        - Send information proactively

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            message: Text message to send (or caption for media)
            instance_name: Your WhatsApp instance (default: "genie")
            message_type: Type of message (text/media/audio, default: text)
            media_url: URL or local file path for media (if sending media)
            media_type: Type of media (image/video/document, default: image if not specified)
            mime_type: MIME type for media (e.g., "image/png", "video/mp4", auto-detected for local files)
            audio_url: URL or local file path for audio (if sending audio)
            quoted_message_id: Message ID to quote/reply to (optional)
            delay: Delay in milliseconds before sending (optional)
            split_message: Whether to split long messages on \\n\\n (optional, uses instance config by default)

        Returns:
            Confirmation that message was sent with message ID

        Examples:
            send_whatsapp(to="5511999999999", message="Hello!")
            send_whatsapp(to="5511999999999", message="Check this out", message_type="media", media_url="https://...")
            send_whatsapp(to="5511999999999", message="Replying to you!", quoted_message_id="ABC123")
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            if message_type == "text":
                # Send "composing" presence (typing indicator) before sending text
                try:
                    await client.evolution_send_presence(
                        instance_name=instance_name,
                        remote_jid=to,
                        presence="composing",
                        delay=3000  # 3 seconds
                    )
                except Exception as e:
                    logger.warning(f"Failed to send presence: {e}")

                # Use Evolution API directly for all text messages to get proper message IDs
                response_data = await client.evolution_send_text(
                    instance_name=instance_name,
                    remote_jid=to,
                    text=message,
                    quoted_msg_id=quoted_message_id,
                    from_me=False if quoted_message_id else True,
                    delay=delay
                )
                message_id = response_data.get('key', {}).get('id', 'Unknown')
                return f"✅ Message sent to {to}\nMessage ID: {message_id}"
            elif message_type == "media":
                if not media_url:
                    return "❌ Error: media_url required for media messages"

                # Detect if media_url is a local file or URL
                import os
                import base64
                from pathlib import Path
                import mimetypes

                detected_mime = mime_type
                detected_media_type = media_type or "image"
                media_base64_data = None
                actual_media_url = None

                # Check if it's a local file path
                if os.path.exists(media_url):
                    # It's a local file - read and encode to base64
                    file_path = Path(media_url).absolute()

                    # Auto-detect mime type if not provided
                    if not detected_mime:
                        detected_mime, _ = mimetypes.guess_type(str(file_path))

                    # Auto-detect media_type from mime_type
                    if not media_type and detected_mime:
                        if detected_mime.startswith("image/"):
                            detected_media_type = "image"
                        elif detected_mime.startswith("video/"):
                            detected_media_type = "video"
                        else:
                            detected_media_type = "document"

                    # Read file and encode to base64
                    try:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            media_base64_data = base64.b64encode(file_data).decode("utf-8")
                    except Exception as e:
                        return f"❌ Error reading file {media_url}: {str(e)}"
                else:
                    # It's a URL
                    actual_media_url = media_url

                # Build request with all parameters
                request_data = {
                    "phone": to,
                    "caption": message,
                    "media_type": detected_media_type,
                    "quoted_message_id": quoted_message_id,
                    "delay": delay,
                }

                # Add media_url OR media_base64
                if media_base64_data:
                    request_data["media_base64"] = media_base64_data
                    request_data["filename"] = Path(media_url).name
                else:
                    request_data["media_url"] = actual_media_url

                # Add mime_type if provided or detected
                if detected_mime:
                    request_data["mime_type"] = detected_mime

                request = SendMediaRequest(**request_data)
                response = await client.send_media(instance_name, request)
            elif message_type == "audio":
                if not audio_url:
                    return "❌ Error: audio_url required for audio messages"

                # Send "recording" presence (recording indicator) before sending audio
                try:
                    await client.evolution_send_presence(
                        instance_name=instance_name,
                        remote_jid=to,
                        presence="recording",
                        delay=3000  # 3 seconds
                    )
                except Exception as e:
                    logger.warning(f"Failed to send presence: {e}")

                # Detect if audio_url is a local file or URL
                import os
                import base64
                from pathlib import Path

                audio_base64_data = None
                actual_audio_url = None

                # Check if it's a local file path
                if os.path.exists(audio_url):
                    # It's a local file - read and encode to base64
                    file_path = Path(audio_url).absolute()

                    try:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            audio_base64_data = base64.b64encode(file_data).decode("utf-8")
                    except Exception as e:
                        return f"❌ Error reading audio file {audio_url}: {str(e)}"
                else:
                    # It's a URL
                    actual_audio_url = audio_url

                # Build request
                request_data = {
                    "phone": to,
                    "quoted_message_id": quoted_message_id,
                    "delay": delay,
                }

                # Add audio_url OR audio_base64
                if audio_base64_data:
                    request_data["audio_base64"] = audio_base64_data
                else:
                    request_data["audio_url"] = actual_audio_url

                request = SendAudioRequest(**request_data)
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
        emoji: str, to_message_id: str, phone: str, instance_name: str = "genie"
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
            react_with(emoji="👍", to_message_id="ABC123", phone="5511999999999")
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(phone)

        if not is_allowed:
            logger.warning(f"Blocked reaction attempt to {phone}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            # Use Evolution API directly for reactions (Omni doesn't support it properly)
            response = await client.evolution_send_reaction(
                instance_name=instance_name,
                remote_jid=phone,
                message_id=to_message_id,
                emoji=emoji,
                from_me=False  # Reacting to messages from others
            )

            return f"✅ Reacted with {emoji} to message {to_message_id}"

        except Exception as e:
            logger.error(f"Error sending reaction: {e}")
            return f"❌ Failed to send reaction: {str(e)}"


    @mcp.tool()
    async def send_sticker(
        to: str,
        sticker_url: str,
        instance_name: str = "genie",
        quoted_message_id: Optional[str] = None,
        delay: Optional[int] = None,
) -> str:
        """
        Send a WhatsApp sticker to someone.

        Use this when you need to:
        - Send a sticker (fun, expressive communication)
        - React visually to a message
        - Add personality to your messages

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            sticker_url: URL of the sticker file (WebP format recommended)
            instance_name: Your WhatsApp instance (default: "genie")
            quoted_message_id: Message ID to quote/reply to (optional)
            delay: Delay in milliseconds before sending (optional)

        Returns:
            Confirmation that sticker was sent with message ID

        Example:
            send_sticker(to="5511999999999", sticker_url="https://example.com/sticker.webp")
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked sticker send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            response = await client.evolution_send_sticker(
                instance_name=instance_name,
                remote_jid=to,
                sticker_url=sticker_url,
                quoted_message_id=quoted_message_id,
                delay=delay,
            )

            # Extract message ID from Evolution API response
            message_id = response.get("key", {}).get("id", "Unknown")

            return f"✅ Sticker sent to {to}\nMessage ID: {message_id}"

        except Exception as e:
            logger.error(f"Error sending sticker: {e}")
            return f"❌ Failed to send sticker: {str(e)}"


    @mcp.tool()
    async def send_contact(
        to: str,
        contacts: List[Dict[str, Any]],
        instance_name: str = "genie",
        quoted_message_id: Optional[str] = None,
        delay: Optional[int] = None,
) -> str:
        """
        Send WhatsApp contact(s) (vCard) to someone.

        Use this when you need to:
        - Share someone's contact information
        - Send business contacts
        - Share multiple contacts at once

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            contacts: List of contact dictionaries with fields:
                     - full_name (required): Contact's full name
                     - phone_number (optional): Contact's phone number
                     - email (optional): Contact's email
                     - organization (optional): Contact's company/org
                     - url (optional): Contact's website
            instance_name: Your WhatsApp instance (default: "genie")
            quoted_message_id: Message ID to quote/reply to (optional)
            delay: Delay in milliseconds before sending (optional)

        Returns:
            Confirmation that contact(s) were sent with message ID

        Example:
            send_contact(
                to="5511999999999",
                contacts=[{
                    "full_name": "John Doe",
                    "phone_number": "5511888888888",
                    "email": "john@example.com",
                    "organization": "Example Corp"
                }]
            )
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked contact send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            # Use Evolution API directly to get proper message IDs
            response_data = await client.evolution_send_contact(
                instance_name=instance_name,
                remote_jid=to,
                contacts=contacts,
                quoted_message_id=quoted_message_id,
                delay=delay
            )

            # Extract message ID from Evolution API response
            message_id = response_data.get("key", {}).get("id", "Unknown")

            contact_count = len(contacts)
            plural = "s" if contact_count > 1 else ""
            return f"✅ {contact_count} contact{plural} sent to {to}\nMessage ID: {message_id}"

        except Exception as e:
            logger.error(f"Error sending contact: {e}")
            return f"❌ Failed to send contact(s): {str(e)}"


    @mcp.tool()
    async def send_location(
        to: str,
        latitude: float,
        longitude: float,
        instance_name: str = "genie",
        name: Optional[str] = None,
        address: Optional[str] = None,
) -> str:
        """
        Send a location to someone via WhatsApp.

        Use this when you need to:
        - Share a specific location (restaurant, office, meeting point)
        - Send coordinates for navigation
        - Show where something is located

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            latitude: Location latitude (e.g., -23.550520)
            longitude: Location longitude (e.g., -46.633308)
            instance_name: Your WhatsApp instance (default: "genie")
            name: Optional location name (e.g., "Paulista Avenue")
            address: Optional address text (e.g., "Av. Paulista, 1578 - São Paulo")

        Returns:
            Confirmation that location was sent with message ID

        Example:
            send_location(
                to="5511999999999",
                latitude=-23.550520,
                longitude=-46.633308,
                name="Paulista Avenue",
                address="Av. Paulista, 1578 - São Paulo, SP"
            )
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked location send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        # Evolution API requires address field - provide default if not given
        if not address:
            address = name if name else f"{latitude}, {longitude}"

        try:
            response = await client.evolution_send_location(
                instance_name=instance_name,
                remote_jid=to,
                latitude=latitude,
                longitude=longitude,
                name=name,
                address=address,
            )

            location_desc = f" ({name})" if name else ""
            return f"✅ Location{location_desc} sent to {to}\nCoordinates: {latitude}, {longitude}\nMessage ID: {response.get('key', {}).get('id', 'None')}"

        except Exception as e:
            logger.error(f"Error sending location: {e}")
            return f"❌ Failed to send location: {str(e)}"


    @mcp.tool()
    async def delete_message(
        message_id: str,
        phone: str,
        instance_name: str = "genie",
        from_me: bool = True,
) -> str:
        """
        Delete a WhatsApp message for everyone.

        Use this when you need to:
        - Remove a message you sent (within allowed time window)
        - Correct a mistake immediately
        - Retract something sent by accident

        IMPORTANT: Only works for messages sent FROM you (from_me=True).
        Messages from others cannot be deleted.
        WhatsApp has time limits for deletion (~48 hours).

        Args:
            message_id: ID of the message to delete
            phone: Phone number of the conversation (e.g., "5511999999999")
            instance_name: Your WhatsApp instance (default: "genie")
            from_me: Whether the message is from you (default: True)

        Returns:
            Confirmation that message was deleted

        Example:
            delete_message(
                message_id="3EB0C1234567890ABCDEF",
                phone="5511999999999"
            )
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(phone)

        if not is_allowed:
            logger.warning(f"Blocked delete attempt for {phone}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            response = await client.evolution_delete_message(
                instance_name=instance_name,
                remote_jid=phone,
                message_id=message_id,
                from_me=from_me,
            )

            return f"✅ Message {message_id} deleted for everyone in chat with {phone}"

        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return f"❌ Failed to delete message: {str(e)}"


    # Internal helper - presence is automatically sent with send_whatsapp
    async def send_presence(
        to: str,
        presence: str = "composing",
        instance_name: str = "genie",
        delay: int = 0,
) -> str:
        """
        Send presence status (typing, recording, etc) to a WhatsApp contact.

        Use this when you need to:
        - Show "typing..." indicator before sending message
        - Show "recording..." indicator before sending audio
        - Provide better UX by simulating human behavior
        - Clear presence indicators (paused/unavailable)

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            presence: Status to show:
                     - "composing": Typing... indicator
                     - "recording": Recording audio... indicator
                     - "paused": Stop typing indicator
                     - "available": Show online
                     - "unavailable": Hide status
            instance_name: Your WhatsApp instance (default: "genie")
            delay: How long to show presence in milliseconds (0 = until next message)

        Returns:
            Confirmation that presence was sent

        Example:
            # Show typing indicator before sending message
            send_presence(to="5511999999999", presence="composing")
            # Then send your message
            send_whatsapp(to="5511999999999", message="Hello!")
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked presence send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            response = await client.evolution_send_presence(
                instance_name=instance_name,
                remote_jid=to,
                presence=presence,
                delay=delay,
            )

            presence_emoji = {
                "composing": "⌨️",
                "recording": "🎤",
                "paused": "⏸️",
                "available": "🟢",
                "unavailable": "⚫"
            }.get(presence, "📡")

            return f"{presence_emoji} Presence '{presence}' sent to {to}"

        except Exception as e:
            logger.error(f"Error sending presence: {e}")
            return f"❌ Failed to send presence: {str(e)}"


    @mcp.tool()
    async def update_message(
        message_id: str,
        new_text: str,
        phone: str,
        instance_name: str = "genie",
        from_me: bool = True,
) -> str:
        """
        Edit/update a WhatsApp message that was already sent.

        Use this when you need to:
        - Fix a typo in a message you sent
        - Update information in a previous message
        - Correct a mistake

        IMPORTANT: Only works for messages sent FROM you (from_me=True).
        Messages from others cannot be edited.
        WhatsApp has time limits for editing (~15 minutes).

        Args:
            message_id: ID of the message to edit
            new_text: New text content for the message
            phone: Phone number of the conversation (e.g., "5511999999999")
            instance_name: Your WhatsApp instance (default: "genie")
            from_me: Whether the message is from you (default: True)

        Returns:
            Confirmation that message was updated

        Example:
            update_message(
                message_id="3EB0C1234567890ABCDEF",
                new_text="Corrected message text",
                phone="5511999999999"
            )
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(phone)

        if not is_allowed:
            logger.warning(f"Blocked update attempt for {phone}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            response = await client.evolution_update_message(
                instance_name=instance_name,
                remote_jid=phone,
                message_id=message_id,
                new_text=new_text,
                from_me=from_me,
            )

            return f"✅ Message {message_id} updated in chat with {phone}\nNew text: {new_text[:50]}..."

        except Exception as e:
            logger.error(f"Error updating message: {e}")
            return f"❌ Failed to update message: {str(e)}"


    @mcp.tool()
    async def check_is_whatsapp(
        phone_numbers: List[str],
        instance_name: str = "genie",
) -> str:
        """
        Check if phone numbers are registered on WhatsApp.

        Use this when you need to:
        - Verify if a number exists on WhatsApp before sending message
        - Check multiple numbers at once
        - Validate phone numbers before bulk messaging

        Args:
            phone_numbers: List of phone numbers to check (e.g., ["5511999999999", "5511888888888"])
            instance_name: Your WhatsApp instance (default: "genie")

        Returns:
            List of numbers with their WhatsApp status

        Example:
            check_is_whatsapp(phone_numbers=["5511999999999", "5511888888888"])
        """
        client = get_client()

        try:
            response = await client.evolution_check_is_whatsapp(
                instance_name=instance_name,
                phone_numbers=phone_numbers,
            )

            # Format response for readability
            result_lines = ["📱 WhatsApp Number Check:\n"]

            # Response format varies, handle both formats
            if isinstance(response, list):
                for item in response:
                    number = item.get("jid", item.get("number", "Unknown"))
                    exists = item.get("exists", False)
                    status = "✅ On WhatsApp" if exists else "❌ Not on WhatsApp"
                    result_lines.append(f"  {number}: {status}")
            elif isinstance(response, dict) and "results" in response:
                for item in response["results"]:
                    number = item.get("jid", item.get("number", "Unknown"))
                    exists = item.get("exists", False)
                    status = "✅ On WhatsApp" if exists else "❌ Not on WhatsApp"
                    result_lines.append(f"  {number}: {status}")
            else:
                result_lines.append(f"  Raw response: {response}")

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error checking WhatsApp numbers: {e}")
            return f"❌ Failed to check WhatsApp numbers: {str(e)}"


    @mcp.tool()
    async def send_poll(
        to: str,
        question: str,
        options: List[str],
        instance_name: str = "genie",
        selectable_count: int = 1,
) -> str:
        """
        Send an interactive poll to a WhatsApp contact.

        Use this when you need to:
        - Gather opinions from contacts
        - Make group decisions
        - Create surveys or feedback forms
        - Get quick responses with predefined options

        Args:
            to: Phone number with country code (e.g., "5511999999999") or contact ID
            question: The poll question (e.g., "What time works best for the meeting?")
            options: List of answer options (e.g., ["9 AM", "2 PM", "5 PM"])
            instance_name: Your WhatsApp instance (default: "genie")
            selectable_count: How many options can be selected (1 = single choice, >1 = multiple choice)

        Returns:
            Confirmation that poll was sent with message ID

        Example:
            send_poll(
                to="5511999999999",
                question="What's your favorite programming language?",
                options=["Python", "JavaScript", "Go", "Rust"],
                selectable_count=1
            )
        """
        # Safety check: validate recipient against master context
        config = get_config()
        is_allowed, validation_message = config.validate_recipient(to)

        if not is_allowed:
            logger.warning(f"Blocked poll send attempt to {to}: {validation_message}")
            return validation_message

        # Show safety warning if in full access mode
        if not config.has_master_context():
            logger.warning(config.get_safety_warning())

        client = get_client()

        try:
            response = await client.evolution_send_poll(
                instance_name=instance_name,
                remote_jid=to,
                name=question,
                options=options,
                selectable_count=selectable_count,
            )

            poll_type = "single choice" if selectable_count == 1 else f"multiple choice (max {selectable_count})"
            return f"📊 Poll sent to {to}\nQuestion: {question}\nOptions: {len(options)} ({poll_type})\nMessage ID: {response.get('key', {}).get('id', 'None')}"

        except Exception as e:
            logger.error(f"Error sending poll: {e}")
            return f"❌ Failed to send poll: {str(e)}"


    # =============================================================================
    # CATEGORY 3: READ (Consume Context)
    # =============================================================================


