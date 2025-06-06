"""
Main entry point for the enhanced automagik tool
"""

from . import create_server

if __name__ == "__main__":
    import uvicorn
    server = create_server()
    uvicorn.run(server.asgi(), host="0.0.0.0", port=8000)

# Export for FastMCP CLI compatibility
mcp = create_server()