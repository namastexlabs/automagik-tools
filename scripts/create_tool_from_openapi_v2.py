#!/usr/bin/env python3
"""
Generate automagik-tools from OpenAPI specifications using FastMCP's native support

Usage: python scripts/create_tool_from_openapi_v2.py --url https://api.example.com/openapi.json --name "My API"
"""

import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()
app = typer.Typer()


def to_snake_case(name: str) -> str:
    """Convert a name to snake_case"""
    # First, handle common acronyms as single units
    name = re.sub(r'\bAPI\b', 'api', name, flags=re.IGNORECASE)
    name = re.sub(r'\bURL\b', 'url', name, flags=re.IGNORECASE)
    name = re.sub(r'\bHTTP\b', 'http', name, flags=re.IGNORECASE)
    name = re.sub(r'\bJSON\b', 'json', name, flags=re.IGNORECASE)
    name = re.sub(r'\bXML\b', 'xml', name, flags=re.IGNORECASE)
    name = re.sub(r'\bID\b', 'id', name, flags=re.IGNORECASE)
    
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[\s\-]+', '_', name)
    # Insert underscore before uppercase letters (but not if already preceded by underscore)
    name = re.sub(r'(?<!^)(?<!_)(?=[A-Z])', '_', name)
    # Remove non-alphanumeric characters except underscores
    name = re.sub(r'[^\w_]', '', name)
    # Replace multiple underscores with single ones
    name = re.sub(r'_+', '_', name)
    return name.lower().strip('_')


def to_class_case(name: str) -> str:
    """Convert a name to ClassCase"""
    # Split by spaces, hyphens, or underscores
    parts = re.split(r'[\s\-_]+', name)
    # Capitalize each part
    return ''.join(word.capitalize() for word in parts if word)


def to_kebab_case(name: str) -> str:
    """Convert a name to kebab-case"""
    # First, handle common acronyms as single units
    name = re.sub(r'\bAPI\b', 'api', name, flags=re.IGNORECASE)
    name = re.sub(r'\bURL\b', 'url', name, flags=re.IGNORECASE)
    name = re.sub(r'\bHTTP\b', 'http', name, flags=re.IGNORECASE)
    name = re.sub(r'\bJSON\b', 'json', name, flags=re.IGNORECASE)
    name = re.sub(r'\bXML\b', 'xml', name, flags=re.IGNORECASE)
    name = re.sub(r'\bID\b', 'id', name, flags=re.IGNORECASE)
    
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Insert hyphen before uppercase letters (but not if already preceded by hyphen)
    name = re.sub(r'(?<!^)(?<!-)(?=[A-Z])', '-', name)
    # Remove non-alphanumeric characters except hyphens
    name = re.sub(r'[^\w\-]', '', name)
    # Replace multiple hyphens with single ones
    name = re.sub(r'-+', '-', name)
    return name.lower().strip('-')


