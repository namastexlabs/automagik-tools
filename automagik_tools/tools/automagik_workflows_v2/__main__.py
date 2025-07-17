"""
CLI compatibility module for automagik-workflows-v2
Exports 'mcp' for FastMCP CLI compatibility
"""

from .server import create_server

# Export for FastMCP CLI compatibility
mcp = create_server()