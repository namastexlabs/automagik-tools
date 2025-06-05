"""
Test using FastMCP Client pattern for better compliance
"""

import pytest
from fastmcp import Client
from automagik_tools.tools.evolution_api import create_server, EvolutionAPIConfig
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])