"""
Tests for teste Tool
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from automagik_tools.tools.teste import create_tool


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    config = Mock()
    config.api_key = "test-api-key"
    config.base_url = "https://api.example.com"
    config.timeout = 30
    return config


@pytest.fixture
def tool(mock_config):
    """Create a tool instance with mock configuration"""
    return create_tool(mock_config)


@pytest.mark.unit
def test_create_tool(mock_config):
    """Test that the tool can be created successfully"""
    tool = create_tool(mock_config)
    assert tool is not None
    assert tool.name == "teste"


@pytest.mark.unit
def test_create_tool_without_config():
    """Test tool creation without configuration"""
    tool = create_tool(None)
    assert tool is not None
    # Tool should still be created but may have limited functionality


@pytest.mark.unit
@pytest.mark.asyncio
async def test_your_main_action(tool):
    """Test the main action functionality"""
    # Test basic functionality
    result = await tool._tool_handlers['your_main_action']['handler'](
        required_param="test"
    )
    assert result["status"] == "success"
    assert "test" in result["message"]
    assert result["optional"] is None
    
    # Test with optional parameter
    result = await tool._tool_handlers['your_main_action']['handler'](
        required_param="test",
        optional_param="optional"
    )
    assert result["optional"] == "optional"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_your_main_action_with_api_call(tool, mock_httpx_client):
    """Test main action with mocked API call"""
    # Mock the API response
    mock_response = {
        "status": "success",
        "data": {"id": "123", "result": "processed"}
    }
    mock_httpx_client.request.return_value.json.return_value = mock_response
    mock_httpx_client.request.return_value.raise_for_status = Mock()
    
    # Uncomment and modify when implementing actual API calls
    # with patch('httpx.AsyncClient') as mock_client:
    #     mock_client.return_value.__aenter__.return_value = mock_httpx_client
    #     
    #     result = await tool._tool_handlers['your_main_action']['handler'](
    #         required_param="test"
    #     )
    #     
    #     assert result["status"] == "success"
    #     mock_httpx_client.request.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_your_secondary_action(tool):
    """Test the secondary action"""
    result = await tool._tool_handlers['your_secondary_action']['handler'](
        param1="hello",
        param2=42
    )
    assert result == "Processed hello with value 42"
    
    # Test with default parameter
    result = await tool._tool_handlers['your_secondary_action']['handler'](
        param1="world"
    )
    assert result == "Processed world with value 10"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_resource(tool):
    """Test the status resource"""
    result = await tool._resource_handlers['teste://status']['handler']()
    assert result["tool"] == "teste"
    assert result["status"] == "operational"
    assert result["configured"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_config_resource(tool, mock_config):
    """Test the config resource"""
    result = await tool._resource_handlers['teste://config']['handler']()
    assert result["base_url"] == mock_config.base_url
    assert result["timeout"] == mock_config.timeout
    assert result["has_api_key"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompts(tool):
    """Test that prompts are registered and return content"""
    # Test setup guide
    assert 'setup_guide' in tool._prompt_handlers
    setup_content = await tool._prompt_handlers['setup_guide']['handler']()
    assert "teste" in setup_content
    assert "API key" in setup_content
    
    # Test usage examples
    assert 'usage_examples' in tool._prompt_handlers
    usage_content = await tool._prompt_handlers['usage_examples']['handler']()
    assert "your_main_action" in usage_content
    assert "example" in usage_content.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_handling(tool):
    """Test error handling in the tool"""
    # Test with missing configuration
    tool_no_config = create_tool(None)
    
    # This should handle the missing config gracefully
    # Modify based on your actual error handling implementation
    with pytest.raises(ValueError):
        # Simulate an action that requires config
        pass  # Replace with actual test


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_mcp_protocol_compliance(tool):
    """Test that the tool follows MCP protocol standards"""
    # Test that all handlers are properly registered
    assert len(tool._tool_handlers) >= 2
    assert len(tool._resource_handlers) >= 2
    assert len(tool._prompt_handlers) >= 2
    
    # Test that handlers have required metadata
    for handler_name, handler_info in tool._tool_handlers.items():
        assert 'handler' in handler_info
        assert callable(handler_info['handler'])
        # Add more MCP compliance checks as needed