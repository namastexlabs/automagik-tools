"""
Evolution API MCP Tool - Complete WhatsApp messaging suite for Evolution API v2
"""

from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from .config import EvolutionAPIConfig
from .client import EvolutionAPIClient

# Global configuration and client
config: Optional[EvolutionAPIConfig] = None
client: Optional[EvolutionAPIClient] = None

# Create FastMCP instance
mcp = FastMCP(
    "Evolution API Tool",
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
async def send_text_message(
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
    global config, client
    
    # Ensure client is initialized (in case MCP hasn't called create_server yet)
    if not client:
        if not config:
            config = EvolutionAPIConfig()
        if config.api_key:
            client = EvolutionAPIClient(config)
        else:
            return {"error": "Evolution API client not configured - missing API key"}
    
    try:
        target_number = _get_target_number(number)
        
        result = await client.send_text_message(
            instance, target_number, message, delay, linkPreview, mentions
        )
        
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
async def send_media(
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
        
        result = await client.send_media(
            instance, target_number, media, mediatype, mimetype, 
            caption, fileName, delay, linkPreview, mentions
        )
        
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
async def send_audio(
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
        await client.send_presence(instance, target_number, "composing", 3000)
        
        result = await client.send_audio(
            instance, target_number, audio, delay, linkPreview, mentions, quoted
        )
        
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
async def send_reaction(
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
        result = await client.send_reaction(
            instance, remote_jid, from_me, message_id, reaction
        )
        
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
async def send_location(
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
        
        result = await client.send_location(
            instance, target_number, latitude, longitude, name, address, delay, mentions
        )
        
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
async def send_contact(
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
        
        result = await client.send_contact(
            instance, target_number, contact, delay, mentions
        )
        
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
async def send_presence(
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
        
        result = await client.send_presence(
            instance, target_number, presence, delay
        )
        
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

@mcp.tool()
async def create_instance(
    instance_name: str,
    token: Optional[str] = None,
    webhook: Optional[str] = None,
    webhookByEvents: bool = False,
    webhookBase64: bool = True,
    events: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new Evolution API instance
    
    Args:
        instance_name: Name for the new instance
        token: Optional authentication token for the instance
        webhook: Optional webhook URL for receiving events
        webhookByEvents: Whether to send events to webhook
        webhookBase64: Whether to encode webhook data in base64
        events: List of events to subscribe to
    
    Returns:
        Dictionary with instance creation status and details
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        result = await client.create_instance(
            instance_name, token, webhook, webhookByEvents, webhookBase64, events
        )
        
        return {
            "status": "success",
            "result": result,
            "instance_name": instance_name,
            "webhook_configured": bool(webhook)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance_name": instance_name
        }

@mcp.tool()
async def get_instance_info(
    instance_name: str
) -> Dict[str, Any]:
    """
    Get information about an Evolution API instance
    
    Args:
        instance_name: Name of the instance to get info for
    
    Returns:
        Dictionary with instance information and status
    """
    if not client:
        return {"error": "Evolution API client not configured"}
    
    try:
        result = await client.get_instance_info(instance_name)
        
        return {
            "status": "success",
            "result": result,
            "instance_name": instance_name
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance_name": instance_name
        }

@mcp.resource("evolution://config")
def get_config_info() -> str:
    """Get Evolution API configuration information"""
    if not config:
        return "Evolution API not configured - missing environment variables"
    
    return f"""Evolution API Configuration:
- Base URL: {config.base_url}
- Instance: {config.instance}
- Timeout: {config.timeout}s
- Max Retries: {config.max_retries}
- Fixed Recipient: {'Yes' if config.fixed_recipient else 'No'}
- API Key: {'Configured' if config.api_key else 'Not configured'}

Connection Settings:
- API URL: {config.base_url}
- Timeout: {config.timeout} seconds
- Max Retries: {config.max_retries}
- Authentication: API Key configured

Security Settings:
- Fixed Recipient Mode: {'Enabled' if config.fixed_recipient else 'Disabled'}
- Target Number: {config.fixed_recipient if config.fixed_recipient else 'Dynamic'}
"""

@mcp.resource("evolution://status")
def get_instance_info_resource() -> str:
    """Get Evolution API instance information"""
    if not config:
        return "Evolution API not configured - missing environment variables"
    
    return f"""Evolution API Instance Status:
- Base URL: {config.base_url}
- Current Instance: {config.instance}
- Available Tools: 9 messaging tools
- Security: {'Fixed recipient' if config.fixed_recipient else 'Dynamic recipient'}

Available messaging functions:
- send_text_message: Send text messages with typing indicators
- send_media: Send images, videos, documents with captions
- send_audio: Send audio messages and voice notes
- send_reaction: Send emoji reactions to messages
- send_location: Send location coordinates with address
- send_contact: Send contact information
- send_presence: Send typing/recording presence indicators
- create_instance: Create new Evolution API instances
- get_instance_info: Get instance information and status
"""

@mcp.prompt()
def whatsapp_message_template(
    message_type: str = "text",
    recipient: str = "",
    urgency: str = "normal"
) -> str:
    """
    Generate a WhatsApp message template for Evolution API
    
    Args:
        message_type: Type of message (text, media, audio, contact, location)
        recipient: Recipient identifier or description
        urgency: Message urgency level (low, normal, high)
    
    Returns:
        Formatted message template
    """
    templates = {
        "text": f"""📱 WhatsApp Text Message Template
To: {recipient or '[recipient]'}
Priority: {urgency}

Message: [Your message here]

Example:
"Hello! This is a test message from Evolution API. 👋"

Tips:
- Keep messages concise and clear
- Use emojis to add personality
- Consider time zones when sending
""",
        "media": f"""📷 WhatsApp Media Message Template
To: {recipient or '[recipient]'}
Priority: {urgency}

Media Type: [image/video/document]
Caption: [Optional caption]
File: [URL or base64 data]

Example:
Caption: "Check out this amazing view! 🌅"

Tips:
- Optimize images for mobile viewing
- Add descriptive captions
- Use appropriate file formats
""",
        "audio": f"""🎵 WhatsApp Audio Message Template
To: {recipient or '[recipient]'}
Priority: {urgency}

Audio Type: Voice message
Duration: [estimated duration]

Tips:
- Keep voice messages under 1 minute
- Speak clearly and at moderate pace
- Consider background noise
""",
        "location": f"""📍 WhatsApp Location Template
To: {recipient or '[recipient]'}
Priority: {urgency}

Location: [Place name]
Address: [Full address]
Coordinates: [Lat, Lng]

Example:
Name: "Coffee Shop Downtown"
Address: "123 Main St, City"

Tips:
- Include landmark references
- Verify coordinates accuracy
""",
        "contact": f"""👤 WhatsApp Contact Template
To: {recipient or '[recipient]'}
Priority: {urgency}

Contact Name: [Full name]
Phone: [Phone number with country code]
Organization: [Company/Organization]
Email: [Email address]

Tips:
- Use complete contact information
- Verify phone number format
- Include professional context
"""
    }
    
    return templates.get(message_type, templates["text"])

@mcp.prompt()
def evolution_api_setup_guide(
    instance_name: str = "my-whatsapp",
    deployment_type: str = "local"
) -> str:
    """
    Generate setup guide for Evolution API integration
    
    Args:
        instance_name: Name for the Evolution API instance
        deployment_type: Deployment type (local, cloud, docker)
    
    Returns:
        Step-by-step setup guide
    """
    return f"""🚀 Evolution API Setup Guide

Instance: {instance_name}
Deployment: {deployment_type}

## Step 1: Environment Configuration
```bash
export EVOLUTION_API_BASE_URL="http://localhost:18080"
export EVOLUTION_API_KEY="your-api-key-here"
export EVOLUTION_API_INSTANCE="{instance_name}"
export EVOLUTION_API_TIMEOUT="30"
```

## Step 2: Create Instance
Use the create_instance tool:
- Instance Name: {instance_name}
- Configure webhook (optional)
- Set authentication token

## Step 3: Connect WhatsApp
1. Call create_instance
2. Get QR code from Evolution API
3. Scan with WhatsApp mobile app
4. Wait for connection confirmation

## Step 4: Test Messaging
Use send_text_message tool:
```
Instance: {instance_name}
Number: +1234567890
Message: "Hello from Evolution API! 👋"
```

## Security Notes:
- Keep API keys secure
- Use EVOLUTION_API_FIXED_RECIPIENT for restricted environments
- Monitor webhook events for security

## Troubleshooting:
- Check Evolution API server status
- Verify network connectivity
- Confirm WhatsApp connection status
- Review API key permissions

Ready to start messaging! 📱
"""

def create_server(server_config: Optional[EvolutionAPIConfig] = None):
    """Create Evolution API MCP server"""
    global config, client
    
    # Always create fresh config to pick up environment variables
    config = server_config or EvolutionAPIConfig()
    
    # Initialize client if we have an API key
    if config and config.api_key:
        client = EvolutionAPIClient(config)
    else:
        # Log for debugging
        print(f"Warning: Evolution API key not found. Base URL: {config.base_url if config else 'No config'}")
    
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