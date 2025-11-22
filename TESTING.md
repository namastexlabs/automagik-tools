# Testing Guide for automagik-tools

This guide documents how to test each MCP tool in both HTTP (PM2) and STDIO modes, leaving a trail for fellow friends to follow.

## Overview

All tools in this repository support **two transport modes**:

1. **HTTP (SSE)** - For production deployment via PM2, accessible via HTTP endpoints
2. **STDIO** - For Claude Desktop integration, uses standard input/output

## Testing Infrastructure

### PM2 Ecosystem (HTTP Mode)

Located at: `ecosystem.config.cjs`

**Port Allocation:**
- 8001: evolution-api
- 8002: openapi
- 8003: genie_tool
- 8004: hive
- 8005: wait
- 8006: omni
- 8007: json-to-google-docs
- 8008: spark
- 8009: gemini-assistant

**Usage:**
```bash
# Start all tools
pm2 start ecosystem.config.cjs

# Start specific tool
pm2 start ecosystem.config.cjs --only openapi

# View logs
pm2 logs openapi

# Monitor all
pm2 monit

# Restart all
pm2 restart all

# Stop all
pm2 stop all

# Delete all (clean state)
pm2 delete all
```

### MCP Configuration (.mcp.json)

Located at: `.mcp.json`

This file configures all tools for Claude Desktop integration. Each tool runs in HTTP mode pointing to the PM2-managed services.

**Usage:**
1. Copy `.mcp.json` to your Claude Desktop config directory
2. Ensure PM2 ecosystem is running
3. Restart Claude Desktop

## Tool-by-Tool Testing Checklist

### ✅ 1. openapi (Universal API Bridge)

**Purpose:** Convert any OpenAPI spec into MCP tools

**Environment Variables:**
```bash
export OPENAPI_OPENAPI_URL=https://petstore.swagger.io/v2/swagger.json
export OPENAPI_API_KEY=optional-api-key
export OPENAPI_BASE_URL=optional-base-url-override
export OPENAPI_NAME="Petstore API"
```

**HTTP Mode Test:**
```bash
# Start via PM2
pm2 start ecosystem.config.cjs --only openapi

# Test endpoint
curl http://localhost:8002/mcp

# View logs
pm2 logs openapi
```

**STDIO Mode Test:**
```bash
# Run standalone
uv run python -m automagik_tools.tools.openapi --transport stdio

# Test with echo (should see MCP protocol)
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | uv run python -m automagik_tools.tools.openapi --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8002
- [ ] STDIO mode accepts MCP JSON-RPC messages
- [ ] Tools are auto-generated from OpenAPI spec
- [ ] API key authentication works
- [ ] Base URL override works

---

### ✅ 2. evolution-api (WhatsApp Integration)

**Purpose:** WhatsApp messaging via Evolution API v2

**Environment Variables:**
```bash
export EVOLUTION_API_BASE_URL=http://localhost:8080
export EVOLUTION_API_API_KEY=your-api-key
export EVOLUTION_API_INSTANCE=default
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only evolution-api
curl http://localhost:8001/mcp
pm2 logs evolution-api
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.evolution_api --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8001
- [ ] STDIO mode works
- [ ] Can list WhatsApp instances
- [ ] Can send test message
- [ ] Can retrieve message history

---

### ✅ 3. wait (Utility Tool)

**Purpose:** Simple wait/delay functionality for agent workflows

**Environment Variables:**
None required

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only wait
curl http://localhost:8005/mcp
pm2 logs wait
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.wait --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8005
- [ ] STDIO mode works
- [ ] Can execute wait commands
- [ ] Timing accuracy verified

---

### ✅ 4. genie_tool (Agent Copilot)

**Purpose:** Enhanced agent for copiloting tool usage

**Environment Variables:**
```bash
# Add specific env vars for genie_tool here
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only genie_tool
curl http://localhost:8003/mcp
pm2 logs genie_tool
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.genie_tool --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8003
- [ ] STDIO mode works
- [ ] Agent functionality verified
- [ ] Tool orchestration works

---

### ✅ 5. hive (Hive API Integration)

**Purpose:** Integration with Hive API

**Environment Variables:**
```bash
export HIVE_BASE_URL=http://localhost:3000
export HIVE_API_KEY=your-hive-api-key
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only hive
curl http://localhost:8004/mcp
pm2 logs hive
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.hive --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8004
- [ ] STDIO mode works
- [ ] API authentication works
- [ ] Core endpoints accessible

---

### ✅ 6. omni (Legacy Omni - Genie v1)

**Purpose:** Legacy version of genie omni, kept for backward compatibility

