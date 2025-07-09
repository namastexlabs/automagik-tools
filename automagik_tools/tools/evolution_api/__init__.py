"""
Evolution API MCP Tool - Complete WhatsApp messaging suite for Evolution API v2
"""

import asyncio
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from .config import EvolutionAPIConfig
from .client import EvolutionAPIClient

# Global configuration and client
config: Optional[EvolutionAPIConfig] = None
client: Optional[EvolutionAPIClient] = None

# Create FastMCP instance
mcp = FastMCP(
    "Evolution API",
    instructions="""
Evolution API - Complete WhatsApp messaging suite for Evolution API v2

🚀 Send WhatsApp messages with auto-typing indicators
📱 Send media (images, videos, documents) with captions
🎵 Send audio messages and voice notes
😊 Send emoji reactions to messages
📍 Send location coordinates with address details
👤 Send contact information
⌨️ Send typing/recording presence indicators

All tools support optional fixed recipient mode for security-controlled access.
""",
)

def _get_target_number(provided_number: Optional[str] = None) -> str:
    """Get target number based on fixed recipient configuration or provided number"""
    if config and config.fixed_recipient:
        return config.fixed_recipient
    if provided_number:
        return provided_number
    raise ValueError("No recipient number provided and EVOLUTION_API_FIXED_RECIPIENT not set")

