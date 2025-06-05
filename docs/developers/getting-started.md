# 🚀 Developer Getting Started Guide

Welcome to AutoMagik Tools development! This guide will help you set up your development environment and start creating MCP tools.

## Prerequisites

- Python 3.11 or higher
- Git
- Make (optional but recommended)
- Docker (for deployment testing)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Arakiss/automagik-tools.git
cd automagik-tools
```

### 2. Set Up Development Environment

```bash
# Using make (recommended)
make install

# Or manually with uv
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then sync dependencies
uv sync --all-extras
```

### 3. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Verify Installation

```bash
# List available tools
make list

# Run tests
make test

# Start development server
make dev-server
```

## Project Structure

```
automagik-tools/
├── automagik_tools/          # Main package
│   ├── cli.py               # CLI entry point
│   ├── hub.py               # Multi-tool server
│   └── tools/               # Tool implementations (self-contained)
│       ├── evolution_api/   # WhatsApp integration
│       │   ├── __init__.py  # Tool server implementation
│       │   ├── config.py    # Configuration
│       │   └── __main__.py  # FastMCP CLI compatibility
│       ├── automagik_agents/# AI agents
│       └── your_tool/       # Your new tool here!
├── scripts/                  # Utility scripts
│   ├── create_tool.py       # Tool generator
│   └── validate_tool.py     # Tool validator
├── tests/                    # Test suite
├── docs/                     # Documentation
├── deploy/                   # Deployment configs
└── Makefile                 # Development commands
```

## Development Workflow

### 1. Create a New Tool

```bash
# Interactive tool creation
make new-tool

# Or from OpenAPI spec
make tool URL=https://api.example.com/openapi.json

# NEW: Dynamic OpenAPI deployment (no generation needed)
uvx automagik-tools serve --openapi-url https://api.example.com/openapi.json --api-key YOUR_KEY
```

### 2. Implement Your Tool

Tools follow the FastMCP pattern:

```python
# automagik_tools/tools/my_tool/__init__.py
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("my-tool")

@mcp.tool()
async def my_function(param: str) -> str:
    """Tool description for the AI."""
    return f"Processed: {param}"

# Export for discovery
__all__ = ["mcp"]
```

### 3. Register Your Tool

Add to `pyproject.toml`:

```toml
[project.entry-points."automagik_tools.plugins"]
my-tool = "automagik_tools.tools.my_tool:mcp"
```

### 4. Test Your Tool

```bash
# Run unit tests
uv run pytest tests/tools/test_my-tool.py -v

# Validate MCP compliance
make validate-tool TOOL=my-tool

# Test manually
make serve TOOL=my-tool
```

### 5. Hot-Reload Development

```bash
# Start dev server with auto-reload
make dev-server

# In another terminal, make changes and see them reflected
```

## Key Concepts

### FastMCP Framework

AutoMagik Tools is built on [FastMCP](https://github.com/jlowin/fastmcp), which provides:

- Automatic tool discovery
- Type validation
- Error handling
- Multiple transport support

### Tool Structure

Each tool should:

1. **Be self-contained**: All code in `tools/your_tool/`
2. **Use environment variables**: For configuration
3. **Be async-first**: Use `async`/`await`
4. **Handle errors gracefully**: Return proper MCP errors
5. **Include tests**: In `tests/tools/test_your_tool.py`

### Example Tool Implementation

```python
# automagik_tools/tools/weather/__init__.py
import os
import httpx
from fastmcp import FastMCP
from typing import Optional

mcp = FastMCP("weather")

# Configuration from environment
API_KEY = os.getenv("WEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"

@mcp.tool()
async def get_weather(city: str, country_code: Optional[str] = None) -> dict:
    """Get current weather for a city.
    
    Args:
        city: City name
        country_code: Optional two-letter country code (e.g., 'US')
    
    Returns:
        Current weather data including temperature, conditions, and humidity
    """
    if not API_KEY:
        raise ValueError("WEATHER_API_KEY environment variable not set")
    
    location = f"{city},{country_code}" if country_code else city
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/weather",
            params={"q": location, "appid": API_KEY, "units": "metric"}
        )
        response.raise_for_status()
        
    data = response.json()
    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "conditions": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"]
    }

@mcp.tool()
async def get_forecast(city: str, days: int = 5) -> list:
    """Get weather forecast for a city.
    
    Args:
        city: City name
        days: Number of days (1-5)
    
    Returns:
        Weather forecast data
    """
    # Implementation here...
    pass
