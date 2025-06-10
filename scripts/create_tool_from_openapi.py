#!/usr/bin/env python3
"""
Generate automagik-tools from OpenAPI specifications

Usage: python scripts/create_tool_from_openapi.py --url https://api.example.com/openapi.json --name "My API"
"""

import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from pydantic import BaseModel, Field

# Import AI processor - use the local script version which has static generation support
try:
    from openapi_static_processor import (
        StaticOpenAPIProcessor,
        ProcessedOpenAPIFunctions,
        FunctionInfo,
        sanitize_python_name,
        enhance_parameter_description
    )
    AI_PROCESSOR_AVAILABLE = True
except ImportError:
    AI_PROCESSOR_AVAILABLE = False
    ProcessedOpenAPIFunctions = None  # For type hints

# Import streaming processor if available
try:
    from openapi_streaming_processor import StreamingOpenAPIProcessor
    STREAMING_PROCESSOR_AVAILABLE = True
except ImportError:
    STREAMING_PROCESSOR_AVAILABLE = False

console = Console()
app = typer.Typer()


class OpenAPIEndpoint:
    """Represents an OpenAPI endpoint with its details"""
    def __init__(self, path: str, method: str, operation: Dict[str, Any]):
        self.path = path
        self.method = method.upper()
        self.operation = operation
        self.operation_id = operation.get('operationId', f"{method}_{path.replace('/', '_')}")
        self.summary = operation.get('summary', '')
        self.description = operation.get('description', self.summary)
        self.parameters = operation.get('parameters', [])
        self.request_body = operation.get('requestBody', {})
        self.responses = operation.get('responses', {})
        self.tags = operation.get('tags', [])
        self.security = operation.get('security', [])


class OpenAPIParser:
    """Parse OpenAPI specification and extract relevant information"""
    
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.info = spec.get('info', {})
        self.servers = spec.get('servers', [])
        self.paths = spec.get('paths', {})
        self.components = spec.get('components', {})
        self.security_schemes = self.components.get('securitySchemes', {})
        
    def get_base_url(self) -> str:
        """Extract base URL from servers"""
        if self.servers:
            return self.servers[0].get('url', 'https://api.example.com')
        return 'https://api.example.com'
    
    def get_auth_info(self) -> Dict[str, Any]:
        """Extract authentication information"""
        auth_info = {
            'type': None,
            'header_name': None,
            'api_key_param': None,
            'bearer_format': None
        }
        
        for scheme_name, scheme_data in self.security_schemes.items():
            scheme_type = scheme_data.get('type')
            if scheme_type == 'apiKey':
                auth_info['type'] = 'api_key'
                auth_info['header_name'] = scheme_data.get('name', 'X-API-Key')
                auth_info['api_key_param'] = scheme_data.get('in', 'header')
            elif scheme_type == 'http' and scheme_data.get('scheme') == 'bearer':
                auth_info['type'] = 'bearer'
                auth_info['bearer_format'] = scheme_data.get('bearerFormat', 'JWT')
            elif scheme_type == 'oauth2':
                auth_info['type'] = 'oauth2'
                # Could extend to handle OAuth2 flows
                
        return auth_info
    
    def get_endpoints(self) -> List[OpenAPIEndpoint]:
        """Extract all endpoints from the spec"""
        endpoints = []
        
        for path, path_item in self.paths.items():
            # Common parameters for all operations on this path
            common_params = path_item.get('parameters', [])
            
            for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                if method in path_item:
                    operation = path_item[method]
                    # Merge common parameters with operation-specific ones
                    if common_params:
                        operation['parameters'] = operation.get('parameters', []) + common_params
                    
                    endpoints.append(OpenAPIEndpoint(path, method, operation))
        
        return endpoints
    
    def resolve_ref(self, ref: str) -> Any:
        """Resolve a $ref reference"""
        if not ref.startswith('#/'):
            return None
            
        path_parts = ref[2:].split('/')
        result = self.spec
        
        for part in path_parts:
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return None
                
        return result
    
    def get_parameter_type(self, param: Dict[str, Any]) -> Tuple[str, bool]:
        """Convert OpenAPI parameter to Python type"""
        schema = param.get('schema', {})
        if '$ref' in schema:
            schema = self.resolve_ref(schema['$ref']) or {}
            
        openapi_type = schema.get('type', 'string')
        required = param.get('required', False)
        
        type_mapping = {
            'string': 'str',
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'array': 'List[str]',  # Simplified
            'object': 'Dict[str, Any]'
        }
        
        return type_mapping.get(openapi_type, 'str'), required


