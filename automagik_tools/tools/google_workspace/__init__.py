"""
Google Workspace MCP Tool

Comprehensive Google Workspace integration for Calendar, Gmail, Docs, Sheets, Slides, Drive, Chat, Forms, Tasks & Search.
"""

import logging
import os
from typing import Optional

from .config import GoogleWorkspaceConfig

# Suppress googleapiclient discovery cache warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Global configuration
config: Optional[GoogleWorkspaceConfig] = None


def create_server(cfg: Optional[GoogleWorkspaceConfig] = None):
    """
    Create and configure Google Workspace MCP server.

    Args:
        cfg: Configuration object. If None, loads from environment.

    Returns:
        Configured FastMCP server instance (from .core.server)
    """
    global config

    # Load configuration
    config = cfg or GoogleWorkspaceConfig()

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
    from .auth.oauth_config import reload_oauth_config
    reload_oauth_config()

    # Import the pre-configured server from core
    from .core.server import server, set_transport_mode, configure_server_for_http

    # Set transport mode
    set_transport_mode('stdio')

    # Import and register tools based on tier
    _register_tools(config.tool_tier)

    # Configure tool registry
    from .core.tool_registry import set_enabled_tools as set_enabled_tool_names, wrap_server_tool_method, filter_server_tools
    from .auth.scopes import set_enabled_tools

    # Wrap server tool method
    wrap_server_tool_method(server)

    # Determine which services to enable based on tool tier
    all_services = ['gmail', 'drive', 'calendar', 'docs', 'sheets', 'chat', 'forms', 'slides', 'tasks', 'search']
    core_services = ['gmail', 'drive', 'calendar', 'docs', 'sheets', 'chat', 'search']

    if config.tool_tier == "core":
        enabled_services = core_services
    elif config.tool_tier == "extended":
        enabled_services = core_services + ['forms', 'tasks']
    else:  # complete
        enabled_services = all_services

    set_enabled_tools(enabled_services)
    set_enabled_tool_names(None)  # Enable all tools within selected services

    # Filter tools
    filter_server_tools(server)

    # Configure authentication
    configure_server_for_http()

    logger.info(f"Google Workspace MCP initialized with tier: {config.tool_tier}")
    logger.info(f"Enabled services: {', '.join(enabled_services)}")

    return server


def _register_tools(tier: str):
    """
    Register Google Workspace tools based on tier.

    Args:
        tier: Tool tier (core, extended, complete)
    """
    # Core tools (always loaded)
    from .services import gmail_tools
    from .services import drive_tools
    from .services import calendar_tools
    from .services import docs_tools
    from .services import sheets_tools
    from .services import chat_tools
    from .services import search_tools

    # Extended tools
    if tier in ["extended", "complete"]:
        from .services import forms_tools
        from .services import tasks_tools

    # Complete tools
    if tier == "complete":
        from .services import slides_tools


def get_config_class():
    """Return configuration class for automagik-tools discovery."""
    return GoogleWorkspaceConfig


def get_metadata():
    """Return tool metadata for automagik-tools."""
    return {
        "name": "google-workspace",
        "version": "1.5.5",
        "description": "Comprehensive Google Workspace integration (Calendar, Gmail, Docs, Sheets, Drive, etc.)",
        "category": "productivity",
        "author": "Namastex Labs",
        "tags": ["google", "workspace", "gmail", "calendar", "docs", "sheets", "drive"],
        "config_env_prefix": "GOOGLE_WORKSPACE_",
    }


# For backwards compatibility
create_tool = create_server
