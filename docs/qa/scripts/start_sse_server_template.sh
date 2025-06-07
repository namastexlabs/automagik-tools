#!/bin/bash
# Start Genie with Linear MCP server on SSE transport

# Set environment variables
# Note: Set your actual API keys in your environment before running this script
export OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_api_key_here}"
export GENIE_MCP_CONFIGS='{"linear":{"command":"npx","args":["-y","@tacticlaunch/mcp-linear"],"env":{"LINEAR_API_TOKEN":"'${LINEAR_API_TOKEN:-your_linear_api_token_here}'"}}}'
export AUTOMAGIK_TRANSPORT="sse"

# Kill any existing processes
echo "Stopping any existing Genie or Linear processes..."
pkill -f "automagik-tools.*genie" 2>/dev/null
pkill -f "mcp-linear" 2>/dev/null
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Start server using local development version
echo "Starting Genie SSE server with Linear on port 8885 (using local code)..."
echo "Logs will be written to logs/genie_linear_sse.log"
# Use uv run to run the local development version
nohup uv run automagik-tools serve --tool genie --transport sse --port 8885 > logs/genie_linear_sse.log 2>&1 &
echo "Server started with PID $!"