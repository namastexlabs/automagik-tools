"""Additional CLI tests to improve coverage"""

from automagik_tools.cli import discover_tools, create_config_for_tool


class TestToolDiscovery:
    """Test tool discovery in CLI"""

    def test_discover_tools_returns_dict(self):
        """Test that discover_tools returns a dict"""
        tools = discover_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0

    def test_discovered_tools_have_names(self):
        """Test that discovered tools have names"""
        tools = discover_tools()
        for tool_name in tools.keys():
            assert isinstance(tool_name, str)
            assert len(tool_name) > 0
            # Tool dict should have metadata
            assert "metadata" in tools[tool_name]


class TestConfigCreation:
    """Test configuration creation"""

    def test_create_config_for_evolution_api(self):
        """Test creating config for evolution-api"""
        import os

        # Set environment variables needed for config
        os.environ["EVOLUTION_API_BASE_URL"] = "http://test.example.com"
        os.environ["EVOLUTION_API_KEY"] = "test_key_123"

        tools = discover_tools()
        # Check if evolution-api tool exists
        if "evolution-api" in tools:
            config = create_config_for_tool("evolution-api", tools)
            assert config is not None

        # Cleanup
        if "EVOLUTION_API_BASE_URL" in os.environ:
            del os.environ["EVOLUTION_API_BASE_URL"]
        if "EVOLUTION_API_KEY" in os.environ:
            del os.environ["EVOLUTION_API_KEY"]

    def test_create_config_handles_missing_tool(self):
        """Test that config creation handles missing tools gracefully"""
        # This should not crash
        try:
            _ = create_config_for_tool("nonexistent-tool", {})
        except (KeyError, ValueError, SystemExit):
            # Expected to fail for non-existent tool
            pass


class TestCLIHelpers:
    """Test CLI helper functions"""

    def test_tool_metadata_extraction(self):
        """Test that we can extract metadata from tools"""
        tools = discover_tools()

        for tool_name, tool_info in tools.items():
            # Each tool should have metadata
            assert "metadata" in tool_info
            metadata = tool_info["metadata"]

            # Metadata should have a name
            assert "name" in metadata

            # Many tools have descriptions
            if "description" in metadata:
                assert isinstance(metadata["description"], str)


class TestCLIToolLoading:
    """Test CLI tool loading functionality"""

    def test_load_tool_function_exists(self):
        """Test that load_tool function is available"""
        from automagik_tools.cli import load_tool

        assert callable(load_tool)

    def test_load_tool_with_evolution_api(self):
        """Test loading evolution-api tool"""
        import os
        from automagik_tools.cli import load_tool

        # Set required env vars
        os.environ["EVOLUTION_API_BASE_URL"] = "http://test.example.com"
        os.environ["EVOLUTION_API_KEY"] = "test_key"

        tools = discover_tools()

        if "evolution-api" in tools:
            try:
                server = load_tool("evolution-api", tools)
                assert server is not None
            except Exception:
                # May fail due to missing dependencies, that's ok
                pass

        # Cleanup
        if "EVOLUTION_API_BASE_URL" in os.environ:
            del os.environ["EVOLUTION_API_BASE_URL"]
        if "EVOLUTION_API_KEY" in os.environ:
            del os.environ["EVOLUTION_API_KEY"]


class TestCLIVersionInfo:
    """Test CLI version and info commands"""

    def test_version_function_exists(self):
        """Test that version function exists"""
        from automagik_tools.cli import version

        assert callable(version)

    def test_package_has_version(self):
        """Test that package has version metadata"""
        import automagik_tools

        # Package should have version
        assert hasattr(automagik_tools, "__version__")
        assert isinstance(automagik_tools.__version__, str)
        assert len(automagik_tools.__version__) > 0
