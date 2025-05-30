"""
Evolution API Tool for automagik-tools

A FastMCP tool that integrates with Evolution API for WhatsApp messaging functionality.
Provides tools for sending messages, managing instances, and handling WhatsApp operations.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import httpx
from fastmcp import FastMCP, Context


# Pydantic models for request validation
class SendTextMessage(BaseModel):
    number: str = Field(description="Number to receive the message (with country code)")
    text: str = Field(description="Text message to send")
    delay: Optional[int] = Field(default=None, description="Presence time in milliseconds before sending message")
    linkPreview: Optional[bool] = Field(default=True, description="Shows a preview of the target website if there's a link")
    mentionsEveryOne: Optional[bool] = Field(default=False, description="Mention everyone when the message is sent")
    mentioned: Optional[List[str]] = Field(default=None, description="Numbers to mention")


class InstanceConfig(BaseModel):
    instanceName: str = Field(description="Name of the WhatsApp instance")
    integration: str = Field(default="WHATSAPP-BAILEYS", description="Integration type")
    token: Optional[str] = Field(default=None, description="Instance token")
    number: Optional[str] = Field(default=None, description="WhatsApp number")
    businessId: Optional[str] = Field(default=None, description="Business account ID")


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Profile name")
    status: Optional[str] = Field(default=None, description="Profile status message")


# Helper function to make Evolution API requests
async def make_evolution_request(
    method: str,
    endpoint: str,
    instance: str,
    data: Optional[Dict] = None,
    ctx: Optional[Context] = None,
    config: Optional[Any] = None
) -> Dict[str, Any]:
    """Make authenticated request to Evolution API"""
    if not config or not config.api_key:
        raise ValueError("Evolution API key is required but not configured")
    
    # Remove trailing slash from base URL and ensure proper URL construction
    base_url = config.base_url.rstrip('/')
    url = f"{base_url}/{endpoint.format(instance=instance)}"
    headers = {
        "apikey": config.api_key,
        "Content-Type": "application/json"
    }
    
    if ctx:
        await ctx.info(f"Making {method} request to Evolution API: {url}")
    
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            error_msg = f"Evolution API error: {e.response.status_code} - {e.response.text}"
            if ctx:
                await ctx.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise ValueError(error_msg)


def create_tool(config: Any) -> FastMCP:
    """Create the Evolution API MCP tool"""
    mcp = FastMCP("Evolution API Tool")
    
    # MCP Tools
    @mcp.tool()
    async def send_text_message(
        instance: str,
        number: str,
        text: str,
        delay: Optional[int] = None,
        link_preview: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Send a plain text message via Evolution API
        
        Args:
            instance: Name of the WhatsApp instance
            number: Phone number to send message to (with country code)
            text: Text message content
            delay: Optional delay in milliseconds before sending
            link_preview: Whether to show link previews
        """
        message_data = SendTextMessage(
            number=number,
            text=text,
            delay=delay,
            linkPreview=link_preview
        )
        
        return await make_evolution_request(
            "POST",
            "message/sendText/{instance}",
            instance,
            message_data.model_dump(exclude_none=True),
            ctx,
            config
        )

    @mcp.tool()
    async def create_instance(
        instance_name: str,
        integration: str = "WHATSAPP-BAILEYS",
        token: Optional[str] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Create a new WhatsApp instance
        
        Args:
            instance_name: Name for the new instance
            integration: Integration type (default: WHATSAPP-BAILEYS)
            token: Optional instance token
        """
        instance_data = InstanceConfig(
            instanceName=instance_name,
            integration=integration,
            token=token
        )
        
        return await make_evolution_request(
            "POST",
            "instance/create",
            instance_name,
            instance_data.model_dump(exclude_none=True),
            ctx,
            config
        )

    @mcp.tool()
    async def get_instance_info(instance: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Get information about a WhatsApp instance
        
        Args:
            instance: Name of the instance to query
        """
        return await make_evolution_request(
            "GET",
            "instance/fetchInstances?instanceName={instance}",
            instance,
            ctx=ctx,
            config=config
        )

    @mcp.tool()
    async def get_connection_state(instance: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Get the connection state of a WhatsApp instance
        
        Args:
            instance: Name of the instance to check
        """
        return await make_evolution_request(
            "GET",
            "instance/connectionState/{instance}",
            instance,
            ctx=ctx,
            config=config
        )

    @mcp.tool()
    async def restart_instance(instance: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Restart a WhatsApp instance
        
        Args:
            instance: Name of the instance to restart
        """
        return await make_evolution_request(
            "PUT",
            "instance/restart/{instance}",
            instance,
            ctx=ctx,
            config=config
        )

    @mcp.tool()
    async def delete_instance(instance: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Delete a WhatsApp instance
        
        Args:
            instance: Name of the instance to delete
        """
        return await make_evolution_request(
            "DELETE",
            "instance/delete/{instance}",
            instance,
            ctx=ctx,
            config=config
        )

    @mcp.tool()
    async def check_whatsapp_number(
        instance: str,
        numbers: List[str],
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Check if phone numbers are registered on WhatsApp
        
        Args:
            instance: Name of the instance
            numbers: List of phone numbers to check
        """
        data = {"numbers": numbers}
        return await make_evolution_request(
            "POST",
            "chat/whatsappNumbers/{instance}",
            instance,
            data,
            ctx,
            config
        )

    @mcp.tool()
    async def fetch_profile(instance: str, number: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Fetch profile information for a WhatsApp number
        
        Args:
            instance: Name of the instance
            number: Phone number to fetch profile for
        """
        data = {"number": number}
        return await make_evolution_request(
            "POST",
            "chat/fetchProfile/{instance}",
            instance,
            data,
            ctx,
            config
        )

    @mcp.tool()
    async def update_profile_name(
        instance: str,
        name: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Update the profile name for the instance
        
        Args:
            instance: Name of the instance
            name: New profile name
        """
        data = {"name": name}
        return await make_evolution_request(
            "POST",
            "chat/updateProfileName/{instance}",
            instance,
            data,
            ctx,
            config
        )

    @mcp.tool()
    async def mark_message_as_read(
        instance: str,
        remote_jid: str,
        read_messages: List[Dict[str, str]],
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Mark messages as read
        
        Args:
            instance: Name of the instance
            remote_jid: Remote JID of the chat
            read_messages: List of message IDs to mark as read
        """
        data = {
            "readMessages": read_messages,
            "remoteJid": remote_jid
        }
        return await make_evolution_request(
            "POST",
            "chat/markMessageAsRead/{instance}",
            instance,
            data,
            ctx,
            config
        )

    # MCP Resources
    @mcp.resource("evolution://instances")
    async def list_all_instances(ctx: Context = None) -> str:
        """Get a list of all Evolution API instances"""
        try:
            result = await make_evolution_request("GET", "instance/fetchInstances", "", ctx=ctx, config=config)
            return f"Available instances: {result}"
        except Exception as e:
            return f"Error fetching instances: {str(e)}"

    @mcp.resource("evolution://instance/{instance}/status")
    async def get_instance_status(instance: str, ctx: Context = None) -> str:
        """Get the status of a specific instance"""
        try:
            result = await get_connection_state(instance, ctx)
            return f"Instance {instance} status: {result}"
        except Exception as e:
            return f"Error getting status for {instance}: {str(e)}"

    @mcp.resource("evolution://config")
    async def get_server_config() -> str:
        """Get Evolution API server configuration"""
        config_info = {
            "base_url": config.base_url,
            "api_key_configured": bool(config.api_key),
            "timeout": config.timeout,
            "supported_features": [
                "Send text messages",
                "Instance management", 
                "Profile management",
                "Message status tracking",
                "WhatsApp number validation"
            ]
        }
        return f"Evolution API Configuration: {config_info}"

    # MCP Prompts
    @mcp.prompt()
    def whatsapp_message_template(recipient: str, message_type: str = "greeting") -> str:
        """Generate a WhatsApp message template"""
        templates = {
            "greeting": f"Hello! 👋 This is a message sent via Evolution API to {recipient}",
            "business": f"Dear {recipient}, thank you for your interest in our services. How can we help you today?",
            "reminder": f"Hi {recipient}, this is a friendly reminder about your upcoming appointment.",
            "support": f"Hello {recipient}, we're here to help! Please let us know how we can assist you."
        }
        
        return templates.get(message_type, templates["greeting"])

    @mcp.prompt()
    def instance_setup_guide(instance_name: str) -> str:
        """Generate a guide for setting up a new WhatsApp instance"""
        return f"""
# Setting up WhatsApp Instance: {instance_name}

## Steps:
1. Create the instance using `create_instance` tool
2. Check connection state with `get_connection_state`
3. Scan QR code when prompted (if using regular WhatsApp)
4. Verify connection with `get_instance_info`
5. Test by sending a message with `send_text_message`

## Important Notes:
- Make sure your phone number is not already connected to WhatsApp Web
- Keep the instance running for continuous connectivity
- Monitor connection state regularly

## Next Steps:
- Configure webhooks for message handling
- Set up message templates
- Configure profile settings
"""

    return mcp


__all__ = ["create_tool"] 