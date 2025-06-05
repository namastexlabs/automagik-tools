# 💻 Cursor Integration Guide

This guide shows you how to integrate AutoMagik Tools with Cursor for AI-powered coding with real-world tool access.

## Prerequisites

- Cursor editor installed
- API keys for the tools you want to use

## Configuration

### Basic Setup

Add AutoMagik Tools to your Cursor configuration:

1. Open Cursor Settings (`Cmd+,` on macOS, `Ctrl+,` on Windows/Linux)
2. Search for "MCP" in settings
3. Add the following configuration:

```json
{
  "mcp": {
    "servers": {
      "automagik": {
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
}
```

### Alternative: Settings.json

You can also edit your Cursor settings.json directly:

**Location:**
- macOS: `~/Library/Application Support/Cursor/User/settings.json`
- Windows: `%APPDATA%\Cursor\User\settings.json`
- Linux: `~/.config/Cursor/User/settings.json`

## Tool Configurations

### WhatsApp Integration (Evolution API)

Perfect for building chat applications or automation:

```json
{
  "mcp": {
    "servers": {
      "whatsapp-dev": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "https://your-evolution-api.com",
          "EVOLUTION_API_KEY": "your-api-key"
        }
      }
    }
  }
}
```

**Use Cases in Cursor:**
- Build WhatsApp bots
- Test messaging workflows
- Debug API integrations
- Generate message templates

### AI Agents Integration

For advanced AI-powered development assistance:

```json
{
  "mcp": {
    "servers": {
      "ai-agents": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
        "env": {
          "OPENAI_API_KEY": "sk-your-openai-key",
          "AGENT_MODEL": "gpt-4-turbo-preview"
        }
      }
    }
  }
}
```

**Use Cases in Cursor:**
- Generate complex code structures
- Automate repetitive tasks
- Analyze and refactor code
- Create test cases

### Multiple Tools Setup

For comprehensive development capabilities:

```json
{
  "mcp": {
    "servers": {
      "automagik-all": {
        "command": "uvx",
        "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "https://your-api.com",
          "EVOLUTION_API_KEY": "your-key",
          "OPENAI_API_KEY": "sk-..."
        }
      },
      "automagik-web": {
        "command": "uvx",
        "args": ["automagik-tools", "serve-all", "--transport", "sse", "--port", "8000"]
      }
    }
  }
}
```

## Project-Specific Configuration

### Workspace Settings

For project-specific tools, create `.vscode/settings.json` in your project:

```json
{
  "mcp": {
    "servers": {
      "project-tools": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "${env:PROJECT_API_URL}",
          "EVOLUTION_API_KEY": "${env:PROJECT_API_KEY}"
        }
      }
    }
  }
}
```

### Environment Variables

Use a `.env` file in your project root:

```bash
# .env
PROJECT_API_URL=https://staging-api.example.com
PROJECT_API_KEY=test-key-12345
```

## Developer Workflows

### 1. API Testing Workflow

```json
{
  "mcp": {
    "servers": {
      "api-test": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "http://localhost:8080",
          "EVOLUTION_API_KEY": "dev-key"
        }
      }
    }
  }
}
```

Now in Cursor, you can:
- Test API endpoints directly
- Generate API client code
- Debug webhook responses
- Validate message formats

### 2. Automation Development

When building automation tools:

```typescript
// Ask Cursor + AutoMagik: "Create a function to send a WhatsApp message with media"

async function sendWhatsAppMedia(to: string, mediaUrl: string, caption: string) {
  // AutoMagik will help generate and test this code with real API calls
}
```

### 3. Integration Testing

Test your integrations without leaving Cursor:

```python
# Ask: "Test sending a message to my test WhatsApp number"
# AutoMagik will execute the actual API call and show results
```

## Advanced Features

### Custom Tool Development

When developing your own MCP tools:

```json
{
  "mcp": {
    "servers": {
      "my-tool-dev": {
        "command": "python",
        "args": ["-m", "automagik_tools", "serve", "--tool", "my-custom-tool"],
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONPATH": "${workspaceFolder}",
          "DEBUG": "true"
        }
      }
    }
  }
}
```

### Debugging MCP Tools

Enable debug logging:

```json
{
  "mcp": {
    "servers": {
      "automagik-debug": {
        "command": "uvx",
        "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
        "env": {
          "DEBUG": "true",
          "LOG_LEVEL": "DEBUG"
        }
      }
    }
  }
}
```

## Best Practices

### 1. Security

- Never commit API keys to your repository
- Use environment variables for sensitive data
- Create separate configs for dev/staging/prod

### 2. Performance

- Use specific tools instead of `serve-all` when possible
- Enable only the tools you need for each project
- Consider running SSE server for shared team access

### 3. Team Collaboration

Share tool configurations with your team:

```json
// .vscode/settings.json (commit this)
{
  "mcp": {
    "servers": {
      "team-tools": {
        "command": "uvx",
        "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "${env:TEAM_API_URL}",
          "EVOLUTION_API_KEY": "${env:TEAM_API_KEY}"
        }
      }
    }
  }
}
```

```bash
# .env.example (commit this)
TEAM_API_URL=https://api.example.com
TEAM_API_KEY=your-key-here
```

## Troubleshooting

### Tools Not Available

1. Restart Cursor after configuration changes
2. Check the Output panel for MCP server logs
3. Verify JSON syntax in settings

### Connection Issues

```bash
# Test AutoMagik Tools directly
uvx automagik-tools list

# Check if uvx is working
uvx --version
```

### Performance Problems

1. Reduce the number of active MCP servers
2. Use project-specific configurations
3. Check API rate limits

## Common Commands

Ask Cursor to help with these tasks:

- "List all available MCP tools"
- "Show me Evolution API capabilities"
- "Send a test WhatsApp message"
- "Create an AI agent for code review"
- "Generate API documentation from MCP tools"

## Integration Examples

### Building a WhatsApp Bot

```python
# Ask Cursor: "Create a WhatsApp bot that responds to commands"
# AutoMagik will provide real API access for testing
```

### API Client Generation

```typescript
// Ask: "Generate a TypeScript client for Evolution API"
// AutoMagik will introspect the actual API and generate types
```

### Automated Testing

```python
# Ask: "Create integration tests for my WhatsApp service"
# AutoMagik enables real API calls during test development
```

## Next Steps

- Explore [tool-specific documentation](./tools/)
- Learn about [custom tool development](../developers/creating-tools.md)
- Set up [team deployment](../deployment/README.md)
- Join our developer community

---

**Pro Tip**: Use Cursor's AI with AutoMagik Tools to build and test integrations in real-time. No more switching between editor and API testing tools! 🚀