def to_snake_case(name: str) -> str:
    """Convert a name to snake_case"""
    # Replace spaces and hyphens with underscores
    name = re.sub(r'[\s\-]+', '_', name)
    # Insert underscore before uppercase letters
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name)
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
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Insert hyphen before uppercase letters
    name = re.sub(r'(?<!^)(?=[A-Z])', '-', name)
    # Remove non-alphanumeric characters except hyphens
    name = re.sub(r'[^\w\-]', '', name)
    # Replace multiple hyphens with single ones
    name = re.sub(r'-+', '-', name)
    return name.lower().strip('-')


def sanitize_function_name(name: str) -> str:
    """Convert operation ID to valid Python function name"""
    # Replace non-alphanumeric with underscores
    name = re.sub(r'[^\w]', '_', name)
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"op_{name}"
    # Replace multiple underscores
    name = re.sub(r'_+', '_', name)
    return name.lower().strip('_')


def generate_tool_code(parser: OpenAPIParser, tool_name: str, tool_name_lower: str, 
                       tool_name_class: str, tool_name_kebab: str, tool_description: str,
                       ai_processed: Optional[ProcessedOpenAPIFunctions] = None) -> str:
    """Generate the main tool implementation code"""
    
    auth_info = parser.get_auth_info()
    endpoints = parser.get_endpoints()
    base_url = parser.get_base_url()
    
    # Create function name mapping from AI processor if available
    ai_function_map = {}
    ai_function_info = {}
    if ai_processed:
        ai_function_map = ai_processed.function_mappings
        for func in ai_processed.functions:
            ai_function_info[func.operation_id] = func
    
    # Group endpoints by tag for better organization
    endpoints_by_tag = {}
    for endpoint in endpoints:
        tag = endpoint.tags[0] if endpoint.tags else 'default'
        if tag not in endpoints_by_tag:
            endpoints_by_tag[tag] = []
        endpoints_by_tag[tag].append(endpoint)
    
    code = f'''"""
{tool_description}

This tool provides MCP integration for {tool_name} API.
Auto-generated from OpenAPI specification.
"""

import os
from typing import Dict, Any, Optional, List
from contextlib import suppress
import httpx
from pydantic import BaseModel, Field

from fastmcp import FastMCP, Context
from .config import {tool_name_class}Config

# Global config instance
config: Optional[{tool_name_class}Config] = None

# Create FastMCP instance
mcp = FastMCP(
    "{tool_name}",
    instructions="""
{tool_description}

Base URL: {base_url}
Authentication: {auth_info.get('type', 'none')}
"""
)


# Pydantic models for request/response validation
'''

    # Add model classes for complex request bodies if needed
    # For now, we'll keep it simple
    
    code += '''
async def make_api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Make HTTP request to the API"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    url = f"{config.base_url}{endpoint}"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
'''

    # Add authentication based on type
    if auth_info['type'] == 'api_key':
        if auth_info['api_key_param'] == 'header':
            code += f'    # Add API key authentication\n'
            code += f'    if config.api_key:\n'
            code += f'        headers["{auth_info["header_name"]}"] = config.api_key\n\n'
    elif auth_info['type'] == 'bearer':
        code += f'    # Add Bearer token authentication\n'
        code += f'    if config.api_key:\n'
        code += f'        headers["Authorization"] = f"Bearer {{config.api_key}}"\n\n'
    
    code += '''    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            
            # Return JSON if available, otherwise return text
            if "application/json" in response.headers.get("content-type", ""):
                return response.json()
            else:
                return {"result": response.text}
                
    except httpx.HTTPStatusError as e:
        if ctx:
            ctx.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        return {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except Exception as e:
        if ctx:
            ctx.error(f"Request failed: {str(e)}")
        return {"error": str(e)}


'''

    # Generate tool functions for each endpoint
    for tag, tag_endpoints in endpoints_by_tag.items():
        if tag != 'default':
            code += f'# {tag.title()} Operations\n\n'
            
        for endpoint in tag_endpoints:
            # Use AI-generated function name if available
            if endpoint.operation_id in ai_function_map:
                func_name = ai_function_map[endpoint.operation_id]
                func_info = ai_function_info.get(endpoint.operation_id)
            else:
                func_name = sanitize_function_name(endpoint.operation_id)
                func_info = None
            
            # Build function signature
            params = []
            param_docs = []
            
            # Extract parameters
            for param in endpoint.parameters:
                param_name = to_snake_case(param.get('name', ''))
                param_type, required = parser.get_parameter_type(param)
                
                # Use AI-enhanced parameter description if available
                if func_info and param.get('name') in func_info.parameter_descriptions:
                    param_desc = func_info.parameter_descriptions[param.get('name')]
                else:
                    param_desc = param.get('description', '')
                
                if required:
                    params.append(f"{param_name}: {param_type}")
                else:
                    default_value = "None" if param_type != "bool" else "False"
                    params.append(f"{param_name}: Optional[{param_type}] = {default_value}")
                
                param_docs.append(f"        {param_name}: {param_desc}")
            
            # Add request body parameters if present
            if endpoint.request_body:
                content = endpoint.request_body.get('content', {})
                if 'application/json' in content:
                    schema = content['application/json'].get('schema', {})
                    # For simplicity, treat request body as dict
                    params.append("data: Optional[Dict[str, Any]] = None")
                    param_docs.append("        data: Request body data")
            
            # Always add context parameter
            params.append("ctx: Optional[Context] = None")
            
            # Generate function
            params_str = ", ".join(params) if params else ""
            
            # Use AI-generated description and docstring if available
            if func_info and func_info.tool_description:
                tool_desc = func_info.tool_description
            else:
                tool_desc = endpoint.summary or endpoint.description or f"{endpoint.method} {endpoint.path}"
            
            code += f'''@mcp.tool()
async def {func_name}({params_str}) -> Dict[str, Any]:
    """
    {tool_desc}
    
    Endpoint: {endpoint.method} {endpoint.path}
'''
            
            if param_docs:
                code += '\n    Args:\n'
                code += '\n'.join(param_docs) + '\n'
                
            code += f'''    """
    if ctx:
        ctx.info(f"Calling {endpoint.method} {endpoint.path}")
    
'''
            
            # Build request parameters
            # Path parameters
            path = endpoint.path
            path_params = []
            query_params = []
            
            for param in endpoint.parameters:
                param_name = to_snake_case(param.get('name', ''))
                if param.get('in') == 'path':
                    path = path.replace(f"{{{param.get('name')}}}", f"{{{param_name}}}")
                    path_params.append(param_name)
                elif param.get('in') == 'query':
                    query_params.append(param_name)
            
            # Format the path
            if path_params:
                code += f'    endpoint = f"{path}"\n'
            else:
                code += f'    endpoint = "{path}"\n'
                
            # Build query parameters
            if query_params:
                code += '    \n    params = {}\n'
                for qp in query_params:
                    code += f'    if {qp} is not None:\n'
                    code += f'        params["{qp}"] = {qp}\n'
                code += '    \n'
            else:
                code += '    params = None\n'
                
            # Add request body
            if 'data' in params_str:
                code += '    json_data = data\n'
            else:
                code += '    json_data = None\n'
                
            code += f'''    
    return await make_api_request(
        method="{endpoint.method}",
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        ctx=ctx
    )


'''

    # Add resources section (commented out due to FastMCP URI validation issues)
    code += f'''# Resources
# Note: Resources are temporarily disabled due to FastMCP URI validation issues
# @mcp.resource("config")
# async def get_api_config(ctx: Optional[Context] = None) -> str:
#     """Get the API configuration and available endpoints"""
#     return """
# This tool was auto-generated from an OpenAPI specification.
# Base URL: {base_url}
# Total endpoints: {len(endpoints)}
# Use the tool functions to interact with the API.
# """


'''

    # Add prompts section
    code += f'''# Prompts
@mcp.prompt()
def api_explorer(endpoint: str = "") -> str:
    """Generate a prompt for exploring {tool_name} API endpoints"""
    if endpoint:
        return f"""
Help me explore the {{endpoint}} endpoint of {tool_name} API.
What parameters does it accept and what does it return?
"""
    else:
        return f"""
What endpoints are available in the {tool_name} API?
List the main operations I can perform.
"""


'''

    # Add standard tool functions
    code += f'''# Tool creation functions (required by automagik-tools)
def create_tool(tool_config: Optional[{tool_name_class}Config] = None) -> FastMCP:
    """Create the MCP tool instance"""
    global config
    config = tool_config or {tool_name_class}Config()
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
        "{tool_name_lower.upper()}_BASE_URL": "Base URL for the API (optional)",
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

    return code


def generate_config_code(tool_name_class: str, tool_name_lower: str, base_url: str) -> str:
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
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="{tool_name_lower.upper()}_TIMEOUT"
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
        timeout=10
    )


@pytest.fixture
def tool_instance(mock_config):
    """Create a tool instance with mock config"""
    return create_tool(mock_config)


@pytest.fixture
def mock_context():
    """Create a mock context"""
    ctx = MagicMock(spec=Context)
    ctx.info = MagicMock()
    ctx.error = MagicMock()
    return ctx


class TestToolCreation:
    """Test tool creation and metadata"""
    
    @pytest.mark.unit
    def test_create_tool(self, mock_config):
        """Test that tool can be created"""
        tool = create_tool(mock_config)
        assert tool is not None
        assert tool.name == "{tool_name}"
    
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
    
    @pytest.mark.unit
    def test_required_env_vars(self):
        """Test required environment variables"""
        env_vars = get_required_env_vars()
        assert "{tool_name_lower.upper()}_API_KEY" in env_vars
        assert "{tool_name_lower.upper()}_BASE_URL" in env_vars


class TestToolFunctions:
    """Test individual tool functions"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_has_functions(self, tool_instance):
        """Test that tool has registered functions"""
        # Get tool handlers
        handlers = tool_instance._tool_handlers
        assert len(handlers) > 0, "Tool should have at least one function"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_has_resources(self, tool_instance):
        """Test that tool has resources"""
        resources = tool_instance._resource_handlers
        assert len(resources) > 0, "Tool should have at least one resource"


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.unit
    def test_tool_without_config(self):
        """Test tool creation without config uses defaults"""
        tool = create_tool()
        assert tool is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_error_handling(self, tool_instance, mock_context):
        """Test API error handling"""
        # This would test specific tool functions
        # Since we don't know the exact functions, this is a placeholder
        pass


class TestMCPProtocol:
    """Test MCP protocol compliance"""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_tool_list(self, tool_instance):
        """Test MCP tools/list"""
        tools = await tool_instance.list_tools()
        assert len(tools) > 0
        
        # Check first tool structure
        first_tool = tools[0]
        assert "name" in first_tool
        assert "description" in first_tool
        assert "inputSchema" in first_tool
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_resource_list(self, tool_instance):
        """Test MCP resources/list"""
        resources = await tool_instance.list_resources()
        assert len(resources) > 0
        
        # Check resource structure
        first_resource = resources[0]
        assert "uri" in first_resource
        assert "name" in first_resource
'''


