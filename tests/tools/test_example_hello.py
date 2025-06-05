"""
Tests for the Example Hello Tool
"""

import pytest
from automagik_tools.tools.example_hello import create_tool


@pytest.mark.unit
def test_create_tool():
    """Test that the tool can be created successfully"""
    tool = create_tool()
    assert tool is not None
    assert tool.name == "Example Hello Tool"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_say_hello():
    """Test the say_hello function"""
    tool = create_tool()
    
    # Test with default parameter
    result = await tool._tool_handlers['say_hello']['handler']()
    assert result == "Hello, World! Welcome to automagik-tools!"
    
    # Test with custom name
    result = await tool._tool_handlers['say_hello']['handler'](name="Alice")
    assert result == "Hello, Alice! Welcome to automagik-tools!"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_numbers():
    """Test the add_numbers function"""
    tool = create_tool()
    
    result = await tool._tool_handlers['add_numbers']['handler'](a=5, b=3)
    assert result == 8
    
    result = await tool._tool_handlers['add_numbers']['handler'](a=-10, b=5)
    assert result == -5
    
    result = await tool._tool_handlers['add_numbers']['handler'](a=0, b=0)
    assert result == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_info_resource():
    """Test the info resource"""
    tool = create_tool()
    
    # Check that the resource is registered
    assert 'example://info' in tool._resource_handlers
    
    # Test getting the resource
    result = await tool._resource_handlers['example://info']['handler']()
    assert "minimal example MCP tool" in result
    assert "Use this as a template" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_example_usage_prompt():
    """Test the example usage prompt"""
    tool = create_tool()
    
    # Check that the prompt is registered
    assert 'example_usage' in tool._prompt_handlers
    
    # Test getting the prompt
    result = await tool._prompt_handlers['example_usage']['handler']()
    assert "say_hello(\"Alice\")" in result
    assert "add_numbers(5, 3)" in result
    assert "example://info" in result