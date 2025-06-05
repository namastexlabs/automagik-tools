# {TOOL_NAME} Tool

{TOOL_DESCRIPTION}

## Features

- **Feature 1**: Description of what this feature does
- **Feature 2**: Another feature description
- **Feature 3**: And another one

## Configuration

Add the following to your `.env` file:

```env
# Required
{TOOL_NAME_UPPER}_API_KEY=your-api-key-here

# Optional (with defaults)
{TOOL_NAME_UPPER}_BASE_URL=https://api.example.com
{TOOL_NAME_UPPER}_TIMEOUT=30
```

### Getting an API Key

1. Sign up at [Service Website](https://example.com)
2. Navigate to API Keys section
3. Generate a new API key
4. Copy the key to your `.env` file

## Usage

### Available Tools

#### `your_main_action`
Main functionality of the tool.

**Parameters:**
- `required_param` (str, required): Description of this parameter
- `optional_param` (str, optional): Description of optional parameter

**Example:**
```python
await your_main_action("test", "optional_value")
```

#### `your_secondary_action`
Additional functionality.

**Parameters:**
- `param1` (str, required): First parameter
- `param2` (int, optional, default=10): Second parameter

**Example:**
```python
await your_secondary_action("hello", 42)
```

### Available Resources

- `{TOOL_NAME_LOWER}://status` - Get current tool status
- `{TOOL_NAME_LOWER}://config` - Get tool configuration (non-sensitive)

### Available Prompts

- `setup_guide` - Step-by-step setup instructions
- `usage_examples` - Common usage patterns and examples

## Examples

### Basic Usage
```python
# Initialize the tool
from automagik_tools.cli import main

# Use the tool via CLI
automagik-tools serve {TOOL_NAME_LOWER}
```

### Integration Example
```python
# In your MCP client
result = await client.call_tool(
    "your_main_action",
    arguments={
        "required_param": "test data",
        "optional_param": "extra info"
    }
)
```

## Development

### Running Tests
```bash
# Run all tests for this tool
pytest tests/tools/test_{TOOL_NAME_LOWER}.py -v

# Run with coverage
pytest tests/tools/test_{TOOL_NAME_LOWER}.py --cov=automagik_tools.tools.{TOOL_NAME_LOWER}
```

### Adding New Features

1. Add new tool methods in `__init__.py`
2. Update tests in `test_{TOOL_NAME_LOWER}.py`
3. Update this README with new functionality
4. Add any new configuration to `.env.example`

## Troubleshooting

### Common Issues

**API Key Not Working**
- Ensure the key is correctly set in `.env`
- Check that the key has the required permissions
- Verify the API endpoint is accessible

**Timeout Errors**
- Increase `{TOOL_NAME_UPPER}_TIMEOUT` in `.env`
- Check your network connection
- Verify the API service is operational

**Rate Limiting**
- The tool respects API rate limits
- Implement exponential backoff for retries
- Consider caching frequently accessed data

## API Reference

This tool integrates with [Service Name API](https://docs.example.com/api).

Key endpoints used:
- `POST /api/v1/action` - Main action endpoint
- `GET /api/v1/status` - Status check
- Additional endpoints as needed

## Contributing

Contributions are welcome! Please:
1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request

## License

This tool is part of automagik-tools and follows the same MIT license.