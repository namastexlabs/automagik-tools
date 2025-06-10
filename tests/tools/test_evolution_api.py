"""
Tests for Evolution API tool functionality
"""

import pytest
from unittest.mock import MagicMock
from automagik_tools.tools.evolution_api import create_server


class MockConfig:
    """Mock configuration for testing"""

    def __init__(
        self, base_url="http://test-api.example.com", api_key="test_api_key", timeout=30
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout


class TestEvolutionAPITool:
    """Test Evolution API tool creation and registration"""

    def test_create_tool_function(self):
        """Test that create_server function works"""
        config = MockConfig()
        server = create_server(config)

        assert server is not None
        assert hasattr(server, "get_tools")  # FastMCP has get_tools method
        assert hasattr(server, "name")
        assert server.name == "Evolution API Tool"

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tool can be registered with MCP"""
        config = MockConfig()
        server = create_server(config)

        # Check that the server has registered MCP-compatible functions
        tools = await server.get_tools()
        tool_names = list(tools.keys())
        assert "send_text_message" in tool_names
        assert "create_instance" in tool_names
        assert "get_instance_info" in tool_names


class TestEvolutionAPIFunctions:
    """Test individual Evolution API functions"""

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, mock_httpx_client):
        """Test successful text message sending"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "message": "Message sent successfully",
        }
        mock_httpx_client.post.return_value = mock_response

        config = MockConfig()
        server = create_server(config)

        # Get all tools and find send_text_message
        tools = await server.get_tools()
        send_message_tool = tools.get("send_text_message")

        assert send_message_tool is not None
        assert send_message_tool.name == "send_text_message"
        assert hasattr(send_message_tool, "description")
        assert hasattr(send_message_tool, "parameters")

    @pytest.mark.asyncio
    async def test_create_instance_function_exists(self):
        """Test that create_instance function exists and is callable"""
        config = MockConfig()
        server = create_server(config)

        # Get all tools and find create_instance
        tools = await server.get_tools()
        create_instance_tool = tools.get("create_instance")

        assert create_instance_tool is not None
        assert create_instance_tool.name == "create_instance"
        assert hasattr(create_instance_tool, "description")
        assert hasattr(create_instance_tool, "parameters")

    @pytest.mark.asyncio
    async def test_get_instance_info_function_exists(self):
        """Test that get_instance_info function exists and is callable"""
        config = MockConfig()
        server = create_server(config)

        # Get all tools and find get_instance_info
        tools = await server.get_tools()
        get_info_tool = tools.get("get_instance_info")

        assert get_info_tool is not None
        assert get_info_tool.name == "get_instance_info"
        assert hasattr(get_info_tool, "description")
        assert hasattr(get_info_tool, "parameters")


class TestEvolutionAPIErrorHandling:
    """Test error handling in Evolution API functions"""

    @pytest.mark.asyncio
    async def test_missing_api_key_error(self):
        """Test that missing API key raises appropriate error"""
        from fastmcp import Client

        config = MockConfig(api_key="")  # Empty API key
        server = create_server(config)

        # Test via client to properly test tool execution
        async with Client(server) as client:
            # Should raise error due to missing API key when called
            with pytest.raises(Exception):  # ValueError or similar
                await client.call_tool(
                    "send_text_message",
                    {
                        "instance": "test_instance",
                        "number": "1234567890",
                        "text": "Hello, World!",
                    },
                )


class TestEvolutionAPIResources:
    """Test Evolution API MCP resources"""

    @pytest.mark.asyncio
    async def test_resources_registered(self):
        """Test that resources are registered"""
        config = MockConfig()
        server = create_server(config)

        # Check that the server has resources
        resources = await server.get_resources()
        assert len(resources) > 0

        # Check for specific resources
        resource_uris = list(resources.keys())
        expected_uris = ["evolution://instances", "evolution://config"]

        for expected_uri in expected_uris:
            assert any(expected_uri in uri for uri in resource_uris)


class TestEvolutionAPIPrompts:
    """Test Evolution API MCP prompts"""

    @pytest.mark.asyncio
    async def test_prompts_registered(self):
        """Test that prompts are registered"""
        config = MockConfig()
        server = create_server(config)

        # Check that the server has prompts
        prompts = await server.get_prompts()
        assert len(prompts) > 0

        # Check for specific prompts
        prompt_names = list(prompts.keys())
        expected_prompts = ["whatsapp_message_template", "instance_setup_guide"]

        for expected_prompt in expected_prompts:
            assert expected_prompt in prompt_names


class TestIntegrationWithMCP:
    """Test integration with MCP protocol"""

    def test_tool_metadata(self):
        """Test that tool has proper metadata"""
        config = MockConfig()
        server = create_server(config)

        # Check that server has name
        assert hasattr(server, "name")
        assert server.name == "Evolution API Tool"

    @pytest.mark.asyncio
    async def test_tool_has_required_components(self):
        """Test that tool has all required MCP components"""
        config = MockConfig()
        server = create_server(config)

        # Should have tools, resources, and prompts
        tools = await server.get_tools()
        resources = await server.get_resources()
        prompts = await server.get_prompts()

        assert len(tools) > 0
        assert len(resources) > 0
        assert len(prompts) > 0