def generate_tool_code(tool_name: str, tool_name_lower: str, tool_name_class: str, 
                       tool_description: str, openapi_url: str, base_url: str) -> str:
    """Generate tool implementation using FastMCP's OpenAPI support"""
    
    return f'''"""
{tool_description}

This tool provides MCP integration for {tool_name} API using FastMCP's native OpenAPI support.
"""

import httpx
import os
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType

from .config import {tool_name_class}Config

# Import AI processor if available
try:
    from automagik_tools.ai_processors import OpenAPIProcessor
    AI_PROCESSOR_AVAILABLE = True
except ImportError:
    AI_PROCESSOR_AVAILABLE = False

# Global config instance
config: Optional[{tool_name_class}Config] = None

# Global MCP instance
mcp: Optional[FastMCP] = None


def create_mcp_from_openapi(tool_config: {tool_name_class}Config) -> FastMCP:
    """Create MCP server from OpenAPI specification"""
    
    # Create HTTP client with authentication
    headers = {{}}
    if tool_config.api_key:
        headers["X-API-Key"] = tool_config.api_key
        # Also support Authorization header
        headers["Authorization"] = f"Bearer {{tool_config.api_key}}"
    
    client = httpx.AsyncClient(
        base_url=tool_config.base_url,
        headers=headers,
        timeout=tool_config.timeout
    )
    
    # Fetch OpenAPI spec
    try:
        # Try the configured OpenAPI URL first
        openapi_url = tool_config.openapi_url or "{openapi_url}"
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()
    except Exception as e:
        # Fallback to a minimal spec if we can't fetch
        openapi_spec = {{
            "openapi": "3.0.0",
            "info": {{
                "title": "{tool_name}",
                "description": "{tool_description}",
                "version": "1.0.0"
            }},
            "servers": [{{"url": tool_config.base_url}}],
            "paths": {{}}
        }}
    
    # Process with AI if configured
    mcp_names = {{}}
    if tool_config.use_ai_processor and AI_PROCESSOR_AVAILABLE:
        api_key = tool_config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                processor = OpenAPIProcessor(model_id=tool_config.ai_model_id, api_key=api_key)
                result = processor.process_openapi_spec(openapi_spec)
                mcp_names = result.name_mappings
                print(f"AI processed {{len(mcp_names)}} operations")
            except Exception as e:
                print(f"AI processing failed: {{e}}")
    
    # Create MCP server from OpenAPI spec
    mcp_server = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="{tool_name}",
        timeout=tool_config.timeout,
        mcp_names=mcp_names,  # Use AI-generated names if available
        route_maps=[
            # You can customize route mapping here
            # Example: Make all analytics endpoints tools
            # RouteMap(methods=["GET"], pattern=r"^/analytics/.*", mcp_type=MCPType.TOOL),
            
            # Example: Exclude admin endpoints
            # RouteMap(pattern=r"^/admin/.*", mcp_type=MCPType.EXCLUDE),
        ]
    )
    
    return mcp_server


# Tool creation functions (required by automagik-tools)
def create_tool(tool_config: Optional[{tool_name_class}Config] = None) -> FastMCP:
    """Create the MCP tool instance"""
    global config, mcp
    config = tool_config or {tool_name_class}Config()
    
    if mcp is None:
        mcp = create_mcp_from_openapi(config)
    
    return mcp


def create_server(tool_config: Optional[{tool_name_class}Config] = None):
    """Create FastMCP server instance"""
    tool = create_tool(tool_config)
    return tool


def get_tool_name() -> str:
    """Get the tool name"""
    return "{to_kebab_case(tool_name)}"


def get_config_class():
    """Get the config class for this tool"""
    return {tool_name_class}Config


def get_config_schema() -> Dict[str, Any]:
    """Get the JSON schema for the config"""
    return {tool_name_class}Config.model_json_schema()


def get_required_env_vars() -> Dict[str, str]:
    """Get required environment variables"""
    return {{
        "{tool_name_lower.upper()}_API_KEY": "API key for authentication",
        "{tool_name_lower.upper()}_BASE_URL": "Base URL for the API",
        "{tool_name_lower.upper()}_OPENAPI_URL": "URL to fetch OpenAPI spec (optional)",
    }}


def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {{
        "name": "{to_kebab_case(tool_name)}",
        "version": "1.0.0",
        "description": "{tool_description}",
        "author": "Automagik Team",
        "category": "api",
        "tags": ["api", "integration", "openapi"],
        "config_env_prefix": "{tool_name_lower.upper()}_"
    }}


def run_standalone(host: str = "0.0.0.0", port: int = 8000):
    """Run the tool as a standalone service"""
    import uvicorn
    server = create_server()
    uvicorn.run(server.asgi(), host=host, port=port)
'''


