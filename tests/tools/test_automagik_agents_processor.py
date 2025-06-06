"""
Tests for the AI-powered OpenAPI processor in automagik.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from automagik_tools.tools.automagik.agent_processor import (
    ToolInfo,
    ProcessedOpenAPITools,
    OpenAPIProcessor,
    create_intelligent_name_mappings
)


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI spec for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "description": "A test API for validating AI processing",
            "version": "1.0.0"
        },
        "paths": {
            "/api/v1/users/{user_id}/sessions/{session_id}/messages": {
                "get": {
                    "operationId": "get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get",
                    "summary": "Get messages for a user session",
                    "tags": ["messages", "sessions"]
                }
            },
            "/api/v1/mcp_servers/{server_name}/restart": {
                "post": {
                    "operationId": "restart_mcp_server_api_v1_mcp_servers__server_name__restart_post",
                    "summary": "Restart an MCP server",
                    "tags": ["servers", "management"]
                }
            }
        }
    }


@pytest.fixture
def mock_tool_info():
    """Sample ToolInfo for testing."""
    return ToolInfo(
        operation_id="test_operation_id",
        tool_name="test_tool",
        description="A test tool for testing",
        category="testing",
        human_readable_params={"param1": "A test parameter"}
    )


@pytest.fixture
def mock_processed_tools():
    """Sample ProcessedOpenAPITools for testing."""
    return ProcessedOpenAPITools(
        tools=[
            ToolInfo(
                operation_id="get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get",
                tool_name="get_messages",
                description="Retrieve messages from a user session",
                category="messaging"
            ),
            ToolInfo(
                operation_id="restart_mcp_server_api_v1_mcp_servers__server_name__restart_post",
                tool_name="restart_server",
                description="Restart a specific MCP server",
                category="server_management"
            )
        ],
        name_mappings={
            "get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get": "get_messages",
            "restart_mcp_server_api_v1_mcp_servers__server_name__restart_post": "restart_server"
        },
        categories=["messaging", "server_management"]
    )


class TestToolInfo:
    """Test the ToolInfo model."""
    
    def test_tool_info_creation(self, mock_tool_info):
        """Test creating a ToolInfo instance."""
        assert mock_tool_info.operation_id == "test_operation_id"
        assert mock_tool_info.tool_name == "test_tool"
        assert mock_tool_info.description == "A test tool for testing"
        assert mock_tool_info.category == "testing"
        assert mock_tool_info.human_readable_params == {"param1": "A test parameter"}
    
    def test_tool_info_validation(self):
        """Test ToolInfo validation."""
        # Test with missing required fields
        with pytest.raises(ValueError):
            ToolInfo(operation_id="test")  # Missing required fields
    
    def test_tool_name_length(self):
        """Test tool name length constraints."""
        # This should succeed (under 40 chars)
        tool = ToolInfo(
            operation_id="test",
            tool_name="a" * 40,
            description="Test",
            category="test"
        )
        assert len(tool.tool_name) == 40
        
        # Note: Pydantic doesn't enforce max length by default
        # The AI agent should be responsible for respecting the limit


class TestProcessedOpenAPITools:
    """Test the ProcessedOpenAPITools model."""
    
    def test_processed_tools_creation(self, mock_processed_tools):
        """Test creating ProcessedOpenAPITools instance."""
        assert len(mock_processed_tools.tools) == 2
        assert len(mock_processed_tools.name_mappings) == 2
        assert len(mock_processed_tools.categories) == 2
        assert "messaging" in mock_processed_tools.categories
    
    def test_name_mappings_consistency(self, mock_processed_tools):
        """Test that name mappings match tool definitions."""
        for tool in mock_processed_tools.tools:
            assert tool.operation_id in mock_processed_tools.name_mappings
            assert mock_processed_tools.name_mappings[tool.operation_id] == tool.tool_name


class TestOpenAPIProcessor:
    """Test the OpenAPIProcessor class."""
    
    @patch('automagik_tools.tools.automagik.agent_processor.Agent')
    def test_processor_initialization(self, mock_agent_class):
        """Test OpenAPIProcessor initialization."""
        processor = OpenAPIProcessor(model_id="test-model", api_key="test-key")
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args.kwargs
        assert "description" in call_kwargs
        assert "instructions" in call_kwargs
        assert call_kwargs["response_model"] == ProcessedOpenAPITools
    
    @patch('automagik_tools.tools.automagik.agent_processor.Agent')
    def test_process_openapi_spec(self, mock_agent_class, sample_openapi_spec, mock_processed_tools):
        """Test processing an OpenAPI specification."""
        # Setup mock agent
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = mock_processed_tools
        mock_agent.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent
        
        # Process the spec
        processor = OpenAPIProcessor()
        result = processor.process_openapi_spec(sample_openapi_spec)
        
        # Verify the agent was called
        mock_agent.run.assert_called_once()
        
        # Verify the result
        assert isinstance(result, ProcessedOpenAPITools)
        assert len(result.tools) == 2
        assert len(result.name_mappings) == 2
    
    @patch('automagik_tools.tools.automagik.agent_processor.Agent')
    def test_process_single_operation(self, mock_agent_class):
        """Test processing a single operation."""
        # Setup mock agent for single operation
        mock_agent = Mock()
        mock_tool_info = ToolInfo(
            operation_id="test_op",
            tool_name="test_tool",
            description="Test description",
            category="testing"
        )
        mock_response = Mock()
        mock_response.content = mock_tool_info
        mock_agent.run.return_value = mock_response
        
        # Create a new mock for the single tool agent
        mock_single_agent = Mock()
        mock_single_agent.run.return_value = mock_response
        
        # Mock both agent creations
        mock_agent_class.side_effect = [mock_agent, mock_single_agent]
        
        # Process single operation
        processor = OpenAPIProcessor()
        result = processor.process_single_operation(
            operation_id="test_op",
            method="POST",
            path="/test/path",
            operation_details={"summary": "Test operation"}
        )
        
        # Verify result
        assert isinstance(result, ToolInfo)
        assert result.operation_id == "test_op"
        assert result.tool_name == "test_tool"


class TestCreateIntelligentNameMappings:
    """Test the create_intelligent_name_mappings function."""
    
    @patch('httpx.get')
    @patch('automagik_tools.tools.automagik.agent_processor.OpenAPIProcessor')
    def test_successful_mapping_generation(self, mock_processor_class, mock_httpx_get, sample_openapi_spec, mock_processed_tools):
        """Test successful generation of name mappings."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = sample_openapi_spec
        mock_response.raise_for_status = Mock()
        mock_httpx_get.return_value = mock_response
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.process_openapi_spec.return_value = mock_processed_tools
        mock_processor_class.return_value = mock_processor
        
        # Generate mappings
        result = create_intelligent_name_mappings(
            openapi_url="http://test.com/openapi.json",
            api_key="test-key"
        )
        
        # Verify
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get"] == "get_messages"
    
    @patch('httpx.get')
    def test_http_error_handling(self, mock_httpx_get):
        """Test handling of HTTP errors."""
        # Mock HTTP error
        mock_httpx_get.side_effect = Exception("Network error")
        
        # Should return empty dict on error
        result = create_intelligent_name_mappings("http://test.com/openapi.json")
        assert result == {}
    
    @patch('httpx.get')
    @patch('automagik_tools.tools.automagik.agent_processor.OpenAPIProcessor')
    def test_processor_error_handling(self, mock_processor_class, mock_httpx_get, sample_openapi_spec):
        """Test handling of processor errors."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.json.return_value = sample_openapi_spec
        mock_response.raise_for_status = Mock()
        mock_httpx_get.return_value = mock_response
        
        # Mock processor error
        mock_processor = Mock()
        mock_processor.process_openapi_spec.side_effect = Exception("AI processing error")
        mock_processor_class.return_value = mock_processor
        
        # Should return empty dict on error
        result = create_intelligent_name_mappings("http://test.com/openapi.json")
        assert result == {}


class TestIntegration:
    """Integration tests with the automagik tool."""
    
    @pytest.mark.asyncio
    async def test_ai_processor_integration(self, tmp_path):
        """Test AI processor integration with the main tool."""
        from automagik_tools.tools.automagik import get_ai_processed_names
        from automagik_tools.tools.automagik.config import AutomagikAgentsConfig
        
        # Create config with AI processing enabled
        config = AutomagikAgentsConfig(
            use_ai_processor=True,
            openai_api_key="test-key",
            cache_ai_results=True
        )
        
        # Create a mock cache directory
        cache_dir = tmp_path / ".cache" / "automagik"
        cache_dir.mkdir(parents=True)
        
        # Test with empty spec (should handle gracefully)
        empty_spec = {"paths": {}}
        
        with patch('automagik_tools.tools.automagik.agent_processor.OpenAPIProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_openapi_spec.return_value = ProcessedOpenAPITools(
                tools=[],
                name_mappings={},
                categories=[]
            )
            mock_processor_class.return_value = mock_processor
            
            with patch('pathlib.Path.home', return_value=tmp_path):
                result = get_ai_processed_names(empty_spec, config)
            
            assert isinstance(result, dict)
            assert len(result) == 0