@mcp.tool()
def send_text_message(
    instance: str,
    message: str,
    number: Optional[str] = None,
    delay: int = 0,
    linkPreview: bool = True,
    mentions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send a text message via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        message: Text message to send
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        delay: Optional delay in milliseconds before sending
        linkPreview: Whether to show link preview for URLs
        mentions: Optional list of numbers to mention in the message
    
    Returns:
        Dictionary with message status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        # Auto-send typing indicator 3 seconds before text
        asyncio.run(client.send_presence(instance, target_number, "composing", 3000))
        
        result = asyncio.run(client.send_text_message(
            instance, target_number, message, delay, linkPreview, mentions
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.tool()
def send_media(
    instance: str,
    media: str,
    mediatype: str,
    mimetype: str,
    number: Optional[str] = None,
    caption: str = "",
    fileName: str = "",
    delay: int = 0,
    linkPreview: bool = True,
    mentions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send media (image, video, document) via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        media: Base64 encoded media data or URL
        mediatype: Type of media (image, video, document)
        mimetype: MIME type (e.g., image/jpeg, video/mp4)
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        caption: Optional caption for the media
        fileName: Optional filename for the media
        delay: Optional delay in milliseconds before sending
        linkPreview: Whether to show link preview for URLs in caption
        mentions: Optional list of numbers to mention in the caption
    
    Returns:
        Dictionary with message status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        result = asyncio.run(client.send_media(
            instance, target_number, media, mediatype, mimetype, 
            caption, fileName, delay, linkPreview, mentions
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "mediatype": mediatype,
            "caption": caption[:50] + "..." if len(caption) > 50 else caption
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.tool()
def send_audio(
    instance: str,
    audio: str,
    number: Optional[str] = None,
    delay: int = 0,
    linkPreview: bool = True,
    mentions: Optional[List[str]] = None,
    quoted: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send audio message via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        audio: Base64 encoded audio data or URL
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        delay: Optional delay in milliseconds before sending
        linkPreview: Whether to show link preview for URLs
        mentions: Optional list of numbers to mention
        quoted: Optional quoted message data
    
    Returns:
        Dictionary with message status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        # Auto-send typing indicator 3 seconds before audio
        asyncio.run(client.send_presence(instance, target_number, "composing", 3000))
        
        result = asyncio.run(client.send_audio(
            instance, target_number, audio, delay, linkPreview, mentions, quoted
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "audio_type": "voice_message"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.tool()
def send_reaction(
    instance: str,
    remote_jid: str,
    from_me: bool,
    message_id: str,
    reaction: str
) -> Dict[str, Any]:
    """
    Send emoji reaction to a message via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        remote_jid: Remote JID of the message
        from_me: Whether the message is from the current user
        message_id: ID of the message to react to
        reaction: Emoji reaction (e.g., "👍", "❤️")
    
    Returns:
        Dictionary with reaction status and details
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        result = asyncio.run(client.send_reaction(
            instance, remote_jid, from_me, message_id, reaction
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "message_id": message_id,
            "reaction": reaction
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "message_id": message_id
        }

@mcp.tool()
def send_location(
    instance: str,
    latitude: float,
    longitude: float,
    number: Optional[str] = None,
    name: str = "",
    address: str = "",
    delay: int = 0,
    mentions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send location via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        name: Optional location name
        address: Optional location address
        delay: Optional delay in milliseconds before sending
        mentions: Optional list of numbers to mention
    
    Returns:
        Dictionary with message status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        result = asyncio.run(client.send_location(
            instance, target_number, latitude, longitude, name, address, delay, mentions
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "coordinates": f"{latitude}, {longitude}",
            "name": name
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.tool()
def send_contact(
    instance: str,
    contact: List[Dict[str, str]],
    number: Optional[str] = None,
    delay: int = 0,
    mentions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send contact information via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        contact: List of contact dictionaries with fullName, wuid, phoneNumber, organization, email, url
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        delay: Optional delay in milliseconds before sending
        mentions: Optional list of numbers to mention
    
    Returns:
        Dictionary with message status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        result = asyncio.run(client.send_contact(
            instance, target_number, contact, delay, mentions
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "contacts_count": len(contact)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.tool()
def send_presence(
    instance: str,
    number: Optional[str] = None,
    presence: str = "composing",
    delay: int = 3000
) -> Dict[str, Any]:
    """
    Send presence indicator (typing, recording) via WhatsApp using Evolution API v2
    
    Args:
        instance: Evolution API instance name
        number: WhatsApp number with country code (optional if EVOLUTION_API_FIXED_RECIPIENT is set)
        presence: Presence type (composing, recording, paused)
        delay: Duration in milliseconds to show presence
    
    Returns:
        Dictionary with presence status and details
    
    Note: If EVOLUTION_API_FIXED_RECIPIENT is set, the number parameter is ignored.
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        target_number = _get_target_number(number)
        
        result = asyncio.run(client.send_presence(
            instance, target_number, presence, delay
        ))
        
        return {
            "status": "success",
            "result": result,
            "instance": instance,
            "number": target_number,
            "presence": presence,
            "delay": delay
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": instance,
            "number": number
        }

@mcp.resource("evolution://config/{config_type}")
def get_config_info(config_type: str) -> str:
    """Get Evolution API configuration information"""
    if not config:
        return "Evolution API not configured"
    
    if config_type == "general":
        return f"""Evolution API Configuration:
- Base URL: {config.base_url}
- Instance: {config.instance}
- Timeout: {config.timeout}s
- Max Retries: {config.max_retries}
- Fixed Recipient: {'Yes' if config.fixed_recipient else 'No'}
"""
    elif config_type == "connection":
        return f"""Connection Settings:
- API URL: {config.base_url}
- Timeout: {config.timeout} seconds
- Max Retries: {config.max_retries}
- Authentication: API Key configured
"""
    elif config_type == "security":
        return f"""Security Settings:
- Fixed Recipient Mode: {'Enabled' if config.fixed_recipient else 'Disabled'}
- Target Number: {config.fixed_recipient if config.fixed_recipient else 'Dynamic'}
- API Key: {'Configured' if config.api_key else 'Not configured'}
"""
    else:
        return "Invalid config type. Use: general, connection, or security"

@mcp.resource("evolution://instances/{instance_id}")
def get_instance_info(instance_id: str) -> str:
    """Get Evolution API instance information"""
    if not config:
        return "Evolution API not configured"
    
    return f"""Evolution API Instance: {instance_id}
- Base URL: {config.base_url}
- Current Instance: {config.instance}
- Status: {'Current' if instance_id == config.instance else 'Other'}
- Available Tools: 7 messaging tools
- Security: {'Fixed recipient' if config.fixed_recipient else 'Dynamic recipient'}
"""

def create_server(server_config: Optional[EvolutionAPIConfig] = None):
    """Create Evolution API MCP server"""
    global config, client
    
    config = server_config or EvolutionAPIConfig()
    if config and config.api_key:
        client = EvolutionAPIClient(config)
    
    return mcp

def get_metadata() -> Dict[str, Any]:
    """Get tool metadata for discovery"""
    return {
        "name": "evolution-api",
        "version": "1.0.0",
        "description": "Complete WhatsApp messaging suite for Evolution API v2",
        "author": "Namastex Labs",
        "category": "communication",
        "tags": ["whatsapp", "messaging", "evolution-api", "chat", "automation"]
    }

def get_config_class():
    """Get configuration class for this tool"""
    return EvolutionAPIConfig