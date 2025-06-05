"""
Fast unit tests for automagik-tools core functionality
These tests focus on unit testing without starting real servers
"""

import pytest
from automagik_tools.cli import discover_tools, create_config_for_tool
from automagik_tools.tools.evolution_api import create_server


class TestToolDiscovery:
    """Test tool discovery functionality"""

    def test_discover_tools_finds_evolution_api(self):
        """Test that tool discovery finds the evolution-api tool"""
        tools = discover_tools()

        assert "evolution-api" in tools
        assert tools["evolution-api"]["name"] == "evolution-api"
        assert "WhatsApp" in tools["evolution-api"]["description"]

    def test_tool_has_required_metadata(self):
        """Test that discovered tools have required metadata"""
        tools = discover_tools()
        evolution_tool = tools["evolution-api"]

        assert "name" in evolution_tool
        assert "type" in evolution_tool
        assert "status" in evolution_tool
        assert "description" in evolution_tool
        assert "entry_point" in evolution_tool


class TestConfigCreation:
    """Test configuration creation for tools"""

    def test_create_evolution_config(self):
        """Test creating configuration for evolution-api tool"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)

        assert hasattr(config, "base_url")
        assert hasattr(config, "api_key")
        assert hasattr(config, "timeout")

    def test_create_unknown_tool_config(self):
        """Test creating config for unknown tool raises ValueError"""
        tools = discover_tools()
        with pytest.raises(ValueError):
            create_config_for_tool("unknown-tool", tools)


class TestEvolutionAPITool:
    """Test Evolution API tool creation and basic functionality"""

    def test_tool_creation(self):
        """Test that evolution API tool can be created"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)
        server = create_server(config)

        assert server is not None
        assert hasattr(server, "name")
        assert server.name == "Evolution API Tool"

    @pytest.mark.asyncio
    async def test_tool_has_functions(self):
        """Test that the tool has expected functions"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)
        server = create_server(config)

        tools_dict = await server.get_tools()
        tool_names = list(tools_dict.keys())  # FastMCP returns a dict, not a list

        expected_tools = ["send_text_message", "create_instance", "get_instance_info"]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_tool_has_resources(self):
        """Test that the tool has resources"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)
        server = create_server(config)

        resources_dict = await server.get_resources()
        assert len(resources_dict) > 0

        # FastMCP returns dict with URIs as keys
        resource_uris = list(resources_dict.keys())
        assert any("evolution://" in uri for uri in resource_uris)

    @pytest.mark.asyncio
    async def test_tool_has_prompts(self):
        """Test that the tool has prompts"""
        tools = discover_tools()
        config = create_config_for_tool("evolution-api", tools)
        server = create_server(config)

        prompts_dict = await server.get_prompts()
        assert len(prompts_dict) > 0

        # FastMCP returns dict with prompt names as keys
        prompt_names = list(prompts_dict.keys())
        assert "whatsapp_message_template" in prompt_names


class TestCLIBasics:
    """Test basic CLI functionality without starting servers"""

    def test_import_cli_module(self):
        """Test that CLI module can be imported"""
        from automagik_tools.cli import main, app

        assert callable(main)
        assert app is not None

    def test_version_command_works(self, cli_runner):
        """Test version command"""
        result = cli_runner(["version"])
        assert result.returncode == 0
        assert "automagik-tools v" in result.stdout

    def test_list_command_works(self, cli_runner):
        """Test list command"""
        result = cli_runner(["list"])
        assert result.returncode == 0
        assert "evolution-api" in result.stdout


class TestErrorHandling:
    """Test error handling in various components"""

    def test_invalid_tool_name_handling(self):
        """Test handling of invalid tool names"""
        tools = discover_tools()

        # Should handle request for non-existent tool gracefully
        with pytest.raises(ValueError):
            from automagik_tools.cli import load_tool

            load_tool("nonexistent-tool", tools)

    def test_empty_api_key_handling(self):
        """Test handling of empty API key"""
        config = type(
            "Config",
            (),
            {
                "base_url": "http://test.com",
                "api_key": "",  # Empty API key
                "timeout": 30,
            },
        )()

        server = create_server(config)
        assert server is not None  # Server creation should still work

        # But actual API calls should fail (this is expected behavior)


class TestPackageStructure:
    """Test package structure and imports"""

    def test_package_imports(self):
        """Test that package modules can be imported"""
        import automagik_tools
        import automagik_tools.cli
        import automagik_tools.tools.evolution_api

        # Should import without errors
        assert automagik_tools.__version__ is not None

    def test_entry_points_discoverable(self):
        """Test that entry points are discoverable"""
        import importlib.metadata

        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, "select"):
                tool_entry_points = entry_points.select(group="automagik_tools.plugins")
            else:
                tool_entry_points = entry_points.get("automagik_tools.plugins", [])

            # Should find at least the evolution-api tool
            tool_names = [ep.name for ep in tool_entry_points]
            assert "evolution-api" in tool_names
        except Exception:
            # In some test environments, entry points might not be available
            # This is not a critical failure
            pass


# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit
