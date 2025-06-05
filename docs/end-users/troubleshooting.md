# 🔧 Troubleshooting Guide

This guide helps you resolve common issues with AutoMagik Tools.

## Quick Diagnostics

Before diving into specific issues, run these diagnostic commands:

```bash
# Check if AutoMagik Tools is accessible
uvx automagik-tools list

# Check version
uvx automagik-tools version

# Test a specific tool
uvx automagik-tools serve --tool evolution-api --transport stdio
```

## Common Issues

### 🚫 Tools Not Showing Up in MCP Client

**Symptoms:**
- MCP client doesn't show AutoMagik tools
- No errors but tools aren't available

**Solutions:**

1. **Restart your MCP client completely**
   - Don't just reload - fully quit and restart
   - Some clients cache MCP server configurations

2. **Check configuration file location**
   ```bash
   # Claude Desktop (macOS)
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Claude Desktop (Windows)
   type %APPDATA%\Claude\claude_desktop_config.json
   ```

3. **Validate JSON syntax**
   ```bash
   # Online validator: https://jsonlint.com/
   # Or use jq
   jq . < your-config-file.json
   ```

4. **Common JSON errors:**
   - Trailing commas (remove comma after last item)
   - Missing quotes around strings
   - Mismatched brackets

### 🔌 Connection Errors

**Symptoms:**
- "Connection refused" errors
- "Failed to connect to MCP server"
- Timeout errors

**Solutions:**

1. **Check internet connection**
   ```bash
   # Test uvx connectivity
   uvx --version
   
   # Test if you can download packages
   uvx pip list
   ```

2. **Firewall/Proxy issues**
   - Allow `uvx` through firewall
   - Configure proxy if needed:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

3. **Check if port is already in use (for SSE/HTTP)**
   ```bash
   # Check port 8000
   lsof -i :8000  # macOS/Linux
   netstat -an | findstr :8000  # Windows
   ```

### 🔑 API Key Issues

**Symptoms:**
- "Unauthorized" or "401" errors
- "Invalid API key" messages
- Features not working despite connection

**Solutions:**

1. **Verify API key format**
   - Evolution API: Usually alphanumeric string
   - OpenAI: Starts with `sk-`
   - Remove extra spaces or quotes

2. **Test API keys directly**
   ```bash
   # Test Evolution API
   curl -H "apikey: YOUR_KEY" https://your-api.com/instance/fetchInstances
   
   # Test OpenAI
   curl -H "Authorization: Bearer sk-YOUR_KEY" https://api.openai.com/v1/models
   ```

3. **Check environment variables**
   ```bash
   # In your terminal
   echo $EVOLUTION_API_KEY
   echo $OPENAI_API_KEY
   ```

### 📦 Package Installation Issues

**Symptoms:**
- "Package not found" errors
- "Failed to install automagik-tools"
- Slow or hanging installation

**Solutions:**

1. **Update uvx**
   ```bash
   pip install --upgrade uvx
   # or
   pipx upgrade uvx
   ```

2. **Clear uvx cache**
   ```bash
   uvx cache clean
   ```

3. **Use specific version**
   ```bash
   uvx automagik-tools@latest list
   ```

4. **Check PyPI status**
   - Visit https://status.python.org/
   - Try alternative index: `--index-url https://pypi.org/simple`

### 🐛 Runtime Errors

**Symptoms:**
- Tools crash during use
- "Internal server error" messages
- Unexpected behavior

**Solutions:**

1. **Enable debug logging**
   ```json
   {
     "mcpServers": {
       "automagik-debug": {
         "command": "uvx",
         "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
         "env": {
           "DEBUG": "true",
           "LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

2. **Check tool-specific requirements**
   - Evolution API: Requires active Evolution instance
   - AutoMagik Agents: Requires valid OpenAI API key

3. **Report issues with logs**
   - Capture full error message
   - Include debug logs
   - Report on GitHub Issues

### ⚡ Performance Issues

**Symptoms:**
- Slow response times
- High CPU/memory usage
- Client freezing

**Solutions:**

1. **Use specific tools instead of serve-all**
   ```json
   // Instead of serve-all
   "args": ["automagik-tools", "serve", "--tool", "evolution-api"]
   ```

2. **Check API rate limits**
   - OpenAI: Check your usage at platform.openai.com
   - Evolution API: Check your instance limits

3. **Monitor resource usage**
   ```bash
   # While running AutoMagik
   top | grep python  # macOS/Linux
   taskmgr  # Windows
   ```

## Platform-Specific Issues

### macOS

**"Command not found: uvx"**
```bash
# Install via pip
pip install uvx

# Or via pipx (recommended)
pipx install uvx
```

**Permission denied errors**
```bash
# Fix permissions
chmod +x ~/.local/bin/uvx
```

### Windows

**"uvx is not recognized"**
1. Add Python Scripts to PATH:
   - Search "Environment Variables" in Start Menu
   - Add `%APPDATA%\Python\Python3X\Scripts` to PATH
   - Restart terminal

**SSL Certificate errors**
```bash
# Update certificates
pip install --upgrade certifi
```

### Linux

**Missing dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv

# Fedora/RHEL
sudo dnf install python3-pip python3-venv
```

## Debugging Steps

### 1. Isolate the Issue

Test each component separately:

```bash
# Test uvx
uvx --help

# Test AutoMagik Tools
uvx automagik-tools --help

# Test specific tool
uvx automagik-tools serve --tool evolution-api --transport stdio
```

### 2. Check Logs

Look for error messages in:
- MCP client logs (varies by client)
- Terminal/console output
- System logs

### 3. Minimal Configuration

Start with the simplest configuration:

```json
{
  "mcpServers": {
    "test": {
      "command": "uvx",
      "args": ["automagik-tools", "list"]
    }
  }
}
```

Then gradually add complexity.

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Try the minimal configuration
4. Collect error messages and logs

### Where to Get Help

1. **GitHub Issues**: For bugs and feature requests
   - Include: OS, MCP client, error messages
   - Provide minimal reproduction steps

2. **GitHub Discussions**: For questions and community help

3. **Documentation**: Check other guides in this directory

### Reporting Bugs

Include:
- Operating System and version
- MCP client and version
- AutoMagik Tools version (`uvx automagik-tools version`)
- Full error message
- Configuration (remove sensitive data)
- Steps to reproduce

## FAQ

**Q: Do I need to install Python?**
A: No! uvx handles everything automatically.

**Q: Can I use multiple versions of AutoMagik Tools?**
A: Yes, use `uvx automagik-tools@version` syntax.

**Q: How do I update AutoMagik Tools?**
A: It updates automatically with uvx. Force update with `uvx cache clean`.

**Q: Can I use AutoMagik Tools offline?**
A: After first use, yes. But you need internet for initial download and updates.

**Q: Is my API key secure?**
A: Yes, when properly configured in your MCP client. Never share your config files.

---

**Still having issues?** Open a GitHub issue with your diagnostic information and we'll help! 🤝