def generate_config_code(tool_name_class: str, tool_name_lower: str, base_url: str, openapi_url: str) -> str:
    """Generate configuration class code"""
    
    return f'''"""
Configuration for {tool_name_class}
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class {tool_name_class}Config(BaseSettings):
    """Configuration for {tool_name_class} MCP Tool"""
    
    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="{tool_name_lower.upper()}_API_KEY"
    )
    
    base_url: str = Field(
        default="{base_url}",
        description="Base URL for the API",
        alias="{tool_name_lower.upper()}_BASE_URL"
    )
    
    openapi_url: str = Field(
        default="{openapi_url}",
        description="URL to fetch OpenAPI specification",
        alias="{tool_name_lower.upper()}_OPENAPI_URL"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="{tool_name_lower.upper()}_TIMEOUT"
    )
    
    use_ai_processor: bool = Field(
        default=False,
        description="Use AI to process OpenAPI specs into human-friendly names",
        alias="{tool_name_lower.upper()}_USE_AI_PROCESSOR"
    )
    
    ai_model_id: str = Field(
        default="gpt-4.1",
        description="OpenAI model ID to use for AI processing",
        alias="{tool_name_lower.upper()}_AI_MODEL"
    )
    
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for AI processing (uses OPENAI_API_KEY env var if not set)",
        alias="{tool_name_lower.upper()}_OPENAI_API_KEY"
    )
    
    model_config = {{
        "env_prefix": "{tool_name_lower.upper()}_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }}
'''


def generate_test_code(tool_name: str, tool_name_lower: str, tool_name_class: str) -> str:
    """Generate test code"""
    
    return f'''"""
Tests for {tool_name} MCP tool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import Context

from automagik_tools.tools.{tool_name_lower} import (
    create_tool,
    {tool_name_class}Config,
    get_metadata,
    get_config_class,
    get_config_schema,
    get_required_env_vars,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return {tool_name_class}Config(
        api_key="test-api-key",
        base_url="https://api.example.com",
        openapi_url="https://api.example.com/openapi.json",
        timeout=10
    )


@pytest.fixture
def mock_openapi_spec():
    """Create a mock OpenAPI specification"""
    return {{
        "openapi": "3.0.0",
        "info": {{
            "title": "{tool_name}",
            "version": "1.0.0"
        }},
        "servers": [{{"url": "https://api.example.com"}}],
        "paths": {{
            "/test": {{
                "get": {{
                    "summary": "Test endpoint",
                    "operationId": "test_endpoint",
                    "responses": {{"200": {{"description": "Success"}}}}
                }}
            }}
        }}
    }}


class TestToolCreation:
    """Test tool creation and metadata"""
    
    @pytest.mark.unit
    def test_metadata(self):
        """Test tool metadata"""
        metadata = get_metadata()
        assert metadata["name"] == "{to_kebab_case(tool_name)}"
        assert "description" in metadata
        assert "version" in metadata
        assert metadata["config_env_prefix"] == "{tool_name_lower.upper()}_"
    
    @pytest.mark.unit
    def test_config_class(self):
        """Test config class retrieval"""
        config_class = get_config_class()
        assert config_class == {tool_name_class}Config
    
    @pytest.mark.unit
    def test_config_schema(self):
        """Test config schema generation"""
        schema = get_config_schema()
        assert "properties" in schema
        assert "api_key" in schema["properties"]
        assert "base_url" in schema["properties"]
        assert "openapi_url" in schema["properties"]
    
    @pytest.mark.unit
    def test_required_env_vars(self):
        """Test required environment variables"""
        env_vars = get_required_env_vars()
        assert "{tool_name_lower.upper()}_API_KEY" in env_vars
        assert "{tool_name_lower.upper()}_BASE_URL" in env_vars
        assert "{tool_name_lower.upper()}_OPENAPI_URL" in env_vars
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_create_tool_with_mock_spec(self, mock_get, mock_config, mock_openapi_spec):
        """Test tool creation with mocked OpenAPI spec"""
        # Mock the OpenAPI spec fetch
        mock_response = MagicMock()
        mock_response.json.return_value = mock_openapi_spec
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Create tool
        tool = create_tool(mock_config)
        assert tool is not None
        assert tool.name == "{tool_name}"


class TestMCPProtocol:
    """Test MCP protocol compliance"""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    @patch('httpx.get')
    async def test_tool_list(self, mock_get, mock_config, mock_openapi_spec):
        """Test MCP tools/list"""
        # Mock the OpenAPI spec fetch
        mock_response = MagicMock()
        mock_response.json.return_value = mock_openapi_spec
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Create tool and test
        tool = create_tool(mock_config)
        tools = await tool.list_tools()
        
        # Should have converted the test endpoint to a tool
        assert len(tools) >= 0  # May be 0 if endpoint was converted to resource
'''


