"""
Evolution API server for direct FastMCP usage
"""

from ..tools.evolution_api import create_server, EvolutionAPIConfig

# Create the server with configuration from environment
config = EvolutionAPIConfig()
server = create_server(config)

# Export for FastMCP CLI
mcp = server

if __name__ == "__main__":
    server.run()