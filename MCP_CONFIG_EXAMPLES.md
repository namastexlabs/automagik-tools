# MCP Configuration Examples

This file shows all the different ways to configure automagik-tools in your `.cursor/mcp.json` or Claude Desktop config.

## 1. Hub Configuration (All Tools)

Serves all available tools in one server. Best for exploring all capabilities.

```json
{
  "mcpServers": {
    "automagik-hub": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "hub"],
      "env": {
        "AUTOMAGIK_API_KEY": "your-api-key",
        "AUTOMAGIK_BASE_URL": "http://localhost:28881",
        "OPENAI_API_KEY": "sk-your-openai-key",
        "GENIE_MODEL": "gpt-4.1"
      }
    }
  }
}
```

## 2. Individual Tool Configurations

### AutoMagik Tool (API Agent)

For working with your AutoMagik Agents instance:

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "automagik"],
      "env": {
        "AUTOMAGIK_API_KEY": "your-api-key",
        "AUTOMAGIK_BASE_URL": "http://localhost:28881",
        "AUTOMAGIK_TIMEOUT": "1000",
        "AUTOMAGIK_ENABLE_MARKDOWN": "true"
      }
    }
  }
}
```

### Genie Tool (MCP Orchestrator)

For orchestrating multiple MCP servers with memory:

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "genie"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key",
        "GENIE_MODEL": "gpt-4.1",
        "GENIE_MEMORY_DB": "/path/to/genie_memory.db",
        "GENIE_SESSION_ID": "my-session",
        "GENIE_MCP_CONFIGS": "{\"filesystem\": {\"command\": \"npx\", \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\", \"/path/to/dir\"]}}"
      }
    }
  }
}
```

### Genie with AutoMagik (Automatic Integration)

Genie automatically detects AutoMagik when you provide the environment variables:

```json
{
  "mcpServers": {
    "genie-with-automagik": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "genie"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key",
        "GENIE_MODEL": "gpt-4.1",
        "AUTOMAGIK_API_KEY": "your-api-key",
        "AUTOMAGIK_BASE_URL": "http://localhost:28881",
        "AUTOMAGIK_TIMEOUT": "600"
      }
    }
  }
}
```

This configuration:
- Automatically creates an SSE connection to AutoMagik at `http://localhost:28881/sse`
- No need to specify MCP_CONFIGS - Genie detects AutoMagik automatically
- Genie can orchestrate AutoMagik alongside other tools

## 3. OpenAPI Configurations

### Discord API

```json
{
  "mcpServers": {
    "discord": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "openapi",
        "https://raw.githubusercontent.com/discord/discord-api-spec/refs/heads/main/specs/openapi.json"
      ],
      "env": {
        "DISCORD_TOKEN": "Bot YOUR_DISCORD_BOT_TOKEN"
      }
    }
  }
}
```

### Custom API with Authentication

```json
{
  "mcpServers": {
    "my-api": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "openapi",
        "https://api.mycompany.com/v1/openapi.json"
      ],
      "env": {
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 4. Local Development Configurations

### Using local installation instead of uvx

```json
{
  "mcpServers": {
    "automagik-dev": {
      "command": "uv",
      "args": ["run", "automagik-tools", "hub"],
      "cwd": "/path/to/automagik-tools",
      "env": {
        "AUTOMAGIK_API_KEY": "test-key",
        "AUTOMAGIK_BASE_URL": "http://localhost:28881"
      }
    }
  }
}
```

## 5. Multiple Tools Configuration

You can run multiple tools simultaneously:

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "automagik"],
      "env": {
        "AUTOMAGIK_API_KEY": "your-key",
        "AUTOMAGIK_BASE_URL": "http://localhost:28881"
      }
    },
    "discord": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "openapi",
        "https://raw.githubusercontent.com/discord/discord-api-spec/refs/heads/main/specs/openapi.json"
      ],
      "env": {
        "DISCORD_TOKEN": "Bot YOUR_TOKEN"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    }
  }
}
```

## Environment Variables Reference

### AutoMagik Tool
- `AUTOMAGIK_API_KEY`: API key for authentication
- `AUTOMAGIK_BASE_URL`: Base URL of your AutoMagik instance
- `AUTOMAGIK_TIMEOUT`: Request timeout in seconds
- `AUTOMAGIK_ENABLE_MARKDOWN`: Enable AI-powered response formatting (true/false)

### Genie Tool
- `OPENAI_API_KEY`: OpenAI API key for Genie's intelligence
- `GENIE_MODEL`: Model to use (gpt-4.1-nano, gpt-4.1, etc.)
- `GENIE_MEMORY_DB`: Path to persistent memory database
- `GENIE_SESSION_ID`: Session identifier for memory isolation
- `GENIE_MCP_CONFIGS`: JSON string of MCP servers to orchestrate

**Note**: When you provide `AUTOMAGIK_API_KEY` and `AUTOMAGIK_BASE_URL`, Genie automatically configures an SSE connection to AutoMagik without needing to specify it in `GENIE_MCP_CONFIGS`.

### OpenAPI Tools
- `API_KEY`: Generic API key (sent as X-API-Key and Bearer token)
- Tool-specific tokens (e.g., `DISCORD_TOKEN`, `GITHUB_TOKEN`)

## Tips

1. **Use Hub for Discovery**: Start with the hub to explore all tools, then switch to individual tools for production.

2. **Persistent Memory**: For Genie, use an absolute path for `GENIE_MEMORY_DB` to keep memories between sessions.

3. **API Keys**: Store sensitive keys in environment variables or use a secrets manager.

4. **Custom OpenAPI**: Any OpenAPI 3.0+ spec works - just provide the URL.

5. **Development**: Use `uv run` with `cwd` for local development instead of `uvx`.