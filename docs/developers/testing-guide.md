# 🧪 Testing Guide

Comprehensive guide for testing AutoMagik Tools and your custom MCP tools.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [MCP Protocol Testing](#mcp-protocol-testing)
6. [Test Utilities](#test-utilities)
7. [CI/CD Testing](#cicd-testing)
8. [Best Practices](#best-practices)

## Testing Philosophy

AutoMagik Tools follows these testing principles:

1. **Fast Feedback**: Unit tests should run in seconds
2. **Comprehensive Coverage**: Aim for >80% code coverage
3. **Real-World Testing**: Integration tests with actual services
4. **Protocol Compliance**: Ensure MCP compatibility
5. **Maintainable Tests**: Clear, focused, and documented

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_unit_fast.py        # Fast unit tests
├── test_integration.py      # Integration tests
├── test_mcp_protocol.py     # MCP compliance tests
├── test_cli_simple.py       # CLI tests
└── tools/                   # Tool-specific tests
    ├── test_evolution_api.py
    ├── test_automagik_agents.py
    └── test_your_tool.py
```

## Unit Testing

### Basic Unit Test

```python
# tests/tools/test_weather.py
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from automagik_tools.tools.weather import mcp
from fastmcp.exceptions import ToolError

class TestWeatherTool:
    """Test suite for weather tool."""
    
    @pytest.mark.asyncio
    async def test_get_weather_success(self):
        """Test successful weather retrieval."""
        # Arrange
        mock_response = {
            "name": "London",
            "sys": {"country": "GB"},
            "main": {
                "temp": 15.5,
                "feels_like": 14.0,
                "humidity": 80
            },
            "weather": [{"description": "light rain"}],
            "wind": {"speed": 3.5}
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = AsyncMock()
            
            # Act
            result = await mcp.tools["get_weather"].fn(city="London")
            
            # Assert
            assert result["city"] == "London"
            assert result["temperature"] == 15.5
            assert result["conditions"] == "light rain"
            
    @pytest.mark.asyncio
    async def test_get_weather_invalid_city(self):
        """Test weather retrieval with invalid city."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value.raise_for_status.side_effect = httpx.HTTPError("404")
            
            with pytest.raises(ToolError) as exc_info:
                await mcp.tools["get_weather"].fn(city="InvalidCity123")
                
            assert exc_info.value.error_code == "CITY_NOT_FOUND"
```

### Testing with Fixtures

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API calls."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def weather_api_response():
    """Sample weather API response."""
    return {
        "name": "Test City",
        "main": {"temp": 20.0, "humidity": 50},
        "weather": [{"description": "clear sky"}]
    }

# Using fixtures in tests
@pytest.mark.asyncio
async def test_with_fixtures(mock_http_client, weather_api_response):
    mock_http_client.get.return_value.json.return_value = weather_api_response
    
    with patch('httpx.AsyncClient', return_value=mock_http_client):
        result = await get_weather("Test City")
        assert result["temperature"] == 20.0
```

### Parametrized Tests

```python
@pytest.mark.parametrize("city,country,expected_url", [
    ("London", None, "/weather?q=London"),
    ("London", "GB", "/weather?q=London,GB"),
    ("New York", "US", "/weather?q=New York,US"),
])
@pytest.mark.asyncio
async def test_location_formatting(city, country, expected_url, mock_http_client):
    """Test different location format combinations."""
    with patch('httpx.AsyncClient', return_value=mock_http_client):
        await get_weather(city, country)
        
        # Verify the correct URL was called
        call_args = mock_http_client.get.call_args
        assert expected_url in str(call_args)
```

### Testing Async Generators

```python
@pytest.mark.asyncio
async def test_streaming_response():
    """Test tools that return async generators."""
    async def mock_analyze():
        yield "Starting analysis..."
        yield "Processing data..."
        yield "Complete!"
        
    with patch.object(mcp.tools["analyze_data"], 'fn', mock_analyze):
        results = []
        async for chunk in mcp.tools["analyze_data"].fn():
            results.append(chunk)
            
        assert len(results) == 3
        assert results[0] == "Starting analysis..."
        assert results[-1] == "Complete!"
```

## Integration Testing

### Testing with Real Services

```python
# tests/test_integration.py
import pytest
import os
from automagik_tools.tools.github import mcp

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set"
)
class TestGitHubIntegration:
    """Integration tests for GitHub tool."""
    
    @pytest.mark.asyncio
    async def test_real_list_repos(self):
        """Test listing real repositories."""
        result = await mcp.tools["list_repos"].fn(
            user="octocat",
            limit=5
        )
        
        assert len(result) <= 5
        assert all("name" in repo for repo in result)
        assert all("url" in repo for repo in result)
```

### Testing with Docker

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_docker_deployment():
    """Test tool in Docker container."""
    import docker
    
    client = docker.from_env()
    
    # Build image
    image = client.images.build(
        path=".",
        dockerfile="Dockerfile.sse",
        tag="test-automagik:latest"
    )
    
    # Run container
    container = client.containers.run(
        "test-automagik:latest",
        detach=True,
        ports={'8000/tcp': 8000},
        environment={
            "EVOLUTION_API_KEY": "test-key"
        }
    )
    
    try:
        # Wait for startup
        await asyncio.sleep(2)
        
        # Test endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            
    finally:
        container.stop()
        container.remove()
```

## MCP Protocol Testing

### Protocol Compliance Tests

```python
# tests/test_mcp_protocol.py
import pytest
from mcp import Client
from automagik_tools.servers.hub import create_hub_server

@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    """Test that tools are discoverable via MCP protocol."""
    server = create_hub_server()
    
    # Create MCP client
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        
        assert len(tools) > 0
        assert any(tool.name == "get_weather" for tool in tools)
        
        # Check tool metadata
        weather_tool = next(t for t in tools if t.name == "get_weather")
        assert weather_tool.description
        assert weather_tool.input_schema
        assert weather_tool.input_schema["type"] == "object"
        assert "city" in weather_tool.input_schema["properties"]

@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """Test tool execution via MCP protocol."""
    server = create_hub_server()
    
    async with Client(server) as client:
        # Execute tool
        result = await client.call_tool(
            "get_weather",
            {"city": "London"}
        )
        
        assert result.is_success()
        assert "temperature" in result.content
        assert "conditions" in result.content

@pytest.mark.asyncio
async def test_mcp_error_handling():
    """Test MCP error responses."""
    server = create_hub_server()
    
    async with Client(server) as client:
        # Call with invalid parameters
        result = await client.call_tool(
            "get_weather",
            {}  # Missing required 'city' parameter
        )
        
        assert result.is_error()
        assert result.error_code == "INVALID_PARAMS"
```

### Transport Testing

```python
@pytest.mark.asyncio
async def test_stdio_transport():
    """Test STDIO transport communication."""
    import asyncio
    
    # Start server process
    proc = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "-m", "automagik_tools", "serve", 
        "--tool", "weather", "--transport", "stdio",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Send JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        proc.stdin.write(json.dumps(request).encode() + b'\n')
        await proc.stdin.drain()
        
        # Read response
        response_line = await proc.stdout.readline()
        response = json.loads(response_line)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        
    finally:
        proc.terminate()
        await proc.wait()
```

## Test Utilities

### Custom Assertions

```python
# tests/utils.py
def assert_valid_timestamp(timestamp: str):
    """Assert that a string is a valid ISO timestamp."""
    from datetime import datetime
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp: {timestamp}")

def assert_api_response(response: dict, required_fields: list):
    """Assert API response has required fields."""
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"
        
# Usage
def test_api_response():
    response = {"id": 1, "created_at": "2024-01-01T00:00:00Z"}
    assert_api_response(response, ["id", "created_at"])
    assert_valid_timestamp(response["created_at"])
```

### Test Data Builders

```python
# tests/builders.py
class WeatherDataBuilder:
    """Builder for test weather data."""
    
    def __init__(self):
        self._data = {
            "name": "Test City",
            "main": {"temp": 20.0, "humidity": 50},
            "weather": [{"description": "clear"}]
        }
        
    def with_temperature(self, temp: float):
        self._data["main"]["temp"] = temp
        return self
        
    def with_condition(self, condition: str):
        self._data["weather"][0]["description"] = condition
        return self
        
    def build(self):
        return self._data
        
# Usage
def test_with_builder():
    weather_data = (
        WeatherDataBuilder()
        .with_temperature(30.0)
        .with_condition("sunny")
        .build()
    )
    
    assert weather_data["main"]["temp"] == 30.0
```

### Mock Factories

```python
# tests/mocks.py
def create_mock_github_client(responses: dict):
    """Create a mock GitHub client with predefined responses."""
    client = AsyncMock()
    
    for method, response_data in responses.items():
        mock_method = getattr(client, method)
        mock_method.return_value.json.return_value = response_data
        mock_method.return_value.raise_for_status = AsyncMock()
        
    return client

# Usage
def test_with_mock_factory():
    client = create_mock_github_client({
        "get": {"name": "test-repo", "stars": 100}
    })
    
    with patch('httpx.AsyncClient', return_value=client):
        result = await get_repo_info("owner/repo")
        assert result["stars"] == 100
```

## CI/CD Testing

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install uv
      uses: astral-sh/setup-uv@v4
    
    - name: Install dependencies
      run: |
        uv sync --all-extras
    
    - name: Run unit tests
      run: |
        uv run pytest tests/test_unit_fast.py -v
    
    - name: Run MCP protocol tests
      run: |
        uv run pytest tests/test_mcp_protocol.py -v
    
    - name: Run integration tests
      env:
        GITHUB_TOKEN: ${{ secrets.TEST_GITHUB_TOKEN }}
      run: |
        uv run pytest tests/test_integration.py -v -m integration
    
    - name: Generate coverage report
      run: |
        uv run pytest --cov=automagik_tools --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Unit Tests
        entry: uv run pytest tests/test_unit_fast.py
        language: system
        pass_filenames: false
        always_run: true
        
      - id: format-check
        name: Format Check
        entry: make lint
        language: system
        pass_filenames: false
```

## Best Practices

### 1. Test Organization

```python
class TestWeatherTool:
    """Group related tests in classes."""
    
    class TestGetWeather:
        """Nested class for specific functionality."""
        
        def test_success_case(self):
            pass
            
        def test_error_case(self):
            pass
            
    class TestGetForecast:
        def test_success_case(self):
            pass
```

### 2. Clear Test Names

```python
# Good test names
def test_get_weather_returns_temperature_in_celsius():
    pass

def test_create_issue_fails_with_invalid_repo_format():
    pass

# Bad test names
def test_weather():  # Too vague
    pass

def test_1():  # Meaningless
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
@pytest.mark.asyncio
async def test_create_github_issue():
    # Arrange
    mock_client = create_mock_github_client()
    repo = "owner/repo"
    title = "Test Issue"
    body = "Issue description"
    
    # Act
    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await create_issue(repo, title, body)
    
    # Assert
    assert result["title"] == title
    assert mock_client.post.called_once_with(
        f"/repos/{repo}/issues",
        json={"title": title, "body": body}
    )
```

### 4. Test Data Isolation

```python
@pytest.fixture
def isolated_test_data(tmp_path):
    """Create isolated test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    
    # Create test files
    (data_dir / "config.json").write_text('{"key": "value"}')
    
    yield data_dir
    
    # Cleanup happens automatically

def test_with_isolated_data(isolated_test_data):
    config_path = isolated_test_data / "config.json"
    assert config_path.exists()
```

### 5. Testing Error Conditions

```python
@pytest.mark.parametrize("error_code,error_class", [
    (401, AuthenticationError),
    (403, RateLimitError),
    (404, NotFoundError),
    (500, ServerError),
])
@pytest.mark.asyncio
async def test_error_handling(error_code, error_class):
    """Test different error conditions."""
    mock_response = AsyncMock()
    mock_response.status_code = error_code
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        f"{error_code} Error",
        request=None,
        response=mock_response
    )
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        with pytest.raises(error_class):
            await make_api_call()
```

### 6. Performance Testing

```python
import time

@pytest.mark.performance
def test_response_time():
    """Ensure operations complete within acceptable time."""
    start = time.time()
    
    result = expensive_operation()
    
    duration = time.time() - start
    assert duration < 1.0, f"Operation too slow: {duration}s"

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling multiple concurrent requests."""
    tasks = [
        get_weather(city) 
        for city in ["London", "Paris", "Tokyo", "New York"]
    ]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    assert len(results) == 4
    assert duration < 2.0  # Should complete in parallel
```

## Running Tests

### Command Line Options

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/tools/test_weather.py

# Run specific test
uv run pytest tests/tools/test_weather.py::test_get_weather

# Run with coverage
uv run pytest --cov=automagik_tools --cov-report=html

# Run only marked tests
uv run pytest -m "not integration"  # Skip integration tests
uv run pytest -m "unit"  # Only unit tests

# Run with verbose output
uv run pytest -v

# Run with print statements
uv run pytest -s

# Run in parallel
uv run pytest -n auto  # Use all CPU cores
```

### Debugging Tests

```python
# Add breakpoint
def test_debugging():
    data = get_data()
    import pdb; pdb.set_trace()  # Debugger stops here
    assert data["key"] == "value"

# Or use pytest's built-in
def test_with_pytest_debug():
    data = get_data()
    pytest.set_trace()  # Better integration with pytest
    assert data["key"] == "value"
```

### Test Coverage

```bash
# Generate coverage report
make test-coverage

# View HTML report
open htmlcov/index.html

# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["automagik_tools"]
omit = ["*/tests/*", "*/conftest.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

## Continuous Improvement

### 1. Monitor Test Health

```bash
# Find slow tests
uv run pytest --durations=10

# Find flaky tests
uv run pytest --lf  # Run last failed
uv run pytest --ff  # Run failed first
```

### 2. Maintain Test Quality

- Review test coverage in PRs
- Refactor tests when they become complex
- Remove obsolete tests
- Keep test data up to date

### 3. Test Documentation

```python
def test_weather_api_integration():
    """Test weather API integration.
    
    This test verifies:
    1. API authentication works
    2. Response parsing is correct
    3. Error handling for invalid cities
    4. Rate limiting is respected
    
    Note: Requires WEATHER_API_KEY environment variable
    """
    pass
```

---

**Remember**: Good tests are the foundation of reliable tools. Test early, test often, and test well! 🧪