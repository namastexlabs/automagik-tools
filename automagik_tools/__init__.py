"""
Automagik Tools - A monorepo package for MCP tools with dynamic loading capabilities
"""

try:
    import importlib.metadata
    __version__ = importlib.metadata.version("automagik-tools")
except ImportError:
    # Fallback for development
    __version__ = "0.1.2pre3"

__all__ = ["__version__"]
