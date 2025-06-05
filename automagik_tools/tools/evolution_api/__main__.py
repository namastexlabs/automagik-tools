#!/usr/bin/env python
"""Run Evolution API tool standalone"""

import sys
import argparse
from . import run_standalone, get_metadata, EvolutionAPIConfig, create_server

# Export for FastMCP CLI: fastmcp run automagik_tools.tools.evolution_api
config = EvolutionAPIConfig()
mcp = create_server(config)


def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata['description']
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--show-config', action='store_true', help='Show configuration and exit')
    
    args = parser.parse_args()
    
    if args.show_config:
        config = EvolutionAPIConfig()
        print("Evolution API Configuration:")
        print(f"  Base URL: {config.base_url}")
        print(f"  API Key: {'***' if config.api_key else 'Not set'}")
        print(f"  Timeout: {config.timeout}s")
        print("\nEnvironment Variables:")
        print("  EVOLUTION_BASE_URL - Evolution API base URL")
        print("  EVOLUTION_API_KEY - Evolution API key for authentication")
        print("  EVOLUTION_TIMEOUT - Request timeout in seconds")
        return
    
    # Run the server
    run_standalone(host=args.host, port=args.port)


if __name__ == "__main__":
    main()