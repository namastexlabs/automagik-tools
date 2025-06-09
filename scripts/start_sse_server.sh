#!/bin/bash
# Start automagik-tools SSE server for internal development
# This script deploys all tools on separate endpoints for network access

set -e

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Configuration with .env fallbacks
DEFAULT_HOST="${HOST:-0.0.0.0}"
DEFAULT_PORT="${PORT:-8000}"
DEFAULT_TOOLS="all"

# Parse command line arguments (override .env values)
HOST="${1:-$DEFAULT_HOST}"
PORT="${2:-$DEFAULT_PORT}"
TOOLS="${3:-$DEFAULT_TOOLS}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Automagik Tools SSE Server Startup ===${NC}"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Tools: $TOOLS"
echo ""

# Kill any existing processes on the port
echo -e "${YELLOW}Stopping any existing processes on port $PORT...${NC}"
pkill -f "automagik-tools.*serve-all.*$PORT" 2>/dev/null || true
pkill -f "automagik-tools.*serve.*$PORT" 2>/dev/null || true
pkill -f "automagik-tools.*genie" 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
sleep 2

# Set transport environment variable
export AUTOMAGIK_TRANSPORT="sse"
echo -e "${BLUE}Transport mode: SSE${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file
LOG_FILE="logs/sse_server_${PORT}.log"

# Build the command
if [ "$TOOLS" = "all" ]; then
    COMMAND="uv run automagik-tools serve-all --host $HOST --port $PORT"
    echo -e "${GREEN}Starting SSE server with ALL tools on http://$HOST:$PORT${NC}"
else
    COMMAND="uv run automagik-tools serve-all --host $HOST --port $PORT --tools $TOOLS"
    echo -e "${GREEN}Starting SSE server with tools: $TOOLS on http://$HOST:$PORT${NC}"
fi

echo -e "${BLUE}Command: $COMMAND${NC}"
echo -e "${BLUE}Logs: $LOG_FILE${NC}"
echo ""

# Start the server
echo -e "${YELLOW}Starting server...${NC}"
nohup $COMMAND > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✅ Server started with PID $SERVER_PID${NC}"
echo ""

# Wait a moment for server to start
sleep 3

# Check if server is still running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}🚀 Server is running successfully!${NC}"
    
    # Display available endpoints
    echo ""
    echo -e "${BLUE}=== Available Endpoints ===${NC}"
    echo -e "${GREEN}• Root: http://$HOST:$PORT/${NC}"
    
    # Get list of tools and show their endpoints
    if [ "$TOOLS" = "all" ]; then
        TOOL_LIST=$(uv run automagik-tools list | grep -E "^\s*[a-z-]+" | awk '{print $1}' | grep -v "Tool" | head -10)
    else
        TOOL_LIST="${TOOLS//,/ }"
    fi
    
    for tool in $TOOL_LIST; do
        echo -e "${GREEN}• $tool: http://$HOST:$PORT/$tool/sse${NC}"
    done
    
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo "• View logs: tail -f $LOG_FILE"
    echo "• Stop server: kill $SERVER_PID"
    echo "• Check status: ps -p $SERVER_PID"
    echo "• Test endpoint: curl http://$HOST:$PORT/"
    
    # Save PID for easy management
    echo $SERVER_PID > "logs/sse_server_${PORT}.pid"
    echo -e "${BLUE}PID saved to logs/sse_server_${PORT}.pid${NC}"
    
else
    echo -e "${RED}❌ Server failed to start. Check logs: $LOG_FILE${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 SSE Server deployment complete!${NC}"