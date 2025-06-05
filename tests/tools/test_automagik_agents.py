"""
Tests for Automagik Agents MCP tool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import Context

from automagik_tools.tools.automagik_agents import (
    create_tool,
    AutomagikAgentsConfig,
    get_metadata,
    get_config_class,
    get_config_schema,
    get_required_env_vars,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return AutomagikAgentsConfig(
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
        assert tool.name == "Automagik Agents"
    
    @pytest.mark.unit
    def test_metadata(self):
        """Test tool metadata"""
        metadata = get_metadata()
        assert metadata["name"] == "automagik-agents"
        assert "description" in metadata
        assert "version" in metadata
        assert metadata["config_env_prefix"] == "AUTOMAGIK_AGENTS_"
    
    @pytest.mark.unit
    def test_config_class(self):
        """Test config class retrieval"""
        config_class = get_config_class()
        assert config_class == AutomagikAgentsConfig
    
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
        assert "AUTOMAGIK_AGENTS_API_KEY" in env_vars
        assert "AUTOMAGIK_AGENTS_BASE_URL" in env_vars


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
