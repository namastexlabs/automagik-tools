"""
Tests for google_workspace_core utilities and configuration.

These tests cover the shared components used by all Google Workspace tools.
"""

import os
import pytest
from automagik_tools.tools.google_workspace_core.auth.scopes import (
    SCOPES,
    set_enabled_tools,
    get_current_scopes,
    get_scopes_for_tools,
    TOOL_SCOPES_MAP,
    BASE_SCOPES,
)
from automagik_tools.tools.google_workspace_core.core.tool_registry import (
    set_enabled_tools as set_enabled_tool_names,
    get_enabled_tools,
    is_tool_enabled,
)
from automagik_tools.tools.google_workspace_core.config import GoogleWorkspaceBaseConfig


class TestGoogleWorkspaceScopes:
    """Test OAuth scope management for Google Workspace services."""

    def test_scopes_default_includes_all_services(self):
        """Test that SCOPES includes all services by default."""
        assert isinstance(SCOPES, list)
        assert len(SCOPES) > 0
        # Should include base scopes
        assert all(scope in SCOPES for scope in BASE_SCOPES)

    def test_get_scopes_for_specific_tools(self):
        """Test getting scopes for specific tools."""
        gmail_scopes = get_scopes_for_tools(["gmail"])
        assert isinstance(gmail_scopes, list)
        # Should include base scopes
        assert all(scope in gmail_scopes for scope in BASE_SCOPES)
        # Should include Gmail-specific scopes
        assert any("gmail" in scope for scope in gmail_scopes)

    def test_get_scopes_for_multiple_tools(self):
        """Test getting scopes for multiple tools."""
        scopes = get_scopes_for_tools(["gmail", "drive", "calendar"])
        assert isinstance(scopes, list)
        # Should have more scopes than a single tool
        gmail_only = get_scopes_for_tools(["gmail"])
        assert len(scopes) >= len(gmail_only)

    def test_set_enabled_tools_updates_current_scopes(self):
        """Test that setting enabled tools updates the current scopes."""
        # Set only Gmail
        set_enabled_tools(["gmail"])
        current = get_current_scopes()

        # Should have Gmail scopes
        assert any("gmail" in scope for scope in current)
        # Should have base scopes
        assert all(scope in current for scope in BASE_SCOPES)

    def test_scopes_are_unique(self):
        """Test that scope lists don't contain duplicates."""
        scopes = get_scopes_for_tools(["gmail", "drive"])
        assert len(scopes) == len(set(scopes)), "Scopes list contains duplicates"

    def test_all_tools_in_scope_map(self):
        """Test that all expected tools are in the scope map."""
        expected_tools = [
            "gmail", "drive", "calendar", "docs",
            "sheets", "chat", "forms", "slides", "tasks", "search"
        ]
        for tool in expected_tools:
            assert tool in TOOL_SCOPES_MAP, f"Tool {tool} missing from TOOL_SCOPES_MAP"


class TestToolRegistry:
    """Test MCP tool registry functionality."""

    def test_set_enabled_tools_none_enables_all(self):
        """Test that setting None enables all tools."""
        set_enabled_tool_names(None)
        assert get_enabled_tools() is None
        assert is_tool_enabled("any_tool_name")

    def test_set_enabled_tools_specific_set(self):
        """Test setting specific enabled tools."""
        enabled = {"tool1", "tool2", "tool3"}
        set_enabled_tool_names(enabled)

        assert get_enabled_tools() == enabled
        assert is_tool_enabled("tool1")
        assert is_tool_enabled("tool2")
        assert not is_tool_enabled("tool4")

    def test_is_tool_enabled_with_none(self):
        """Test that all tools are enabled when registry is None."""
        set_enabled_tool_names(None)
        assert is_tool_enabled("random_tool")
        assert is_tool_enabled("another_tool")

    def test_different_from_scopes_set_enabled(self):
        """Test that tool registry set_enabled_tools is independent from scopes."""
        # This test documents that there are TWO different set_enabled_tools functions
        # One for services (auth.scopes) and one for tool functions (core.tool_registry)

        # Set service-level tools (scopes)
        set_enabled_tools(["gmail", "drive"])

        # Set tool-level functions (registry)
        set_enabled_tool_names({"send_gmail_message"})

        # They should be independent
        assert get_enabled_tools() == {"send_gmail_message"}
        current_scopes = get_current_scopes()
        assert any("gmail" in scope for scope in current_scopes)


class TestGoogleWorkspaceConfig:
    """Test Google Workspace configuration."""

    def test_config_class_exists(self):
        """Test that the config class can be imported and has expected fields."""
        # Just verify the class structure exists - actual instantiation is tested
        # in integration tests to avoid conflicts with .env files
        assert GoogleWorkspaceBaseConfig is not None

        # Check that expected field names are in the model
        field_names = GoogleWorkspaceBaseConfig.model_fields.keys()
        assert "client_id" in field_names
        assert "client_secret" in field_names
        assert "credentials_dir" in field_names
        assert "user_email" in field_names
        assert "enable_oauth21" in field_names
        assert "single_user_mode" in field_names
        assert "stateless_mode" in field_names
        assert "base_uri" in field_names
        assert "port" in field_names
        assert "log_level" in field_names


class TestGoogleWorkspaceCoreModule:
    """Test the google_workspace_core module itself."""

    def test_module_marked_as_not_a_tool(self):
        """Test that google_workspace_core is marked as not being a standalone tool."""
        import automagik_tools.tools.google_workspace_core as core_module

        assert hasattr(core_module, "__AUTOMAGIK_NOT_A_TOOL__")
        assert core_module.__AUTOMAGIK_NOT_A_TOOL__ is True

    def test_module_has_version(self):
        """Test that the module has a version attribute."""
        import automagik_tools.tools.google_workspace_core as core_module

        assert hasattr(core_module, "__version__")
        assert isinstance(core_module.__version__, str)

    def test_module_no_public_exports(self):
        """Test that the module doesn't expose a public API via __all__."""
        import automagik_tools.tools.google_workspace_core as core_module

        # Should NOT have __all__ (we removed it to fix the bug)
        assert not hasattr(core_module, "__all__")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
