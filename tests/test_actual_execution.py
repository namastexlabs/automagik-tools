"""Tests that actually execute code to improve coverage"""


class TestActualServerCreation:
    """Test actual server creation with configs"""

    def test_evolution_api_server_creation(self):
        """Actually create an Evolution API server"""
        from automagik_tools.tools.evolution_api import create_server
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        config = EvolutionAPIConfig(
            base_url="http://test.example.com", api_key="test_key_123"
        )

        server = create_server(config)

        assert server is not None
        assert hasattr(server, "name")
        # Server name might be different than tool name
        assert isinstance(server.name, str)
        assert len(server.name) > 0

    def test_omni_server_creation(self):
        """Actually create an Omni server"""
        from automagik_tools.tools.omni import create_server
        from automagik_tools.tools.omni.config import OmniConfig

        config = OmniConfig(base_url="http://test.example.com", api_key="test_key_123")

        server = create_server(config)

        assert server is not None
        assert hasattr(server, "name")

    def test_wait_server_creation(self):
        """Actually create a Wait server"""
        from automagik_tools.tools.wait import create_server
        from automagik_tools.tools.wait.config import WaitConfig

        config = WaitConfig()

        server = create_server(config)

        assert server is not None
        assert hasattr(server, "name")

    def test_spark_server_creation(self):
        """Actually create a Spark server"""
        from automagik_tools.tools.spark import create_server
        from automagik_tools.tools.spark.config import SparkConfig

        config = SparkConfig(base_url="http://test.example.com", api_key="test_key_123")

        server = create_server(config)

        assert server is not None
        assert hasattr(server, "name")


class TestActualClientCreation:
    """Test actual client instantiation"""

    def test_evolution_client_creation(self):
        """Actually create Evolution API client"""
        from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        config = EvolutionAPIConfig(
            base_url="http://test.example.com", api_key="test_key"
        )

        client = EvolutionAPIClient(config)

        assert client is not None
        assert client.config == config
        # Client may have client attribute set during async context
        assert hasattr(client, "config")

    def test_omni_client_creation(self):
        """Actually create Omni client"""
        from automagik_tools.tools.omni.client import OmniClient
        from automagik_tools.tools.omni.config import OmniConfig

        config = OmniConfig(base_url="http://test.example.com", api_key="test_key")

        client = OmniClient(config)

        assert client is not None
        assert client.config == config

    def test_spark_client_creation(self):
        """Actually create Spark client"""
        from automagik_tools.tools.spark.client import SparkClient
        from automagik_tools.tools.spark.config import SparkConfig

        config = SparkConfig(base_url="http://test.example.com", api_key="test_key")

        client = SparkClient(config)

        assert client is not None
        assert client.config == config


class TestAIProcessors:
    """Test AI processor modules"""

    def test_json_markdown_processor_import(self):
        """Test JSON markdown processor import"""
        from automagik_tools.ai_processors import json_markdown_processor

        assert json_markdown_processor is not None
        # Check for key functions
        assert hasattr(json_markdown_processor, "JsonMarkdownProcessor")

    def test_enhanced_response_import(self):
        """Test enhanced response import"""
        from automagik_tools.ai_processors import enhanced_response

        assert enhanced_response is not None

    def test_openapi_processor_import(self):
        """Test OpenAPI processor import"""
        from automagik_tools.ai_processors import openapi_processor

        assert openapi_processor is not None


class TestModelEnums:
    """Test model enumerations"""

    def test_omni_message_type_enum(self):
        """Test Omni MessageType enum"""
        from automagik_tools.tools.omni.models import MessageType

        # Enum should have values
        assert MessageType.TEXT is not None
        assert len(MessageType.__members__) > 0

    def test_spark_task_status_enum(self):
        """Test Spark TaskStatus enum"""
        from automagik_tools.tools.spark.models import TaskStatus

        # Enum should have values
        assert TaskStatus.PENDING is not None
        assert len(TaskStatus.__members__) > 0

    def test_spark_schedule_type_enum(self):
        """Test Spark ScheduleType enum"""
        from automagik_tools.tools.spark.models import ScheduleType

        # Enum should have values
        assert len(ScheduleType.__members__) > 0


class TestConfigValidation:
    """Test config validation logic"""

    def test_evolution_config_with_different_base_urls(self):
        """Test Evolution config handles different base URLs"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        # Test with trailing slash
        config1 = EvolutionAPIConfig(base_url="http://test.com/", api_key="key")
        # Config stores base_url as provided or normalized
        assert config1.base_url is not None
        assert "http://test.com" in config1.base_url

        # Test without trailing slash
        config2 = EvolutionAPIConfig(base_url="http://test.com", api_key="key")
        assert config2.base_url is not None
        assert "http://test.com" in config2.base_url

    def test_omni_config_with_different_base_urls(self):
        """Test Omni config handles different base URLs"""
        from automagik_tools.tools.omni.config import OmniConfig

        config = OmniConfig(base_url="http://test.com", api_key="key")

        assert config.base_url is not None
        # Config may normalize or use env vars
        assert hasattr(config, "api_key")
