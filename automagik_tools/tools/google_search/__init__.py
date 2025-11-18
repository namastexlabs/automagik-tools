"""
Google Search - Google Workspace search

9+ tools for managing Search.
"""

import logging
import os
from typing import Optional

from automagik_tools.tools.google_workspace_core.config import GoogleWorkspaceBaseConfig
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

# Global configuration
config: Optional["SearchConfig"] = None


class SearchConfig(GoogleWorkspaceBaseConfig):
    """Search-specific configuration"""

    model_config = ConfigDict(
        env_prefix="GOOGLE_SEARCH_", env_file=".env", env_file_encoding="utf-8"
    )


def create_server(cfg: Optional[SearchConfig] = None):
    """Create and configure Search MCP server."""
    global config

    config = cfg or SearchConfig()

    # Set environment variables
    if config.client_id:
        os.environ["GOOGLE_OAUTH_CLIENT_ID"] = config.client_id
    if config.client_secret:
        os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = config.client_secret
    os.environ["GOOGLE_MCP_CREDENTIALS_DIR"] = os.path.expanduser(
        config.credentials_dir
    )
    os.environ["USER_GOOGLE_EMAIL"] = config.user_email or ""
    os.environ["MCP_ENABLE_OAUTH21"] = str(config.enable_oauth21).lower()
    os.environ["MCP_SINGLE_USER_MODE"] = str(config.single_user_mode).lower()
    os.environ["WORKSPACE_MCP_STATELESS_MODE"] = str(config.stateless_mode).lower()
    os.environ["WORKSPACE_MCP_BASE_URI"] = config.base_uri
    os.environ["WORKSPACE_MCP_PORT"] = str(config.port)
    os.environ["WORKSPACE_MCP_LOG_LEVEL"] = config.log_level

    # Reload OAuth configuration
    from automagik_tools.tools.google_workspace_core.auth.oauth_config import (
        reload_oauth_config,
    )

    reload_oauth_config()

    # Import the server from core
    from automagik_tools.tools.google_workspace_core.core.server import (
        server,
        set_transport_mode,
        configure_server_for_http,
    )

    set_transport_mode("stdio")

    # Import Search tools to register them
    from . import search_tools  # noqa: F401

    # Configure tool registry
    from automagik_tools.tools.google_workspace_core.core.tool_registry import (
        set_enabled_tools as set_enabled_tool_names,
        wrap_server_tool_method,
        filter_server_tools,
    )
    from automagik_tools.tools.google_workspace_core.auth.scopes import (
        set_enabled_tools,
    )

    wrap_server_tool_method(server)
    set_enabled_tools(["search"])
    set_enabled_tool_names(None)
    filter_server_tools(server)
    configure_server_for_http()

    logger.info("Search MCP initialized")

    return server


def get_config_class():
    return SearchConfig


def get_metadata():
    return {
        "name": "google-search",
        "version": "2.0.0",
        "description": "Google Workspace search",
        "category": "productivity",
        "author": "Namastex Labs",
        "tags": ["google", "search", "workspace"],
        "config_env_prefix": "GOOGLE_SEARCH_",
    }


create_tool = create_server
