# PM2 Setup Guide for automagik-tools

Complete guide for deploying automagik-tools MCP servers using PM2 process manager.

## Why PM2?

- **Process Management**: Auto-restart on crashes, manage multiple tools
- **Production Ready**: Built for 24/7 uptime, memory limits, log rotation
- **HTTP/SSE Support**: Serve MCP tools via HTTP endpoints
- **Monitoring**: Real-time CPU, memory, and log monitoring
- **Zero Downtime**: Graceful restarts and updates

## Prerequisites

### 1. Install Node.js and PM2

```bash
# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or on macOS with Homebrew
brew install node

# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version
```

### 2. Install Python and uv

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### 3. Clone and Setup Repository

```bash
# Clone repository
git clone https://github.com/namastexlabs/automagik-tools.git
cd automagik-tools

# Install Python dependencies
uv sync

# Create logs directory
mkdir -p logs
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the repository root:

```bash
# OpenAPI Universal Bridge
OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json
OPENAPI_API_KEY=your-api-key
OPENAPI_BASE_URL=https://api.example.com
OPENAPI_NAME="My API"

# Evolution API (WhatsApp)
EVOLUTION_API_BASE_URL=http://localhost:8080
EVOLUTION_API_API_KEY=your-evolution-api-key
EVOLUTION_API_INSTANCE=default

# Hive
HIVE_BASE_URL=http://localhost:3000
HIVE_API_KEY=your-hive-api-key

# Omni (Legacy)
OMNI_BASE_URL=http://localhost:8080
OMNI_API_KEY=your-omni-api-key

# Spark (Experimental)
SPARK_API_URL=your-spark-api-url
SPARK_API_KEY=your-spark-api-key

# Gemini Assistant (Experimental)
GEMINI_API_KEY=your-gemini-api-key
```

### 2. PM2 Ecosystem Configuration

The ecosystem configuration is already set up in `ecosystem.config.cjs`. Review and adjust if needed:

```javascript
// Key settings per tool:
// - name: Unique identifier for PM2
// - script: uv (Python runner)
// - args: Python module + transport mode + port
// - env: Environment variables
// - max_memory_restart: Auto-restart if memory exceeds limit
// - error_file/out_file: Log locations
```

## Deployment

### Quick Start

```bash
# Start all tools
pm2 start ecosystem.config.cjs

# Save PM2 configuration
pm2 save

# Setup PM2 to start on system boot
pm2 startup
# Follow the instructions printed (may require sudo)
```

### Start Specific Tools

```bash
# Start only specific tools
pm2 start ecosystem.config.cjs --only openapi
pm2 start ecosystem.config.cjs --only evolution-api
pm2 start ecosystem.config.cjs --only wait
```

### Start Tool Groups

```bash
# Start core tools only (ports 8001-8005)
pm2 start ecosystem.config.cjs --only "evolution-api,openapi,genie-tool,hive,wait"

# Start legacy tools (ports 8006-8007)
pm2 start ecosystem.config.cjs --only "omni,json-to-google-docs"

# Start experimental tools (ports 8008-8009)
pm2 start ecosystem.config.cjs --only "spark,gemini-assistant"
```

## Management Commands

### Process Control

```bash
# List all running processes
pm2 list

# Get detailed info about a tool
pm2 show openapi

# Restart a tool
pm2 restart openapi

# Restart all tools
pm2 restart all

# Stop a tool
pm2 stop openapi

# Stop all tools
pm2 stop all

# Delete a tool (removes from PM2)
pm2 delete openapi

# Delete all tools
pm2 delete all
```

### Monitoring

```bash
# Real-time monitoring (CPU, memory, logs)
pm2 monit

# View logs
pm2 logs                    # All tools
pm2 logs openapi           # Specific tool
pm2 logs --lines 100       # Last 100 lines
pm2 logs --err             # Only error logs

# Flush logs (clear all logs)
pm2 flush

# Reload logs (useful after log rotation)
pm2 reloadLogs
```

### Resource Management

```bash
# Check memory usage
pm2 list

# Reset restart counter
pm2 reset openapi

# Scale (run multiple instances - use with caution)
pm2 scale openapi 2  # NOT recommended for MCP tools
```

## Testing Deployment

### 1. Verify All Tools Started

```bash
pm2 list
# Should show all tools with status "online"
```

### 2. Test HTTP Endpoints

```bash
# Test each endpoint
curl http://localhost:8001/mcp  # evolution-api
curl http://localhost:8002/mcp  # openapi
curl http://localhost:8003/mcp  # genie-tool
curl http://localhost:8004/mcp  # hive
curl http://localhost:8005/mcp  # wait
curl http://localhost:8006/mcp  # omni
curl http://localhost:8007/mcp  # json-to-google-docs
curl http://localhost:8008/mcp  # spark
curl http://localhost:8009/mcp  # gemini-assistant
```

### 3. Check Logs

```bash
# Check for errors
pm2 logs --err --lines 50

# Check specific tool
pm2 logs openapi --lines 20
```

### 4. Monitor Resources

```bash
# Open monitoring dashboard
pm2 monit

# Check memory usage
pm2 list
```

## Integration with Claude Desktop

### 1. Update Claude Config

The `.mcp.json` file in this repository is configured for HTTP mode:

```bash
# Copy to Claude Desktop config directory

# macOS
cp .mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
cp .mcp.json ~/.config/Claude/claude_desktop_config.json

