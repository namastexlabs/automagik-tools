"""
Main entry point for JSON to Google Docs tool
"""

import asyncio
from . import create_server

async def main():
    """Entry point for running the JSON to Google Docs tool server."""
    server = create_server()
    await server.run(show_banner=False)

# Export mcp for FastMCP CLI compatibility
mcp = create_server()

if __name__ == "__main__":
    asyncio.run(main())