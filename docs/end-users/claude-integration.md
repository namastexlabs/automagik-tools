# 🤖 Claude Desktop Integration Guide

This guide shows you how to integrate AutoMagik Tools with Claude Desktop for enhanced AI capabilities.

## Prerequisites

- Claude Desktop app installed
- macOS or Windows
- API keys for the tools you want to use

## Configuration File Location

First, locate your Claude Desktop configuration file:

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Note**: You may need to create this file if it doesn't exist yet.

## Basic Configuration

### Single Tool Setup

Here's how to add a single AutoMagik tool to Claude Desktop:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-evolution-api.com",
        "EVOLUTION_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Multiple Tools Setup

Want to use multiple tools? Add each as a separate server:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-evolution-api.com",
        "EVOLUTION_API_KEY": "your-api-key"
      }
    },
    "ai-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key"
      }
    }
  }
}
```

### All Tools in One

For access to all AutoMagik tools through a single server:

```json
{
  "mcpServers": {
    "automagik-all": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-evolution-api.com",
        "EVOLUTION_API_KEY": "your-api-key",
        "OPENAI_API_KEY": "sk-your-openai-key"
      }
    }
  }
}
```

## Tool-Specific Configurations

### Evolution API (WhatsApp)

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-evolution-instance.com",
        "EVOLUTION_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Required Environment Variables:**
- `EVOLUTION_API_BASE_URL`: Your Evolution API server URL
- `EVOLUTION_API_KEY`: Your API authentication key

**What you can do:**
- Send WhatsApp messages
- Create groups
- Manage contacts
- Send media files
- Check message status

### AutoMagik Agents

```json
{
  "mcpServers": {
    "agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-api-key",
        "AGENT_MODEL": "gpt-4-turbo-preview"
      }
    }
  }
}
```

**Required Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key

**Optional Environment Variables:**
- `AGENT_MODEL`: AI model to use (default: gpt-4-turbo-preview)
- `AGENT_MAX_TOKENS`: Maximum tokens per request

**What you can do:**
- Create autonomous AI agents
- Execute complex multi-step tasks
- Process and analyze data
- Generate content

## Step-by-Step Setup

### 1. Open Configuration File

**macOS (Terminal):**
```bash
mkdir -p ~/Library/Application\ Support/Claude
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows (PowerShell):**
```powershell
mkdir -Force "$env:APPDATA\Claude"
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

### 2. Add Your Configuration

Copy one of the configurations above and paste it into the file. Make sure to:
- Replace placeholder API keys with your actual keys
- Use proper JSON syntax (watch for trailing commas!)
- Save the file

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

### 4. Verify Integration

In Claude Desktop, try these commands:
- "What MCP tools do I have available?"
- "Show me the Evolution API tools"
- "List my AutoMagik capabilities"

## Advanced Configurations

### Custom Ports for SSE/HTTP

If you need web-based access alongside Claude Desktop:

```json
{
  "mcpServers": {
    "automagik-stdio": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api.com",
        "EVOLUTION_API_KEY": "your-key"
      }
    }
  }
}
```

Then separately run for web access:
```bash
uvx automagik-tools serve-all --transport sse --port 8000
```

### Development Mode

For tool developers who want to test local changes:

```json
{
  "mcpServers": {
    "automagik-dev": {
      "command": "python",
      "args": ["-m", "automagik_tools", "serve-all", "--transport", "stdio"],
      "cwd": "/path/to/your/automagik-tools",
      "env": {
        "PYTHONPATH": "/path/to/your/automagik-tools",
        "EVOLUTION_API_BASE_URL": "https://your-api.com",
        "EVOLUTION_API_KEY": "your-key"
      }
    }
  }
}
```

## Troubleshooting

### Tools Not Appearing

1. **Check JSON Syntax**: Use a JSON validator to ensure your config is valid
2. **Verify File Location**: Make sure the config file is in the correct directory
3. **Check Logs**: Look for errors in Claude Desktop's developer console

### Connection Errors

1. **Test with uvx directly**:
   ```bash
   uvx automagik-tools list
   ```
   
2. **Verify API Keys**: Ensure all required environment variables are set
3. **Check Network**: Ensure your firewall allows uvx to download packages

### Performance Issues

1. **Use specific tools** instead of `serve-all` when you only need one
2. **Check API rate limits** for your external services
3. **Monitor memory usage** if running many tools

## Best Practices

1. **Security**: Never commit your config file to version control
2. **Backup**: Keep a backup of your working configuration
3. **Updates**: AutoMagik Tools updates automatically with uvx
4. **Organization**: Use descriptive names for multiple tool instances

## Getting Help

- 📖 See [troubleshooting.md](troubleshooting.md) for common issues
- 💬 Check our GitHub Discussions
- 🐛 Report bugs on GitHub Issues
- 📧 Contact support (if available)

## Next Steps

- Explore tool-specific features in their documentation
- Learn about [advanced configurations](configuration-examples.md)
- Set up [Cursor integration](cursor-integration.md) for coding
- Deploy your own instance with [Docker](../deployment/README.md)

---

**Pro Tip**: Save your configuration file before making changes so you can always restore a working setup! 💾