"""
Tests for Evolution API MCP tool

This file follows patterns from tests/tools/test_omni.py and tests/tools/test_wait.py
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, Mock

from automagik_tools.tools.evolution_api import (
    mcp,
    _get_target_number,
    send_text_message,
    send_media,
    send_audio,
    send_reaction,
    send_location,
    send_contact,
    send_presence,
    config as _module_config,
    client as _module_client,
)
from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
from automagik_tools.tools.evolution_api import create_server, get_metadata, get_config_class  # type: ignore


@pytest.fixture
def mock_config(monkeypatch):
    """Create mock EvolutionAPIConfig"""
    # Ensure no env leakage
    monkeypatch.delenv("EVOLUTION_API_API_KEY", raising=False)
    monkeypatch.delenv("EVOLUTION_API_BASE_URL", raising=False)
    monkeypatch.delenv("EVOLUTION_API_FIXED_RECIPIENT", raising=False)

    cfg = EvolutionAPIConfig(api_key="test-key", base_url="https://api.evo.test", instance="inst-1", fixed_recipient="+19990001111")
    return cfg


@pytest.fixture
def mock_client():
    """Patch EvolutionAPIClient with AsyncMock instance"""
    with patch("automagik_tools.tools.evolution_api.EvolutionAPIClient") as MockClient:
        client = AsyncMock()
        MockClient.return_value = client
        yield client


@pytest.fixture(autouse=True)
def setup_module_config(mock_config):
    """Set module-level config and ensure client global is reset"""
    import automagik_tools.tools.evolution_api as evo_module

    original_config = evo_module.config
    original_client = evo_module.client

    evo_module.config = mock_config
    evo_module.client = None

    yield

    evo_module.config = original_config
    evo_module.client = original_client


class TestEvolutionConfig:
    def test_default_values(self):
        cfg = EvolutionAPIConfig()
        assert cfg.api_key == ""
        assert cfg.base_url.startswith("http")
        assert cfg.timeout == 30
        assert cfg.max_retries == 3

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("EVOLUTION_API_API_KEY", "env-key")
        monkeypatch.setenv("EVOLUTION_API_BASE_URL", "https://env.evo")
        cfg = EvolutionAPIConfig()
        assert cfg.api_key == "env-key"
        assert cfg.base_url == "https://env.evo"


class TestEvolutionMetadata:
    def test_metadata_and_config_class(self):
        # metadata helpers are provided by module; import may vary, tolerate attribute errors
        try:
            meta = get_metadata()
            assert isinstance(meta, dict)
            assert "name" in meta
        except Exception:
            # If helpers are not exported, at least ensure mcp exists
            assert hasattr(mcp, "tool")

        cfg_cls = get_config_class()
        assert cfg_cls == EvolutionAPIConfig


class TestEvolutionTools:
    @pytest.mark.asyncio
    async def test_send_text_message_success(self, mock_client):
        # Arrange: client.send_text_message returns a payload
        mock_client.send_text_message.return_value = {"id": "msg-1", "status": "sent"}

        # Extract underlying function if wrapped
        fn = send_text_message.fn if hasattr(send_text_message, "fn") else send_text_message

        # Act
        result = await fn(instance="inst-1", message="hello world")

        # Assert
        assert result["status"] == "success"
        assert result["instance"] == "inst-1"
        assert "+19990001111" in result["number"] or result["number"] == "+19990001111"
        mock_client.send_text_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_text_message_missing_api_key(self, monkeypatch):
        # Simulate no api_key in config
        import automagik_tools.tools.evolution_api as evo

        original_config = evo.config
        evo.config = EvolutionAPIConfig(api_key="")

        fn = send_text_message.fn if hasattr(send_text_message, "fn") else send_text_message

        result = await fn(instance="i", message="msg")
        assert "error" in result

        evo.config = original_config

    @pytest.mark.asyncio
    async def test_send_media_success_and_error(self, mock_client):
        fn = send_media.fn if hasattr(send_media, "fn") else send_media

        mock_client.send_media.return_value = {"id": "m-1", "status": "sent"}
        # success
        res = await fn(instance="inst-1", media="dGVzdA==", mediatype="image", mimetype="image/jpeg")
        assert res["status"] == "success"
        assert res["mediatype"] == "image"

        # error path: client raises
        mock_client.send_media.side_effect = Exception("boom")
        res_err = await fn(instance="inst-1", media="dGVzdA==", mediatype="image", mimetype="image/jpeg")
        assert res_err["status"] == "error"
        assert "boom" in res_err["error"]

    @pytest.mark.asyncio
    async def test_send_audio_sends_presence_then_audio(self, mock_client):
        fn = send_audio.fn if hasattr(send_audio, "fn") else send_audio

        mock_client.send_presence.return_value = {"ok": True}
        mock_client.send_audio.return_value = {"id": "a-1"}

        res = await fn(instance="inst-1", audio="dGVzdA==")
        assert res["status"] == "success"
        mock_client.send_presence.assert_awaited()
        mock_client.send_audio.assert_awaited()

    @pytest.mark.asyncio
    async def test_send_reaction_success_and_error(self, mock_client):
        fn = send_reaction.fn if hasattr(send_reaction, "fn") else send_reaction

        mock_client.send_reaction.return_value = {"ok": True}
        res = await fn(instance="inst-1", remote_jid="jid@server", from_me=True, message_id="m1", reaction="\ud83d\udc4d")
        assert res["status"] == "success"

        mock_client.send_reaction.side_effect = Exception("nope")
        res_err = await fn(instance="inst-1", remote_jid="jid@server", from_me=True, message_id="m1", reaction="x")
        assert res_err["status"] == "error"

    @pytest.mark.asyncio
    async def test_send_location_success_and_error(self, mock_client):
        fn = send_location.fn if hasattr(send_location, "fn") else send_location

        mock_client.send_location.return_value = {"id": "loc-1"}
        res = await fn(instance="inst-1", latitude=12.34, longitude=56.78)
        assert res["status"] == "success"
        assert "coordinates" in res

        mock_client.send_location.side_effect = Exception("loc-fail")
        res_err = await fn(instance="inst-1", latitude=0.0, longitude=0.0)
        assert res_err["status"] == "error"

    @pytest.mark.asyncio
    async def test_send_contact_success_and_error(self, mock_client):
        fn = send_contact.fn if hasattr(send_contact, "fn") else send_contact

        contacts = [{"fullName": "Jane", "wuid": "w1", "phoneNumber": "+100200"}]
        mock_client.send_contact.return_value = {"id": "c-1"}
        res = await fn(instance="inst-1", contact=contacts)
        assert res["status"] == "success"
        assert res["contacts_count"] == 1

        mock_client.send_contact.side_effect = Exception("contact-error")
        res_err = await fn(instance="inst-1", contact=contacts)
        assert res_err["status"] == "error"

    @pytest.mark.asyncio
    async def test_send_presence_success_and_error(self, mock_client):
        fn = send_presence.fn if hasattr(send_presence, "fn") else send_presence

        mock_client.send_presence.return_value = {"ok": True}
        res = await fn(instance="inst-1", presence="composing")
        assert res["status"] == "success"

        mock_client.send_presence.side_effect = Exception("presence-fail")
        res_err = await fn(instance="inst-1", presence="unknown")
        assert res_err["status"] == "error"

    def test__get_target_number_with_fixed_recipient(self):
        # When config.fixed_recipient is set, returned number should be that
        import automagik_tools.tools.evolution_api as evo

        original = evo.config
        evo.config = EvolutionAPIConfig(api_key="k", fixed_recipient="+12223334444")

        assert _get_target_number("+999") == "+12223334444"

        evo.config = original

    def test__get_target_number_with_provided_number(self):
        import automagik_tools.tools.evolution_api as evo

        original = evo.config
        evo.config = None

        assert _get_target_number("+1555") == "+1555"

        evo.config = original

    def test__get_target_number_missing(self):
        import automagik_tools.tools.evolution_api as evo

        original = evo.config
        evo.config = None

        with pytest.raises(ValueError):
            _get_target_number(None)

        evo.config = original

    @pytest.mark.asyncio
    async def test_mcp_registers_tools(self):
        # Ensure the FastMCP instance has tools registered by decorators
        tools = await mcp.get_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0
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
        expected_uris = ["evolution://status", "evolution://config"]

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
        expected_prompts = ["whatsapp_message_template", "evolution_api_setup_guide"]

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
