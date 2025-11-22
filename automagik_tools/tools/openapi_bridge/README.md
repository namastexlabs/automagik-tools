# OpenAPI Bridge MCP Tool

Universal OpenAPI to MCP converter - turn any OpenAPI specification into MCP tools automatically.

This tool replaces the legacy `automagik` tool with a modern implementation using FastMCP's native `from_openapi()` method.

## Features

- **Zero-code API integration** - Just provide an OpenAPI spec URL
- **Automatic tool generation** - All endpoints become MCP tools
- **Authentication support** - Bearer tokens and custom headers
- **Base URL override** - Point to different API environments
- **Custom instructions** - Add AI-specific guidance for tool usage
- **Type-safe parameters** - Automatic validation from OpenAPI schema

## Configuration

### Required Environment Variables

```bash
# OpenAPI specification URL (REQUIRED)
OPENAPI_BRIDGE_OPENAPI_URL=https://api.example.com/openapi.json

# Optional configurations
OPENAPI_BRIDGE_API_KEY=your-api-key-here
OPENAPI_BRIDGE_BASE_URL=https://api.staging.example.com
OPENAPI_BRIDGE_NAME="My Custom API"
OPENAPI_BRIDGE_INSTRUCTIONS="This API provides..."
```

### Configuration Options

- `OPENAPI_BRIDGE_OPENAPI_URL` **(required)** - URL to your OpenAPI/Swagger specification
- `OPENAPI_BRIDGE_API_KEY` (optional) - API key for Bearer token authentication
- `OPENAPI_BRIDGE_BASE_URL` (optional) - Override the base URL from the OpenAPI spec
- `OPENAPI_BRIDGE_NAME` (optional) - Custom name for the MCP server (default: "OpenAPI Bridge")
- `OPENAPI_BRIDGE_INSTRUCTIONS` (optional) - Custom instructions for AI agents using this tool

## Usage

### With automagik-tools CLI

```bash
# Serve the tool with your OpenAPI spec
export OPENAPI_BRIDGE_OPENAPI_URL=https://api.example.com/openapi.json
automagik-tools serve openapi_bridge

# With authentication
export OPENAPI_BRIDGE_API_KEY=your-secret-key
automagik-tools serve openapi_bridge
```

### In Python Code

```python
from automagik_tools.tools.openapi_bridge import create_server, OpenAPIBridgeConfig

# Create configuration
config = OpenAPIBridgeConfig(
    openapi_url="https://api.example.com/openapi.json",
    api_key="your-api-key",
    name="Example API Tools",
    instructions="Use these tools to interact with Example API"
)

# Create and run server
server = create_server(config)
# Server is now ready to handle MCP requests
```

### Standalone Execution

```bash
# STDIO transport (for MCP clients)
python -m automagik_tools.tools.openapi_bridge --transport stdio

# SSE transport (for web clients)
python -m automagik_tools.tools.openapi_bridge --transport sse --port 8000
```

## How It Works

1. **Load OpenAPI Spec** - Fetches your API's OpenAPI/Swagger specification
2. **Parse Schema** - Analyzes endpoints, parameters, and response types
3. **Generate Tools** - Creates MCP tools for each API endpoint automatically
4. **Add Authentication** - Injects your API key and custom headers
5. **Serve Tools** - Makes all endpoints available as MCP tools

## Example Use Cases

### Internal APIs
```bash
# Convert your company's internal API
export OPENAPI_BRIDGE_OPENAPI_URL=https://internal-api.company.com/openapi.json
export OPENAPI_BRIDGE_API_KEY=$COMPANY_API_KEY
automagik-tools serve openapi_bridge
```

### Public APIs
```bash
# Use with any public API that has OpenAPI spec
export OPENAPI_BRIDGE_OPENAPI_URL=https://petstore.swagger.io/v2/swagger.json
automagik-tools serve openapi_bridge
```

### Staging vs Production
```bash
# Point to staging environment
export OPENAPI_BRIDGE_OPENAPI_URL=https://api.example.com/openapi.json
export OPENAPI_BRIDGE_BASE_URL=https://api.staging.example.com
automagik-tools serve openapi_bridge
```

## Comparison with Legacy Automagik Tool

### Old Automagik (deprecated)
- Manual httpx request building
- 1800+ lines of code
- Custom parameter handling
- Manual error formatting

### New OpenAPI Bridge
- Uses FastMCP.from_openapi()
- ~70 lines of code
- Automatic parameter validation
- Native FastMCP error handling
- Better type safety
- Easier to maintain

## Troubleshooting

### "OPENAPI_BRIDGE_OPENAPI_URL must be set"
Make sure you've set the environment variable pointing to your OpenAPI spec:
```bash
export OPENAPI_BRIDGE_OPENAPI_URL=https://api.example.com/openapi.json
```

### Authentication Issues
If you're getting 401/403 errors:
1. Verify your API key is correct
2. Check if the API uses Bearer token authentication
3. Try adding custom headers via `extra_headers` if needed

### Base URL Issues
If requests are going to the wrong server:
1. Check the `servers` section in your OpenAPI spec
2. Override with `OPENAPI_BRIDGE_BASE_URL` if needed

## Development

### Running Tests

```bash
pytest tests/tools/test_openapi_bridge.py -v
```

### Testing with Real APIs

```bash
# Test with Swagger Petstore (public API)
export OPENAPI_BRIDGE_OPENAPI_URL=https://petstore.swagger.io/v2/swagger.json
uv run automagik-tools serve openapi_bridge
```

## Contributing

This tool uses FastMCP's built-in OpenAPI support. To improve it:
1. Update configuration options in `config.py`
2. Enhance server creation logic in `__init__.py`
3. Add tests for new features
4. Update this README

## Migration from Automagik

If you were using the old `automagik` tool:

1. **Rename environment variables**:
   - `AUTOMAGIK_OPENAPI_URL` → `OPENAPI_BRIDGE_OPENAPI_URL`
   - `AUTOMAGIK_API_KEY` → `OPENAPI_BRIDGE_API_KEY`
   - `AUTOMAGIK_BASE_URL` → `OPENAPI_BRIDGE_BASE_URL`

2. **Update CLI commands**:
   - `automagik-tools serve automagik` → `automagik-tools serve openapi_bridge`

3. **Update Python imports**:
   ```python
   # Old
   from automagik_tools.tools.automagik import create_server

   # New
   from automagik_tools.tools.openapi_bridge import create_server
   ```

4. **Configuration changes**:
   - Remove `AUTOMAGIK_ENABLE_MARKDOWN` (no longer needed)
   - Remove `AUTOMAGIK_TIMEOUT` (handled by FastMCP)
   - Add `OPENAPI_BRIDGE_INSTRUCTIONS` if you want custom AI guidance

## License

MIT
