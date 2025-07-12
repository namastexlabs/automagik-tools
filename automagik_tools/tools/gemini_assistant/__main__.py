"""Main entry point for Gemini Assistant MCP tool"""

from .server import create_server

# Export mcp for FastMCP CLI compatibility
mcp = create_server()

if __name__ == "__main__":
    mcp.run()