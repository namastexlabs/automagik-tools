"""
Google Chat - Google Chat messaging

7+ tools for managing Chat.
"""

import logging
import os
from typing import Optional

from automagik_tools.tools.google_workspace_core.config import GoogleWorkspaceBaseConfig
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

# Global configuration
config: Optional["ChatConfig"] = None


class ChatConfig(GoogleWorkspaceBaseConfig):
    """Chat-specific configuration"""

    model_config = ConfigDict(
        env_prefix="GOOGLE_CHAT_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


def create_server(cfg: Optional[ChatConfig] = None):
    """Create and configure Chat MCP server."""
    global config

    config = cfg or ChatConfig()

    # Set environment variables
    if config.client_id:
        os.environ["GOOGLE_OAUTH_CLIENT_ID"] = config.client_id
    if config.client_secret:
        os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = config.client_secret
    os.environ["GOOGLE_MCP_CREDENTIALS_DIR"] = os.path.expanduser(config.credentials_dir)
    os.environ["USER_GOOGLE_EMAIL"] = config.user_email or ""
    os.environ["MCP_ENABLE_OAUTH21"] = str(config.enable_oauth21).lower()
    os.environ["MCP_SINGLE_USER_MODE"] = str(config.single_user_mode).lower()
    os.environ["WORKSPACE_MCP_STATELESS_MODE"] = str(config.stateless_mode).lower()
    os.environ["WORKSPACE_MCP_BASE_URI"] = config.base_uri
    os.environ["WORKSPACE_MCP_PORT"] = str(config.port)
    os.environ["WORKSPACE_MCP_LOG_LEVEL"] = config.log_level

    # Reload OAuth configuration
    from automagik_tools.tools.google_workspace_core.auth.oauth_config import reload_oauth_config
    reload_oauth_config()

    # Import the server from core
    from automagik_tools.tools.google_workspace_core.core.server import server, set_transport_mode, configure_server_for_http

    set_transport_mode('stdio')

    # Import Chat tools to register them
    from . import chat_tools  # noqa: F401

    # Configure tool registry
    from automagik_tools.tools.google_workspace_core.core.tool_registry import set_enabled_tools as set_enabled_tool_names, wrap_server_tool_method, filter_server_tools
    from automagik_tools.tools.google_workspace_core.auth.scopes import set_enabled_tools

    wrap_server_tool_method(server)
    set_enabled_tools(['chat'])
    set_enabled_tool_names(None)
    filter_server_tools(server)
    configure_server_for_http()

    logger.info("Chat MCP initialized")

    return server


def get_config_class():
    return ChatConfig


def get_metadata():
    return {
        "name": "google-chat",
        "version": "2.0.0",
        "description": "Google Chat messaging",
        "category": "productivity",
        "author": "Namastex Labs",
        "tags": ["google", "chat", "workspace"],
        "config_env_prefix": "GOOGLE_CHAT_",
    }


create_tool = create_server
