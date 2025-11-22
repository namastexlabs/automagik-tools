# OpenAPI - Universal API Bridge

**The universal bridge to plugin any OpenAPI spec - never develop another API integration again.**

This tool automatically converts any OpenAPI specification into MCP tools using FastMCP's native `from_openapi()` method.

## Philosophy

Instead of building individual MCP tools for every API, just point this tool at any OpenAPI spec and get instant MCP integration. One tool to rule them all.

## Features

- **Zero-code API integration** - Just provide an OpenAPI spec URL
- **Automatic tool generation** - All endpoints become MCP tools
- **Authentication support** - Bearer tokens and custom headers
- **Base URL override** - Point to different API environments
- **Custom instructions** - Add AI-specific guidance for tool usage
- **Type-safe parameters** - Automatic validation from OpenAPI schema

## Quick Start

### Basic Usage

```bash
# Set your OpenAPI spec URL
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json

# Serve the tool
automagik-tools serve openapi
```

### With Authentication

```bash
# Add API key
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json
export OPENAPI_API_KEY=your-secret-key

automagik-tools serve openapi
```

### Custom Configuration

```bash
# Full configuration
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json
export OPENAPI_API_KEY=your-api-key
export OPENAPI_BASE_URL=https://api.staging.example.com
export OPENAPI_NAME="My Custom API"
export OPENAPI_INSTRUCTIONS="This API provides access to..."

automagik-tools serve openapi
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAPI_OPENAPI_URL` | ✅ Yes | - | URL to your OpenAPI/Swagger specification |
| `OPENAPI_API_KEY` | No | - | API key for Bearer token authentication |
| `OPENAPI_BASE_URL` | No | - | Override the base URL from the spec |
| `OPENAPI_NAME` | No | "OpenAPI" | Custom name for the MCP server |
| `OPENAPI_INSTRUCTIONS` | No | - | Custom instructions for AI agents |

### Python Usage

```python
from automagik_tools.tools.openapi import create_server, OpenAPIConfig

# Create configuration
config = OpenAPIConfig(
    openapi_url="https://api.example.com/openapi.json",
    api_key="your-api-key",
    name="Example API",
    instructions="Use these tools to interact with Example API"
)

# Create and run server
server = create_server(config)
server.run()
```

## Real-World Examples

### Swagger Petstore (Public API)
```bash
export OPENAPI_OPENAPI_URL=https://petstore.swagger.io/v2/swagger.json
automagik-tools serve openapi
```

### Internal Company API
```bash
export OPENAPI_OPENAPI_URL=https://internal-api.company.com/openapi.json
export OPENAPI_API_KEY=$COMPANY_API_KEY
automagik-tools serve openapi
```

### Staging vs Production
```bash
# Point to production spec but use staging server
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json
export OPENAPI_BASE_URL=https://api.staging.example.com
export OPENAPI_API_KEY=$STAGING_API_KEY
automagik-tools serve openapi
```

## Use Cases

### 1. Rapid Prototyping
Test any API without writing integration code:
```bash
export OPENAPI_OPENAPI_URL=https://new-api.example.com/openapi.json
automagik-tools serve openapi
```

### 2. Multi-Environment Testing
Switch between environments with just a URL change:
```bash
# Development
export OPENAPI_BASE_URL=https://dev-api.example.com

# Staging
export OPENAPI_BASE_URL=https://staging-api.example.com

# Production
export OPENAPI_BASE_URL=https://api.example.com
```

### 3. Legacy API Integration
Integrate with any API that has an OpenAPI spec, no matter how old:
```bash
export OPENAPI_OPENAPI_URL=https://legacy-api.example.com/swagger.json
export OPENAPI_API_KEY=$LEGACY_API_KEY
automagik-tools serve openapi
```

### 4. Third-Party API Exploration
Explore and test third-party APIs:
```bash
export OPENAPI_OPENAPI_URL=https://api.third-party.com/openapi.json
export OPENAPI_API_KEY=$THIRD_PARTY_KEY
automagik-tools serve openapi
```

## How It Works

1. **Load OpenAPI Spec** - Fetches your API's OpenAPI/Swagger specification
2. **Parse Schema** - Analyzes endpoints, parameters, and response types
3. **Generate Tools** - Creates MCP tools for each API endpoint automatically
4. **Add Authentication** - Injects your API key and custom headers
5. **Serve Tools** - Makes all endpoints available as MCP tools

## Architecture

This tool uses FastMCP's built-in `from_openapi()` method, which means:

- ✅ **Zero manual code** - No httpx requests, no parameter parsing
- ✅ **Automatic validation** - Type checking from OpenAPI schema
- ✅ **Native error handling** - FastMCP handles all errors properly
- ✅ **Always up-to-date** - Uses FastMCP's latest OpenAPI parser
- ✅ **Minimal code** - ~70 lines vs 1800+ lines in old implementations

## Troubleshooting

### "OPENAPI_OPENAPI_URL must be set"
Make sure you've set the environment variable:
```bash
export OPENAPI_OPENAPI_URL=https://api.example.com/openapi.json
```

### Authentication Errors (401/403)
1. Verify your API key is correct: `echo $OPENAPI_API_KEY`
2. Check if the API uses Bearer token authentication
3. Try adding custom headers via code if Bearer token doesn't work

### Wrong Server/Base URL
1. Check the `servers` section in your OpenAPI spec
2. Override with `OPENAPI_BASE_URL` if needed:
```bash
export OPENAPI_BASE_URL=https://correct-server.example.com
```

### OpenAPI Spec Not Found (404)
1. Verify the URL is correct and accessible
2. Check if the spec requires authentication to download
3. Try downloading the spec manually to verify it exists

## Migration from Legacy Tools

If you were using the old `automagik` tool:

### Environment Variables
```bash
# Old
AUTOMAGIK_OPENAPI_URL → OPENAPI_OPENAPI_URL
AUTOMAGIK_API_KEY     → OPENAPI_API_KEY
AUTOMAGIK_BASE_URL    → OPENAPI_BASE_URL

# Removed (no longer needed)
AUTOMAGIK_ENABLE_MARKDOWN  # AI enhancement now handled by FastMCP
AUTOMAGIK_TIMEOUT          # Handled by FastMCP internally
```

### CLI Commands
```bash
# Old
automagik-tools serve automagik

# New
automagik-tools serve openapi
```

### Python Imports
```python
# Old
from automagik_tools.tools.automagik import create_server

# New
from automagik_tools.tools.openapi import create_server
```

## Contributing

This tool uses FastMCP's built-in OpenAPI support. To improve it:
1. Update configuration options in `config.py`
2. Enhance server creation logic in `__init__.py`
3. Add tests for new features
4. Update this README

## License

MIT

---

**The last API integration tool you'll ever need.**
