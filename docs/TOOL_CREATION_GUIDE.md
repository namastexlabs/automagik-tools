# Tool Creation Guide for automagik-tools

This guide will help you create new MCP tools for the automagik-tools repository.

## Quick Start: Creating Your First Tool

### 1. Tool Structure

Create a new directory under `automagik_tools/tools/your_tool_name/`:

```
automagik_tools/tools/your_tool_name/
├── __init__.py      # Main tool implementation
├── config.py        # Configuration class (optional)
├── models.py        # Pydantic models (optional)
└── utils.py         # Helper functions (optional)
```

### 2. Basic Tool Template

Here's a minimal tool implementation (`__init__.py`):

```python
"""Your Tool Name - Brief description"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastmcp import FastMCP

# Request/Response models
class YourRequest(BaseModel):
    param1: str = Field(description="Description of param1")
    param2: Optional[int] = Field(default=None, description="Optional param")

def create_tool(config: Any) -> FastMCP:
    """Create the MCP tool instance"""
    mcp = FastMCP("Your Tool Name")
    
    # Define a tool
    @mcp.tool()
    async def your_action(
        param1: str,
        param2: Optional[int] = None
    ) -> str:
        """Brief description of what this tool does"""
        # Your implementation here
        return f"Result: {param1}"
    
    # Define a resource (optional)
    @mcp.resource("your-tool://status")
    async def get_status() -> str:
        """Get current tool status"""
        return "Tool is operational"
    
    # Define a prompt (optional)
    @mcp.prompt()
    async def setup_guide() -> str:
        """Guide for setting up this tool"""
        return """To use this tool:
        1. Configure your API key
        2. Set the base URL
        3. Start using the tool"""
    
    return mcp
```

### 3. Configuration Pattern

Add configuration support in `cli.py`:

```python
class YourToolConfig(BaseSettings):
    """Configuration for Your Tool"""
    api_key: str = Field(default="", alias="your_tool_api_key")
    base_url: str = Field(default="https://api.example.com", alias="your_tool_base_url")
    timeout: int = Field(default=30, alias="your_tool_timeout")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
```

Update `create_config_for_tool()` in `cli.py`:

```python
def create_config_for_tool(tool_name: str) -> Any:
    if tool_name == 'your-tool':
        return YourToolConfig()
    # ... other tools
```

### 4. Register Your Tool

Add to `pyproject.toml`:

```toml
[project.entry-points."automagik_tools.plugins"]
your-tool = "automagik_tools.tools.your_tool:create_tool"
```

### 5. Add Tests

Create `tests/tools/test_your_tool.py`:

```python
import pytest
from automagik_tools.tools.your_tool import create_tool

@pytest.mark.asyncio
async def test_your_action():
    # Mock configuration
    config = type('Config', (), {'api_key': 'test-key', 'base_url': 'https://test.com'})
    
    # Create tool
    mcp = create_tool(config)
    
    # Test your tool's functionality
    # Use the test patterns from existing tests
```

## Common Patterns

### REST API Integration

```python
import httpx

async def make_api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    config: Any = None
) -> Dict[str, Any]:
    """Make authenticated API request"""
    headers = {"Authorization": f"Bearer {config.api_key}"}
    
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        response = await client.request(
            method=method,
            url=f"{config.base_url}/{endpoint}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
```

### Error Handling

```python
@mcp.tool()
async def safe_operation(param: str) -> str:
    """Operation with proper error handling"""
    try:
        result = await risky_operation(param)
        return result
    except httpx.HTTPStatusError as e:
        raise ValueError(f"API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise ValueError(f"Operation failed: {str(e)}")
```

### Using Context for Logging

```python
from fastmcp import Context

@mcp.tool()
async def operation_with_logging(
    param: str,
    ctx: Optional[Context] = None
) -> str:
    """Operation that logs progress"""
    if ctx:
        await ctx.info(f"Starting operation with param: {param}")
    
    try:
        result = await do_work(param)
        if ctx:
            await ctx.info(f"Operation completed successfully")
        return result
    except Exception as e:
        if ctx:
            await ctx.error(f"Operation failed: {str(e)}")
        raise
```

## Tool Categories & Examples

### 1. Communication Tools
- WhatsApp (Evolution API) ✅
- Discord
- Slack
- Telegram
- Email (SMTP/IMAP)

### 2. Productivity Tools
- Notion
- Google Workspace
- Microsoft 365
- Todoist
- Trello

### 3. Development Tools
- GitHub/GitLab
- Jira
- Docker
- Kubernetes
- CI/CD (Jenkins, CircleCI)

### 4. AI/ML Tools
- OpenAI
- Anthropic
- Hugging Face
- Replicate
- Stability AI

### 5. Data Tools
- PostgreSQL/MySQL
- Redis
- Elasticsearch
- MongoDB
- S3/Cloud Storage

### 6. Monitoring Tools
- Datadog
- New Relic
- Prometheus
- Grafana
- Sentry

### 7. Finance Tools
- Stripe
- PayPal
- Cryptocurrency APIs
- Banking APIs
- Invoice/Accounting

### 8. IoT/Smart Home
- Home Assistant
- Philips Hue
- Nest
- Arduino/Raspberry Pi
- MQTT Brokers

## Best Practices

### 1. Configuration
- Use environment variables with clear prefixes (TOOLNAME_)
- Provide sensible defaults
- Validate configuration on tool creation
- Document all configuration options

### 2. Error Handling
- Always catch and wrap external API errors
- Provide clear error messages
- Use MCP's error response format
- Log errors with context when available

### 3. Documentation
- Write clear docstrings for all tools
- Include parameter descriptions
- Provide usage examples in prompts
- Document rate limits and restrictions

### 4. Testing
- Mock external API calls
- Test error scenarios
- Verify MCP protocol compliance
- Test with various parameter combinations

### 5. Security
- Never log sensitive data (API keys, passwords)
- Validate all inputs
- Use HTTPS for all external calls
- Implement rate limiting where needed

## Contributing Your Tool

1. Fork the repository
2. Create a feature branch: `git checkout -b add-toolname-tool`
3. Implement your tool following this guide
4. Add comprehensive tests
5. Update README.md with your tool's description
6. Add configuration to .env.example
7. Submit a pull request

## Getting Help

- Check existing tools for examples
- Review the FastMCP documentation
- Open an issue for questions
- Join our Discord community (coming soon)

Remember: The goal is to make MCP tools accessible and easy to use. Focus on clean APIs, good documentation, and reliable operation.