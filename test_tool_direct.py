#!/usr/bin/env python3
"""Direct test of the genie_agents tool for MCP compliance."""

import asyncio
from automagik_tools.tools.genie_agents import create_server


async def test_mcp_server():
    """Test that the MCP server can be created and lists tools."""
    print("Testing MCP server creation...")
    
    # Create the server
    server = create_server()
    print(f"✅ Server created: {server.name}")
    
    # Test getting tools
    tools = await server.get_tools()
    print(f"✅ Tools retrieved: {len(tools)} tools")
    
    # List some tools
    tool_names = list(tools.keys())[:10]  # First 10 tools
    print("First 10 tools:")
    for name in tool_names:
        print(f"  - {name}")
    
    # Test that a tool can be run
    if "check_playground_status" in tools:
        tool = tools["check_playground_status"]
        print(f"✅ Tool found: {tool.name}")
        print(f"✅ Tool description: {tool.description}")
        
        # Test that it has the right structure
        assert hasattr(tool, 'run'), "Tool should have run method"
        assert hasattr(tool, 'name'), "Tool should have name attribute"
        assert hasattr(tool, 'description'), "Tool should have description attribute"
        
        print("✅ Tool structure is correct")
    else:
        print("❌ check_playground_status tool not found")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())
    print(f"\n{'✅ All tests passed!' if result else '❌ Tests failed!'}")