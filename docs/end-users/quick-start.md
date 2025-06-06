# 🚀 AutoMagik Tools Quick Start Guide

**Get up and running with MCP tools in under 2 minutes!**

## What is AutoMagik Tools?

AutoMagik Tools provides instant access to real-world integrations for your AI assistant through the Model Context Protocol (MCP). No installation, no setup - just copy, paste, and start using powerful tools.

## Prerequisites

- An MCP-compatible client (Claude Desktop, Cursor, Continue, etc.)
- Internet connection
- API keys for the tools you want to use (optional for some tools)

## 🎯 2-Minute Setup

### Step 1: Choose Your Tool

First, see what tools are available:

```bash
uvx automagik-tools list
```

Available tools include:
- `evolution-api` - WhatsApp messaging integration
- `automagik` - AI-powered automation agents
- **NEW**: Dynamic OpenAPI tools - Deploy any OpenAPI spec instantly!
- More tools added regularly!

### Step 2: Copy the Configuration

Choose your MCP client below and copy the configuration:

<details>
<summary><b>Claude Desktop</b></summary>

Add to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api.com",
        "EVOLUTION_API_KEY": "your-api-key"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

Add to your Cursor settings:

```json
{
  "mcp": {
    "servers": {
      "automagik": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"]
      }
    }
  }
}
```

</details>

<details>
<summary><b>Continue</b></summary>

Add to your Continue configuration:

```json
{
  "mcpServers": [
    {
      "name": "automagik",
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"]
    }
  ]
}
```

</details>

### Step 3: Add Your API Keys

Replace the placeholder values with your actual API keys:
- `EVOLUTION_API_BASE_URL`: Your Evolution API endpoint
- `EVOLUTION_API_KEY`: Your API key

Don't have API keys yet? Check the tool-specific guides in this directory.

### Step 4: Restart Your Client

Restart your MCP client to load the new configuration.

## ✅ Verify It's Working

After restarting, you should see the AutoMagik tools available in your client. Try asking:

- "List my available MCP tools"
- "Show me what AutoMagik tools can do"
- "Send a WhatsApp message using Evolution API"

## 🎉 That's It!

You're now ready to use AutoMagik Tools. No installation, no dependencies, no complex setup.

## Common Configurations

### Multiple Tools

Want to use multiple tools? Just add more server configurations:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api.com",
        "EVOLUTION_API_KEY": "your-api-key"
      }
    },
    "agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### All Tools at Once

Want access to all AutoMagik tools in one server?

```json
{
  "mcpServers": {
    "automagik-all": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api.com",
        "EVOLUTION_API_KEY": "your-api-key",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Dynamic OpenAPI Tools (NEW!)

Deploy any OpenAPI specification as an MCP tool instantly:

```json
{
  "mcpServers": {
    "my-api": {
      "command": "uvx",
      "args": [
        "automagik-tools", 
        "serve", 
        "--openapi-url", "https://api.example.com/openapi.json",
        "--api-key", "YOUR_API_KEY",
        "--transport", "stdio"
      ]
    }
  }
}
```

No code generation needed - just point to your OpenAPI spec and go!

## Troubleshooting

### Tools not showing up?
1. Make sure you restarted your MCP client
2. Check that the configuration file is in the correct location
3. Verify JSON syntax is correct (no trailing commas!)

### Connection errors?
1. Check your internet connection
2. Verify API keys are correct
3. Ensure API endpoints are accessible

### Need more help?
- See [troubleshooting.md](troubleshooting.md) for detailed solutions
- Check tool-specific guides in this directory
- Visit our GitHub issues page

## Next Steps

- 📖 Read tool-specific integration guides
- 🔧 Learn about [configuration options](configuration-examples.md)
- 🚀 Explore [advanced features](../developers/getting-started.md)
- 🐳 Deploy your own instance with [Docker](../deployment/README.md)

---

**Remember**: With `uvx`, you never need to install anything. AutoMagik Tools just works! 🎉