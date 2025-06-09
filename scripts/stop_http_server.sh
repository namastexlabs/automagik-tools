#!/bin/bash
# Stop automagik-tools HTTP server

set -e

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Configuration with .env fallbacks
DEFAULT_PORT="${PORT:-8000}"

# Parse command line arguments (override .env values)
PORT="${1:-$DEFAULT_PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Stopping Automagik Tools HTTP Server ===${NC}"
echo "Port: $PORT"

# PID file location
PID_FILE="logs/http_server_${PORT}.pid"

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Found PID file: $PID_FILE (PID: $SERVER_PID)${NC}"
    
    # Check if process is still running
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping server with PID $SERVER_PID...${NC}"
        kill $SERVER_PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! ps -p $SERVER_PID > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Server stopped gracefully${NC}"
                break
            fi
            sleep 1
            echo -e "${YELLOW}Waiting for graceful shutdown... ($i/10)${NC}"
        done
        
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo -e "${RED}Forcing server shutdown...${NC}"
            kill -9 $SERVER_PID 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}Process $SERVER_PID is not running (stale PID file)${NC}"
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
    echo -e "${GREEN}Removed PID file${NC}"
else
    echo -e "${YELLOW}No PID file found at $PID_FILE${NC}"
fi

# Kill any remaining processes on the port
echo -e "${YELLOW}Cleaning up any remaining processes on port $PORT...${NC}"
pkill -f "automagik-tools.*serve-all.*$PORT" 2>/dev/null || true
pkill -f "automagik-tools.*serve.*$PORT" 2>/dev/null || true
pkill -f "automagik-tools.*genie" 2>/dev/null || true

# Kill processes using the port
PIDS=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Killing processes using port $PORT: $PIDS${NC}"
    echo $PIDS | xargs kill -9 2>/dev/null || true
fi

# Wait a moment
sleep 1

# Verify port is free
if lsof -i:$PORT > /dev/null 2>&1; then
    echo -e "${RED}⚠️  Port $PORT may still be in use${NC}"
    echo -e "${YELLOW}Check with: lsof -i:$PORT${NC}"
else
    echo -e "${GREEN}✅ Port $PORT is now free${NC}"
fi

echo -e "${GREEN}🎉 Server cleanup complete!${NC}"