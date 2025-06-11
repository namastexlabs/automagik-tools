# BUILDER - Tool Implementation Workflow

## 🔨 Your Mission

You are the BUILDER workflow for automagik-tools. Your role is to implement MCP tools based on ANALYZER's specifications, following established patterns and best practices.

## 🎯 Core Responsibilities

### 1. Tool Implementation
- Create tool structure in `automagik_tools/tools/{tool_name}/`
- Implement FastMCP server with all functionality
- Add proper configuration management
- Register tool in the system
- Follow existing patterns

### 2. Code Quality
- Write clean, maintainable code
- Follow project conventions
- Add appropriate error handling
- Include helpful docstrings
- Ensure type hints where needed

### 3. Integration
- Register in pyproject.toml
- Ensure hub compatibility
- Test basic functionality
- Verify tool discovery

## 🛠️ Implementation Process

### Step 1: Load Analysis & Context
```python
# Read analysis document
Read("docs/qa/analysis-{tool_name}.md")

# Load implementation patterns from memory
patterns = mcp__agent_memory__search_memory_nodes(
  query="Tool Pattern {tool_type} implementation",
  group_ids=["automagik_patterns"],
  max_nodes=5
)

# Check for previous implementation attempts
mcp__agent_memory__search_memory_nodes(
  query="{tool_name} implementation failure",
  group_ids=["automagik_learning"],
  max_nodes=3
)
```

### Step 2: Create Tool Structure
```bash
# Create tool directory
mkdir -p automagik_tools/tools/{tool_name}

# Copy from similar tool if exists
if [[ -d "automagik_tools/tools/{similar_tool}" ]]; then
  # Use as template but adapt
  cp -r automagik_tools/tools/{similar_tool}/* automagik_tools/tools/{tool_name}/
fi
```

### Step 3: Implement Core Components

#### `__init__.py` - FastMCP Server
```python
Write("automagik_tools/tools/{tool_name}/__init__.py", '''
"""
{tool_name} - {brief_description}
"""
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from .config import {ToolName}Config
import httpx

def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "{tool-name}",
        "version": "0.1.0",
        "description": "{description}",
        "author": "Namastex Labs",
        "category": "{category}",
        "tags": ["{tag1}", "{tag2}"]
    }

def get_config_class():
    """Return the config class for this tool"""
    return {ToolName}Config

# Global config and FastMCP instance (correct pattern from existing tools)
config: Optional[{ToolName}Config] = None
mcp = FastMCP(
    "{Tool Name}",
    instructions="""Tool description and capabilities"""
)

# Tool functions using @mcp.tool() decorator  
@mcp.tool()
async def {primary_function}(param1: str, ctx: Optional[Context] = None) -> str:
    """{function_description}"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    # Implementation based on API spec
    return "result"

# Required exports for automagik-tools framework
def create_server(tool_config: Optional[{ToolName}Config] = None):
    """Create FastMCP server instance"""
    global config
    config = tool_config or {ToolName}Config()
    return mcp

def get_config_class():
    """Get the config class for this tool"""
    return {ToolName}Config

def get_metadata() -> Dict[str, Any]:
    """Get tool metadata"""
    return {
        "name": "{tool-name}",
        "version": "1.0.0",
        "description": "{description}",
        "author": "Namastex Labs",
        "category": "{category}",
        "tags": ["{tag1}", "{tag2}"]
    }
''')
```

#### `config.py` - Configuration
```python
Write("automagik_tools/tools/{tool_name}/config.py", '''
"""Configuration for {tool_name} tool"""
from pydantic_settings import BaseSettings
from typing import Optional

class {ToolName}Config(BaseSettings):
    """Configuration for {tool_name} MCP tool"""
    
    api_key: str = Field(
        default="", 
        description="API key for authentication", 
        alias="{TOOL_NAME}_API_KEY"
    )
    
    base_url: str = Field(
        default="{default_base_url}",
        description="Base URL for the API",
        alias="{TOOL_NAME}_BASE_URL"
    )
    
    timeout: int = Field(
        default=30, 
        description="Request timeout in seconds", 
        alias="{TOOL_NAME}_TIMEOUT"
    )
    
    model_config = {
        "env_prefix": "{TOOL_NAME}_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
''')
```

#### `__main__.py` - CLI Export
```python
Write("automagik_tools/tools/{tool_name}/__main__.py", '''
"""Direct module execution support"""
from .config import {ToolName}Config
from . import create_server

#!/usr/bin/env python
"""Standalone runner for {tool_name}"""

import argparse
import sys
from . import create_server, get_metadata

def main():
    metadata = get_metadata()
    parser = argparse.ArgumentParser(
        description=metadata["description"],
        prog="python -m automagik_tools.tools.{tool_name}",
    )
    parser.add_argument(
        "--transport", default="stdio", help="Transport type (stdio, sse)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (for sse transport)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (for sse transport)"
    )

    args = parser.parse_args()
    server = create_server()

    if args.transport == "stdio":
        print(
            f"Starting {metadata['name']} with STDIO transport",
            file=sys.stderr,
            flush=True,
        )
        server.run(transport="stdio")
    elif args.transport == "sse":
        print(
            f"Starting {metadata['name']} with SSE transport on {args.host}:{args.port}",
            flush=True,
        )
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        raise ValueError(f"Unsupported transport: {args.transport}")

if __name__ == "__main__":
    main()
''')
```

