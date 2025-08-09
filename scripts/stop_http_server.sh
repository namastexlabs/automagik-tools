#!/bin/bash
# Stop HTTP server for automagik-tools

set -e

# Arguments
PORT="${1:-8000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Automagik Tools HTTP Server on port $PORT...${NC}"

# Find and kill process using the port
PID=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -n "$PID" ]; then
    echo -e "${YELLOW}Found process $PID using port $PORT${NC}"
    kill -TERM $PID 2>/dev/null || true
    sleep 2
    
    # Check if process is still running
    if kill -0 $PID 2>/dev/null; then
        echo -e "${RED}Process didn't stop gracefully, forcing...${NC}"
        kill -KILL $PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Server stopped successfully${NC}"
else
    echo -e "${YELLOW}No server found running on port $PORT${NC}"
fi