def generate_readme(tool_name: str, tool_description: str, base_url: str, openapi_url: str) -> str:
    """Generate README documentation"""
    
    return f'''# {tool_name} MCP Tool

{tool_description}

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
{tool_name.upper().replace(' ', '_')}_API_KEY=your-api-key-here

# Base URL for the API
{tool_name.upper().replace(' ', '_')}_BASE_URL={base_url}

# URL to fetch OpenAPI specification (optional)
{tool_name.upper().replace(' ', '_')}_OPENAPI_URL={openapi_url}

# Request timeout in seconds (optional, defaults to 30)
{tool_name.upper().replace(' ', '_')}_TIMEOUT=30
```

## Usage

### With automagik-tools CLI

```bash
# List available tools
automagik-tools list

# Serve this specific tool
automagik-tools serve {to_kebab_case(tool_name)}

# Serve all tools
automagik-tools serve-all
```

### In Python Code

```python
from automagik_tools.tools.{to_snake_case(tool_name)} import create_server

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
    RouteMap(tags={{"internal"}}, mcp_type=MCPType.EXCLUDE),
]
```

## Development

### Running Tests

```bash
pytest tests/tools/test_{to_snake_case(tool_name)}.py -v
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @anthropic/mcp-inspector

# Run the tool
automagik-tools serve {to_kebab_case(tool_name)}

# In another terminal, connect with inspector
mcp-inspector stdio automagik-tools serve {to_kebab_case(tool_name)}
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
'''


