# 📚 API Reference

Complete API reference for AutoMagik Tools development.

## Core Components

### FastMCP Server

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="tool-name",
    version="1.0.0",
    description="Tool description",
    lifespan=optional_lifespan_handler
)
```

**Parameters:**
- `name` (str): Unique tool identifier
- `version` (str): Semantic version
- `description` (str): Human-readable description
- `lifespan` (callable): Async context manager for startup/shutdown

### Tool Decorator

```python
@mcp.tool(
    name="optional_override",
    description="Override default docstring",
    schema=optional_pydantic_model
)
async def tool_function(param1: str, param2: int = 10) -> dict:
    """Default description from docstring."""
    return {"result": "value"}
```

**Parameters:**
- `name` (str): Override function name
- `description` (str): Override docstring
- `schema` (Type[BaseModel]): Pydantic model for validation

## CLI Commands

### Main Commands

```bash
automagik-tools [OPTIONS] COMMAND [ARGS]...
```

**Commands:**
- `list` - List available tools
- `serve` - Serve a single tool
- `serve-all` - Serve all tools on multi-tool server
- `version` - Show version information
- `info` - Display tool information
- `tool` - Create tool from OpenAPI spec

### Serve Command

```bash
automagik-tools serve [OPTIONS]
```

**Options:**
- `--tool TEXT` - Tool name to serve (required)
- `--transport [stdio|sse|http]` - Transport type (default: stdio)
- `--host TEXT` - Host for SSE/HTTP (default: 127.0.0.1)
- `--port INTEGER` - Port for SSE/HTTP (default: 8000)

**Examples:**
```bash
# Serve via stdio for MCP clients
automagik-tools serve --tool evolution-api --transport stdio

# Serve via SSE for web clients
automagik-tools serve --tool evolution-api --transport sse --port 8080

# Serve via HTTP API
automagik-tools serve --tool evolution-api --transport http --host 0.0.0.0
```

### Serve-All Command

```bash
automagik-tools serve-all [OPTIONS]
```

**Options:**
- `--transport [stdio|sse|http]` - Transport type (default: stdio)
- `--host TEXT` - Host for SSE/HTTP (default: 127.0.0.1)
- `--port INTEGER` - Port for SSE/HTTP (default: 8000)

### Tool Command

```bash
automagik-tools tool --url OPENAPI_URL
```

**Options:**
- `--url TEXT` - OpenAPI specification URL (required)

**Example:**
```bash
automagik-tools tool --url https://api.stripe.com/openapi/v3.json
```

## Configuration

### Environment Variables

#### Global Settings
- `DEBUG` - Enable debug logging (true/false)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT` - Log format (simple, detailed, json)

#### Tool-Specific Settings

**Evolution API:**
- `EVOLUTION_API_BASE_URL` - API endpoint URL
- `EVOLUTION_API_KEY` - Authentication key
- `EVOLUTION_TIMEOUT` - Request timeout (seconds)

**AutoMagik Agents:**
- `OPENAI_API_KEY` - OpenAI API key
- `AGENT_MODEL` - Model to use (gpt-4-turbo-preview)
- `AGENT_MAX_TOKENS` - Maximum tokens per request
- `AGENT_TEMPERATURE` - Response randomness (0-1)

### Pydantic Settings

```python
from pydantic_settings import BaseSettings

class ToolConfig(BaseSettings):
    api_key: str
    api_url: str = "https://api.example.com"
    timeout: int = 30
    retry_count: int = 3
    
    class Config:
        env_prefix = "TOOL_"
        env_file = ".env"
        case_sensitive = False
```

## Tool Development API

### Basic Tool Structure

```python
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any

# Create server
mcp = FastMCP("my-tool")

# Define tool
@mcp.tool()
async def my_function(
    required_param: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """Tool description.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        
    Returns:
        Dictionary with results
    """
    return {
        "status": "success",
        "data": process_data(required_param, optional_param)
    }

# Export for discovery
__all__ = ["mcp"]
```

### Advanced Tool Features

#### Streaming Responses

```python
from typing import AsyncIterator

@mcp.tool()
async def stream_data(query: str) -> AsyncIterator[str]:
    """Stream data progressively."""
    yield "Starting process...\n"
    
    for item in await fetch_items(query):
        yield f"Processing: {item}\n"
        await asyncio.sleep(0.1)  # Simulate work
        
    yield "Complete!"
```

#### File Handling

```python
from pathlib import Path
import base64

@mcp.tool()
async def process_file(
    file_path: str,
    encoding: str = "utf-8"
) -> Dict[str, Any]:
    """Process a file."""
    path = Path(file_path)
    
    if not path.exists():
        raise ToolError("File not found", error_code="FILE_NOT_FOUND")
        
    if path.stat().st_size > 10_000_000:  # 10MB limit
        raise ToolError("File too large", error_code="FILE_TOO_LARGE")
        
    content = path.read_text(encoding=encoding)
    
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "lines": len(content.splitlines()),
        "preview": content[:1000]
    }
```

#### Error Handling

```python
from fastmcp.exceptions import ToolError

@mcp.tool()
async def safe_operation(param: str) -> str:
    """Operation with proper error handling."""
    try:
        if not param:
            raise ToolError(
                "Parameter cannot be empty",
                error_code="INVALID_PARAM"
            )
            
        result = await risky_operation(param)
        return result
        
    except ExternalAPIError as e:
        raise ToolError(
            f"External API failed: {e}",
            error_code="EXTERNAL_API_ERROR"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ToolError(
            "An unexpected error occurred",
            error_code="INTERNAL_ERROR"
        )
```

