"""
Test using FastMCP Client pattern for better compliance
"""

import pytest
from fastmcp import Client
from automagik_tools.tools.evolution_api import create_server, EvolutionAPIConfig
from automagik_tools.tools.example_hello import create_server as create_hello_server, ExampleHelloConfig
from unittest.mock import AsyncMock, patch


class TestEvolutionAPIWithClient:
    """Test Evolution API using FastMCP Client pattern"""
    
    @pytest.fixture
    async def evolution_client(self):
        """Create a test client for Evolution API"""
        config = EvolutionAPIConfig(
            base_url="http://test.evolution.api",
            api_key="test-key",
            timeout=5
        )
        server = create_server(config)
        async with Client(server) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_list_tools(self, evolution_client):
        """Test listing available tools"""
        tools = await evolution_client.list_tools()
        
        tool_names = [tool.name for tool in tools]
        assert "send_text_message" in tool_names
        assert "create_instance" in tool_names
        assert "get_connection_state" in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_annotations(self, evolution_client):
        """Test that tools have proper annotations"""
        tools = await evolution_client.list_tools()
        
        send_message_tool = next(t for t in tools if t.name == "send_text_message")
        # Check annotations exist
        assert hasattr(send_message_tool, 'annotations')
        if send_message_tool.annotations:
            assert send_message_tool.annotations.get('readOnlyHint') is False
            assert send_message_tool.annotations.get('openWorldHint') is True
        
        get_info_tool = next(t for t in tools if t.name == "get_instance_info")
        if get_info_tool.annotations:
            assert get_info_tool.annotations.get('readOnlyHint') is True
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_send_text_message(self, mock_post, evolution_client):
        """Test sending a text message through client"""
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "sent", "message_id": "123"}
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        result = await evolution_client.call_tool(
            "send_text_message",
            {
                "instance": "test-instance",
                "number": "+1234567890",
                "text": "Hello from test"
            }
        )
        
        assert result[0].text  # Should return some result
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_resources(self, evolution_client):
        """Test listing available resources"""
        resources = await evolution_client.list_resources()
        
        resource_uris = [r.uri for r in resources]
        assert "evolution://instances" in resource_uris
        assert "evolution://config" in resource_uris
    
    @pytest.mark.asyncio
    async def test_list_prompts(self, evolution_client):
        """Test listing available prompts"""
        prompts = await evolution_client.list_prompts()
        
        prompt_names = [p.name for p in prompts]
        assert "whatsapp_message_template" in prompt_names
        assert "instance_setup_guide" in prompt_names


class TestExampleHelloWithClient:
    """Test Example Hello tool using FastMCP Client pattern"""
    
    @pytest.fixture
    async def hello_client(self):
        """Create a test client for Example Hello"""
        config = ExampleHelloConfig()
        server = create_hello_server(config)
        async with Client(server) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_say_hello(self, hello_client):
        """Test the say_hello tool"""
        result = await hello_client.call_tool("say_hello", {"name": "Test User"})
        assert "Hello, Test User!" in result[0].text
        assert "Welcome to automagik-tools" in result[0].text
    
    @pytest.mark.asyncio
    async def test_add_numbers(self, hello_client):
        """Test the add_numbers tool"""
        result = await hello_client.call_tool("add_numbers", {"a": 5, "b": 3})
        assert "8" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_resource(self, hello_client):
        """Test getting a resource"""
        result = await hello_client.read_resource("example://info")
        assert "minimal example MCP tool" in result[0].text


class TestServerComposition:
    """Test FastMCP server composition patterns"""
    
    @pytest.mark.asyncio
    async def test_multiple_servers_with_client(self):
        """Test accessing multiple servers through clients"""
        # Create configs
        evolution_config = EvolutionAPIConfig(
            base_url="http://test.api",
            api_key="test"
        )
        hello_config = ExampleHelloConfig()
        
        # Create servers
        evolution_server = create_server(evolution_config)
        hello_server = create_hello_server(hello_config)
        
        # Test each server independently with its own client
        async with Client(evolution_server) as evolution_client:
            evolution_tools = await evolution_client.list_tools()
            assert any(t.name == "send_text_message" for t in evolution_tools)
        
        async with Client(hello_server) as hello_client:
            hello_tools = await hello_client.list_tools()
            assert any(t.name == "say_hello" for t in hello_tools)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])