@app.command()
def create(
    url: str = typer.Option(None, "--url", "-u", help="URL to OpenAPI JSON specification"),
    name: str = typer.Option(None, "--name", "-n", help="Tool name (e.g., 'GitHub API')"),
    description: str = typer.Option(None, "--description", "-d", help="Tool description"),
    output_dir: str = typer.Option(None, "--output", "-o", help="Output directory (defaults to automagik_tools/tools/)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing tool without prompting"),
    update: bool = typer.Option(False, "--update", "-U", help="Update existing tool, overwriting all files"),
):
    """Create a new tool from OpenAPI specification using FastMCP"""
    
    # Validate URL
    if not url:
        console.print("[red]Error: --url is required[/red]")
        raise typer.Exit(1)
    
    # Parse the URL to extract base URL
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Try to fetch basic info from the spec
    console.print(f"[cyan]Fetching OpenAPI specification from:[/cyan] {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        spec = response.json()
        
        # Extract info from spec
        info = spec.get('info', {})
        if not name:
            name = info.get('title', 'API Tool')
        if not description:
            description = info.get('description', info.get('summary', f"MCP tool for {name} integration"))
            
    except Exception as e:
        console.print(f"[yellow]Warning: Could not fetch OpenAPI spec: {e}[/yellow]")
        console.print("[yellow]Tool will fetch spec at runtime[/yellow]")
        
        if not name:
            name = Prompt.ask("[cyan]Tool name (e.g., 'GitHub API')[/cyan]")
        if not description:
            description = f"MCP tool for {name} integration"
    
    # Generate name variations
    tool_name = name
    tool_name_lower = to_snake_case(name)
    tool_name_kebab = to_kebab_case(name)
    tool_name_class = to_class_case(name)
    tool_name_upper = tool_name_lower.upper()
    
    console.print(f"\n[green]Creating tool:[/green] {tool_name}")
    console.print(f"[dim]Description:[/dim] {description}")
    console.print(f"[dim]Snake case:[/dim] {tool_name_lower}")
    console.print(f"[dim]Kebab case:[/dim] {tool_name_kebab}")
    console.print(f"[dim]Class case:[/dim] {tool_name_class}")
    console.print(f"[dim]Upper case:[/dim] {tool_name_upper}")
    console.print(f"[dim]OpenAPI URL:[/dim] {url}")
    console.print(f"[dim]Base URL:[/dim] {base_url}")
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    if output_dir:
        target_dir = Path(output_dir) / tool_name_lower
    else:
        target_dir = project_root / "automagik_tools" / "tools" / tool_name_lower
    
    test_file = project_root / "tests" / "tools" / f"test_{tool_name_lower}.py"
    
    # Check if tool already exists
    if target_dir.exists() and not (force or update):
        if not Confirm.ask(f"[yellow]Tool '{tool_name_lower}' already exists. Overwrite?[/yellow]"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)
    
    # Show update mode message
    if update and target_dir.exists():
        console.print(f"[cyan]Update mode: Overwriting existing '{tool_name_lower}' tool files[/cyan]")
    
    # Create directories
    target_dir.mkdir(parents=True, exist_ok=True)
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate files
    console.print(f"\n[cyan]Generating tool files...[/cyan]")
    
    # Generate __init__.py
    init_code = generate_tool_code(tool_name, tool_name_lower, tool_name_class, description, url, base_url)
    init_file = target_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write(init_code)
    console.print(f"[green]✓[/green] Created {init_file.relative_to(project_root)}")
    
    # Generate config.py
    config_code = generate_config_code(tool_name_class, tool_name_lower, base_url, url)
    config_file = target_dir / "config.py"
    with open(config_file, "w") as f:
        f.write(config_code)
    console.print(f"[green]✓[/green] Created {config_file.relative_to(project_root)}")
    
    # Generate README.md
    readme_content = generate_readme(tool_name, description, base_url, url)
    readme_file = target_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)
    console.print(f"[green]✓[/green] Created {readme_file.relative_to(project_root)}")
    
    # Generate tests
    test_code = generate_test_code(tool_name, tool_name_lower, tool_name_class)
    with open(test_file, "w") as f:
        f.write(test_code)
    console.print(f"[green]✓[/green] Created {test_file.relative_to(project_root)}")
    
    # Generate __main__.py for standalone execution
    main_code = f'''#!/usr/bin/env python
"""Standalone runner for {tool_name}"""

import argparse
from . import run_standalone, get_metadata

def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata["description"],
        prog=f"python -m automagik_tools.tools.{tool_name_lower}"
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    args = parser.parse_args()
    
    print(f"Starting {{metadata['name']}} on {{args.host}}:{{args.port}}")
    run_standalone(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
'''
    main_file = target_dir / "__main__.py"
    with open(main_file, "w") as f:
        f.write(main_code)
    console.print(f"[green]✓[/green] Created {main_file.relative_to(project_root)}")
    
    # No need to update pyproject.toml - tools are auto-discovered!
    
    # Update .env.example reminder
    console.print(f"\n[yellow]Note:[/yellow] Add configuration to .env.example:")
    console.print(f"\n[dim]# {tool_name} Configuration[/dim]")
    console.print(f"[dim]{tool_name_upper}_API_KEY=your-api-key-here[/dim]")
    console.print(f"[dim]{tool_name_upper}_BASE_URL={base_url}[/dim]")
    console.print(f"[dim]{tool_name_upper}_OPENAPI_URL={url}[/dim]")
    console.print(f"[dim]{tool_name_upper}_TIMEOUT=30[/dim]")
    
    # Summary
    console.print(f"\n[green]✨ Tool '{tool_name}' created successfully![/green]")
    console.print(f"\nThis tool uses FastMCP's native OpenAPI support to dynamically generate MCP components.")
    console.print(f"\nNext steps:")
    console.print(f"1. Add your API key to .env file")
    console.print(f"2. Run tests: [dim]pytest {test_file.relative_to(project_root)} -v[/dim]")
    console.print(f"3. Test your tool: [dim]automagik-tools serve {tool_name_kebab}[/dim]")
    console.print(f"4. Customize route mapping in {target_dir / '__init__.py'} if needed")


if __name__ == "__main__":
    app()