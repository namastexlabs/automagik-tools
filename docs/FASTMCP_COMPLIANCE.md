# FastMCP Compliance Guide

This document describes the FastMCP patterns implemented in automagik-tools to ensure full compliance with FastMCP best practices.

## 🎯 Compliance Overview

### ✅ Implemented Patterns

1. **Tool Annotations**
   - All tools now include proper annotations (`readOnlyHint`, `destructiveHint`, `openWorldHint`)
   - Helps LLMs understand tool behavior and safety characteristics
   - Example: Delete operations marked as `destructiveHint: true`

2. **FastMCP Client Testing**
   - New test file `test_fastmcp_client.py` uses FastMCP's `Client` class
   - In-memory testing without process management
   - Clean async patterns with proper fixtures

3. **Server Composition with mount()**
   - Created `automagik_tools/servers/hub.py` demonstrating proper composition
   - Tools are mounted with prefixes (e.g., `/evolution/*`, `/hello/*`)
   - Automatic lifespan coordination

4. **FastMCP CLI Integration**
   - Direct server files in `automagik_tools/servers/`
   - Can run with `fastmcp run` command
   - Support for `fastmcp dev` with MCP Inspector

5. **Hidden Parameters**
   - Configuration is stored at module level
   - Tools don't expose internal `config` parameter to LLMs
   - Cleaner tool signatures

## 📁 New Structure

```
automagik_tools/
├── servers/              # FastMCP server implementations
│   ├── __init__.py
│   ├── hub.py           # Main hub using mount()
│   ├── evolution_api.py # Standalone Evolution API
│   └── example_hello.py # Standalone Example Hello
└── tools/               # Tool implementations (unchanged)
    ├── evolution_api/
    └── example_hello/
```

## 🚀 Usage Examples

### Using FastMCP CLI

```bash
# Run the hub server (all tools)
fastmcp run automagik_tools.servers.hub:hub

# Run individual tools
fastmcp run automagik_tools.servers.evolution_api:mcp
fastmcp run automagik_tools.servers.example_hello:mcp

# Development with MCP Inspector
fastmcp dev automagik_tools.servers.hub:hub
```

### Using Make Commands

```bash
# Standard commands (recommended)
make serve-all              # Run hub server with all tools
make serve TOOL=evolution-api  # Run Evolution API only
make serve TOOL=example-hello  # Run Example Hello only
make watch                  # Run with auto-restart on changes
```

### Testing with FastMCP Client

```python
from fastmcp import Client
from automagik_tools.tools.evolution_api import create_server

async def test_with_client():
    server = create_server(config)
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        
        # Call a tool
        result = await client.call_tool(
            "send_text_message",
            {"instance": "test", "number": "+123", "text": "Hi"}
        )
```

## 🔧 Tool Annotations

All tools now include semantic hints:

```python
@mcp.tool(
    annotations={
        "readOnlyHint": True,      # Doesn't modify state
        "destructiveHint": False,   # Not destructive
        "openWorldHint": True,      # Makes external API calls
    }
)
async def get_instance_info(...):
    """Get information about a WhatsApp instance"""
```

## 🧪 Testing Improvements

The new `test_fastmcp_client.py` demonstrates:
- Proper client fixtures
- Testing tool discovery
- Verifying annotations
- Mocking external calls
- Resource and prompt testing

## 🎨 Benefits

1. **Better LLM Understanding**: Annotations help AI agents use tools more safely
2. **Cleaner Testing**: FastMCP Client simplifies test setup
3. **Proper Composition**: Mount pattern enables modular tool organization
4. **Native CLI Support**: Direct integration with `fastmcp` command
5. **Hidden Complexity**: Internal parameters don't confuse LLMs

## 🔄 Migration Notes

The existing CLI still works for backward compatibility:
- `automagik-tools serve` - Legacy single tool mode
- `automagik-tools serve-all` - Legacy multi-tool mode

New FastMCP-native alternatives:
- `fastmcp run automagik_tools.servers.hub:hub` - Composed server
- `fastmcp dev` - Development with inspector

## 🚦 Next Steps

1. Gradually migrate all tests to use FastMCP Client
2. Add more semantic annotations as needed
3. Explore custom tool serializers for complex types
4. Consider using FastMCP's configuration patterns
5. Implement proper error handling with `ToolError`

This compliance work ensures automagik-tools follows FastMCP best practices while maintaining backward compatibility.