"""
OMNI - Multi-tenant Omnichannel Messaging MCP Tool

Intelligent MCP interface for managing messaging instances, sending messages,
tracking traces, and managing profiles across WhatsApp, Slack, Discord and more.
"""
from typing import Dict, Any, Optional, List
import logging
import json
from fastmcp import FastMCP

from .config import OmniConfig
from .client import OmniClient
from .models import (
    InstanceOperation, MessageType, TraceOperation, ProfileOperation,
    InstanceConfig, SendTextRequest, SendMediaRequest, SendAudioRequest,
    SendStickerRequest, SendContactRequest, SendReactionRequest,
    TraceFilter, FetchProfileRequest, UpdateProfilePictureRequest,
    ContactInfo
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global config and client
_config: Optional[OmniConfig] = None
_client: Optional[OmniClient] = None

# FastMCP server
mcp = FastMCP(
    "OMNI Messaging",
    instructions="""Multi-tenant omnichannel messaging tool for managing instances,
    sending messages, tracking traces, and managing profiles across WhatsApp, Slack, Discord."""
)


def _ensure_client() -> OmniClient:
    """Ensure client is initialized"""
    global _config, _client
    if not _config:
        _config = OmniConfig()
        _config.validate_for_use()
    if not _client:
        _client = OmniClient(_config)
    return _client


@mcp.tool()
async def manage_instances(
    operation: InstanceOperation,
    instance_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    include_status: bool = True,
    skip: int = 0,
    limit: int = 100
) -> str:
    """
    Manage messaging instances (WhatsApp, Slack, Discord, etc.)
    
    Operations:
    - list: List all instances with status
    - get: Get specific instance details
    - create: Create new instance (requires config)
    - update: Update instance configuration
    - delete: Delete an instance
    - set_default: Set instance as default
    - status: Get connection status
    - qr: Get QR code for connection
    - restart: Restart instance connection
    - logout: Logout/disconnect instance
    
    Args:
        operation: Operation to perform (list, get, create, update, delete, set_default, status, qr, restart, logout)
        instance_name: Name of the instance (required for most operations except list/create)
        config: Configuration dict for create/update operations
        include_status: Include Evolution API status (default: True)
        skip: Number of items to skip (for list)
        limit: Maximum items to return (for list)
    
    Returns:
        JSON formatted response with operation results
    
    Examples:
        manage_instances(operation="list")
        manage_instances(operation="get", instance_name="my-whatsapp")
        manage_instances(operation="create", config={"name": "new-instance", "channel_type": "whatsapp"})
        manage_instances(operation="qr", instance_name="my-whatsapp")
    """
    client = _ensure_client()
    
    try:
        if operation == InstanceOperation.LIST:
            instances = await client.list_instances(skip, limit, include_status)
            return json.dumps({
                "success": True,
                "count": len(instances),
                "instances": [inst.model_dump() for inst in instances]
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.GET:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for get operation"})
            instance = await client.get_instance(instance_name, include_status)
            return json.dumps({
                "success": True,
                "instance": instance.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.CREATE:
            if not config:
                return json.dumps({"success": False, "error": "config required for create operation"})
            instance_config = InstanceConfig(**config)
            instance = await client.create_instance(instance_config)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance.name}' created",
                "instance": instance.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.UPDATE:
            if not instance_name or not config:
                return json.dumps({"success": False, "error": "instance_name and config required for update"})
            instance = await client.update_instance(instance_name, config)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance_name}' updated",
                "instance": instance.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.DELETE:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for delete"})
            await client.delete_instance(instance_name)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance_name}' deleted"
            })
            
        elif operation == InstanceOperation.SET_DEFAULT:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for set_default"})
            instance = await client.set_default_instance(instance_name)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance_name}' set as default",
                "instance": instance.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.STATUS:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for status"})
            status = await client.get_instance_status(instance_name)
            return json.dumps({
                "success": True,
                "status": status.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.QR:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for QR"})
            qr = await client.get_instance_qr(instance_name)
            return json.dumps({
                "success": True,
                "qr": qr.model_dump()
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.RESTART:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for restart"})
            result = await client.restart_instance(instance_name)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance_name}' restarted",
                "result": result
            }, default=str, indent=2)
            
        elif operation == InstanceOperation.LOGOUT:
            if not instance_name:
                return json.dumps({"success": False, "error": "instance_name required for logout"})
            result = await client.logout_instance(instance_name)
            return json.dumps({
                "success": True,
                "message": f"Instance '{instance_name}' logged out",
                "result": result
            }, default=str, indent=2)
            
        else:
            return json.dumps({"success": False, "error": f"Unknown operation: {operation}"})
            
    except Exception as e:
        logger.error(f"Instance operation failed: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def send_message(
    message_type: MessageType,
    instance_name: Optional[str] = None,
    phone: Optional[str] = None,
    message: Optional[str] = None,
    media_url: Optional[str] = None,
    media_type: Optional[str] = "image",
    caption: Optional[str] = None,
    audio_url: Optional[str] = None,
    sticker_url: Optional[str] = None,
    contacts: Optional[List[Dict[str, Any]]] = None,
    message_id: Optional[str] = None,
    emoji: Optional[str] = None,
    quoted_message_id: Optional[str] = None,
    delay: Optional[int] = None
) -> str:
    """
    Send messages through any configured instance (WhatsApp, Slack, Discord)
    
    Message Types:
    - text: Send text message (requires: phone, message)
    - media: Send image/video/document (requires: phone, media_url, media_type)
    - audio: Send audio/voice note (requires: phone, audio_url)
    - sticker: Send sticker (requires: phone, sticker_url)
    - contact: Send contact cards (requires: phone, contacts list)
    - reaction: Send emoji reaction (requires: phone, message_id, emoji)
    
    Args:
        message_type: Type of message to send
        instance_name: Instance to use (uses default if not specified)
        phone: Recipient phone number with country code
        message: Text message content
        media_url: URL of media file (for media messages)
        media_type: Type of media (image, video, document)
        caption: Caption for media messages
        audio_url: URL of audio file
        sticker_url: URL of sticker file
        contacts: List of contact dictionaries with full_name, phone_number, etc.
        message_id: Message ID to react to (for reactions)
        emoji: Emoji for reaction
        quoted_message_id: ID of message to quote/reply to
        delay: Delay in milliseconds before sending
    
    Returns:
        JSON formatted response with message ID and status
    
    Examples:
        send_message(message_type="text", phone="+1234567890", message="Hello!")
        send_message(message_type="media", phone="+1234567890", media_url="https://...", media_type="image")
        send_message(message_type="reaction", phone="+1234567890", message_id="...", emoji="👍")
    """
    client = _ensure_client()
    
    # Use default instance if not specified
    if not instance_name:
        if _config.default_instance:
            instance_name = _config.default_instance
        else:
            return json.dumps({"success": False, "error": "No instance_name provided and no default instance configured"})
    
    try:
        if message_type == MessageType.TEXT:
            if not phone or not message:
                return json.dumps({"success": False, "error": "phone and message required for text messages"})
            request = SendTextRequest(
                phone_number=phone,
                text=message,
                quoted_message_id=quoted_message_id,
                delay=delay
            )
            response = await client.send_text(instance_name, request)
            
        elif message_type == MessageType.MEDIA:
            if not phone or not media_url:
                return json.dumps({"success": False, "error": "phone and media_url required for media messages"})
            request = SendMediaRequest(
                phone_number=phone,
                media_url=media_url,
                media_type=media_type,
                caption=caption,
                quoted_message_id=quoted_message_id,
                delay=delay
            )
            response = await client.send_media(instance_name, request)
            
        elif message_type == MessageType.AUDIO:
            if not phone or not audio_url:
                return json.dumps({"success": False, "error": "phone and audio_url required for audio messages"})
            request = SendAudioRequest(
                phone_number=phone,
                audio_url=audio_url,
                quoted_message_id=quoted_message_id,
                delay=delay
            )
            response = await client.send_audio(instance_name, request)
            
        elif message_type == MessageType.STICKER:
            if not phone or not sticker_url:
                return json.dumps({"success": False, "error": "phone and sticker_url required for sticker messages"})
            request = SendStickerRequest(
                phone_number=phone,
                sticker_url=sticker_url,
                quoted_message_id=quoted_message_id,
                delay=delay
            )
            response = await client.send_sticker(instance_name, request)
            
        elif message_type == MessageType.CONTACT:
            if not phone or not contacts:
                return json.dumps({"success": False, "error": "phone and contacts required for contact messages"})
            contact_objs = [ContactInfo(**c) for c in contacts]
            request = SendContactRequest(
                phone_number=phone,
                contacts=contact_objs,
                quoted_message_id=quoted_message_id,
                delay=delay
            )
            response = await client.send_contact(instance_name, request)
            
        elif message_type == MessageType.REACTION:
            if not phone or not message_id or not emoji:
                return json.dumps({"success": False, "error": "phone, message_id and emoji required for reactions"})
            request = SendReactionRequest(
                phone_number=phone,
                message_id=message_id,
                emoji=emoji
            )
            response = await client.send_reaction(instance_name, request)
            
        else:
            return json.dumps({"success": False, "error": f"Unknown message type: {message_type}"})
        
        return json.dumps({
            "success": response.success,
            "message_id": response.message_id,
            "status": response.status,
            "instance": instance_name,
            "type": message_type.value
        }, default=str, indent=2)
        
    except Exception as e:
        logger.error(f"Send message failed: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def manage_traces(
    operation: TraceOperation,
    trace_id: Optional[str] = None,
    phone: Optional[str] = None,
    instance_name: Optional[str] = None,
    trace_status: Optional[str] = None,
    message_type: Optional[str] = None,
    session_name: Optional[str] = None,
    has_media: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_payload: bool = False,
    days_old: int = 30,
    dry_run: bool = True
) -> str:
    """
    Manage message traces for debugging and analytics
    
    Operations:
    - list: List traces with filters
    - get: Get specific trace details
    - get_payloads: Get trace payloads for debugging
    - analytics: Get analytics summary
    - by_phone: Get traces for specific phone number
    - cleanup: Clean up old traces
    
    Args:
        operation: Operation to perform
        trace_id: Specific trace ID (for get/get_payloads)
        phone: Filter by phone number
        instance_name: Filter by instance
        trace_status: Filter by status (received, processing, completed, failed)
        message_type: Filter by message type
        session_name: Filter by session name
        has_media: Filter by media presence
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        limit: Maximum results to return
        offset: Number of results to skip
        include_payload: Include payload data (for get_payloads)
        days_old: Days threshold for cleanup
        dry_run: Preview cleanup without deleting
    
    Returns:
        JSON formatted trace data or analytics
    
    Examples:
        manage_traces(operation="list", instance_name="my-whatsapp", limit=10)
        manage_traces(operation="analytics", start_date="2024-01-01")
        manage_traces(operation="by_phone", phone="+1234567890")
    """
    client = _ensure_client()
    
    try:
        if operation == TraceOperation.LIST:
            filters = TraceFilter(
                phone=phone,
                instance_name=instance_name,
                trace_status=trace_status,
                message_type=message_type,
                session_name=session_name,
                has_media=has_media,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            traces = await client.list_traces(filters)
            return json.dumps({
                "success": True,
                "count": len(traces),
                "traces": [t.model_dump() for t in traces]
            }, default=str, indent=2)
            
        elif operation == TraceOperation.GET:
            if not trace_id:
                return json.dumps({"success": False, "error": "trace_id required for get operation"})
            trace = await client.get_trace(trace_id)
            return json.dumps({
                "success": True,
                "trace": trace.model_dump()
            }, default=str, indent=2)
            
        elif operation == TraceOperation.GET_PAYLOADS:
            if not trace_id:
                return json.dumps({"success": False, "error": "trace_id required for get_payloads"})
            payloads = await client.get_trace_payloads(trace_id, include_payload)
            return json.dumps({
                "success": True,
                "count": len(payloads),
                "payloads": [p.model_dump() for p in payloads]
            }, default=str, indent=2)
            
        elif operation == TraceOperation.ANALYTICS:
            analytics = await client.get_trace_analytics(start_date, end_date, instance_name)
            return json.dumps({
                "success": True,
                "analytics": analytics.model_dump()
            }, default=str, indent=2)
            
        elif operation == TraceOperation.BY_PHONE:
            if not phone:
                return json.dumps({"success": False, "error": "phone required for by_phone operation"})
            traces = await client.get_traces_by_phone(phone, limit)
            return json.dumps({
                "success": True,
                "count": len(traces),
                "phone": phone,
                "traces": [t.model_dump() for t in traces]
            }, default=str, indent=2)
            
        elif operation == TraceOperation.CLEANUP:
            result = await client.cleanup_traces(days_old, dry_run)
            return json.dumps({
                "success": True,
                "dry_run": dry_run,
                "days_old": days_old,
                "result": result
            }, default=str, indent=2)
            
        else:
            return json.dumps({"success": False, "error": f"Unknown operation: {operation}"})
            
    except Exception as e:
        logger.error(f"Trace operation failed: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def manage_profiles(
    operation: ProfileOperation,
    instance_name: Optional[str] = None,
    user_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    picture_url: Optional[str] = None
) -> str:
    """
    Manage user profiles and profile pictures
    
    Operations:
    - fetch: Fetch user profile information
    - update_picture: Update instance profile picture
    
    Args:
        operation: Operation to perform (fetch, update_picture)
        instance_name: Instance to use (uses default if not specified)
        user_id: User ID for profile fetch
        phone_number: Phone number for profile fetch
        picture_url: URL of new profile picture (for update_picture)
    
    Returns:
        JSON formatted profile data or update confirmation
    
    Examples:
        manage_profiles(operation="fetch", phone_number="+1234567890")
        manage_profiles(operation="update_picture", picture_url="https://...")
    """
    client = _ensure_client()
    
    # Use default instance if not specified
    if not instance_name:
        if _config.default_instance:
            instance_name = _config.default_instance
        else:
            return json.dumps({"success": False, "error": "No instance_name provided and no default instance configured"})
    
    try:
        if operation == ProfileOperation.FETCH:
            if not user_id and not phone_number:
                return json.dumps({"success": False, "error": "Either user_id or phone_number required for fetch"})
            request = FetchProfileRequest(
                user_id=user_id,
                phone_number=phone_number
            )
            profile = await client.fetch_profile(instance_name, request)
            return json.dumps({
                "success": True,
                "instance": instance_name,
                "profile": profile
            }, default=str, indent=2)
            
        elif operation == ProfileOperation.UPDATE_PICTURE:
            if not picture_url:
                return json.dumps({"success": False, "error": "picture_url required for update_picture"})
            request = UpdateProfilePictureRequest(picture_url=picture_url)
            response = await client.update_profile_picture(instance_name, request)
            return json.dumps({
                "success": response.success,
                "instance": instance_name,
                "message": "Profile picture updated",
                "status": response.status
            }, default=str, indent=2)
            
        else:
            return json.dumps({"success": False, "error": f"Unknown operation: {operation}"})
            
    except Exception as e:
        logger.error(f"Profile operation failed: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "omni",
        "version": "1.0.0",
        "description": "Multi-tenant omnichannel messaging API tool for WhatsApp, Slack, Discord",
        "author": "Namastex Labs",
        "category": "messaging",
        "tags": ["whatsapp", "slack", "discord", "messaging", "omnichannel", "traces", "analytics"],
        "capabilities": [
            "instance_management",
            "multi_channel_messaging",
            "trace_analytics",
            "profile_management",
            "qr_code_generation",
            "connection_status"
        ]
    }


def get_config_class():
    """Return the config class for this tool"""
    return OmniConfig


def create_server(tool_config: Optional[OmniConfig] = None):
    """Create FastMCP server instance"""
    global _config, _client
    _config = tool_config or OmniConfig()
    _client = OmniClient(_config)
    return mcp


__all__ = ["create_server", "get_metadata", "get_config_class", "OmniConfig"]