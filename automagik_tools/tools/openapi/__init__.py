"""
OpenAPI - Universal API to MCP Converter

Convert any OpenAPI specification into an MCP server automatically.
Uses FastMCP's native from_openapi() for zero-code API integration.
"""

from typing import Optional
from fastmcp import FastMCP
from .config import OpenAPIConfig

# Global config instance
config: Optional[OpenAPIConfig] = None

# MCP server instance (initialized in create_server)
mcp: Optional[FastMCP] = None


def get_metadata():
    """Get tool metadata for discovery"""
    return {
        "name": "openapi",
        "version": "2.0.0",
        "description": "Universal OpenAPI to MCP converter - plugin any API spec automatically",
        "author": "Namastex Labs",
    }


def get_config_class():
    """Return the config class for this tool"""
    return OpenAPIConfig


def create_server(cfg: Optional[OpenAPIConfig] = None):
    """Create MCP server from OpenAPI spec"""
    global config, mcp

    # Use provided config or create from environment
    if cfg:
        config = cfg
    else:
        config = OpenAPIConfig()

    if not config.openapi_url:
        raise ValueError(
            "OPENAPI_OPENAPI_URL must be set. "
            "Point it to your OpenAPI spec URL."
        )

    # Create MCP server from OpenAPI spec using modern FastMCP
    mcp = FastMCP.from_openapi(
        openapi_url=config.openapi_url,
        name=config.name or "OpenAPI",
        instructions=config.instructions or "API tools auto-generated from OpenAPI spec",
        # Pass authentication if configured
        headers={
            "Authorization": f"Bearer {config.api_key}" if config.api_key else None,
            **(config.extra_headers or {}),
        },
        # Pass base URL override if configured
        base_url=config.base_url if config.base_url else None,
    )

    return mcp


# For backwards compatibility
def get_server():
    """Get or create the MCP server instance"""
    global mcp
    if mcp is None:
        create_server()
    return mcp
