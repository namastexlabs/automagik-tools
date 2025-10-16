"""
Tests for OMNI client HTTP methods
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from automagik_tools.tools.omni.client import OmniClient
from automagik_tools.tools.omni.config import OmniConfig
from automagik_tools.tools.omni.models import (
    InstanceConfig,
    ChannelType,
    SendTextRequest,
    SendMediaRequest,
    SendAudioRequest,
    SendStickerRequest,
    SendContactRequest,
    SendReactionRequest,
    ContactInfo,
    TraceFilter,
    FetchProfileRequest,
    UpdateProfilePictureRequest,
)


@pytest.fixture
def client_config():
    """Create test configuration"""
    return OmniConfig(
        api_key="test-key",
        base_url="http://localhost:8882",
        timeout=30,
    )


@pytest.fixture
def client(client_config):
    """Create test client"""
    return OmniClient(client_config)


class TestOmniClientInit:
    """Test client initialization"""

    def test_client_initialization(self, client_config):
        """Test client is initialized with correct config"""
        client = OmniClient(client_config)
        assert client.config == client_config
        assert client.base_url == "http://localhost:8882"
        # Headers are set from config
        assert "x-api-key" in client.headers
        assert "Content-Type" in client.headers
        assert isinstance(client.timeout, httpx.Timeout)


class TestClientInstanceOperations:
    """Test instance HTTP operations"""

    @pytest.mark.asyncio
    async def test_list_instances(self, client):
        """Test list instances HTTP call"""
        mock_response_data = [
            {"name": "test-instance", "channel_type": "whatsapp", "is_active": True}
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.list_instances(skip=0, limit=100, include_status=True)

            assert len(result) == 1
            assert result[0].name == "test-instance"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instance(self, client):
        """Test get instance HTTP call"""
        mock_response_data = {
            "name": "test-instance",
            "channel_type": "whatsapp",
            "is_active": True,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_instance("test-instance")

            assert result.name == "test-instance"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_instance(self, client):
        """Test create instance HTTP call"""
        config = InstanceConfig(
            name="new-instance", channel_type=ChannelType.WHATSAPP, auto_qr=True
        )

        mock_response_data = {"name": "new-instance", "channel_type": "whatsapp"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.create_instance(config)

            assert result.name == "new-instance"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_instance(self, client):
        """Test update instance HTTP call"""
        update_data = {"is_active": False}
        mock_response_data = {
            "name": "test-instance",
            "channel_type": "whatsapp",
            "is_active": False,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.update_instance("test-instance", update_data)

            assert result.name == "test-instance"
            assert result.is_active is False
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_instance(self, client):
        """Test delete instance HTTP call"""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 204
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.delete_instance("test-instance")

            assert result is True
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_default_instance(self, client):
        """Test set default instance HTTP call"""
        mock_response_data = {
            "name": "test-instance",
            "channel_type": "whatsapp",
            "is_default": True,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.set_default_instance("test-instance")

            assert result.name == "test-instance"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instance_status(self, client):
        """Test get instance status HTTP call"""
        mock_response_data = {
            "instance_name": "test-instance",
            "channel_type": "whatsapp",
            "status": "connected",
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_instance_status("test-instance")

            assert result.instance_name == "test-instance"
            assert result.status == "connected"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instance_qr(self, client):
        """Test get instance QR HTTP call"""
        mock_response_data = {
            "instance_name": "test-instance",
            "qr_code": "base64data",
            "connection_type": "qr",
            "status": "pending",
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_instance_qr("test-instance")

            assert result.instance_name == "test-instance"
            assert result.qr_code == "base64data"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_instance(self, client):
        """Test restart instance HTTP call"""
        mock_response_data = {"status": "restarting"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.restart_instance("test-instance")

            assert result["status"] == "restarting"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_instance(self, client):
        """Test logout instance HTTP call"""
        mock_response_data = {"status": "logged_out"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.logout_instance("test-instance")

            assert result["status"] == "logged_out"
            mock_client_instance.request.assert_called_once()


class TestClientMessageOperations:
    """Test message sending HTTP operations"""

    @pytest.mark.asyncio
    async def test_send_text(self, client):
        """Test send text message HTTP call"""
        request = SendTextRequest(phone_number="+1234567890", text="Hello")
        mock_response_data = {"success": True, "message_id": "msg_123"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_text("test-instance", request)

            assert result.success is True
            assert result.message_id == "msg_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_media(self, client):
        """Test send media message HTTP call"""
        request = SendMediaRequest(
            phone_number="+1234567890",
            media_url="https://example.com/image.jpg",
            media_type="image",
        )
        mock_response_data = {"success": True, "message_id": "media_123"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_media("test-instance", request)

            assert result.success is True
            assert result.message_id == "media_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_audio(self, client):
        """Test send audio message HTTP call"""
        request = SendAudioRequest(
            phone_number="+1234567890",
            audio_url="https://example.com/audio.mp3",
            ptt=True,
        )
        mock_response_data = {"success": True, "message_id": "audio_123"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_audio("test-instance", request)

            assert result.success is True
            assert result.message_id == "audio_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sticker(self, client):
        """Test send sticker message HTTP call"""
        request = SendStickerRequest(
            phone_number="+1234567890",
            sticker_url="https://example.com/sticker.webp",
        )
        mock_response_data = {"success": True, "message_id": "sticker_123"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_sticker("test-instance", request)

            assert result.success is True
            assert result.message_id == "sticker_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_contact(self, client):
        """Test send contact message HTTP call"""
        contact = ContactInfo(full_name="John Doe", phone_number="+0987654321")
        request = SendContactRequest(phone_number="+1234567890", contacts=[contact])
        mock_response_data = {"success": True, "message_id": "contact_123"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_contact("test-instance", request)

            assert result.success is True
            assert result.message_id == "contact_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_reaction(self, client):
        """Test send reaction HTTP call"""
        request = SendReactionRequest(
            phone_number="+1234567890", message_id="msg_123", emoji="👍"
        )
        mock_response_data = {"success": True}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.send_reaction("test-instance", request)

            assert result.success is True
            mock_client_instance.request.assert_called_once()


class TestClientTraceOperations:
    """Test trace HTTP operations"""

    @pytest.mark.asyncio
    async def test_list_traces(self, client):
        """Test list traces HTTP call"""
        filters = TraceFilter(instance_name="test-instance", limit=10)
        mock_response_data = [
            {
                "trace_id": "trace_123",
                "instance_name": "test-instance",
                "sender_phone": "+1234567890",
                "status": "completed",
                "received_at": datetime.now().isoformat(),
            }
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.list_traces(filters)

            assert len(result) == 1
            assert result[0].trace_id == "trace_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trace(self, client):
        """Test get trace HTTP call"""
        mock_response_data = {
            "trace_id": "trace_123",
            "instance_name": "test-instance",
            "sender_phone": "+1234567890",
            "status": "completed",
            "received_at": datetime.now().isoformat(),
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_trace("trace_123")

            assert result.trace_id == "trace_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trace_payloads(self, client):
        """Test get trace payloads HTTP call"""
        mock_response_data = [
            {
                "id": "payload_123",
                "trace_id": "trace_123",
                "payload_type": "request",
                "direction": "inbound",
                "created_at": datetime.now().isoformat(),
            }
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_trace_payloads("trace_123", include_payload=True)

            assert len(result) == 1
            assert result[0].trace_id == "trace_123"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trace_analytics(self, client):
        """Test get trace analytics HTTP call"""
        mock_response_data = {
            "total_messages": 100,
            "successful_messages": 80,
            "failed_messages": 20,
            "success_rate": 0.8,
            "message_types": {"text": 90, "media": 10},
            "error_stages": {},
            "instances": {"test-instance": 100},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_trace_analytics(instance_name="test-instance")

            assert result.total_messages == 100
            assert result.success_rate == 0.8
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_traces_by_phone(self, client):
        """Test get traces by phone HTTP call"""
        mock_response_data = [
            {
                "trace_id": "trace_123",
                "instance_name": "test-instance",
                "sender_phone": "+1234567890",
                "status": "completed",
                "received_at": datetime.now().isoformat(),
            }
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_traces_by_phone("+1234567890", limit=10)

            assert len(result) == 1
            assert result[0].sender_phone == "+1234567890"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_traces(self, client):
        """Test cleanup traces HTTP call"""
        mock_response_data = {"deleted_count": 50, "status": "completed"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.cleanup_traces(days_old=30, dry_run=True)

            assert result["deleted_count"] == 50
            mock_client_instance.request.assert_called_once()


class TestClientProfileOperations:
    """Test profile HTTP operations"""

    @pytest.mark.asyncio
    async def test_fetch_profile(self, client):
        """Test fetch profile HTTP call"""
        request = FetchProfileRequest(phone_number="+1234567890")
        mock_response_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "picture_url": "https://example.com/pic.jpg",
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.fetch_profile("test-instance", request)

            assert result["name"] == "John Doe"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_picture(self, client):
        """Test update profile picture HTTP call"""
        request = UpdateProfilePictureRequest(
            picture_url="https://example.com/new-pic.jpg"
        )
        mock_response_data = {"success": True, "status": "updated"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.update_profile_picture("test-instance", request)

            assert result.success is True
            mock_client_instance.request.assert_called_once()


class TestClientChatContactChannelOperations:
    """Test chat, contact, and channel HTTP operations"""

    @pytest.mark.asyncio
    async def test_list_chats(self, client):
        """Test list chats HTTP call"""
        mock_response_data = {
            "chats": [
                {
                    "id": "chat_123",
                    "name": "Test Chat",
                    "chat_type": "direct",
                    "channel_type": "whatsapp",
                    "instance_name": "test-instance",
                }
            ],
            "total_count": 1,
            "page": 1,
            "page_size": 50,
            "has_more": False,
            "instance_name": "test-instance",
            "partial_errors": [],
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.list_chats("test-instance", page=1, page_size=50)

            assert len(result.chats) == 1
            assert result.total_count == 1
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat(self, client):
        """Test get chat HTTP call"""
        mock_response_data = {
            "id": "chat_123",
            "name": "Test Chat",
            "chat_type": "direct",
            "channel_type": "whatsapp",
            "instance_name": "test-instance",
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_chat("test-instance", "chat_123")

            assert result.id == "chat_123"
            assert result.name == "Test Chat"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_contacts(self, client):
        """Test list contacts HTTP call"""
        mock_response_data = {
            "contacts": [
                {
                    "id": "555196644761@s.whatsapp.net",
                    "name": "John Doe",
                    "channel_type": "whatsapp",
                    "instance_name": "test-instance",
                }
            ],
            "total_count": 1,
            "page": 1,
            "page_size": 50,
            "has_more": False,
            "instance_name": "test-instance",
            "partial_errors": [],
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.list_contacts("test-instance", page=1, page_size=50)

            assert len(result.contacts) == 1
            assert result.total_count == 1
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact(self, client):
        """Test get contact HTTP call"""
        mock_response_data = {
            "id": "555196644761@s.whatsapp.net",
            "name": "John Doe",
            "channel_type": "whatsapp",
            "instance_name": "test-instance",
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.get_contact(
                "test-instance", "555196644761@s.whatsapp.net"
            )

            assert result.id == "555196644761@s.whatsapp.net"
            assert result.name == "John Doe"
            mock_client_instance.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_channels(self, client):
        """Test list channels HTTP call"""
        mock_response_data = {
            "channels": [
                {
                    "instance_name": "ember",
                    "channel_type": "whatsapp",
                    "display_name": "ember",
                    "status": "connected",
                    "is_healthy": True,
                    "supports_contacts": True,
                    "supports_groups": True,
                    "supports_media": True,
                    "supports_voice": False,
                }
            ],
            "total_count": 1,
            "healthy_count": 1,
            "partial_errors": [],
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.list_channels()

            assert len(result.channels) == 1
            assert result.healthy_count == 1
            mock_client_instance.request.assert_called_once()


class TestClientErrorHandling:
    """Test error handling in client"""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, client):
        """Test HTTP error is properly handled"""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=mock_response
            )
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception) as exc_info:
                await client.list_instances()

            assert "API error" in str(exc_info.value)
            assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, client):
        """Test 204 empty response handling"""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response = Mock()
            mock_response.status_code = 204
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            result = await client.delete_instance("test-instance")

            assert result is True

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Test connection error handling"""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.request = AsyncMock(
                side_effect=Exception("Connection failed")
            )

            with pytest.raises(Exception) as exc_info:
                await client.list_instances()

            assert "Connection failed" in str(exc_info.value)
