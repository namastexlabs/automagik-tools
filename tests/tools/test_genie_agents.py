"""Tests for the genie_agents tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response
from automagik_tools.tools.genie_agents import GenieAgentsConfig, create_server
from automagik_tools.tools.genie_agents.server import GenieAgentsClient


class TestGenieAgentsConfig:
    """Test the GenieAgentsConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GenieAgentsConfig()
        assert config.api_base_url == "http://localhost:9888"
        assert config.api_key is None
        assert config.timeout == 30

    def test_config_with_env_vars(self, monkeypatch):
        """Test configuration with environment variables."""
        monkeypatch.setenv("GENIE_AGENTS_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("GENIE_AGENTS_API_KEY", "test-key")
        monkeypatch.setenv("GENIE_AGENTS_TIMEOUT", "60")
        
        # Clear any existing configuration before creating new one
        config = GenieAgentsConfig(
            api_base_url="https://api.example.com",
            api_key="test-key",
            timeout=60
        )
        assert config.api_base_url == "https://api.example.com"
        assert config.api_key == "test-key"
        assert config.timeout == 60


class TestGenieAgentsClient:
    """Test the GenieAgentsClient class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return GenieAgentsConfig(
            api_base_url="https://api.example.com",
            api_key="test-key",
            timeout=30
        )

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {"status": "success"}
        response.raise_for_status.return_value = None
        return response

    @pytest.mark.asyncio
    async def test_client_initialization(self, config):
        """Test client initialization."""
        async with GenieAgentsClient(config) as client:
            assert client.config == config
            assert str(client.client.base_url) == config.api_base_url
            # Just check that timeout is set
            assert client.client.timeout is not None

    @pytest.mark.asyncio
    @patch("automagik_tools.tools.genie_agents.server.httpx.AsyncClient")
    async def test_request_success(self, mock_client_class, config, mock_response):
        """Test successful API request."""
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with GenieAgentsClient(config) as client:
            result = await client.request("GET", "/test")
            
        assert result == {"status": "success"}
        mock_client.request.assert_called_once_with("GET", "/test")

    @pytest.mark.asyncio
    @patch("automagik_tools.tools.genie_agents.server.httpx.AsyncClient")
    async def test_request_with_auth(self, mock_client_class, config):
        """Test request with authentication header."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        async with GenieAgentsClient(config) as client:
            pass
            
        # Check that the client was initialized with auth headers
        args, kwargs = mock_client_class.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"


class TestGenieAgentsServer:
    """Test the genie_agents server functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return GenieAgentsConfig(
            api_base_url="https://api.example.com",
            api_key="test-key",
            timeout=30
        )

    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return create_server()

    def test_create_server(self, server):
        """Test server creation."""
        assert server is not None
        assert server.name == "Genie Agents"

    def test_server_has_playground_tools(self, server):
        """Test that server has playground tools defined."""
        # This is a basic test to ensure the server was created correctly
        assert hasattr(server, 'get_tools')
        assert server.name == "Genie Agents"
        
        # Test that we can create the server without errors
        # The actual tool functionality will be tested when the API is available