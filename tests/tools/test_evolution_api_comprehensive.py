"""
Comprehensive tests for Evolution API MCP tool
"""

import pytest
from unittest.mock import AsyncMock, patch

from automagik_tools.tools.evolution_api import (
    create_server,
    get_metadata,
    get_config_class,
    send_text_message,
    send_media,
    send_audio,
    send_reaction,
    send_location,
    send_contact,
    send_presence,
    create_instance,
    get_instance_info,
)
from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

# Handle potential FastMCP wrapper
send_text_message_fn = (
    send_text_message.fn if hasattr(send_text_message, "fn") else send_text_message
)
send_media_fn = send_media.fn if hasattr(send_media, "fn") else send_media
send_audio_fn = send_audio.fn if hasattr(send_audio, "fn") else send_audio
send_reaction_fn = (
    send_reaction.fn if hasattr(send_reaction, "fn") else send_reaction
)
send_location_fn = (
    send_location.fn if hasattr(send_location, "fn") else send_location
)
send_contact_fn = (
    send_contact.fn if hasattr(send_contact, "fn") else send_contact
)
send_presence_fn = (
    send_presence.fn if hasattr(send_presence, "fn") else send_presence
)
create_instance_fn = (
    create_instance.fn if hasattr(create_instance, "fn") else create_instance
)
get_instance_info_fn = (
    get_instance_info.fn if hasattr(get_instance_info, "fn") else get_instance_info
)


@pytest.fixture(autouse=True)
def restore_globals():
    """Ensure module globals are restored between tests"""
    import automagik_tools.tools.evolution_api as evo_module

    original_config = evo_module.config
    original_client = evo_module.client
    yield
    evo_module.config = original_config
    evo_module.client = original_client


@pytest.fixture
def mock_config():
    return EvolutionAPIConfig(
        api_key="test-key",
        base_url="http://localhost:18080",
        instance="test-instance",
        fixed_recipient="",
        timeout=10,
        max_retries=2,
    )


@pytest.fixture
def patched_client():
    with patch(
        "automagik_tools.tools.evolution_api.EvolutionAPIClient"
    ) as MockClient:
        client = AsyncMock()
        client.send_text_message = AsyncMock(return_value={"id": "t1", "status": "sent"})
        client.send_media = AsyncMock(return_value={"id": "m1", "status": "sent"})
        client.send_audio = AsyncMock(return_value={"id": "a1", "status": "sent"})
        client.send_reaction = AsyncMock(return_value={"ok": True})
        client.send_location = AsyncMock(return_value={"id": "loc1", "status": "sent"})
        client.send_contact = AsyncMock(return_value={"id": "c1", "status": "sent"})
        client.send_presence = AsyncMock(return_value={"ok": True})
        client.create_instance = AsyncMock(return_value={"instance": "new"})
        client.get_instance_info = AsyncMock(return_value={"name": "test-instance", "status": "connected"})
        MockClient.return_value = client
        yield client


class TestMetadataAndConfig:
    def test_metadata(self):
        m = get_metadata()
        assert m["name"] == "evolution-api"
        assert m["version"] == "1.0.0"
        assert "whatsapp" in m["tags"]

    def test_get_config_class(self):
        assert get_config_class() == EvolutionAPIConfig

    def test_config_defaults_and_env(self, monkeypatch):
        monkeypatch.delenv("EVOLUTION_API_API_KEY", raising=False)
        monkeypatch.delenv("EVOLUTION_API_BASE_URL", raising=False)
        c = EvolutionAPIConfig()
        assert c.base_url == "https://api.evolution.com"
        monkeypatch.setenv("EVOLUTION_API_BASE_URL", "https://evo.local")
        c2 = EvolutionAPIConfig()
        assert c2.base_url == "https://evo.local"


