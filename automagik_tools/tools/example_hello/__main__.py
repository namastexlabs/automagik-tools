#!/usr/bin/env python
"""Run Example Hello tool standalone"""

import sys
import argparse
from . import run_standalone, get_metadata


def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata['description']
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    args = parser.parse_args()
    
    # Run the server
    run_standalone(host=args.host, port=args.port)


if __name__ == "__main__":
    main()