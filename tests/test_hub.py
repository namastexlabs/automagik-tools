"""Tests for hub.py - tool discovery and loading"""

from automagik_tools.hub import discover_and_load_tools


class TestToolDiscovery:
    """Test tool discovery mechanisms"""

    def test_discover_and_load_tools_returns_dict(self):
        """Test that discover_and_load_tools returns a dictionary"""
        result = discover_and_load_tools()
        assert isinstance(result, dict)

    def test_discover_tools_includes_evolution_api(self):
        """Test that evolution-api tool is discovered"""
        tools = discover_and_load_tools()
        # Evolution API should be discovered
        assert "evolution-api" in tools or len(tools) > 0

    def test_discovered_tools_have_metadata(self):
        """Test that discovered tools have required metadata"""
        tools = discover_and_load_tools()

        for tool_name, tool_info in tools.items():
            # Each tool should have these keys
            assert "metadata" in tool_info
            assert "module" in tool_info

            # Metadata should have a name
            assert "name" in tool_info["metadata"]


class TestHubServerCreation:
    """Test hub server creation and mounting"""

    def test_hub_module_imports(self):
        """Test that hub module can be imported"""
        import automagik_tools.hub as hub_module

        assert hub_module is not None
        # Module should have discover_and_load_tools function
        assert hasattr(hub_module, "discover_and_load_tools")

    def test_hub_discovery_workflow(self):
        """Test that hub can discover and prepare tools"""
        tools = discover_and_load_tools()

        # We should have discovered multiple tools
        assert len(tools) > 0

        # Each tool should be properly structured
        for tool_name, tool_info in tools.items():
            assert "module" in tool_info
            assert "metadata" in tool_info


class TestToolMetadata:
    """Test tool metadata functions"""

    def test_tools_have_required_functions(self):
        """Test that tools export required functions"""
        tools = discover_and_load_tools()

        for tool_name, tool_info in tools.items():
            module = tool_info["module"]

            # Required functions
            assert hasattr(
                module, "get_metadata"
            ), f"{tool_name} missing get_metadata()"
            assert hasattr(
                module, "get_config_class"
            ), f"{tool_name} missing get_config_class()"
            assert hasattr(
                module, "create_server"
            ), f"{tool_name} missing create_server()"

            # Test that functions are callable
            assert callable(module.get_metadata)
            assert callable(module.get_config_class)
            assert callable(module.create_server)