```

## Testing

### Unit Tests

```python
# tests/tools/test_weather.py
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from automagik_tools.tools.weather import mcp

@pytest.mark.asyncio
async def test_get_weather():
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = {
            "name": "London",
            "sys": {"country": "GB"},
            "main": {"temp": 15.5, "feels_like": 14.0, "humidity": 80},
            "weather": [{"description": "light rain"}],
            "wind": {"speed": 3.5}
        }
        
        result = await mcp.tools["get_weather"].fn(city="London")
        
        assert result["city"] == "London"
        assert result["temperature"] == 15.5
        assert result["conditions"] == "light rain"
```

### Integration Tests

```bash
# Test with real MCP client
make serve TOOL=weather

# In another terminal
uvx automagik-tools list
```

### MCP Compliance Testing

```bash
# Automated validation
make validate-tool TOOL=weather

# Checks:
# ✓ Tool discovery
# ✓ Parameter validation
# ✓ Error handling
# ✓ Async execution
# ✓ Documentation
```

## Best Practices

### 1. Configuration Management

```python
from pydantic import BaseSettings

class WeatherConfig(BaseSettings):
    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"
    timeout: int = 30
    
    class Config:
        env_prefix = "WEATHER_"

config = WeatherConfig()
```

### 2. Error Handling

```python
from fastmcp.exceptions import ToolError

@mcp.tool()
async def safe_operation(param: str) -> str:
    try:
        # Your code here
        result = await risky_operation(param)
        return result
    except SpecificError as e:
        raise ToolError(f"Operation failed: {e}", error_code="OPERATION_FAILED")
    except Exception as e:
        # Log error for debugging
        logger.error(f"Unexpected error: {e}")
        raise ToolError("An unexpected error occurred", error_code="INTERNAL_ERROR")
```

### 3. Logging

```python
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
async def logged_operation(param: str) -> str:
    logger.debug(f"Starting operation with param: {param}")
    try:
        result = await do_something(param)
        logger.info(f"Operation successful: {result}")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

### 4. Type Safety

```python
from typing import TypedDict, Literal

class WeatherData(TypedDict):
    city: str
    country: str
    temperature: float
    conditions: str
    humidity: int
    wind_speed: float

@mcp.tool()
async def get_weather(
    city: str,
    units: Literal["metric", "imperial"] = "metric"
) -> WeatherData:
    # Implementation with type safety
    pass
```

## Advanced Topics

### Custom Transports

```python
# Support custom transport configurations
@mcp.server()
async def configure_transport(transport: str):
    if transport == "websocket":
        # Configure WebSocket-specific settings
        pass
```

### Resource Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan():
    # Startup
    await initialize_connections()
    yield
    # Shutdown
    await cleanup_connections()

mcp = FastMCP("my-tool", lifespan=lifespan)
```

### Performance Optimization

```python
from functools import lru_cache
import asyncio

# Cache expensive operations
@lru_cache(maxsize=100)
def process_data(data: str) -> str:
    # Expensive processing
    return result

# Batch operations
async def batch_process(items: list[str]) -> list[str]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

## Debugging Tips

### 1. Enable Debug Logging

```bash
# In your .env
DEBUG=true
LOG_LEVEL=DEBUG

# Or when running
DEBUG=true make serve TOOL=my-tool
```

### 2. Use the Development Server

```bash
# Auto-reload on changes
make dev-server
```

### 3. Test with MCP Inspector

```bash
# Install MCP Inspector
npx @modelcontextprotocol/inspector

# Inspect your tool
npx @modelcontextprotocol/inspector uvx automagik-tools serve --tool my-tool --transport stdio
```

## Next Steps

1. **Read the Tool Creation Guide**: Detailed instructions for building tools
2. **Study Existing Tools**: Learn from `evolution_api` and `automagik_agents`
3. **Join the Community**: Contribute and get help
4. **Deploy Your Tools**: See the deployment guide

## Common Commands Reference

```bash
# Development
make install          # Set up environment
make list            # List all tools
make serve TOOL=name # Serve specific tool
make dev-server      # Hot-reload server

# Testing
make test            # Run all tests
make test-tool TOOL=name  # Test specific tool
make validate-tool TOOL=name  # Validate MCP compliance

# Code Quality
make lint            # Check code style
make format          # Auto-format code

# Building
make build           # Build package
make docker-build    # Build Docker images

# Documentation
make docs            # Build documentation
```

---

**Ready to build?** Check out the [Tool Creation Guide](creating-tools.md) for detailed instructions! 🛠️