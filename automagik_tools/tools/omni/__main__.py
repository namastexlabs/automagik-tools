#!/usr/bin/env python
"""Standalone runner for OMNI MCP tool"""

import argparse
import sys
import asyncio
from . import create_server, get_metadata


def main():
    """Main entry point for OMNI tool"""
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata["description"],
        prog="python -m automagik_tools.tools.omni",
    )
    parser.add_argument(
        "--transport", 
        default="stdio", 
        choices=["stdio", "sse"],
        help="Transport type (stdio for Claude/Cursor, sse for web)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (for sse transport)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (for sse transport)"
    )

    args = parser.parse_args()
    
    # Create server
    server = create_server()
    
    # Run with appropriate transport
    if args.transport == "stdio":
        print(
            f"Starting {metadata['name']} v{metadata['version']} with STDIO transport",
            file=sys.stderr,
            flush=True,
        )
        server.run(transport="stdio")
    elif args.transport == "sse":
        print(
            f"Starting {metadata['name']} v{metadata['version']} with SSE transport on {args.host}:{args.port}",
            flush=True,
        )
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        raise ValueError(f"Unsupported transport: {args.transport}")


if __name__ == "__main__":
    main()