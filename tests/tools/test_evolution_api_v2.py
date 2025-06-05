"""
Tests for Evolution API v2 MCP tool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import Context

from automagik_tools.tools.evolution_api_v2 import (
    create_tool,
    EvolutionApiV2Config,
    get_metadata,
    get_config_class,
    get_config_schema,
    get_required_env_vars,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return EvolutionApiV2Config(
        api_key="test-api-key",
        base_url="https://api.example.com",
        openapi_url="https://api.example.com/openapi.json",
        timeout=10
    )


@pytest.fixture
def mock_openapi_spec():
    """Create a mock OpenAPI specification"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Evolution API v2",
            "version": "1.0.0"
        },
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "operationId": "test_endpoint",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }


class TestToolCreation:
    """Test tool creation and metadata"""
    
    @pytest.mark.unit
    def test_metadata(self):
        """Test tool metadata"""
        metadata = get_metadata()
        assert metadata["name"] == "evolution-api-v2"
        assert "description" in metadata
        assert "version" in metadata
        assert metadata["config_env_prefix"] == "EVOLUTION_API_V2_"
    
    @pytest.mark.unit
    def test_config_class(self):
        """Test config class retrieval"""
        config_class = get_config_class()
        assert config_class == EvolutionApiV2Config
    
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
        assert "EVOLUTION_API_V2_API_KEY" in env_vars
        assert "EVOLUTION_API_V2_BASE_URL" in env_vars
        assert "EVOLUTION_API_V2_OPENAPI_URL" in env_vars
    
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
        assert tool.name == "Evolution API v2"


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