def generate_readme(tool_name: str, tool_description: str, base_url: str, 
                   endpoints: List[OpenAPIEndpoint]) -> str:
    """Generate README documentation"""
    
    # Group endpoints by tag
    endpoints_by_tag = {}
    for endpoint in endpoints:
        tag = endpoint.tags[0] if endpoint.tags else 'default'
        if tag not in endpoints_by_tag:
            endpoints_by_tag[tag] = []
        endpoints_by_tag[tag].append(endpoint)
    
    readme = f'''# {tool_name} MCP Tool

{tool_description}

This tool was auto-generated from an OpenAPI specification.

## Features

- Full API integration with {tool_name}
- Automatic authentication handling
- Comprehensive error handling
- Type-safe parameter validation
- Async/await support

## Configuration

### Required Environment Variables

```bash
# API authentication key
{tool_name.upper().replace(' ', '_')}_API_KEY=your-api-key-here

# Base URL for the API (optional, defaults to {base_url})
{tool_name.upper().replace(' ', '_')}_BASE_URL={base_url}

# Request timeout in seconds (optional, defaults to 30)
{tool_name.upper().replace(' ', '_')}_TIMEOUT=30
```

## Available Operations

'''
    
    # Document endpoints by tag
    for tag, tag_endpoints in endpoints_by_tag.items():
        if tag != 'default':
            readme += f'\n### {tag.title()}\n\n'
        
        for endpoint in tag_endpoints[:10]:  # Limit to first 10 per tag
            func_name = sanitize_function_name(endpoint.operation_id)
            readme += f'- **{func_name}**: {endpoint.summary or endpoint.description or endpoint.path}\n'
            readme += f'  - Endpoint: `{endpoint.method} {endpoint.path}`\n'
            
    if len(endpoints) > 10:
        readme += f'\n... and {len(endpoints) - 10} more operations\n'
    
    readme += '''
## Usage

### With automagik-tools CLI

```bash
# List available tools
automagik-tools list

# Serve this specific tool
automagik-tools serve ''' + to_kebab_case(tool_name) + '''

# Serve all tools
automagik-tools serve-all
```

### In Python Code

```python
from automagik_tools.tools.''' + to_snake_case(tool_name) + ''' import create_server

# Create and run server
server = create_server()
# Server is now ready to handle MCP requests
```

## Development

### Running Tests

```bash
pytest tests/tools/test_''' + to_snake_case(tool_name) + '''.py -v
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @anthropic/mcp-inspector

# Run the tool in one terminal
automagik-tools serve ''' + to_kebab_case(tool_name) + '''

# In another terminal, connect with inspector
mcp-inspector stdio automagik-tools serve ''' + to_kebab_case(tool_name) + '''
```

## API Reference

This tool was generated from an OpenAPI specification. For detailed API documentation, please refer to the original API documentation.

## Troubleshooting

### Authentication Issues

If you're getting authentication errors:
1. Verify your API key is correctly set in the environment
2. Check that the API key has the necessary permissions
3. Ensure the base URL is correct for your API instance

### Connection Issues

If you're having connection problems:
1. Check your internet connection
2. Verify the base URL is accessible
3. Check if you're behind a proxy or firewall

## Contributing

This tool was auto-generated. To update it:
1. Obtain the latest OpenAPI specification
2. Re-run the generation script
3. Test the updated tool
4. Submit a pull request
'''
    
    return readme


