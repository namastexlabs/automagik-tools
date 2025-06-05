"""
Example Hello server for direct FastMCP usage
"""

from ..tools.example_hello import create_server, ExampleHelloConfig

# Create the server
config = ExampleHelloConfig()
server = create_server(config)

# Export for FastMCP CLI
mcp = server

if __name__ == "__main__":
    server.run()