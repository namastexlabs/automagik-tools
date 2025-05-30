"""
Simple CLI tests that don't hang - focused on basic functionality
"""

import pytest
from automagik_tools.cli import discover_tools, create_config_for_tool
from automagik_tools.cli import app
import subprocess
import os


class TestCLIQuick:
    """Quick CLI tests that don't start servers"""
    
    def test_import_cli(self):
        """Test that CLI module imports correctly"""
        from automagik_tools.cli import main, app
        assert callable(main)
        assert app is not None
    
    def test_discover_tools_function(self):
        """Test the discover_tools function directly"""
        tools = discover_tools()
        assert 'evolution-api' in tools
        assert tools['evolution-api']['name'] == 'evolution-api'
    
    def test_create_config_function(self):
        """Test the create_config_for_tool function directly"""
        config = create_config_for_tool('evolution-api')
        assert hasattr(config, 'base_url')
        assert hasattr(config, 'api_key')
    
    def test_basic_cli_commands(self):
        """Test basic CLI commands that should be fast"""
        # Test help
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['--help'])"],
            capture_output=True, text=True, timeout=5
        )
        # Note: help typically exits with code 0 in some CLI frameworks
        assert "MCP Tools Framework" in result.stdout or "Usage:" in result.stdout
    
    def test_version_command_direct(self):
        """Test version command directly"""
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['version'])"],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        assert "automagik-tools v" in result.stdout
    
    def test_list_command_direct(self):
        """Test list command directly"""
        result = subprocess.run(
            ["python", "-c", "from automagik_tools.cli import app; app(['list'])"],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        assert "evolution-api" in result.stdout


class TestCLIValidation:
    """Test CLI validation without starting servers"""
    
    def test_invalid_tool_handling(self):
        """Test handling of invalid tool names"""
        tools = discover_tools()
        # Should not contain invalid tools
        assert 'nonexistent-tool' not in tools
    
    def test_tool_metadata_complete(self):
        """Test that tools have complete metadata"""
        tools = discover_tools()
        evolution_tool = tools['evolution-api']
        
        required_fields = ['name', 'type', 'status', 'description', 'entry_point']
        for field in required_fields:
            assert field in evolution_tool
            assert evolution_tool[field] is not None


# Mark all tests in this module as fast
pytestmark = pytest.mark.unit 