@app.command()
def create(
    url: str = typer.Option(None, "--url", "-u", help="URL to OpenAPI JSON specification"),
    name: str = typer.Option(None, "--name", "-n", help="Tool name (e.g., 'GitHub API')"),
    description: str = typer.Option(None, "--description", "-d", help="Tool description"),
    output_dir: str = typer.Option(None, "--output", "-o", help="Output directory (defaults to automagik_tools/tools/)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing tool without prompting"),
    update: bool = typer.Option(False, "--update", "-U", help="Update existing tool, overwriting all files"),
    use_ai: bool = typer.Option(False, "--use-ai", help="Use AI to generate human-friendly function names and descriptions"),
    ai_model: str = typer.Option("gpt-4.1", "--ai-model", help="AI model to use for processing (gpt-4.1, gpt-4.1-nano)"),
    openai_key: Optional[str] = typer.Option(None, "--openai-key", help="OpenAI API key (uses OPENAI_API_KEY env var if not provided)"),
    use_streaming: bool = typer.Option(False, "--use-streaming", help="Use streaming processor for real-time progress (experimental)"),
):
    """Create a new tool from OpenAPI specification"""
    
    # Validate URL
    if not url:
        console.print("[red]Error: --url is required[/red]")
        raise typer.Exit(1)
    
    # Fetch OpenAPI spec
    console.print(f"[cyan]Fetching OpenAPI specification from:[/cyan] {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        spec = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error fetching OpenAPI spec:[/red] {str(e)}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing OpenAPI spec:[/red] {str(e)}")
        raise typer.Exit(1)
    
    # Parse OpenAPI spec
    parser = OpenAPIParser(spec)
    
    # Get tool name and description
    if not name:
        name = parser.info.get('title', 'API Tool')
    
    if not description:
        description = parser.info.get('description', parser.info.get('summary', f"MCP tool for {name} integration"))
    
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
    
    # Show API info
    endpoints = parser.get_endpoints()
    console.print(f"\n[cyan]API Information:[/cyan]")
    console.print(f"[dim]Base URL:[/dim] {parser.get_base_url()}")
    console.print(f"[dim]Endpoints:[/dim] {len(endpoints)}")
    console.print(f"[dim]Authentication:[/dim] {parser.get_auth_info().get('type', 'none')}")
    
    # Process with AI if requested
    ai_processed = None
    if use_ai:
        if not AI_PROCESSOR_AVAILABLE:
            console.print("[yellow]Warning: AI processor not available. Install 'agno' and 'openai' packages.[/yellow]")
        else:
            console.print(f"\n[cyan]Processing with AI ({ai_model})...[/cyan]")
            
            # Get API key - try multiple sources
            api_key = openai_key
            if not api_key:
                # Try environment variable
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Try reading from .env file directly
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv("OPENAI_API_KEY")
                except ImportError:
                    pass
            if not api_key:
                # Try reading .env manually
                try:
                    env_file = Path(".env")
                    if env_file.exists():
                        with open(env_file) as f:
                            for line in f:
                                if line.startswith("OPENAI_API_KEY="):
                                    api_key = line.split("=", 1)[1].strip()
                                    break
                except Exception:
                    pass
            
            if not api_key:
                console.print("[red]Error: OpenAI API key required for AI processing. Set OPENAI_API_KEY in .env or use --openai-key[/red]")
                raise typer.Exit(1)
            
            try:
                # Choose processor based on streaming option
                if use_streaming and STREAMING_PROCESSOR_AVAILABLE:
                    console.print("[cyan]Using streaming processor for real-time progress...[/cyan]")
                    processor = StreamingOpenAPIProcessor(model_id=ai_model, api_key=api_key)
                else:
                    # Use the StaticOpenAPIProcessor from the local script
                    processor = StaticOpenAPIProcessor(model_id=ai_model, api_key=api_key)
                
                # The method name should match what's in the processor
                if hasattr(processor, 'process_for_static_generation'):
                    ai_processed = processor.process_for_static_generation(
                        openapi_spec=spec,
                        tool_name=tool_name,
                        base_description=description
                    )
                else:
                    # Fallback if method doesn't exist
                    console.print("[yellow]Warning: AI processor method not found, using standard generation[/yellow]")
                    ai_processed = None
                
                console.print(f"[green]✓[/green] AI processing complete!")
                console.print(f"[dim]Generated {len(ai_processed.functions)} enhanced function definitions[/dim]")
                console.print(f"[dim]Categories: {', '.join(ai_processed.categories)}[/dim]")
                
            except Exception as e:
                console.print(f"[red]AI processing failed: {str(e)}[/red]")
                console.print("[yellow]Continuing with standard generation...[/yellow]")
    
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
    init_code = generate_tool_code(parser, tool_name, tool_name_lower, tool_name_class, tool_name_kebab, description, ai_processed)
    init_file = target_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write(init_code)
    console.print(f"[green]✓[/green] Created {init_file.relative_to(project_root)}")
    
    # Generate config.py
    config_code = generate_config_code(tool_name_class, tool_name_lower, parser.get_base_url())
    config_file = target_dir / "config.py"
    with open(config_file, "w") as f:
        f.write(config_code)
    console.print(f"[green]✓[/green] Created {config_file.relative_to(project_root)}")
    
    # Generate README.md
    readme_content = generate_readme(tool_name, description, parser.get_base_url(), endpoints[:20])
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
    
    # Update pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Add entry point
    entry_point_line = f'{tool_name_kebab} = "automagik_tools.tools.{tool_name_lower}:create_tool"'
    if entry_point_line not in content:
        # Find the entry points section
        pattern = r'(\[project\.entry-points\."automagik_tools\.plugins"\]\n)([^\[]*)'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            existing_entries = match.group(2).strip()
            new_entries = existing_entries + "\n" + entry_point_line
            content = content.replace(match.group(0), match.group(1) + new_entries + "\n")
            
            with open(pyproject_path, "w") as f:
                f.write(content)
            
            console.print(f"[green]✓[/green] Updated pyproject.toml")
    
    # Update CLI config reminder
    cli_path = project_root / "automagik_tools" / "cli.py"
    console.print(f"\n[yellow]Note:[/yellow] Add configuration class to {cli_path.relative_to(project_root)}:")
    console.print(f"\n[dim]from automagik_tools.tools.{tool_name_lower}.config import {tool_name_class}Config[/dim]")
    console.print(f"\n[dim]In create_config_for_tool():[/dim]")
    console.print(f"[dim]    elif tool_name == '{tool_name_kebab}':[/dim]")
    console.print(f"[dim]        return {tool_name_class}Config()[/dim]")
    
    # Update .env.example reminder
    console.print(f"\n[yellow]Note:[/yellow] Add configuration to .env.example:")
    console.print(f"\n[dim]# {tool_name} Configuration[/dim]")
    console.print(f"[dim]{tool_name_upper}_API_KEY=your-api-key-here[/dim]")
    console.print(f"[dim]{tool_name_upper}_BASE_URL={parser.get_base_url()}[/dim]")
    console.print(f"[dim]{tool_name_upper}_TIMEOUT=30[/dim]")
    
    # Summary
    console.print(f"\n[green]✨ Tool '{tool_name}' created successfully![/green]")
    console.print(f"\nGenerated {len(endpoints)} operations from OpenAPI spec")
    console.print(f"\nNext steps:")
    console.print(f"1. Review generated code in {target_dir.relative_to(project_root)}")
    console.print(f"2. Update the configuration class in {cli_path.name}")
    console.print(f"3. Add your configuration to .env file")
    console.print(f"4. Run tests: [dim]pytest {test_file.relative_to(project_root)} -v[/dim]")
    console.print(f"5. Test your tool: [dim]automagik-tools serve {tool_name_kebab}[/dim]")


if __name__ == "__main__":
    app()