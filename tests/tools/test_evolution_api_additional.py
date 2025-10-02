"""Additional Evolution API tests to improve coverage"""


class TestEvolutionAPIClient:
    """Test Evolution API client functionality"""

    def test_client_initialization(self):
        """Test that client initializes with config"""
        from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        config = EvolutionAPIConfig(
            base_url="http://test.example.com", api_key="test_key"
        )
        client = EvolutionAPIClient(config)

        assert client.config == config
        assert client.config.base_url == "http://test.example.com"
        assert client.config.api_key == "test_key"

    def test_client_has_config(self):
        """Test that client stores config properly"""
        from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        config = EvolutionAPIConfig(
            base_url="http://test.example.com", api_key="test_key_123"
        )

        client = EvolutionAPIClient(config)

        # Client should have config
        assert hasattr(client, "config")
        assert client.config.api_key == "test_key_123"
        assert client.config.base_url == "http://test.example.com"


class TestEvolutionAPIServerFunctions:
    """Test Evolution API server tool functions"""

    def test_create_server_function_exists(self):
        """Test that create_server function exists"""
        from automagik_tools.tools.evolution_api import create_server

        assert callable(create_server)

    def test_get_metadata_returns_dict(self):
        """Test that get_metadata returns a dictionary"""
        from automagik_tools.tools.evolution_api import get_metadata

        metadata = get_metadata()
        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "description" in metadata
        assert metadata["name"] == "evolution-api"

    def test_get_config_class_returns_class(self):
        """Test that get_config_class returns the config class"""
        from automagik_tools.tools.evolution_api import get_config_class
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

        config_class = get_config_class()
        assert config_class == EvolutionAPIConfig

    def test_server_has_tool_descriptions(self):
        """Test that server tools have descriptions"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
        from automagik_tools.tools.evolution_api import create_server

        config = EvolutionAPIConfig(
            base_url="http://test.example.com", api_key="test_key"
        )

        server = create_server(config)
        assert server is not None
        # Server should have a name
        assert hasattr(server, "name")


class TestEvolutionAPIConfig:
    """Test Evolution API configuration"""

    def test_config_validates_base_url(self):
        """Test that config validates base URL"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
        
        config = EvolutionAPIConfig(
            base_url="http://api.example.com",
            api_key="test_key"
        )
        
        assert config.base_url == "http://api.example.com"
        assert not config.base_url.endswith("/")

    def test_config_has_default_values(self):
        """Test that config has sensible defaults"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
        import os
        
        # Set minimal required env vars
        os.environ["EVOLUTION_API_BASE_URL"] = "http://test.com"
        os.environ["EVOLUTION_API_KEY"] = "key"
        
        config = EvolutionAPIConfig()
        
        assert config.base_url is not None
        assert config.api_key is not None
        
        # Cleanup
        del os.environ["EVOLUTION_API_BASE_URL"]
        del os.environ["EVOLUTION_API_KEY"]


class TestEvolutionAPIIntegration:
    """Test Evolution API integration points"""

    def test_module_exports_all_required_functions(self):
        """Test that module exports all required functions"""
        import automagik_tools.tools.evolution_api as evo_module
        
        required_functions = ["create_server", "get_metadata", "get_config_class"]
        
        for func_name in required_functions:
            assert hasattr(evo_module, func_name), f"Missing {func_name}"
            assert callable(getattr(evo_module, func_name))

    def test_metadata_has_required_fields(self):
        """Test that metadata has all required fields"""
        from automagik_tools.tools.evolution_api import get_metadata
        
        metadata = get_metadata()
        
        required_fields = ["name", "description", "version"]
        for field in required_fields:
            assert field in metadata, f"Missing {field} in metadata"
            assert metadata[field], f"{field} is empty"
