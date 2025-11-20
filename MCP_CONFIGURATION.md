# MCP Configuration Guide

This guide explains how to configure automagik-tools for use with MCP clients like Claude Desktop, Cline, or other MCP-compatible applications.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .mcp.json.example ~/.mcp.json
   # Or for Claude Desktop on Mac:
   cp .mcp.json.example ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Edit the configuration:**
   - Replace placeholder values like `your_api_key_here` with your actual API keys
   - Update paths (credentials directories, database files, etc.)
   - Disable tools you don't need by setting `"disabled": true`

3. **Restart your MCP client** (e.g., Claude Desktop)

## Available Tools

### 🌍 Google Workspace Suite
Complete integration with Google services. All tools require OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

- **google-gmail** - Email search, read, send, draft management
- **google-drive** - File management and sharing
- **google-calendar** - Event and calendar management
- **google-docs** - Document creation and editing
- **google-sheets** - Spreadsheet management
- **google-slides** - Presentation management
- **google-forms** - Survey and form management
- **google-tasks** - Task list management
- **google-chat** - Google Chat messaging
- **google-search** - Google Workspace search

**Google Workspace Setup:**
1. Create OAuth 2.0 credentials in Google Cloud Console
2. Enable required APIs (Gmail API, Drive API, etc.)
3. Set up OAuth consent screen
4. Configure redirect URIs for each tool (e.g., `http://localhost:8001/oauth2callback` for Gmail)

### 💬 Messaging & Communication
WhatsApp, Discord, and Slack integrations through various platforms.

- **genie-omni** - Agent-first WhatsApp via Omni Hub (recommended)
  - Context isolation for safety (`OMNI_MASTER_PHONE` / `OMNI_MASTER_GROUP`)
  - Agent-owned or act-on-behalf modes
  - Media download support

- **omni** - Multi-tenant omnichannel messaging (WhatsApp, Slack, Discord)
  - Administrative perspective
  - Full platform management

- **evolution-api** - WhatsApp automation via Evolution API v2
  - Instance management
  - Message sending and receiving
  - Optional fixed recipient for security

### 🤖 AI & Agent Orchestration
Tools for AI agents, workflows, and orchestration.

- **genie** - Generic MCP tool orchestrator with persistent memory
  - Orchestrates other MCP servers
  - Session management with memory
  - Requires OpenAI API key
  - Configure child MCP servers via `GENIE_MCP_CONFIGS`

- **gemini-assistant** - Advanced Google Gemini consultations
  - Session management
  - File attachments support
  - Multiple model support (gemini-2.0-flash-exp, etc.)

- **automagik** - AI-powered agents and workflows
  - Markdown enhancement
  - OpenAPI integration
  - Workflow orchestration

- **spark** - AutoMagik Spark workflow orchestration
  - AI agent management
  - Workflow execution

### 🛠️ Utility Tools
Helper tools for various tasks.

- **wait** - Smart timing functions for agent workflows
  - Progress reporting
  - Configurable intervals

- **automagik-hive** - Testing tool for Automagik Hive API
  - API capability testing
  - Integration validation

- **json-to-google-docs** - Convert JSON to Google Docs
  - Template-based document generation
  - Placeholder substitution
  - Markdown support
  - Service account authentication

## Configuration Examples

### Minimal Configuration (Local Development)
```json
{
  "mcpServers": {
    "wait": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "wait"],
      "env": {}
    }
  }
}
```

### WhatsApp with Context Isolation (Recommended)
```json
{
  "mcpServers": {
    "genie-omni": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "tool",
        "genie-omni",
        "--transport",
        "stdio"
      ],
      "env": {
        "OMNI_API_KEY": "your_key",
        "OMNI_BASE_URL": "http://localhost:8882",
        "OMNI_DEFAULT_INSTANCE": "genie",
        "OMNI_MASTER_PHONE": "5511999999999"
      }
    }
  }
}
```

### Google Workspace (Gmail + Drive)
```json
{
  "mcpServers": {
    "google-gmail": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "tool",
        "google-gmail",
        "--transport",
        "stdio"
      ],
      "env": {
        "GOOGLE_GMAIL_CLIENT_ID": "123-xyz.apps.googleusercontent.com",
        "GOOGLE_GMAIL_CLIENT_SECRET": "GOCSPX-abc123",
        "GOOGLE_GMAIL_CREDENTIALS_DIR": "/path/to/.credentials",
        "GOOGLE_GMAIL_USER_EMAIL": "you@example.com",
        "GOOGLE_GMAIL_PORT": "8001"
      }
    },
    "google-drive": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "tool",
        "google-drive",
        "--transport",
        "stdio"
      ],
      "env": {
        "GOOGLE_DRIVE_CLIENT_ID": "123-xyz.apps.googleusercontent.com",
        "GOOGLE_DRIVE_CLIENT_SECRET": "GOCSPX-abc123",
        "GOOGLE_DRIVE_CREDENTIALS_DIR": "/path/to/.credentials",
        "GOOGLE_DRIVE_USER_EMAIL": "you@example.com",
        "GOOGLE_DRIVE_PORT": "8002"
      }
    }
  }
}
```

