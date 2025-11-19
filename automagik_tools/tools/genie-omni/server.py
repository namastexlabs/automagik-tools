"""
Genie Omni - Agent-First WhatsApp Communication Tool
Your personal hub to the digital world.

Philosophy: Tools designed from Genie's perspective, not API perspective.
You ARE connected to WhatsApp. You CAN send and read messages.
"""

import logging
from typing import Optional
from fastmcp import FastMCP
from .client import OmniClient
from .config import OmniConfig

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("genie-omni")

# Global client and config (initialized on first use)
_client: Optional[OmniClient] = None
_config: Optional[OmniConfig] = None


def initialize_client(config: OmniConfig) -> None:
    """Initialize the global client with a specific config.

    Args:
        config: Configuration for the Omni client
    """
    global _client, _config
    _config = config
    _client = OmniClient(config)


def get_client() -> OmniClient:
    """Get or create Omni client."""
    global _client, _config
    if _client is None:
        _config = OmniConfig.from_env()
        _client = OmniClient(_config)
    return _client


def get_config() -> OmniConfig:
    """Get or create Omni config."""
    global _config
    if _config is None:
        _config = OmniConfig.from_env()
    return _config


# Register all tool modules
from .tools import identity, contacts, reading, messaging, discovery, admin, multimodal

identity.register_tools(mcp, get_client)
contacts.register_tools(mcp, get_client)
reading.register_tools(mcp, get_client)
messaging.register_tools(mcp, get_client, get_config)
discovery.register_tools(mcp, get_client, get_config)
admin.register_tools(mcp, get_client)
multimodal.register_tools(mcp, get_client, get_config)
