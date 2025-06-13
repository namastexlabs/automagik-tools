"""Validate automagik_workflows MCP compliance"""
import asyncio
from automagik_tools.tools.automagik_workflows import create_server, get_config_class

async def validate_mcp_compliance():
    """Validate MCP protocol compliance"""
    
    # Create server with test config
    config_class = get_config_class()
    config = config_class(api_key="test-key")
    server = create_server(config)
    
    # Test 1: Server has name and version
    assert hasattr(server, 'name'), "Server missing name"
    assert server.name == "AutoMagik Workflows", f"Expected 'AutoMagik Workflows', got '{server.name}'"
    print("✅ Server metadata valid")
    
    # Test 2: Tools are properly registered
    tools = await server.get_tools()
    assert len(tools) > 0, "No tools registered"
    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
    print(f"✅ Found {len(tools)} tools")
    
    # Test 3: Each tool has required fields
    expected_tools = ["run_workflow", "list_workflows", "list_recent_runs", "get_workflow_status"]
    for tool_name in expected_tools:
        assert tool_name in tools, f"Missing tool: {tool_name}"
        tool = tools[tool_name]
        assert hasattr(tool, 'name'), f"Tool {tool_name} missing name"
        assert hasattr(tool, 'description'), f"Tool {tool_name} missing description"
        assert hasattr(tool, 'fn'), f"Tool {tool_name} missing fn attribute"
        assert len(tool.description.strip()) > 0, f"Tool {tool_name} has empty description"
    print("✅ All tools have required fields")
    
    # Test 4: Resources (if any)
    try:
        resources = await server.get_resources()
        for resource in resources:
            assert hasattr(resource, 'uri'), "Resource missing URI"
            assert hasattr(resource, 'name'), "Resource missing name"
        print(f"✅ {len(resources)} resources validated")
    except AttributeError:
        # FastMCP may not have resources
        print("✅ No resources to validate (expected for tool-only server)")
    
    # Test 5: Server instructions
    assert hasattr(server, 'instructions'), "Server missing instructions"
    assert len(server.instructions.strip()) > 0, "Server instructions empty"
    assert "workflow orchestration" in server.instructions.lower(), "Instructions missing key content"
    print("✅ Server instructions validated")
    
    return True

if __name__ == "__main__":
    asyncio.run(validate_mcp_compliance())
    print("\n✅ MCP Protocol Compliance: PASSED")