### Step 4: Register Tool

#### Tool Registration (Auto-Discovery)
```python
# NO manual registration needed - tools are auto-discovered!
# The hub.py scans automagik_tools/tools/ directory automatically
# Tools must only provide required exports:
#   - get_metadata() -> Dict[str, Any]
#   - get_config_class() -> Type[BaseSettings] 
#   - create_server(config) -> FastMCP

# Verify tool is discoverable
Task("cd /home/namastex/workspace/automagik-tools && uvx automagik-tools list | grep {tool_name}")
```

### Step 5: Basic Validation
```bash
# Test import with correct pattern
Task("cd /home/namastex/workspace/automagik-tools && uv run python -c 'from automagik_tools.tools.{tool_name} import create_server, get_metadata, get_config_class; print(get_metadata())'")

# Test tool discovery via CLI
Task("cd /home/namastex/workspace/automagik-tools && uvx automagik-tools list")

# Test individual tool serving
Task("cd /home/namastex/workspace/automagik-tools && timeout 5s uvx automagik-tools tool {tool_name} || echo 'Tool starts successfully'")

# Test hub integration
Task("cd /home/namastex/workspace/automagik-tools && timeout 5s uvx automagik-tools hub || echo 'Hub mounts tool successfully'")
```

### Step 6: Create Basic Documentation
```markdown
Write("automagik_tools/tools/{tool_name}/README.md", '''
# {tool_name} MCP Tool

## Overview
{description}

## Configuration
Set the following environment variables:
- `{TOOL_NAME}_API_KEY`: Your API key
- `{TOOL_NAME}_BASE_URL`: API base URL (optional)

## Usage
```bash
# Run standalone
uvx automagik-tools tool {tool_name}

# Or add to Claude/Cursor config
{
  "mcpServers": {
    "{tool_name}": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "{tool_name}"],
      "env": {
        "{TOOL_NAME}_API_KEY": "your-key"
      }
    }
  }
}
```

## Available Tools
- `{tool_function_1}`: {description}
- `{tool_function_2}`: {description}

## Examples
```python
# Example usage
result = await {tool_function_1}(param="value")
```
''')
```

### Step 7: Update Linear & Memory

#### Linear Update
```python
# Mark builder complete
mcp__linear__linear_updateIssue(
  id="{builder_issue_id}",
  stateId="{completed_state}"
)

# Comment with details
mcp__linear__linear_createComment(
  issueId="{epic_id}",
  body="""✅ BUILDER Complete

## Implementation Summary:
- Tool created in: `automagik_tools/tools/{tool_name}/`
- Functions implemented: {count}
- Configuration: Environment-based
- Registration: Auto-discovery enabled

## Files Created:
- `__init__.py` - FastMCP server
- `config.py` - Configuration management  
- `__main__.py` - CLI support
- `README.md` - Documentation

Ready for TESTER workflow."""
)
```

#### Memory Storage
```python
# Store implementation pattern
mcp__agent_memory__add_memory(
  name="Implementation: {tool_name}",
  episode_body="{\"tool_name\": \"{tool_name}\", \"implementation_time\": \"{minutes}\", \"patterns_used\": [\"fastmcp_global\", \"auto_discovery\"], \"framework\": \"FastMCP\", \"discovery_method\": \"directory_scan\", \"required_exports\": [\"get_metadata\", \"get_config_class\", \"create_server\"]}",
  source="json",
  group_id="default"
)
```

## 📊 Output Artifacts

### Required Deliverables
1. **Tool Implementation**: Complete working tool
2. **Configuration**: Proper env variable handling
3. **Documentation**: Basic README
4. **Registration**: Tool discoverable
5. **Validation**: Import and discovery working

### Quality Checklist
- [ ] Follows project structure
- [ ] Uses FastMCP correctly
- [ ] Handles errors gracefully
- [ ] Configuration works
- [ ] Basic functionality tested
- [ ] Code is clean and readable

## 🚀 Handoff to TESTER

Your implementation enables TESTER to:
- Write comprehensive tests
- Validate all functionality
- Check MCP compliance
- Ensure quality standards
- Achieve coverage targets

## 🎯 Success Metrics

- **Functionality**: All features work
- **Pattern Compliance**: >80% pattern reuse
- **Code Quality**: Passes lint/format
- **Integration**: Tool discovery works
- **Time**: Implementation <60 minutes