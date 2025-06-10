"""
Automagik Tools - A monorepo package for MCP tools with dynamic loading capabilities
"""

import os

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("automagik-tools")
except ImportError:
    # Fallback for development
    __version__ = "0.1.2pre3"

# Configure FastMCP resource prefix format globally
# This sets the recommended "path" format for all FastMCP servers in this package
# Can be overridden with FASTMCP_RESOURCE_PREFIX_FORMAT environment variable
if not os.environ.get("FASTMCP_RESOURCE_PREFIX_FORMAT"):
    os.environ["FASTMCP_RESOURCE_PREFIX_FORMAT"] = "path"

__all__ = ["__version__"]