### Server Lifecycle

```python
from contextlib import asynccontextmanager
import httpx

# Global resources
_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan():
    """Manage server lifecycle."""
    global _client
    
    # Startup
    logger.info("Starting up...")
    _client = httpx.AsyncClient()
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down...")
        if _client:
            await _client.aclose()

# Use in server
mcp = FastMCP("my-tool", lifespan=lifespan)
```

## Transport Protocols

### STDIO Transport

Used for CLI integration (Claude Desktop, Cursor).

**Message Format:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {"param": "value"}
  },
  "id": 1
}
```

### SSE Transport

Server-Sent Events for web applications.

**Endpoints:**
- `GET /` - SSE event stream
- `POST /` - Send commands
- `GET /health` - Health check

**Event Format:**
```
event: message
data: {"type": "tool_result", "data": {...}}

event: error
data: {"error": "Error message"}
```

### HTTP Transport

RESTful API for standard HTTP clients.

**Endpoints:**
- `GET /tools` - List available tools
- `POST /tools/{name}/invoke` - Call a tool
- `GET /health` - Health check

**Request Format:**
```json
POST /tools/get_weather/invoke
Content-Type: application/json

{
  "arguments": {
    "city": "London"
  }
}
```

## Testing API

### Test Fixtures

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    from automagik_tools.tools.my_tool import mcp
    return mcp

@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client
```

### Test Utilities

```python
from automagik_tools.testing import (
    create_mock_tool,
    assert_tool_response,
    validate_mcp_compliance
)

# Create mock tool
mock_tool = create_mock_tool("test-tool")

# Validate response
assert_tool_response(
    response,
    required_fields=["status", "data"],
    expected_type=dict
)

# Check MCP compliance
await validate_mcp_compliance(mcp_server)
```

## Error Codes

Standard error codes used across all tools:

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_PARAMS` | Invalid or missing parameters | 400 |
| `AUTH_FAILED` | Authentication failed | 401 |
| `FORBIDDEN` | Access denied | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `EXTERNAL_API_ERROR` | External API failed | 502 |
| `TIMEOUT` | Operation timed out | 504 |

## Type Definitions

### Common Types

```python
from typing import TypedDict, Literal, Union

class ToolResult(TypedDict):
    """Standard tool result format."""
    status: Literal["success", "error"]
    data: Union[dict, list, str]
    error: Optional[str]
    error_code: Optional[str]

class PaginatedResult(TypedDict):
    """Paginated result format."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    has_next: bool

class FileData(TypedDict):
    """File information format."""
    name: str
    path: str
    size: int
    mime_type: str
    content: Optional[str]
    base64: Optional[str]
```

## Validation

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class SearchParams(BaseModel):
    """Search parameters validation."""
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort: Literal["asc", "desc"] = "desc"
    
    @validator("query")
    def clean_query(cls, v):
        return v.strip()

@mcp.tool()
async def search(params: SearchParams) -> list:
    """Search with validated parameters."""
    validated = params.dict()
    return await perform_search(**validated)
```

### Output Validation

```python
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    """Weather response validation."""
    city: str
    temperature: float
    conditions: str
    humidity: int = Field(..., ge=0, le=100)

@mcp.tool()
async def get_weather(city: str) -> WeatherResponse:
    """Get weather with validated response."""
    data = await fetch_weather_data(city)
    return WeatherResponse(**data)  # Validates output
```

## Performance

### Caching

```python
from functools import lru_cache
import aiocache

# Simple in-memory cache
@lru_cache(maxsize=100)
def expensive_computation(param: str) -> str:
    return process(param)

# Async cache with TTL
cache = aiocache.Cache()

@mcp.tool()
async def cached_operation(key: str) -> dict:
    # Try cache first
    cached = await cache.get(key)
    if cached:
        return cached
        
    # Compute and cache
    result = await expensive_async_operation(key)
    await cache.set(key, result, ttl=300)  # 5 minutes
    return result
```

### Rate Limiting

```python
from asyncio import Semaphore
from datetime import datetime, timedelta

# Concurrent request limiting
_semaphore = Semaphore(10)  # Max 10 concurrent requests

@mcp.tool()
async def rate_limited_operation(param: str) -> str:
    async with _semaphore:
        return await external_api_call(param)

# Time-based rate limiting
_last_call = {}
_min_interval = timedelta(seconds=1)

@mcp.tool()
async def time_limited_operation(user_id: str) -> str:
    now = datetime.now()
    last = _last_call.get(user_id)
    
    if last and now - last < _min_interval:
        wait_time = (_min_interval - (now - last)).total_seconds()
        raise ToolError(
            f"Rate limited. Try again in {wait_time:.1f} seconds",
            error_code="RATE_LIMITED"
        )
        
    _last_call[user_id] = now
    return await perform_operation(user_id)
```

## Deployment

### Docker Configuration

```dockerfile
# Multi-stage build example
FROM python:3.11-slim as builder

WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system .

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY automagik_tools ./automagik_tools

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "automagik_tools", "serve-all"]
```

### Environment Configuration

```python
import os
from pathlib import Path

# Configuration precedence
# 1. Environment variables
# 2. .env file in current directory
# 3. .env file in home directory
# 4. Default values

def load_config():
    """Load configuration with precedence."""
    # Load .env files
    env_files = [
        Path.cwd() / ".env",
        Path.home() / ".automagik" / ".env"
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file)
            
    # Return config
    return {
        "api_key": os.getenv("API_KEY", ""),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "timeout": int(os.getenv("TIMEOUT", "30"))
    }
```

---

**Need more details?** Check the source code or open an issue! 📖