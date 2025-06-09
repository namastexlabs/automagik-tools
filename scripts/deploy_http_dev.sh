#!/bin/bash
# Development deployment script for automagik-tools HTTP server
# Provides convenient commands for common deployment scenarios using streamable-http transport

set -e

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Show usage
show_usage() {
    echo -e "${BLUE}=== Automagik Tools HTTP Development Deployment ===${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  start [host] [port] [tools]  - Start HTTP server (default: 0.0.0.0 8000 all)"
    echo "  stop [port]                  - Stop HTTP server (default: 8000)"
    echo "  restart [host] [port] [tools] - Restart HTTP server"
    echo "  status [port]                - Check server status (default: 8000)"
    echo "  logs [port]                  - Show server logs (default: 8000)"
    echo "  dev                          - Start development server (localhost:8000)"
    echo "  network                      - Start network server (0.0.0.0:8000)"
    echo "  test                         - Start test server (localhost:8001)"
    echo "  evolution                    - Start only evolution-api tools (port 8002)"
    echo "  genie                        - Start only genie tool (port 8003)"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 start                     # Start all tools on 0.0.0.0:8000"
    echo "  $0 start localhost 8001      # Start all tools on localhost:8001"
    echo "  $0 start 0.0.0.0 8000 genie # Start only genie tool"
    echo "  $0 dev                       # Quick development setup"
    echo "  $0 stop                      # Stop server on port 8000"
    echo "  $0 logs                      # View logs for port 8000"
    echo ""
}

# Check server status
check_status() {
    local port="${1:-8000}"
    local pid_file="logs/http_server_${port}.pid"
    
    echo -e "${BLUE}=== Server Status (Port $port) ===${NC}"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is running (PID: $pid)${NC}"
            echo -e "${BLUE}Endpoint: http://localhost:$port/${NC}"
            
            # Test if endpoint is responsive
            if curl -s "http://localhost:$port/" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Server is responding to requests${NC}"
            else
                echo -e "${YELLOW}⚠️  Server process exists but not responding${NC}"
            fi
        else
            echo -e "${RED}❌ Server not running (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}No PID file found${NC}"
    fi
    
    # Check if port is in use
    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}Port $port is in use${NC}"
        lsof -i:$port
    else
        echo -e "${GREEN}Port $port is available${NC}"
    fi
}

# Show logs
show_logs() {
    local port="${1:-8000}"
    local log_file="logs/http_server_${port}.log"
    
    if [ -f "$log_file" ]; then
        echo -e "${BLUE}=== Server Logs (Port $port) ===${NC}"
        tail -f "$log_file"
    else
        echo -e "${RED}Log file not found: $log_file${NC}"
    fi
}

# Main command handling
case "${1:-}" in
    "start")
        "$SCRIPT_DIR/start_http_server.sh" "${2:-0.0.0.0}" "${3:-8000}" "${4:-all}"
        ;;
    
    "stop")
        "$SCRIPT_DIR/stop_http_server.sh" "${2:-8000}"
        ;;
    
    "restart")
        "$SCRIPT_DIR/stop_http_server.sh" "${3:-8000}"
        sleep 2
        "$SCRIPT_DIR/start_http_server.sh" "${2:-0.0.0.0}" "${3:-8000}" "${4:-all}"
        ;;
    
    "status")
        check_status "${2:-8000}"
        ;;
    
    "logs")
        show_logs "${2:-8000}"
        ;;
    
    "dev")
        echo -e "${BLUE}Starting development server...${NC}"
        "$SCRIPT_DIR/start_http_server.sh" "localhost" "8000" "all"
        ;;
    
    "network")
        echo -e "${BLUE}Starting network server...${NC}"
        "$SCRIPT_DIR/start_http_server.sh" "0.0.0.0" "8000" "all"
        ;;
    
    "test")
        echo -e "${BLUE}Starting test server...${NC}"
        "$SCRIPT_DIR/start_http_server.sh" "localhost" "8001" "all"
        ;;
    
    "evolution")
        echo -e "${BLUE}Starting Evolution API server...${NC}"
        "$SCRIPT_DIR/start_http_server.sh" "0.0.0.0" "8002" "evolution-api,evolution-api-v2"
        ;;
    
    "genie")
        echo -e "${BLUE}Starting Genie server...${NC}"
        "$SCRIPT_DIR/start_http_server.sh" "0.0.0.0" "8003" "genie"
        ;;
    
    "")
        show_usage
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac