# 📝 Configuration Examples

This document provides ready-to-use configuration examples for various scenarios and MCP clients.

## Table of Contents

- [Basic Configurations](#basic-configurations)
- [Multi-Tool Setups](#multi-tool-setups)
- [Environment-Specific Configs](#environment-specific-configs)
- [Advanced Configurations](#advanced-configurations)
- [Security Best Practices](#security-best-practices)

## Basic Configurations

### Minimal Setup (Single Tool)

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "your-key-here"
      }
    }
  }
}
```

### All Tools (Simple)

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"]
    }
  }
}
```

## Multi-Tool Setups

### Development Environment

Perfect for developers working with multiple services:

```json
{
  "mcpServers": {
    "whatsapp-prod": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://prod-api.example.com",
        "EVOLUTION_API_KEY": "prod-key-xxx"
      }
    },
    "whatsapp-dev": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "http://localhost:8080",
        "EVOLUTION_API_KEY": "dev-key-xxx"
      }
    },
    "ai-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-xxx",
        "AGENT_MODEL": "gpt-4-turbo-preview",
        "AGENT_MAX_TOKENS": "4000"
      }
    }
  }
}
```

### Team Setup with Shared Server

One SSE server for web access, one stdio for local:

```json
{
  "mcpServers": {
    "automagik-local": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "${TEAM_API_URL}",
        "EVOLUTION_API_KEY": "${TEAM_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

Then run separately for team access:
```bash
uvx automagik-tools serve-all --transport sse --port 8000 --host 0.0.0.0
```

## Environment-Specific Configs

### Using System Environment Variables

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "${EVOLUTION_API_BASE_URL}",
        "EVOLUTION_API_KEY": "${EVOLUTION_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

Set variables in your shell:
```bash
export EVOLUTION_API_BASE_URL="https://api.example.com"
export EVOLUTION_API_KEY="your-key"
export OPENAI_API_KEY="sk-xxx"
```

### Per-Project Configuration

For Cursor/VS Code - create `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "project-tools": {
        "command": "uvx",
        "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
        "env": {
          "EVOLUTION_API_BASE_URL": "${workspaceFolder}/.env.EVOLUTION_API_BASE_URL",
          "EVOLUTION_API_KEY": "${workspaceFolder}/.env.EVOLUTION_API_KEY"
        }
      }
    }
  }
}
```

### Docker-Based Development

```json
{
  "mcpServers": {
    "automagik-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", ".env",
        "automagik-tools:latest",
        "serve-all", "--transport", "stdio"
      ]
    }
  }
}
```

## Advanced Configurations

### Custom Tool Development

For developing your own tools:

```json
{
  "mcpServers": {
    "my-tool-dev": {
      "command": "python",
      "args": ["-m", "automagik_tools", "serve", "--tool", "my-tool", "--transport", "stdio"],
      "cwd": "/path/to/automagik-tools",
      "env": {
        "PYTHONPATH": "/path/to/automagik-tools",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### High-Performance Setup

Optimized for performance:

```json
{
  "mcpServers": {
    "whatsapp-fast": {
      "command": "uvx",
      "args": [
        "automagik-tools", 
        "serve", 
        "--tool", "evolution-api",
        "--transport", "stdio"
      ],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "your-key",
        "CONNECTION_TIMEOUT": "30",
        "MAX_RETRIES": "3",
        "CACHE_TTL": "300"
      }
    }
  }
}
```

### Multi-Region Setup

For global applications:

```json
{
  "mcpServers": {
    "whatsapp-us": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://us-api.example.com",
        "EVOLUTION_API_KEY": "us-key"
      }
    },
    "whatsapp-eu": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://eu-api.example.com",
        "EVOLUTION_API_KEY": "eu-key"
      }
    },
    "whatsapp-asia": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://asia-api.example.com",
        "EVOLUTION_API_KEY": "asia-key"
      }
    }
  }
}
```

### Debugging Configuration

With maximum logging:

```json
{
  "mcpServers": {
    "automagik-debug": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "detailed",
        "TRACE_REQUESTS": "true",
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "your-key"
      }
    }
  }
}
```

## Security Best Practices

### Using External Secret Management

```json
{
  "mcpServers": {
    "automagik-secure": {
      "command": "sh",
      "args": [
        "-c",
        "EVOLUTION_API_KEY=$(cat ~/.secrets/evolution.key) OPENAI_API_KEY=$(cat ~/.secrets/openai.key) uvx automagik-tools serve-all --transport stdio"
      ]
    }
  }
}
```

### Read-Only Configuration

For shared environments:

```json
{
  "mcpServers": {
    "automagik-readonly": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "readonly-key-with-limited-permissions",
        "READ_ONLY_MODE": "true"
      }
    }
  }
}
```

### Credential Rotation

Using environment variable indirection:

```json
{
  "mcpServers": {
    "automagik-rotating": {
      "command": "sh",
      "args": [
        "-c",
        "source ~/.automagik/current-env && uvx automagik-tools serve-all --transport stdio"
      ]
    }
  }
}
```

## Transport-Specific Examples

### SSE for Web Clients

```json
{
  "webServer": {
    "command": "uvx",
    "args": [
      "automagik-tools", 
      "serve-all", 
      "--transport", "sse",
      "--host", "0.0.0.0",
      "--port", "8000"
    ],
    "env": {
      "CORS_ORIGINS": "https://app.example.com,http://localhost:3000",
      "EVOLUTION_API_BASE_URL": "https://api.example.com",
      "EVOLUTION_API_KEY": "your-key"
    }
  }
}
```

### HTTP API Mode

```json
{
  "apiServer": {
    "command": "uvx",
    "args": [
      "automagik-tools", 
      "serve-all", 
      "--transport", "http",
      "--host", "0.0.0.0",
      "--port", "8080"
    ],
    "env": {
      "API_KEY": "internal-api-key",
      "RATE_LIMIT": "100",
      "EVOLUTION_API_BASE_URL": "https://api.example.com",
      "EVOLUTION_API_KEY": "your-key"
    }
  }
}
```

## Client-Specific Examples

### Claude Desktop (Full Featured)

```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "your-key",
        "OPENAI_API_KEY": "sk-xxx",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Cursor (Project Specific)

```json
{
  "mcp": {
    "servers": {
      "backend-tools": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
        "cwd": "${workspaceFolder}",
        "env": {
          "EVOLUTION_API_BASE_URL": "${config:project.apiUrl}",
          "EVOLUTION_API_KEY": "${config:project.apiKey}"
        }
      }
    }
  }
}
```

### Continue (Minimal)

```json
{
  "mcpServers": [
    {
      "name": "automagik",
      "command": "uvx",
      "args": ["automagik-tools", "serve-all", "--transport", "stdio"]
    }
  ]
}
```

## Tips and Tricks

### 1. Version Pinning

```json
{
  "mcpServers": {
    "automagik-stable": {
      "command": "uvx",
      "args": ["automagik-tools@0.5.0", "serve-all", "--transport", "stdio"]
    }
  }
}
```

### 2. Conditional Loading

```json
{
  "mcpServers": {
    "automagik": {
      "command": "sh",
      "args": [
        "-c",
        "if [ -f ~/.automagik-enabled ]; then uvx automagik-tools serve-all --transport stdio; else echo 'AutoMagik disabled'; fi"
      ]
    }
  }
}
```

### 3. Custom Aliases

```json
{
  "mcpServers": {
    "wa": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://api.example.com",
        "EVOLUTION_API_KEY": "your-key"
      }
    },
    "ai": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-xxx"
      }
    }
  }
}
```

---

**Remember**: Always test your configuration with a simple command first, then add complexity. And never commit sensitive API keys to version control! 🔐