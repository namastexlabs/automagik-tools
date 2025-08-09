#!/bin/bash
# Start HTTP server for automagik-tools

set -e

# Arguments
HOST="${1:-0.0.0.0}"
PORT="${2:-8000}"
TOOLS="${3:-all}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Automagik Tools HTTP Server${NC}"
echo -e "${GREEN}Configuration:${NC}"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Tools: $TOOLS"
echo ""

# Determine which command to run based on tools selection
if [ "$TOOLS" = "all" ]; then
    echo -e "${GREEN}Starting hub server with all tools...${NC}"
    exec uv run automagik-tools hub --host "$HOST" --port "$PORT" --transport http
else
    echo -e "${GREEN}Starting specific tool: $TOOLS${NC}"
    exec uv run automagik-tools serve --tool "$TOOLS" --host "$HOST" --port "$PORT" --transport http
fi