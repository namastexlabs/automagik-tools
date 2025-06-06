#!/bin/bash
# Wrapper script for running Genie with stdio transport for MCP

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the automagik-tools directory
cd "$SCRIPT_DIR"

# Run the command using uv run
exec uv run automagik-tools serve --tool genie --transport stdio