**Environment Variables:**
```bash
export OMNI_BASE_URL=http://localhost:8080
export OMNI_API_KEY=your-omni-api-key
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only omni
curl http://localhost:8006/mcp
pm2 logs omni
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.omni --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8006
- [ ] STDIO mode works
- [ ] Legacy functionality maintained
- [ ] No regressions from updates

---

### ✅ 7. json-to-google-docs (Google Docs Converter)

**Purpose:** Convert JSON data to Google Docs format

**Environment Variables:**
```bash
# Add Google Docs specific env vars here
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only json-to-google-docs
curl http://localhost:8007/mcp
pm2 logs json-to-google-docs
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.json_to_google_docs --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8007
- [ ] STDIO mode works
- [ ] JSON to Google Docs conversion works
- [ ] Authentication with Google works

---

### ⚠️ 8. spark (Experimental)

**Purpose:** Spark API integration (not currently running in production)

**Environment Variables:**
```bash
export SPARK_API_URL=your-spark-api-url
export SPARK_API_KEY=your-spark-api-key
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only spark
curl http://localhost:8008/mcp
pm2 logs spark
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.spark --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8008
- [ ] STDIO mode works
- [ ] Basic functionality verified
- [ ] Ready for future deployment

---

### ⚠️ 9. gemini-assistant (Experimental)

**Purpose:** Google Gemini AI assistant integration

**Environment Variables:**
```bash
export GEMINI_API_KEY=your-gemini-api-key
```

**HTTP Mode Test:**
```bash
pm2 start ecosystem.config.cjs --only gemini-assistant
curl http://localhost:8009/mcp
pm2 logs gemini-assistant
```

**STDIO Mode Test:**
```bash
uv run python -m automagik_tools.tools.gemini_assistant --transport stdio
```

**Success Criteria:**
- [ ] HTTP endpoint responds on port 8009
- [ ] STDIO mode works
- [ ] Gemini API authentication works
- [ ] Assistant responses verified

---

## General Testing Procedures

### 1. Pre-Test Setup

```bash
# Ensure uv is installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd /home/namastex/workspace/automagik-tools
uv sync

# Create logs directory
mkdir -p logs

# Load environment variables
source .env  # or export manually
```

### 2. HTTP Mode Testing (PM2)

```bash
# Start all tools
pm2 start ecosystem.config.cjs

# Check status
pm2 status

# Test each endpoint
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/mcp | head -5
done

# Monitor logs
pm2 logs --lines 50
```

### 3. STDIO Mode Testing

```bash
# Test each tool individually
tools=(evolution_api openapi genie_tool hive wait omni json_to_google_docs spark gemini_assistant)

for tool in "${tools[@]}"; do
  echo "Testing $tool in STDIO mode..."
  echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1}' | \
    uv run python -m automagik_tools.tools.$tool --transport stdio
done
```

### 4. Integration Testing

```bash
# Test with Claude Desktop
# 1. Copy .mcp.json to Claude config
cp .mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS

# 2. Restart Claude Desktop

# 3. Test tool availability in Claude chat
# - Each tool should appear in Claude's tool list
# - Test basic functionality of each tool
```

### 5. Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils  # Linux
brew install apache2            # macOS

# Test endpoint under load
ab -n 1000 -c 10 http://localhost:8002/mcp
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>
```

**PM2 Not Starting:**
```bash
# Check PM2 logs
pm2 logs --err

# Reset PM2
pm2 kill
pm2 start ecosystem.config.cjs
```

**STDIO Mode Not Responding:**
```bash
# Check Python environment
uv run python --version

# Verify tool exists
ls automagik_tools/tools/

# Test with verbose output
uv run python -m automagik_tools.tools.openapi --transport stdio --verbose
```

**Environment Variables Not Loaded:**
```bash
# Verify .env exists
cat .env

# Export manually
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json

# Or use direnv
direnv allow
```

## Testing Results Template

Use this template to document testing results:

```markdown
## Test Results - [Tool Name]

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Version:** [Tool Version]

### HTTP Mode
- [ ] Port accessible
- [ ] MCP endpoint responds
- [ ] Logs show no errors
- [ ] Memory usage normal (<500MB)

### STDIO Mode
- [ ] Accepts MCP messages
- [ ] Returns valid JSON-RPC
- [ ] No stderr errors

### Functionality
- [ ] [Specific feature 1] works
- [ ] [Specific feature 2] works
- [ ] Authentication successful

### Notes
- Any issues encountered:
- Performance observations:
- Recommendations:
```

## Continuous Integration

### Automated Testing (Future)

```bash
# Run all tests
make test

# Run specific tool tests
pytest tests/tools/test_openapi.py -v

# Run integration tests
pytest tests/integration/ -v
```

## Contributing

When adding a new tool:

1. Add to `ecosystem.config.cjs` with unique port
2. Add to `.mcp.json` with HTTP endpoint
3. Create test section in this file
4. Test both HTTP and STDIO modes
5. Document any special requirements
6. Update port allocation list

---

**Remember:** Leave a trail for fellow friends to follow. Document everything! 🚀
