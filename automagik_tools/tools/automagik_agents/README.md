# Automagik Agents MCP Tool

Automagik agents templates and API

This tool uses FastMCP's native OpenAPI support to automatically generate MCP components from an OpenAPI specification.

## Features

- **Automatic API Discovery**: Fetches and parses OpenAPI specification
- **Dynamic Component Generation**: Converts API endpoints to appropriate MCP components
- **Full Authentication Support**: Handles API key and Bearer token authentication
- **Type-Safe Operations**: Validates requests and responses according to OpenAPI schema
- **Intelligent Route Mapping**: 
  - GET endpoints with parameters → MCP Resources
  - GET endpoints with path parameters → MCP Resource Templates
  - POST/PUT/DELETE endpoints → MCP Tools

## Configuration

### Required Environment Variables

```bash
# API authentication key
AUTOMAGIK_AGENTS_API_KEY=your-api-key-here

# Base URL for the API
AUTOMAGIK_AGENTS_BASE_URL=http://192.168.112.148:8881

# URL to fetch OpenAPI specification (optional)
AUTOMAGIK_AGENTS_OPENAPI_URL=http://192.168.112.148:8881/api/v1/openapi.json

# Request timeout in seconds (optional, defaults to 30)
AUTOMAGIK_AGENTS_TIMEOUT=30
```

## Usage

### With automagik-tools CLI

```bash
# List available tools
automagik-tools list

# Serve this specific tool
automagik-tools serve automagik-agents

# Serve all tools
automagik-tools serve-all
```

### In Python Code

```python
from automagik_tools.tools.automagik_agents import create_server

# Create and run server
server = create_server()
# Server is now ready to handle MCP requests
```

## How It Works

1. **Fetches OpenAPI Spec**: On startup, the tool fetches the OpenAPI specification from the configured URL
2. **Analyzes Endpoints**: FastMCP analyzes all API endpoints and their parameters
3. **Generates MCP Components**: Each endpoint is converted to the appropriate MCP component type
4. **Handles Requests**: When MCP clients call tools/resources, requests are proxied to the actual API

## Customization

You can customize how endpoints are mapped to MCP components by editing the `route_maps` in the tool implementation:

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

## Development

### Running Tests

```bash
pytest tests/tools/test_automagik_agents.py -v
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @anthropic/mcp-inspector

# Run the tool
automagik-tools serve automagik-agents

# In another terminal, connect with inspector
mcp-inspector stdio automagik-tools serve automagik-agents
```

## Troubleshooting

### OpenAPI Fetch Issues

If the tool can't fetch the OpenAPI specification:
1. Check that the OPENAPI_URL is accessible
2. Verify any required authentication headers
3. The tool will fall back to a minimal spec if fetch fails

### Authentication Issues

1. Verify your API key is correctly set
2. Check if the API uses a different header name for authentication
3. Some APIs may require additional headers - customize the client creation

### Component Generation

- By default, GET endpoints become resources and other methods become tools
- Use route_maps to customize this behavior
- Check the FastMCP logs to see how endpoints were mapped

## API Reference

This tool dynamically generates MCP components based on the OpenAPI specification. The available tools and resources depend on the API endpoints discovered.

To see all available components, use the MCP Inspector or check the API's OpenAPI documentation.
