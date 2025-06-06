#!/bin/bash
# Start Genie SSE server with Automagik MCP configuration

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set it using: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

# Set up Genie with Automagik configuration (these can have defaults)
export GENIE_AUTOMAGIK_API_KEY="${GENIE_AUTOMAGIK_API_KEY:-namastex888}"
export GENIE_AUTOMAGIK_BASE_URL="${GENIE_AUTOMAGIK_BASE_URL:-http://192.168.112.148:8881}"
export GENIE_AUTOMAGIK_TIMEOUT="${GENIE_AUTOMAGIK_TIMEOUT:-600}"

echo "🚀 Starting Genie SSE server with Automagik integration..."
echo "📡 Automagik API: $GENIE_AUTOMAGIK_BASE_URL"
echo "🌐 SSE endpoint: http://localhost:8000/sse"
echo ""

# Start Genie with SSE transport
uv run automagik-tools serve --tool genie --transport sse