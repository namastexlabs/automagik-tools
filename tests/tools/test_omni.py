"""
Tests for OMNI MCP tool
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from automagik_tools.tools.omni import create_server, get_metadata, get_config_class
from automagik_tools.tools.omni.config import OmniConfig
from automagik_tools.tools.omni.models import (
    InstanceOperation,
    MessageType,
    TraceOperation,
    ProfileOperation,
    InstanceConfig,
    SendTextRequest,
    SendMediaRequest,
    ChannelType,
)


class TestOmniMetadata:
    """Test tool metadata and discovery"""

    def test_metadata_structure(self):
        """Test that metadata has required fields"""
        metadata = get_metadata()
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert "author" in metadata
        assert "category" in metadata
        assert "tags" in metadata
        assert "capabilities" in metadata

        assert metadata["name"] == "omni"
        assert metadata["version"] == "1.0.0"
        assert metadata["category"] == "messaging"
        assert "whatsapp" in metadata["tags"]
        assert "instance_management" in metadata["capabilities"]

    def test_config_class(self):
        """Test config class is returned correctly"""
        config_class = get_config_class()
        assert config_class == OmniConfig


class TestOmniConfig:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration values"""
        config = OmniConfig()
        assert config.base_url == "http://localhost:8882"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.default_instance is None

    def test_env_config(self, monkeypatch):
        """Test configuration from environment"""
        monkeypatch.setenv("OMNI_API_KEY", "namastex888")
        monkeypatch.setenv("OMNI_BASE_URL", "https://test.omni.com")
        monkeypatch.setenv("OMNI_DEFAULT_INSTANCE", "test-instance")
        monkeypatch.setenv("OMNI_TIMEOUT", "60")

        config = OmniConfig()
        assert config.api_key == "namastex888"
        assert config.base_url == "https://test.omni.com"
        assert config.default_instance == "test-instance"
        assert config.timeout == 60

    def test_config_validation(self, monkeypatch):
        """Test configuration validation"""
        # Clear env vars
        monkeypatch.delenv("OMNI_API_KEY", raising=False)
        monkeypatch.delenv("OMNI_BASE_URL", raising=False)

        # Test missing API key
        config = OmniConfig()
        with pytest.raises(ValueError, match="OMNI_API_KEY is required"):
            config.validate_for_use()

        # Test missing base URL - need to set api_key first
        monkeypatch.setenv("OMNI_API_KEY", "test-key")
        monkeypatch.setenv("OMNI_BASE_URL", "")  # Empty string
        config = OmniConfig()
        with pytest.raises(ValueError, match="OMNI_BASE_URL is required"):
            config.validate_for_use()


