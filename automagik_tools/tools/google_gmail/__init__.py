"""
Google Gmail - Email management for Google Workspace

Comprehensive Gmail integration with 12+ tools for searching, reading, sending,
drafting, and managing email messages and threads.

Tools:
- search_gmail_messages: Search for messages with Gmail query syntax
- get_gmail_message_content: Get full content of a single message
- get_gmail_messages_content_batch: Get content of multiple messages
- get_gmail_attachment_content: Download message attachments
- send_gmail_message: Send new email messages
- draft_gmail_message: Create draft messages
- get_gmail_thread_content: Get full conversation thread
- get_gmail_threads_content_batch: Get multiple threads
- list_gmail_labels: List all labels
- apply_gmail_labels: Apply labels to messages
- remove_gmail_labels: Remove labels from messages
- trash_gmail_messages: Move messages to trash
"""

import logging
import os
from typing import Optional

from automagik_tools.tools.google_workspace_core.config import GoogleWorkspaceBaseConfig
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

# Global configuration
config: Optional["GmailConfig"] = None


class GmailConfig(GoogleWorkspaceBaseConfig):
    """Gmail-specific configuration"""

    model_config = ConfigDict(
        env_prefix="GOOGLE_GMAIL_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


def create_server(cfg: Optional[GmailConfig] = None):
    """
    Create and configure Gmail MCP server.

    Args:
        cfg: Configuration object. If None, loads from environment.

    Returns:
        Configured FastMCP server instance
    """
    global config

    # Load configuration
    config = cfg or GmailConfig()

    # Set environment variables for Google Workspace modules
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

    # Set transport mode
    set_transport_mode('stdio')

    # Import Gmail tools to register them
    from . import gmail_tools  # noqa: F401

    # Configure tool registry
    from automagik_tools.tools.google_workspace_core.core.tool_registry import set_enabled_tools as set_enabled_tool_names, wrap_server_tool_method, filter_server_tools
    from automagik_tools.tools.google_workspace_core.auth.scopes import set_enabled_tools

    # Wrap server tool method
    wrap_server_tool_method(server)

    # Enable Gmail service
    set_enabled_tools(['gmail'])
    set_enabled_tool_names(None)  # Enable all Gmail tools

    # Filter tools
    filter_server_tools(server)

    # Configure authentication
    configure_server_for_http()

    logger.info("Gmail MCP initialized")

    return server


def get_config_class():
    """Return configuration class for automagik-tools discovery."""
    return GmailConfig


def get_metadata():
    """Return tool metadata for automagik-tools."""
    return {
        "name": "google-gmail",
        "version": "2.0.0",
        "description": "Gmail integration - search, read, send, draft, and manage email",
        "category": "productivity",
        "author": "Namastex Labs",
        "tags": ["google", "gmail", "email", "workspace"],
        "config_env_prefix": "GOOGLE_GMAIL_",
    }


# For backwards compatibility
create_tool = create_server
