"""Identity tools - Who am I on WhatsApp?"""

import logging
from typing import Callable
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable):
    """Register identity tools with the MCP server."""

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
            result.append("📱 MY WHATSAPP IDENTITY")
            result.append(f"Instance: {instance.name}")
            result.append(f"Number: {instance.phone_number or 'Not configured'}")
            result.append(f"Type: {instance.channel_type}")
            result.append(
                f"Status: {instance.evolution_status.get('state', 'unknown') if instance.evolution_status else 'unknown'}"
            )
            result.append(f"Connected: {'✅ Yes' if instance.is_active else '❌ No'}")

            return "\n".join(result)

        except Exception as e:
            logger.error(f"Error getting WhatsApp info: {e}")
            return f"❌ Failed to get WhatsApp info: {str(e)}"
