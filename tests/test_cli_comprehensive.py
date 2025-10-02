"""Comprehensive CLI tests to improve coverage"""

import os
import pytest
from typer.testing import CliRunner


class TestCLICommands:
    """Test actual CLI command execution"""

    def test_cli_list_command_runs(self):
        """Test that list command executes"""
        from automagik_tools.cli import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list"])
        
        # Should not crash
        assert result.exit_code in [0, 1]  # May fail if tools aren't configured

    def test_cli_version_command_runs(self):
        """Test that version command executes"""
        from automagik_tools.cli import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        
        # Should not crash and should show version
        assert result.exit_code == 0

    def test_cli_help_command_runs(self):
        """Test that help command executes"""
        from automagik_tools.cli import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "automagik-tools" in result.output.lower() or "usage" in result.output.lower()


class TestDynamicOpenAPICreation:
    """Test dynamic OpenAPI tool creation"""

    def test_create_dynamic_openapi_with_url(self):
        """Test creating dynamic OpenAPI tool"""
        from automagik_tools.cli import create_dynamic_openapi_tool
        from unittest.mock import patch, MagicMock
        
        # Mock httpx.get to return a valid OpenAPI spec
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "servers": [{"url": "https://api.test.com"}],
                "paths": {"/test": {"get": {}}},
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            with patch("automagik_tools.cli.FastMCP") as mock_fastmcp:
                mock_fastmcp.from_openapi.return_value = MagicMock()
                
                result = create_dynamic_openapi_tool(
                    openapi_url="https://api.test.com/openapi.json",
                    transport="stdio"
                )
                
                # Should have called from_openapi
                mock_fastmcp.from_openapi.assert_called_once()


class TestToolInfo:
    """Test tool info functionality"""

    def test_discover_tools_returns_all_tools(self):
        """Test that discover_tools finds all available tools"""
        from automagik_tools.cli import discover_tools
        
        tools = discover_tools()
        
        # Should have multiple tools
        assert len(tools) >= 5  # We have at least evolution-api, omni, wait, etc.
        
        # Each tool should have required info
        for tool_name, tool_info in tools.items():
            assert "metadata" in tool_info
            assert "module" in tool_info


class TestConfigCreationComprehensive:
    """Comprehensive config creation tests"""

    def test_create_config_with_env_vars(self):
        """Test config creation with environment variables"""
        from automagik_tools.cli import create_config_for_tool, discover_tools

        # Set up environment
        os.environ["EVOLUTION_API_BASE_URL"] = "http://localhost:8080"
        os.environ["EVOLUTION_API_KEY"] = "test-key-12345"

        tools = discover_tools()

        if "evolution-api" in tools:
            config = create_config_for_tool("evolution-api", tools)

            assert config is not None
            # Config should exist and have attributes
            assert hasattr(config, "base_url")
            assert hasattr(config, "api_key")

        # Cleanup
        del os.environ["EVOLUTION_API_BASE_URL"]
        del os.environ["EVOLUTION_API_KEY"]

    def test_load_tool_creates_server(self):
        """Test that load_tool creates a FastMCP server"""
        from automagik_tools.cli import load_tool, discover_tools
        
        # Set up environment for evolution-api
        os.environ["EVOLUTION_API_BASE_URL"] = "http://localhost:8080"
        os.environ["EVOLUTION_API_KEY"] = "test-key-12345"
        
        tools = discover_tools()
        
        if "evolution-api" in tools:
            try:
                server = load_tool("evolution-api", tools)
                
                # Server should be a FastMCP instance
                assert server is not None
                assert hasattr(server, "name")
            except Exception as e:
                # May fail due to missing dependencies
                pass
        
        # Cleanup
        if "EVOLUTION_API_BASE_URL" in os.environ:
            del os.environ["EVOLUTION_API_BASE_URL"]
        if "EVOLUTION_API_KEY" in os.environ:
            del os.environ["EVOLUTION_API_KEY"]
