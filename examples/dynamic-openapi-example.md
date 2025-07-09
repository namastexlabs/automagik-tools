# Dynamic OpenAPI Tool Example

This example demonstrates how to use automagik-tools to run any OpenAPI-based API as an MCP tool without pre-generating files.

## 1. Direct Command Line Usage

```bash
# Basic usage with an OpenAPI spec URL
uvx automagik-tools serve --openapi-url https://petstore3.swagger.io/api/v3/openapi.json

# With authentication
uvx automagik-tools serve --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_...

# With custom base URL (if different from OpenAPI spec)
uvx automagik-tools openapi --openapi-url https://example.com/openapi.json --base-url https://api.example.com --api-key your-key

# For stdio transport (Claude Desktop, Cursor, etc.)
uvx automagik-tools openapi --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_... --transport stdio
```

## 2. MCP Client Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stripe-api": {
      "command": "uvx",
      "args": [
        "automagik-tools", 
        "serve", 
        "--openapi-url", "https://api.stripe.com/v1/openapi.json",
        "--api-key", "sk_test_...",
        "--transport", "stdio"
      ]
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "github-api": {
      "command": "uvx",
      "args": [
        "automagik-tools", 
        "serve", 
        "--openapi-url", "https://api.github.com/openapi.json",
        "--api-key", "ghp_...",
        "--transport", "stdio"
      ]
    }
  }
}
```

## 3. Examples with Popular APIs

### Stripe API
```bash
uvx automagik-tools serve --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_...
```

### OpenAI API
```bash
uvx automagik-tools serve --openapi-url https://api.openai.com/openapi.json --api-key sk-...
```

### Twilio API
```bash
uvx automagik-tools serve --openapi-url https://www.twilio.com/openapi.json --api-key your-twilio-key
```

### Pet Store (Testing)
```bash
uvx automagik-tools serve --openapi-url https://petstore3.swagger.io/api/v3/openapi.json
```

## 4. Features

- **Zero Configuration**: No need to pre-generate tool files
- **Authentication Support**: Automatically configures API key headers
- **Base URL Override**: Can specify a different base URL than in the OpenAPI spec
- **All Transports**: Supports stdio, SSE, and HTTP transports
- **FastMCP Native**: Uses FastMCP's built-in OpenAPI support

## 5. How It Works

1. Fetches the OpenAPI specification from the provided URL
2. Extracts API title, description, and server information
3. Creates an HTTP client with authentication headers if API key is provided
4. Uses FastMCP's `from_openapi()` to create an MCP server dynamically
5. Runs the server with the specified transport

This feature makes it incredibly easy to expose any OpenAPI-based API to AI agents without any code generation or file creation.