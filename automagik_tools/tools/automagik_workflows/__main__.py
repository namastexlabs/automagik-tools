#!/usr/bin/env python
"""Standalone runner for automagik_workflows"""

import argparse
import sys

# Handle both direct execution and module execution
try:
    from . import create_server, get_metadata
except ImportError:
    # When run directly (uvx fastmcp run __main__.py)
    import os
    # Add the project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    sys.path.insert(0, project_root)
    from automagik_tools.tools.automagik_workflows import create_server, get_metadata


def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata["description"],
        prog="python -m automagik_tools.tools.automagik_workflows",
    )
    parser.add_argument(
        "--transport", default="stdio", help="Transport type (stdio, sse)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (for sse transport)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (for sse transport)"
    )

    args = parser.parse_args()
    server = create_server()

    if args.transport == "stdio":
        print(
            f"Starting {metadata['name']} with STDIO transport",
            file=sys.stderr,
            flush=True,
        )
        server.run(transport="stdio")
    elif args.transport == "sse":
        print(
            f"Starting {metadata['name']} with SSE transport on {args.host}:{args.port}",
            flush=True,
        )
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        raise ValueError(f"Unsupported transport: {args.transport}")


# Export the mcp server for FastMCP CLI compatibility
mcp = create_server()

if __name__ == "__main__":
    main()
