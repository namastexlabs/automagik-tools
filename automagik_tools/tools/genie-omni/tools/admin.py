"""Admin tools - Manage connections and configuration."""

import logging
from typing import Callable
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_client: Callable):
    """Register admin tools with the MCP server."""
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
