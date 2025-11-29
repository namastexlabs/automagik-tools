#!/bin/bash
# Development environment runner with graceful shutdown
# Usage: ./scripts/dev_runner.sh
#
# Dynamically allocates ports starting from:
#   Backend:  8000
#   Frontend: 3000

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Dynamic ports (set in main)
BACKEND_PORT=""
FRONTEND_PORT=""

# Find next available port starting from a given port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while lsof -i:$port >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down development servers...${NC}"

    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi

    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi

    # Kill any orphaned processes on our allocated ports
    if [ -n "$BACKEND_PORT" ]; then
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PORT" ]; then
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    fi

    echo -e "${GREEN}Development servers stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

check_prerequisites() {
    echo -e "${PURPLE}Checking prerequisites...${NC}"

    if ! command -v uv &>/dev/null; then
        echo -e "${RED}Error: uv not found. Run: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi

    if ! command -v pnpm &>/dev/null; then
        echo -e "${RED}Error: pnpm not found. Run: npm install -g pnpm${NC}"
        exit 1
    fi

    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Virtual environment not found. Running: uv sync${NC}"
        uv sync --all-extras
    fi

    if [ ! -d "automagik_tools/hub_ui/node_modules" ]; then
        echo -e "${YELLOW}Node modules not found. Running: pnpm install${NC}"
        cd automagik_tools/hub_ui && pnpm install && cd "$PROJECT_ROOT"
    fi

    echo -e "${GREEN}Prerequisites OK${NC}"
}

start_backend() {
    echo -e "${CYAN}Starting backend on http://localhost:$BACKEND_PORT...${NC}"

    (
        cd "$PROJECT_ROOT"
        HUB_PORT=$BACKEND_PORT uv run uvicorn automagik_tools.hub_http:app \
            --host 0.0.0.0 \
            --port $BACKEND_PORT \
            --reload \
            --reload-dir automagik_tools \
            --log-level info \
            2>&1 | sed 's/^/[BACKEND] /'
    ) &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
}

start_frontend() {
    echo -e "${CYAN}Starting frontend on http://localhost:$FRONTEND_PORT...${NC}"

    (
        cd "$PROJECT_ROOT/automagik_tools/hub_ui"
        VITE_BACKEND_PORT=$BACKEND_PORT pnpm dev --port $FRONTEND_PORT 2>&1 | sed 's/^/[FRONTEND] /'
    ) &
    FRONTEND_PID=$!
    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
}

main() {
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  Automagik Tools - Development Mode${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
    echo ""

    check_prerequisites

    # Find available ports
    echo ""
    echo -e "${BLUE}Finding available ports...${NC}"
    BACKEND_PORT=$(find_available_port 8000)
    FRONTEND_PORT=$(find_available_port 3000)
    echo -e "${GREEN}  Backend:  $BACKEND_PORT${NC}"
    echo -e "${GREEN}  Frontend: $FRONTEND_PORT${NC}"

    echo ""
    start_backend

    echo -e "${YELLOW}Waiting for backend to start...${NC}"
    for i in {1..30}; do
        if curl -sf http://localhost:$BACKEND_PORT/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}Backend is ready!${NC}"
            break
        fi
        sleep 1
    done

    echo ""
    start_frontend

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Development servers are running!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}  Backend:  http://localhost:$BACKEND_PORT${NC}"
    echo -e "${CYAN}  Frontend: http://localhost:$FRONTEND_PORT${NC}"
    echo -e "${CYAN}  API Docs: http://localhost:$BACKEND_PORT/docs${NC}"
    echo ""
    echo -e "${YELLOW}  Press Ctrl+C to stop all servers${NC}"
    echo ""

    wait
}

main "$@"