## Security Best Practices

### 1. Context Isolation for Messaging Tools
Always set `OMNI_MASTER_PHONE` or `OMNI_MASTER_GROUP` for genie-omni to prevent unrestricted access:

```json
"env": {
  "OMNI_MASTER_PHONE": "5511999999999"
}
```

**⚠️ WARNING:** Without context isolation, the agent can send messages to ANYONE in your WhatsApp contacts.

### 2. API Key Management
- Never commit `.mcp.json` with real API keys to version control
- Use environment variables or secret management tools
- Rotate API keys regularly
- Use separate keys for development and production

### 3. OAuth Credentials
- Store credentials in secure, user-specific directories
- Use separate OAuth apps for different environments
- Configure appropriate OAuth scopes (minimum required permissions)
- Regularly review authorized applications

### 4. Network Security
- Use HTTPS for production deployments
- Configure appropriate CORS settings
- Use reverse proxies for OAuth callbacks in production
- Set `WORKSPACE_EXTERNAL_URL` for public-facing deployments

## Transport Modes

Automagik-tools supports multiple MCP transport modes:

- **stdio** (default) - Standard input/output, best for Claude Desktop
- **sse** - Server-Sent Events, for web-based clients
- **http** - HTTP REST API

Specify transport in the command:
```json
"args": ["automagik-tools@latest", "tool", "genie-omni", "--transport", "stdio"]
```

## Troubleshooting

### Tools Not Appearing
1. Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log` (Mac)
2. Verify API keys are correct
3. Ensure tool is not disabled: `"disabled": false`
4. Check network connectivity to APIs

### OAuth Issues
1. Verify redirect URIs match exactly in Google Cloud Console
2. Check credentials directory permissions
3. Delete old tokens and re-authenticate
4. Ensure all required APIs are enabled

### Performance Issues
1. Disable unused tools
2. Increase timeout values for slow networks
3. Use local caching where available
4. Check `GENIE_MCP_CLEANUP_TIMEOUT` for Genie orchestration

### Connection Errors
1. Verify base URLs are accessible
2. Check firewall settings
3. Ensure services are running (Omni, Spark, etc.)
4. Review timeout settings

## Advanced Configuration

### Using Development Version
For development, use local installation instead of `uvx`:
```json
{
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "/path/to/automagik-tools",
    "automagik-tools",
    "tool",
    "genie-omni"
  ]
}
```

### Multiple Instances
Run multiple instances of the same tool with different configs:
```json
{
  "mcpServers": {
    "omni-personal": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "genie-omni"],
      "env": {
        "OMNI_API_KEY": "personal_key",
        "OMNI_DEFAULT_INSTANCE": "personal"
      }
    },
    "omni-work": {
      "command": "uvx",
      "args": ["automagik-tools@latest", "tool", "genie-omni"],
      "env": {
        "OMNI_API_KEY": "work_key",
        "OMNI_DEFAULT_INSTANCE": "work"
      }
    }
  }
}
```

### Genie with Child MCP Servers
Configure Genie to orchestrate other MCP servers:
```json
{
  "env": {
    "OPENAI_API_KEY": "your_key",
    "GENIE_MCP_CONFIGS": "{\"filesystem\": {\"command\": \"npx\", \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\", \"/tmp\"]}, \"github\": {\"command\": \"npx\", \"args\": [\"-y\", \"@modelcontextprotocol/server-github\"]}}"
  }
}
```

## Environment Variables Reference

See `.env.example` in the repository for a complete list of all available environment variables for each tool.

## Getting Help

- **Documentation**: [https://github.com/namastexlabs/automagik-tools](https://github.com/namastexlabs/automagik-tools)
- **Issues**: [https://github.com/namastexlabs/automagik-tools/issues](https://github.com/namastexlabs/automagik-tools/issues)
- **Tool List**: Run `uvx automagik-tools list` to see all available tools
- **Tool Help**: Run `uvx automagik-tools tool <tool-name> --help`

## Contributing

Found an issue or want to add a new tool? See [CLAUDE.md](./CLAUDE.md) for development workflows and contribution guidelines.