# Windows
cp .mcp.json %APPDATA%\Claude\claude_desktop_config.json
```

### 2. Restart Claude Desktop

After updating the config:
1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. All tools should appear in Claude's available tools

## Troubleshooting

### Tool Won't Start

```bash
# Check logs
pm2 logs openapi --err --lines 50

# Common issues:
# 1. Port already in use
lsof -i :8002
kill -9 <PID>

# 2. Missing environment variables
pm2 show openapi  # Check env section

# 3. Python module not found
uv sync  # Reinstall dependencies

# 4. Permission issues
chmod +x automagik_tools/tools/openapi/__main__.py
```

### High Memory Usage

```bash
# Check memory per tool
pm2 list

# Restart specific tool to free memory
pm2 restart openapi

# Adjust memory limit in ecosystem.config.cjs
# Change max_memory_restart: '500M' to lower value
```

### Logs Growing Too Large

```bash
# Install PM2 log rotation module
pm2 install pm2-logrotate

# Configure log rotation
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

### Tool Keeps Crashing

```bash
# Check crash logs
pm2 logs openapi --err --lines 100

# Check restart count
pm2 list  # Look at "restart" column

# View detailed error info
pm2 show openapi

# Common fixes:
# 1. Increase memory limit in ecosystem.config.cjs
# 2. Check environment variables are set correctly
# 3. Verify API endpoints are accessible
# 4. Check Python dependencies are installed
```

### Port Conflicts

```bash
# Check what's using a port
lsof -i :8002

# Change port in ecosystem.config.cjs if needed
# Update corresponding port in .mcp.json
```

## Production Best Practices

### 1. Enable Startup Script

```bash
# Generate startup script
pm2 startup

# This ensures PM2 starts on system boot
# Follow the instructions printed (may require sudo)

# After starting all tools, save config
pm2 save
```

### 2. Configure Log Rotation

```bash
# Install log rotation
pm2 install pm2-logrotate

# Configure
pm2 set pm2-logrotate:max_size 10M      # Rotate when log reaches 10MB
pm2 set pm2-logrotate:retain 7          # Keep 7 days of logs
pm2 set pm2-logrotate:compress true     # Compress old logs
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # Rotate daily at midnight
```

### 3. Set Up Monitoring

```bash
# PM2 Plus (optional, requires account)
pm2 plus

# Or use custom monitoring
pm2 monit  # Terminal-based
```

### 4. Regular Maintenance

```bash
# Weekly tasks
pm2 flush                  # Clear old logs
pm2 restart all           # Fresh restart
pm2 save                  # Save configuration

# Monthly tasks
uv sync                   # Update dependencies
pm2 update                # Update PM2
```

### 5. Backup Configuration

```bash
# Save PM2 ecosystem
cp ecosystem.config.cjs ecosystem.config.cjs.backup

# Save PM2 process list
pm2 save

# PM2 saves to ~/.pm2/dump.pm2
cp ~/.pm2/dump.pm2 ~/.pm2/dump.pm2.backup
```

## Advanced Usage

### Environment-Specific Configurations

```bash
# Development
pm2 start ecosystem.config.cjs --env development

# Production (default)
pm2 start ecosystem.config.cjs --env production

# Staging
pm2 start ecosystem.config.cjs --env staging
```

### Custom Deployment Scripts

Create `deploy.sh`:

```bash
#!/bin/bash
# Deploy automagik-tools with PM2

# Pull latest code
git pull origin main

# Update dependencies
uv sync

# Restart PM2 processes
pm2 restart all

# Check status
pm2 list

echo "Deployment complete!"
```

Make executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Health Checks

Create `health-check.sh`:

```bash
#!/bin/bash
# Health check for all tools

tools=(8001 8002 8003 8004 8005 8006 8007 8008 8009)

for port in "${tools[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/mcp)
  if [ "$status" -eq 200 ]; then
    echo "✓ Port $port: OK"
  else
    echo "✗ Port $port: FAILED (status: $status)"
  fi
done
```

Run periodically:
```bash
chmod +x health-check.sh
# Add to crontab for automated checks
crontab -e
# Add: */5 * * * * /path/to/health-check.sh >> /var/log/mcp-health.log
```

## Updating Tools

### Zero-Downtime Update

```bash
# Pull latest code
git pull origin main

# Update dependencies
uv sync

# Reload tools (graceful restart)
pm2 reload all

# Or reload one by one
pm2 reload openapi
pm2 reload evolution-api
# ... etc
```

### Full Restart Update

```bash
# Stop all
pm2 stop all

# Pull latest code
git pull origin main

# Update dependencies
uv sync

# Start all
pm2 start ecosystem.config.cjs

# Save configuration
pm2 save
```

## Uninstallation

```bash
# Stop and remove all tools
pm2 delete all

# Remove from startup
pm2 unstartup

# Remove PM2 (optional)
npm uninstall -g pm2

# Remove logs
rm -rf logs/
rm -rf ~/.pm2/logs/
```

## Resources

- **PM2 Documentation**: https://pm2.keymetrics.io/docs/
- **PM2 Plus (Monitoring)**: https://pm2.io/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **automagik-tools Repository**: https://github.com/namastexlabs/automagik-tools

## Support

For issues specific to:
- **PM2**: Check PM2 documentation or GitHub issues
- **automagik-tools**: Open an issue at https://github.com/namastexlabs/automagik-tools/issues
- **Individual tools**: Check tool-specific README files in `automagik_tools/tools/`

---

**Happy deploying! Leave a trail for fellow friends to follow.** 🚀
