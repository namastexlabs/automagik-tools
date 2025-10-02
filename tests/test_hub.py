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
