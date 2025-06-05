# 🛠️ Tool Development Guide

Welcome to the Automagik Tools development guide! This repository makes it **trivially easy** to add new MCP tools that are automatically discovered and integrated.

## 🚀 Quick Start: Add a New Tool in 5 Minutes

### 1. Create Your Tool Directory

```bash
mkdir -p automagik_tools/tools/my_awesome_tool
cd automagik_tools/tools/my_awesome_tool
```

### 2. Create Required Files

Every tool needs these 4 files:

#### `__init__.py` - Main tool implementation
```python
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from .config import MyAwesomeToolConfig

def get_metadata() -> Dict[str, Any]:
    """Required: Tool metadata for discovery"""
    return {
        "name": "my-awesome-tool",
        "version": "1.0.0",
        "description": "Does awesome things",
        "author": "Your Name",
        "category": "productivity",
        "tags": ["awesome", "tool", "example"]
    }

def get_config_class():
    """Required: Return configuration class"""
    return MyAwesomeToolConfig

def create_server(config: Optional[MyAwesomeToolConfig] = None):
    """Required: Create FastMCP server instance"""
    if config is None:
        config = MyAwesomeToolConfig()
    
    mcp = FastMCP(
        name="My Awesome Tool",
        instructions="Use this tool to do awesome things"
    )
    
    @mcp.tool(
        annotations={
            "readOnlyHint": True,      # Doesn't modify state
            "destructiveHint": False,   # Not destructive
            "openWorldHint": False,     # Doesn't call external APIs
        }
    )
    async def do_something_awesome(input: str) -> str:
        """Do something awesome with the input"""
        return f"Awesome result: {input.upper()}"
    
    return mcp

# Legacy support
create_tool = create_server
```

#### `config.py` - Tool configuration
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class MyAwesomeToolConfig(BaseSettings):
    """Configuration for My Awesome Tool"""
    # Add any configuration your tool needs
    api_key: str = Field(default="", description="API key if needed")
    timeout: int = Field(default=30, description="Timeout in seconds")
    
    model_config = {
        "env_prefix": "MY_AWESOME_TOOL_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
```

#### `__main__.py` - Standalone execution
```python
#!/usr/bin/env python
"""Run My Awesome Tool standalone"""

import sys
import argparse
from . import run_standalone, get_metadata

def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata['description']
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    args = parser.parse_args()
    run_standalone(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
```

#### `README.md` - Tool documentation
```markdown
# My Awesome Tool

Does awesome things via MCP protocol.

## Configuration

Set these environment variables:
- `MY_AWESOME_TOOL_API_KEY` - API key (if needed)
- `MY_AWESOME_TOOL_TIMEOUT` - Timeout in seconds

## Usage

```bash
# Run standalone
python -m automagik_tools.tools.my_awesome_tool

# Or use the hub
make fastmcp-hub
```
```

### 3. Register in pyproject.toml (Optional but Recommended)

Add your tool to the entry points in `pyproject.toml`:

```toml
[project.entry-points."automagik_tools.plugins"]
my-awesome-tool = "automagik_tools.tools.my_awesome_tool:create_tool"
```

### 4. That's It! 🎉

Your tool is now:
- ✅ Automatically discovered by the hub
- ✅ Available in `automagik-tools list`
- ✅ Mountable via FastMCP
- ✅ Runnable standalone
- ✅ Testable with FastMCP Client

## 🔍 How Auto-Discovery Works

The hub server (`automagik_tools/servers/hub.py`) automatically:

1. **Scans entry points** - Looks for registered tools in `pyproject.toml`
2. **Scans directory** - Finds all folders in `tools/` directory
3. **Validates tools** - Checks for required functions
4. **Mounts tools** - Adds each tool with its own prefix
5. **Handles config** - Creates configuration from environment

**No manual registration needed!** Just drop your tool in the `tools/` directory.

## 📋 Tool Requirements Checklist

Your tool MUST have these functions in `__init__.py`:

- [ ] `get_metadata()` - Returns tool information
- [ ] `get_config_class()` - Returns configuration class
- [ ] `create_server(config)` - Creates FastMCP server

Optional but recommended:

- [ ] `get_config_schema()` - Returns JSON schema
- [ ] `get_required_env_vars()` - Lists required environment variables
- [ ] `run_standalone()` - Enables standalone execution

## 🎨 Best Practices

### 1. Use Annotations
```python
@mcp.tool(
    annotations={
        "readOnlyHint": False,     # This modifies data
        "destructiveHint": True,   # This deletes data
        "openWorldHint": True,     # This calls external APIs
    }
)
```

### 2. Handle Errors Gracefully
```python
try:
    result = await external_api_call()
except Exception as e:
    if ctx:
        await ctx.error(f"API call failed: {str(e)}")
    raise ToolError(f"Failed to complete operation: {str(e)}")
```

### 3. Use Context for Logging
```python
async def my_tool(input: str, ctx: Context = None):
    if ctx:
        await ctx.info("Starting operation...")
        await ctx.progress(0.5, "Halfway done...")
    # Do work
    if ctx:
        await ctx.info("Operation completed!")
```

### 4. Make Configuration Optional
```python
class MyToolConfig(BaseSettings):
    api_key: str = Field(default="", description="Optional API key")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
```

## 🧪 Testing Your Tool

Create `tests/tools/test_my_awesome_tool.py`:

```python
import pytest
from fastmcp import Client
from automagik_tools.tools.my_awesome_tool import create_server, MyAwesomeToolConfig

@pytest.fixture
async def client():
    config = MyAwesomeToolConfig(api_key="test")
    server = create_server(config)
    async with Client(server) as client:
        yield client

async def test_do_something_awesome(client):
    result = await client.call_tool(
        "do_something_awesome",
        {"input": "hello"}
    )
    assert "HELLO" in result[0].text
```

## 🚀 Advanced Features

### Resource Providers
```python
@mcp.resource("mytool://data/{id}")
async def get_data(id: str) -> str:
    """Provide data resources"""
    return f"Data for {id}"
```

### Prompt Templates
```python
@mcp.prompt()
async def example_prompt(task: str) -> str:
    """Generate prompts for common tasks"""
    return f"Help me {task} using My Awesome Tool"
```

### Complex Types with Pydantic
```python
class ComplexInput(BaseModel):
    items: List[str]
    options: Dict[str, Any]
    
@mcp.tool()
async def process_complex(data: ComplexInput) -> Dict[str, Any]:
    """Process complex structured data"""
    return {"processed": len(data.items)}
```

## 🎯 Examples to Study

Look at these existing tools for inspiration:

1. **evolution_api** - External API integration with auth
2. **example_hello** - Minimal tool structure

## 🆘 Troubleshooting

### Tool Not Discovered?

Check:
1. Tool has `get_metadata()`, `get_config_class()`, `create_server()`
2. No Python syntax errors
3. Tool directory name matches metadata name

### Configuration Issues?

1. Check environment variable prefix matches `env_prefix`
2. Use `.env` file for development
3. Run `make info TOOL=my-awesome-tool` to see config

### Testing Problems?

1. Use `fastmcp dev` for interactive testing
2. Check logs with `make logs FOLLOW=1`
3. Validate with `uv run automagik-tools info my-awesome-tool`

## 🎉 Congratulations!

You've added a new tool to the Automagik Tools ecosystem! Your tool is now:
- Automatically discovered
- Available to all users
- Part of the largest MCP tool collection

Share your tool with the community and help make MCP development truly automagik! 🪄