class TestOmniServer:
    """Test MCP server creation and tools"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = OmniConfig(
            api_key="namastex888",
            base_url="http://localhost:8882",
            default_instance="test-whatsapp",
            timeout=30,
        )
        return config

    @pytest.fixture
    def server(self, mock_config):
        """Create test server instance"""
        return create_server(mock_config)

    def test_server_creation(self, server):
        """Test server is created with correct metadata"""
        assert server.name == "OMNI Messaging"
        assert hasattr(server, "tool")

    async def test_server_has_tools(self, server):
        """Test server has expected tools registered"""
        # FastMCP registers tools differently, let's check they exist
        assert hasattr(server, "get_tools")
        # The tools should be registered via the @mcp.tool() decorator
        tools = await server.get_tools()
        assert len(tools) > 0


class TestManageInstances:
    """Test manage_instances tool"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OMNI client"""
        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            MockClient.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_list_instances(self, mock_client):
        """Test listing instances"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        # Mock the response
        mock_instance = Mock()
        mock_instance.model_dump.return_value = {
            "id": 1,
            "name": "test-instance",
            "channel_type": "whatsapp",
            "is_active": True,
        }
        mock_client.list_instances.return_value = [mock_instance]

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_instances_fn(operation=InstanceOperation.LIST)
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["count"] == 1
            assert result_data["instances"][0]["name"] == "test-instance"
            mock_client.list_instances.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_instance(self, mock_client):
        """Test creating an instance"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        mock_instance = Mock()
        mock_instance.name = "new-instance"
        mock_instance.model_dump.return_value = {
            "name": "new-instance",
            "channel_type": "whatsapp",
        }
        mock_client.create_instance.return_value = mock_instance

        config = {"name": "new-instance", "channel_type": "whatsapp", "auto_qr": True}

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_instances_fn(
                operation=InstanceOperation.CREATE, config=config
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert "Instance 'new-instance' created" in result_data["message"]
            mock_client.create_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instance_qr(self, mock_client):
        """Test getting instance QR code"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        mock_qr = Mock()
        mock_qr.model_dump.return_value = {
            "instance_name": "test-instance",
            "qr_code": "base64_qr_data",
            "status": "pending",
        }
        mock_client.get_instance_qr.return_value = mock_qr

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_instances_fn(
                operation=InstanceOperation.QR, instance_name="test-instance"
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["qr"]["qr_code"] == "base64_qr_data"
            mock_client.get_instance_qr.assert_called_once_with("test-instance")

    @pytest.mark.asyncio
    async def test_instance_operation_error_handling(self, mock_client):
        """Test error handling in instance operations"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        # Test missing instance_name for operations that require it
        result = await manage_instances_fn(operation=InstanceOperation.GET)
        result_data = json.loads(result)
        assert "error" in result_data
        assert "instance_name required" in result_data["error"]

        # Test API error handling
        mock_client.get_instance.side_effect = Exception("API Error")

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_instances_fn(
                operation=InstanceOperation.GET, instance_name="test"
            )
            result_data = json.loads(result)
            assert "error" in result_data
            assert "API Error" in result_data["error"]


class TestSendMessage:
    """Test send_message tool"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OMNI client"""
        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            MockClient.return_value = client
            yield client

    @pytest.fixture
    def mock_config(self):
        """Create mock config with default instance"""
        config = Mock()
        config.default_instance = "test-instance"
        return config

    @pytest.mark.asyncio
    async def test_send_text_message(self, mock_client):
        """Test sending text message"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.message_id = "msg_123"
        mock_response.status = "sent"
        mock_client.send_text.return_value = mock_response

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await send_message_fn(
                message_type=MessageType.TEXT,
                instance_name="test-instance",
                phone="+1234567890",
                message="Hello World!",
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["message_id"] == "msg_123"
            assert result_data["type"] == "text"
            mock_client.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_media_message(self, mock_client):
        """Test sending media message"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.message_id = "media_123"
        mock_response.status = "sent"
        mock_client.send_media.return_value = mock_response

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await send_message_fn(
                message_type=MessageType.MEDIA,
                instance_name="test-instance",
                phone="+1234567890",
                media_url="https://example.com/image.jpg",
                media_type="image",
                caption="Test image",
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["message_id"] == "media_123"
            assert result_data["type"] == "media"
            mock_client.send_media.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_contact_message(self, mock_client):
        """Test sending contact message"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.message_id = "contact_123"
        mock_response.status = "sent"
        mock_client.send_contact.return_value = mock_response

        contacts = [
            {
                "full_name": "John Doe",
                "phone_number": "+0987654321",
                "email": "john@example.com",
            }
        ]

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await send_message_fn(
                message_type=MessageType.CONTACT,
                instance_name="test-instance",
                phone="+1234567890",
                contacts=contacts,
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["type"] == "contact"
            mock_client.send_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_default_instance(self, mock_client, mock_config):
        """Test sending message with default instance"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.message_id = "msg_123"
        mock_response.status = "sent"
        mock_client.send_text.return_value = mock_response

        with patch("automagik_tools.tools.omni._config", mock_config):
            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=mock_client
            ):
                result = await send_message_fn(
                    message_type=MessageType.TEXT,
                    phone="+1234567890",
                    message="Using default instance",
                )
                result_data = json.loads(result)

                assert result_data["success"] is True
                assert result_data["instance"] == "test-instance"

    @pytest.mark.asyncio
    async def test_send_message_error_handling(self, mock_client):
        """Test error handling in send_message"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        # Test missing required parameters
        result = await send_message_fn(
            message_type=MessageType.TEXT, instance_name="test"
        )
        result_data = json.loads(result)
        assert "error" in result_data
        assert "phone and message required" in result_data["error"]


class TestManageTraces:
    """Test manage_traces tool"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OMNI client"""
        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            MockClient.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_list_traces(self, mock_client):
        """Test listing traces with filters"""
        from automagik_tools.tools.omni import manage_traces

        manage_traces_fn = (
            manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces
        )

        mock_trace = Mock()
        mock_trace.model_dump.return_value = {
            "id": "trace_123",
            "instance_name": "test-instance",
            "sender_phone": "+1234567890",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
        }
        mock_client.list_traces.return_value = [mock_trace]

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_traces_fn(
                operation=TraceOperation.LIST, instance_name="test-instance", limit=10
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["count"] == 1
            assert result_data["traces"][0]["id"] == "trace_123"
            mock_client.list_traces.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trace_analytics(self, mock_client):
        """Test getting trace analytics"""
        from automagik_tools.tools.omni import manage_traces

        manage_traces_fn = (
            manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces
        )

        mock_analytics = Mock()
        mock_analytics.model_dump.return_value = {
            "total_traces": 100,
            "by_status": {"completed": 80, "failed": 20},
            "by_instance": {"test-instance": 100},
            "error_rate": 0.2,
        }
        mock_client.get_trace_analytics.return_value = mock_analytics

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_traces_fn(
                operation=TraceOperation.ANALYTICS,
                start_date="2024-01-01",
                instance_name="test-instance",
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["analytics"]["total_traces"] == 100
            assert result_data["analytics"]["error_rate"] == 0.2

    @pytest.mark.asyncio
    async def test_cleanup_traces(self, mock_client):
        """Test trace cleanup operation"""
        from automagik_tools.tools.omni import manage_traces

        manage_traces_fn = (
            manage_traces.fn if hasattr(manage_traces, "fn") else manage_traces
        )

        mock_client.cleanup_traces.return_value = {
            "deleted_count": 50,
            "status": "completed",
        }

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_traces_fn(
                operation=TraceOperation.CLEANUP, days_old=30, dry_run=True
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["dry_run"] is True
            assert result_data["days_old"] == 30
            mock_client.cleanup_traces.assert_called_once_with(30, True)


class TestManageProfiles:
    """Test manage_profiles tool"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OMNI client"""
        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            MockClient.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_fetch_profile(self, mock_client):
        """Test fetching user profile"""
        from automagik_tools.tools.omni import manage_profiles

        manage_profiles_fn = (
            manage_profiles.fn if hasattr(manage_profiles, "fn") else manage_profiles
        )

        mock_client.fetch_profile.return_value = {
            "name": "John Doe",
            "phone": "+1234567890",
            "status": "Available",
            "picture_url": "https://example.com/profile.jpg",
        }

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_profiles_fn(
                operation=ProfileOperation.FETCH,
                instance_name="test-instance",
                phone_number="+1234567890",
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["profile"]["name"] == "John Doe"
            mock_client.fetch_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_picture(self, mock_client):
        """Test updating profile picture"""
        from automagik_tools.tools.omni import manage_profiles

        manage_profiles_fn = (
            manage_profiles.fn if hasattr(manage_profiles, "fn") else manage_profiles
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.status = "updated"
        mock_client.update_profile_picture.return_value = mock_response

        with patch(
            "automagik_tools.tools.omni._ensure_client", return_value=mock_client
        ):
            result = await manage_profiles_fn(
                operation=ProfileOperation.UPDATE_PICTURE,
                instance_name="test-instance",
                picture_url="https://example.com/new-profile.jpg",
            )
            result_data = json.loads(result)

            assert result_data["success"] is True
            assert result_data["message"] == "Profile picture updated"
            mock_client.update_profile_picture.assert_called_once()


class TestFlexibleSchemaSupport:
    """Test flexible schema support for future API updates"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        from automagik_tools.tools.omni.config import OmniConfig

        return OmniConfig(
            api_key="test-api-key",
            base_url="http://test.omni.api",
            timeout=10,
            max_retries=3,
        )

    @pytest.fixture
    def tool_instance(self, mock_config):
        """Create a tool instance with mock config"""
        return create_server(mock_config)

    @pytest.mark.unit
    def test_instance_config_accepts_discord_fields(self):
        """Test that InstanceConfig accepts Discord-specific fields"""

        # Create config with Discord fields
        config = InstanceConfig(
            name="test-discord",
            channel_type=ChannelType.DISCORD,
            discord_bot_token="test-token",
            discord_client_id="test-client-id",
            discord_public_key="test-public-key",
            discord_voice_enabled=True,
            discord_slash_commands_enabled=True,
            agent_api_url="http://localhost:8886",
            agent_api_key="test-key",
            default_agent="test-agent",
        )

        assert config.name == "test-discord"
        assert config.channel_type == ChannelType.DISCORD
        assert config.discord_bot_token == "test-token"
        assert config.discord_client_id == "test-client-id"
        assert config.discord_public_key == "test-public-key"

    @pytest.mark.unit
    def test_instance_config_accepts_slack_fields(self):
        """Test that InstanceConfig accepts Slack-specific fields"""

        # Create config with Slack fields
        config = InstanceConfig(
            name="test-slack",
            channel_type=ChannelType.SLACK,
            slack_bot_token="xoxb-test-token",
            slack_app_token="xapp-test-token",
            slack_signing_secret="test-secret",
            slack_workspace_id="T12345",
            agent_api_url="http://localhost:8886",
        )

        assert config.name == "test-slack"
        assert config.channel_type == ChannelType.SLACK
        assert config.slack_bot_token == "xoxb-test-token"
        assert config.slack_app_token == "xapp-test-token"

    @pytest.mark.unit
    def test_instance_config_accepts_arbitrary_fields(self):
        """Test that InstanceConfig accepts any future fields"""

        # Create config with arbitrary future fields
        config = InstanceConfig(
            name="test-future",
            channel_type=ChannelType.WHATSAPP,
            future_field_1="value1",
            future_nested_config={"key": "value"},
            future_list_field=[1, 2, 3],
            completely_unknown_field=True,
        )

        assert config.name == "test-future"
        assert config.future_field_1 == "value1"
        assert config.future_nested_config == {"key": "value"}
        assert config.future_list_field == [1, 2, 3]
        assert config.completely_unknown_field is True

    @pytest.mark.unit
    def test_all_models_accept_extra_fields(self):
        """Test that all Omni models accept extra fields"""
        from automagik_tools.tools.omni.models import (
            InstanceResponse,
            ConnectionStatus,
            QRCodeResponse,
            MessageResponse,
        )

        # Test each model accepts extra fields (with required fields included)
        models_to_test = [
            (InstanceResponse, {"name": "test", "extra_field": "value"}),
            (
                ConnectionStatus,
                {
                    "instance_name": "test",
                    "channel_type": "whatsapp",
                    "status": "connected",
                    "new_status_field": True,
                },
            ),
            (
                QRCodeResponse,
                {
                    "instance_name": "test",
                    "connection_type": "qr",
                    "status": "pending",
                    "qr_code": "data",
                    "qr_metadata": {"size": 256},
                },
            ),
            (SendTextRequest, {"phone": "123", "text": "hi", "delivery_receipt": True}),
            (
                SendMediaRequest,
                {"phone": "123", "media_url": "http://test", "media_metadata": {}},
            ),
            (
                MessageResponse,
                {"message_id": "123", "success": True, "extra_response_data": "test"},
            ),
        ]

        for model_class, data in models_to_test:
            instance = model_class(**data)
            # Should not raise validation errors
            assert instance is not None
            # Check that model was created without errors
            # Note: Extra fields might not be directly accessible as attributes
            # but are stored in the model's __pydantic_extra__ if ConfigDict(extra="allow")

    @pytest.mark.unit
    def test_json_string_parsing(self):
        """Test that JSON string config parsing works correctly"""
        import json

        # Test JSON string parsing (simulating MCP input)
        config_json = json.dumps(
            {
                "name": "test-discord",
                "channel_type": "discord",
                "discord_bot_token": "test-token",
                "discord_client_id": "test-client",
                "discord_public_key": "test-key",
                "is_active": True,
            }
        )

        # Parse JSON string back to dict
        config_dict = json.loads(config_json)

        # Create model from parsed dict
        config = InstanceConfig(**config_dict)

        assert config.name == "test-discord"
        assert config.channel_type == ChannelType.DISCORD
        assert config.discord_bot_token == "test-token"
        assert config.is_active is True


class TestOmniIntegration:
    """Test integration with automagik hub"""

    @pytest.mark.asyncio
    async def test_tool_import(self):
        """Test that tool can be imported correctly"""
        from automagik_tools.tools.omni import (
            create_server,
            get_metadata,
            get_config_class,
        )

        assert create_server is not None
        assert get_metadata is not None
        assert get_config_class is not None

    def test_tool_discovery(self):
        """Test tool is discoverable by the framework"""
        import importlib

        # Test module can be imported
        module = importlib.import_module("automagik_tools.tools.omni")

        # Test required exports exist
        assert hasattr(module, "create_server")
        assert hasattr(module, "get_metadata")
        assert hasattr(module, "get_config_class")

        # Test metadata is valid
        metadata = module.get_metadata()
        assert isinstance(metadata, dict)
        assert metadata["name"] == "omni"


class TestOmniErrorHandling:
    """Test error scenarios"""

    @pytest.mark.asyncio
    async def test_missing_config_error(self):
        """Test behavior with missing API key"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        # Clear any existing config
        import automagik_tools.tools.omni as omni_module

        omni_module._config = None
        omni_module._client = None

        # Try to use tool without config
        with pytest.raises(ValueError, match="OMNI_API_KEY is required"):
            await manage_instances_fn(operation=InstanceOperation.LIST)

    @pytest.mark.asyncio
    async def test_api_connection_error(self):
        """Test handling of API connection errors"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            client.list_instances.side_effect = ConnectionError("Cannot connect to API")
            MockClient.return_value = client

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                result = await manage_instances_fn(operation=InstanceOperation.LIST)
                result_data = json.loads(result)

                assert "error" in result_data
                assert "Cannot connect to API" in result_data["error"]

    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test handling of invalid operations"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        with patch("automagik_tools.tools.omni._ensure_client"):
            result = await manage_instances_fn(operation="invalid_op")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Unknown operation" in result_data["error"]


class TestOmniEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_instance_list(self):
        """Test handling of empty instance list"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            client.list_instances.return_value = []
            MockClient.return_value = client

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                result = await manage_instances_fn(operation=InstanceOperation.LIST)
                result_data = json.loads(result)

                assert result_data["success"] is True
                assert result_data["count"] == 0
                assert result_data["instances"] == []

    @pytest.mark.asyncio
    async def test_large_message_payload(self):
        """Test handling of large message payloads"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            mock_response = Mock()
            mock_response.success = True
            mock_response.message_id = "large_msg"
            mock_response.status = "sent"
            client.send_text.return_value = mock_response
            MockClient.return_value = client

            large_message = "x" * 10000  # 10KB message

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                result = await send_message_fn(
                    message_type=MessageType.TEXT,
                    instance_name="test",
                    phone="+1234567890",
                    message=large_message,
                )
                result_data = json.loads(result)

                assert result_data["success"] is True
                client.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self):
        """Test handling of special characters in messages"""
        from automagik_tools.tools.omni import send_message

        send_message_fn = (
            send_message.fn if hasattr(send_message, "fn") else send_message
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            mock_response = Mock()
            mock_response.success = True
            mock_response.message_id = "special_msg"
            mock_response.status = "sent"
            client.send_text.return_value = mock_response
            MockClient.return_value = client

            special_message = 'Hello 👋 World! @#$%^&*() \n\t"quotes"'

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                result = await send_message_fn(
                    message_type=MessageType.TEXT,
                    instance_name="test",
                    phone="+1234567890",
                    message=special_message,
                )
                result_data = json.loads(result)

                assert result_data["success"] is True


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance"""

    @pytest.mark.mcp
    def test_server_exports(self):
        """Test server exports required functions"""
        from automagik_tools.tools.omni import (
            create_server,
            get_metadata,
            get_config_class,
        )

        assert callable(create_server)
        assert callable(get_metadata)
        assert callable(get_config_class)

    @pytest.mark.mcp
    def test_metadata_format(self):
        """Test metadata follows MCP format"""
        from automagik_tools.tools.omni import get_metadata

        metadata = get_metadata()

        # Required fields for MCP tools
        assert isinstance(metadata, dict)
        assert isinstance(metadata.get("name"), str)
        assert isinstance(metadata.get("version"), str)
        assert isinstance(metadata.get("description"), str)

    @pytest.mark.mcp
    def test_tool_functions_return_json(self):
        """Test all tool functions return JSON strings"""
        # This is tested implicitly in other tests
        # All our tool functions return JSON strings via json.dumps()
        pass

    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test tools execute asynchronously"""
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )
        import asyncio

        # Test that tool functions are coroutines
        coro = manage_instances_fn(operation=InstanceOperation.LIST)
        assert asyncio.iscoroutine(coro)

        # Clean up the coroutine
        try:
            await coro
        except:
            pass  # Expected to fail without proper setup


# Performance tests (optional but good to have)
class TestOmniPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_response_time(self):
        """Test tool response time"""
        import time
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            client.list_instances.return_value = []
            MockClient.return_value = client

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                start = time.time()
                await manage_instances_fn(operation=InstanceOperation.LIST)
                duration = time.time() - start

                # Should respond quickly for mocked calls
                assert duration < 0.5  # 500ms threshold

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_operations(self):
        """Test handling of concurrent operations"""
        import asyncio
        import time
        from automagik_tools.tools.omni import manage_instances

        manage_instances_fn = (
            manage_instances.fn if hasattr(manage_instances, "fn") else manage_instances
        )

        with patch("automagik_tools.tools.omni.OmniClient") as MockClient:
            client = AsyncMock()
            client.list_instances.return_value = []
            MockClient.return_value = client

            with patch(
                "automagik_tools.tools.omni._ensure_client", return_value=client
            ):
                # Run multiple operations concurrently
                tasks = [
                    manage_instances_fn(operation=InstanceOperation.LIST)
                    for _ in range(10)
                ]

                start = time.time()
                results = await asyncio.gather(*tasks)
                duration = time.time() - start

                # All should complete successfully
                assert len(results) == 10
                for result in results:
                    result_data = json.loads(result)
                    assert result_data["success"] is True

                # Should handle concurrent requests efficiently
                assert duration < 1.0  # 1 second for 10 concurrent requests
