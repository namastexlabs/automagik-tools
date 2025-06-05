#!/usr/bin/env python
"""Standalone runner for Evolution API v2"""

import argparse
from . import run_standalone, get_metadata, EvolutionAPIv2Config, create_server

# Export for FastMCP CLI: fastmcp run automagik_tools.tools.evolution_api_v2
config = EvolutionAPIv2Config()
mcp = create_server(config)


def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata["description"],
        prog="python -m automagik_tools.tools.evolution_api_v2",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    print(f"Starting {metadata['name']} on {args.host}:{args.port}")
    run_standalone(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
