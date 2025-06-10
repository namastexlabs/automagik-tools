"""
Simple CLI tests that don't hang - focused on basic functionality
"""

import pytest
from automagik_tools.cli import (
    discover_tools,
    create_config_for_tool,
    create_dynamic_openapi_tool,
)
from automagik_tools.cli import app
import subprocess
from unittest.mock import patch, MagicMock


class TestCLIQuick:
    """Quick CLI tests that don't start servers"""

    def test_import_cli(self):
        """Test that CLI module imports correctly"""
        from automagik_tools.cli import main

        assert callable(main)
        assert app is not None

    def test_discover_tools_function(self):
        """Test the discover_tools function directly"""
        tools = discover_tools()
        assert "evolution-api" in tools
        assert tools["evolution-api"]["name"] == "evolution-api"

    def test_create_config_function(self):
        """Test the create_config_for_tool function directly"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)
        assert hasattr(config, "base_url")
        assert hasattr(config, "api_key")

    def test_basic_cli_commands(self):
        """Test basic CLI commands that should be fast"""
        # Test help
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['--help'])"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Note: help typically exits with code 0 in some CLI frameworks
        assert "MCP Tools Framework" in result.stdout or "Usage:" in result.stdout

    def test_version_command_direct(self):
        """Test version command directly"""
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['version'])"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "automagik-tools v" in result.stdout

    def test_list_command_direct(self):
        """Test list command directly"""
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['list'])"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "evolution-api" in result.stdout


class TestCLIValidation:
    """Test CLI validation without starting servers"""

    def test_invalid_tool_handling(self):
        """Test handling of invalid tool names"""
        tools = discover_tools()
        # Should not contain invalid tools
        assert "nonexistent-tool" not in tools

    def test_tool_metadata_complete(self):
        """Test that tools have complete metadata"""
        tools = discover_tools()
        evolution_tool = tools["evolution-api"]

        required_fields = ["name", "type", "status", "description", "entry_point"]
        for field in required_fields:
            assert field in evolution_tool
            assert evolution_tool[field] is not None


class TestDynamicOpenAPITool:
    """Test dynamic OpenAPI tool creation"""

    @patch("httpx.get")
    @patch("automagik_tools.cli.FastMCP.from_openapi")
    def test_create_dynamic_openapi_tool(self, mock_from_openapi, mock_get):
        """Test creating a dynamic tool from OpenAPI spec"""
        # Mock the OpenAPI spec response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "description": "Test API Description",
                "version": "1.0.0",
            },
            "servers": [{"url": "https://api.test.com"}],
            "paths": {},
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Mock FastMCP.from_openapi
        mock_mcp_server = MagicMock()
        mock_from_openapi.return_value = mock_mcp_server

        # Test creating dynamic tool
        result = create_dynamic_openapi_tool(
            openapi_url="https://api.test.com/openapi.json",
            api_key="test-key",
            transport="sse",
        )

        # Verify the calls
        mock_get.assert_called_once_with(
            "https://api.test.com/openapi.json", timeout=30
        )
        mock_from_openapi.assert_called_once()

        # Verify FastMCP.from_openapi was called with correct parameters
        call_args = mock_from_openapi.call_args
        assert call_args[1]["name"] == "Test API"
        assert call_args[1]["instructions"] == "Test API Description"
        assert result == mock_mcp_server

    @patch("httpx.get")
    def test_create_dynamic_openapi_tool_fetch_error(self, mock_get):
        """Test error handling when fetching OpenAPI spec fails"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(ValueError, match="Failed to fetch OpenAPI spec"):
            create_dynamic_openapi_tool(
                openapi_url="https://api.test.com/openapi.json", transport="sse"
            )

    @patch("httpx.get")
    def test_create_dynamic_openapi_tool_no_servers(self, mock_get):
        """Test handling OpenAPI spec without servers"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "openapi": "3.0.0",
            "info": {"title": "Test API"},
            "paths": {},
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch("automagik_tools.cli.FastMCP.from_openapi") as mock_from_openapi:
            mock_from_openapi.return_value = MagicMock()

            result = create_dynamic_openapi_tool(
                openapi_url="https://api.test.com/openapi.json", transport="sse"
            )

            # Should extract base URL from OpenAPI URL
            call_args = mock_from_openapi.call_args
            client = call_args[1]["client"]
            assert client.base_url == "https://api.test.com"


# Mark all tests in this module as fast
pytestmark = pytest.mark.unit