class TestServer:
    def test_server_creation(self, mock_config, patched_client):
        server = create_server(mock_config)
        assert server.name == "Evolution API Tool"

    @pytest.mark.asyncio
    async def test_server_has_tools(self, mock_config, patched_client):
        server = create_server(mock_config)
        tools = await server.get_tools()
        assert any("send_text_message" in name for name in tools)

    def test_server_without_api_key_does_not_init_client(self):
        # Reset any prior global state that may have been set by other tests
        import automagik_tools.tools.evolution_api as evo_module
        evo_module.client = None
        evo_module.config = None

        server = create_server(EvolutionAPIConfig(api_key=""))
        assert evo_module.client is None


class TestMessagingTools:
    @pytest.mark.asyncio
    async def test_send_text_message(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_text_message_fn(
            instance="i1", message="Hello", number="+123"
        )
        assert res["status"] == "success"
        assert res["number"] == "+123"

    @pytest.mark.asyncio
    async def test_send_media(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_media_fn(
            instance="i1",
            media="data:image/png;base64,AAA",
            mediatype="image",
            mimetype="image/png",
            number="+123",
            caption="cap",
        )
        assert res["status"] == "success"
        assert res["mediatype"] == "image"

    @pytest.mark.asyncio
    async def test_send_audio_sends_presence_first(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_audio_fn(
            instance="i1", audio="data:audio/ogg;base64,BBB", number="+123"
        )
        assert res["status"] == "success"
        assert patched_client.send_presence.await_count >= 1

    @pytest.mark.asyncio
    async def test_send_reaction(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_reaction_fn(
            instance="i1",
            remote_jid="123@s.whatsapp.net",
            from_me=True,
            message_id="m1",
            reaction="👍",
        )
        assert res["status"] == "success"
        assert res["reaction"] == "👍"

    @pytest.mark.asyncio
    async def test_send_location(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_location_fn(
            instance="i1",
            latitude=1.23,
            longitude=4.56,
            number="+123",
            name="Place",
            address="Addr",
        )
        assert res["status"] == "success"
        assert res["coordinates"] == "1.23, 4.56"

    @pytest.mark.asyncio
    async def test_send_contact(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_contact_fn(
            instance="i1",
            contact=[{"fullName": "A", "phoneNumber": "+1"}],
            number="+123",
        )
        assert res["status"] == "success"
        assert res["contacts_count"] == 1

    @pytest.mark.asyncio
    async def test_send_presence(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_presence_fn(
            instance="i1", number="+123", presence="composing", delay=1000
        )
        assert res["status"] == "success"
        assert res["presence"] == "composing"
        assert res["delay"] == 1000


class TestErrorsAndEdgeCases:
    @pytest.mark.asyncio
    async def test_missing_client_returns_error(self):
        import automagik_tools.tools.evolution_api as evo_module
        evo_module.client = None
        evo_module.config = EvolutionAPIConfig(api_key="")
        res = await send_presence_fn(instance="i1")
        assert "error" in res
        assert "not configured" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_recipient_error(self, mock_config, patched_client):
        create_server(mock_config)
        res = await send_media_fn(
            instance="i1", media="x", mediatype="image", mimetype="image/png"
        )
        assert res["status"] == "error"
        assert "no recipient number" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_fixed_recipient_overrides_number(self, patched_client):
        cfg = EvolutionAPIConfig(api_key="k", fixed_recipient="+1999")
        create_server(cfg)
        res = await send_text_message_fn(
            instance="i1", message="hi", number="+1222"
        )
        assert res["number"] == "+1999"


class TestInstanceWrappers:
    @pytest.mark.asyncio
    async def test_create_instance(self, mock_config, patched_client):
        create_server(mock_config)
        res = await create_instance_fn(
            instance_name="new",
            token="t",
            webhook="https://hook",
            webhookByEvents=True,
            webhookBase64=False,
            events=["messages"],
        )
        assert res["status"] == "success"
        assert res["instance_name"] == "new"
        assert res["webhook_configured"] is True

    @pytest.mark.asyncio
    async def test_get_instance_info(self, mock_config, patched_client):
        create_server(mock_config)
        res = await get_instance_info_fn(instance_name="test-instance")
        assert res["status"] == "success"
        assert res["instance_name"] == "test-instance"
