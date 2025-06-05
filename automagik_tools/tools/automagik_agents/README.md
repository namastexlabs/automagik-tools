# mcp-automagik-agents: An Automagik Agents MCP Server

<div align="center">

![Namastex Logo](https://namastex.com/logo.png)

**Powered by Namastex Labs**

</div>

## Overview

A Model Context Protocol server for Automagik Agents API interaction and automation. This server provides seamless integration with Automagik Agents through dynamic OpenAPI-based tool generation, enabling Large Language Models to interact with agent workflows, templates, and automation systems.

The server uses FastMCP's native OpenAPI support to automatically discover and generate MCP components from the Automagik Agents API specification, providing type-safe operations and intelligent route mapping.

### Tools

All tools are dynamically generated from the Automagik Agents OpenAPI specification, providing direct access to all available API endpoints as MCP tools and resources.

### Features

- **Automatic API Discovery**: Fetches and parses OpenAPI specification
- **Dynamic Component Generation**: Converts API endpoints to appropriate MCP components
- **Full Authentication Support**: Handles API key and Bearer token authentication
- **Type-Safe Operations**: Validates requests and responses according to OpenAPI schema
- **Intelligent Route Mapping**: 
  - GET endpoints with parameters → MCP Resources
  - GET endpoints with path parameters → MCP Resource Templates
  - POST/PUT/DELETE endpoints → MCP Tools

## Installation

### Using uvx (recommended)

The easiest way to use automagik-tools is with [uvx](https://docs.astral.sh/uv/guides/tools/), which runs the tool in an isolated environment without affecting your system Python:

```bash
# Run directly without installation
uvx automagik-tools serve --tool automagik-agents

# List available tools
uvx automagik-tools list
```

### Alternative: Development Installation

For development, clone the repository and use uv:

```bash
git clone https://github.com/namastexlabs/automagik-tools.git
cd automagik-tools
uv sync --all-extras

# Run with uv
uv run automagik-tools serve --tool automagik-agents
```

## Configuration

### Environment Variables

Configure your environment variables using a `.env` file. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Add the following configuration to your `.env` file:

```env
# API authentication key (required)
AUTOMAGIK_AGENTS_API_KEY=your-api-key-here

# Base URL for the API (required)
AUTOMAGIK_AGENTS_BASE_URL=http://localhost:8881

# URL to fetch OpenAPI specification (optional)
AUTOMAGIK_AGENTS_OPENAPI_URL=http://localhost:8881/api/v1/openapi.json

# Request timeout in milliseconds (optional, defaults to 300)
AUTOMAGIK_AGENTS_TIMEOUT=300
```

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

<details>
<summary>Using uvx (recommended)</summary>

```json
{
  "mcpServers": {
    "automagik-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "namastex888",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "300"
      }
    }
  }
}
```
</details>

<details>
<summary>Using development installation</summary>

```json
{
  "mcpServers": {
    "automagik-agents": {
      "command": "uv",
      "args": ["--directory", "/path/to/automagik-tools", "run", "automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your-api-key-here",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "300"
      }
    }
  }
}
```
</details>

### Usage with Cursor

For Cursor integration, add the following to your Cursor settings or project configuration:

<details>
<summary>Using uvx (recommended)</summary>

```json
{
  "mcp": {
    "servers": {
      "automagik-agents": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
        "env": {
          "AUTOMAGIK_AGENTS_API_KEY": "your-api-key-here",
          "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
          "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
          "AUTOMAGIK_AGENTS_TIMEOUT": "300"
        }
      }
    }
  }
}
```
</details>

You can also create a `.vscode/mcp.json` file in your workspace to share the configuration:

```json
{
  "servers": {
    "automagik-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your-api-key-here",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "300"
      }
    }
  }
}
```

### Usage with VS Code

Add the following JSON block to your User Settings (JSON) file in VS Code:

```json
{
  "mcp": {
    "servers": {
      "automagik-agents": {
        "command": "uvx",
        "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
        "env": {
          "AUTOMAGIK_AGENTS_API_KEY": "your-api-key-here",
          "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
          "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
          "AUTOMAGIK_AGENTS_TIMEOUT": "300"
        }
      }
    }
  }
}
```

## Debugging

You can use the MCP inspector to debug the server:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Debug using uvx
npx @modelcontextprotocol/inspector uvx automagik-tools serve --tool automagik-agents
```

For detailed logging, check the MCP logs:

```bash
# On macOS
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log

# On Linux
tail -n 20 -f ~/.local/share/Claude/logs/mcp*.log
```

## Development

### Running Tests

```bash
# Run tests for the automagik-agents tool
pytest tests/tools/test_automagik_agents.py -v
```

### Local Development

For local development and testing:

1. **Using MCP Inspector**:
   ```bash
   cd /path/to/automagik-tools
   npx @modelcontextprotocol/inspector uv run automagik-tools serve --tool automagik-agents
   ```

2. **Using Claude Desktop** - Add to your `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "automagik-agents-dev": {
         "command": "uv",
         "args": [
           "--directory", "/path/to/automagik-tools",
           "run", "automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"
         ],
         "env": {
           "AUTOMAGIK_AGENTS_API_KEY": "your-api-key-here",
           "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
           "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json",
           "AUTOMAGIK_AGENTS_TIMEOUT": "300"
         }
       }
     }
   }
   ```

### Customization

You can customize how endpoints are mapped to MCP components by editing the route configuration:

```python
from fastmcp.server.openapi import RouteMap, MCPType

route_maps=[
    # Make all analytics endpoints tools
    RouteMap(methods=["GET"], pattern=r"^/analytics/.*", mcp_type=MCPType.TOOL),
    
    # Exclude admin endpoints
    RouteMap(pattern=r"^/admin/.*", mcp_type=MCPType.EXCLUDE),
    
    # Exclude internal endpoints
    RouteMap(tags={"internal"}, mcp_type=MCPType.EXCLUDE),
]
```

## Troubleshooting

### OpenAPI Fetch Issues

If the server can't fetch the OpenAPI specification:
1. Verify that `AUTOMAGIK_AGENTS_OPENAPI_URL` is accessible
2. Check network connectivity to the Automagik Agents API
3. Ensure proper authentication headers are configured
4. The server will fall back to a minimal spec if fetch fails

### Authentication Issues

1. Verify your `AUTOMAGIK_AGENTS_API_KEY` is correctly set
2. Check that the API key has proper permissions
3. Ensure the `AUTOMAGIK_AGENTS_BASE_URL` is correct
4. Test API connectivity with curl or similar tools

### Component Generation

- GET endpoints become resources, other methods become tools by default
- Use route_maps to customize endpoint-to-component mapping
- Check the server logs to see how endpoints were discovered and mapped
- Use the MCP inspector to verify available tools and resources

## API Reference

This server dynamically generates MCP components from the Automagik Agents OpenAPI specification. All API endpoints are automatically converted to corresponding MCP tools and resources.

To explore available components:
- Use the MCP Inspector: `npx @modelcontextprotocol/inspector uvx automagik-tools serve --tool automagik-agents`
- Check the OpenAPI documentation at `{BASE_URL}/api/v1/openapi.json`

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License.

---

<div align="center">

**Built with ❤️ by [Namastex Labs](https://namastex.com)**

*Empowering AI automation through intelligent agent orchestration*

</div>
