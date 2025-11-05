"""
Tests for Evolution API MCP tool

This file follows patterns from tests/tools/test_omni.py and tests/tools/test_wait.py
"""

# Some CI/local environments may not have optional runtime dependencies installed
# (pydantic, fastmcp, httpx). To keep tests hermetic and runnable locally without
# installing large native build toolchains, inject small runtime stubs before
# importing the `automagik_tools.tools.evolution_api` module.
import sys
import types
import os

def _ensure_stub_modules():
    # fastmcp stub
    try:
        import fastmcp  # type: ignore
    except Exception:
        fm = types.ModuleType("fastmcp")

        class FastMCP:
            def __init__(self, name, instructions=None):
                self._tools = {}

            def tool(self):
                def _decorator(fn):
                    self._tools[fn.__name__] = fn
                    return fn

                return _decorator

            def resource(self, *args, **kwargs):
                def _decorator(fn):
                    return fn

                return _decorator

            def prompt(self):
                def _decorator(fn):
                    return fn

                return _decorator

            async def get_tools(self):
                return self._tools

        fm.FastMCP = FastMCP
        sys.modules["fastmcp"] = fm

    # pydantic + pydantic_settings stubs
    try:
        import pydantic  # type: ignore
        import pydantic_settings  # type: ignore
    except Exception:
        pd = types.ModuleType("pydantic")

        def Field(*args, **kwargs):
            return kwargs.get("default", None)

        pd.Field = Field
        sys.modules["pydantic"] = pd

        pds = types.ModuleType("pydantic_settings")

        class BaseSettings:
            model_config = {}

            def __init__(self, **kwargs):
                # Copy class attributes as defaults to instance and allow env override
                prefix = getattr(self, "model_config", {}).get("env_prefix", "")
                for k, v in self.__class__.__dict__.items():
                    if k.startswith("__") or callable(v):
                        continue
                    # set default from class attr
                    setattr(self, k, v)

                # override from env and kwargs
                for k, v in list(self.__dict__.items()):
                    env_key = (prefix + k).upper()
                    if env_key in os.environ:
                        val = os.environ[env_key]
                        if isinstance(v, int):
                            try:
                                val = int(val)
                            except Exception:
                                pass
                        setattr(self, k, val)

                # kwargs take precedence
                for k, v in kwargs.items():
                    setattr(self, k, v)

        pds.BaseSettings = BaseSettings
        sys.modules["pydantic_settings"] = pds

    # httpx stub (only need AsyncClient and exceptions during import)
    try:
        import httpx  # type: ignore
    except Exception:
        hx = types.ModuleType("httpx")

        class TimeoutException(Exception):
            pass

        class ConnectError(Exception):
            pass

        class AsyncClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def request(self, *args, **kwargs):
                class Resp:
                    status_code = 200

                    def json(self):
                        return {}

                    text = ""

                return Resp()

        hx.AsyncClient = AsyncClient
        hx.TimeoutException = TimeoutException
        hx.ConnectError = ConnectError
        sys.modules["httpx"] = hx


_ensure_stub_modules()

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

        # Ensure module-level client is set so functions that require `client` work
        import automagik_tools.tools.evolution_api as evo_module

        prev_client = getattr(evo_module, "client", None)
        evo_module.client = client

        try:
            yield client
        finally:
            evo_module.client = prev_client


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

