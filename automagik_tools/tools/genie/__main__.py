"""
Genie - Main module for MCP server execution

This module provides the entry point for running Genie as an MCP server.
"""

from . import create_server

# Export the FastMCP server for CLI compatibility
mcp = create_server()

if __name__ == "__main__":
    # This allows running the tool directly
    import sys

    # Run the server
    # Use stderr for startup message to avoid stdout pollution
    print("🧞 Starting Genie MCP server...", file=sys.stderr)
    mcp.run()
