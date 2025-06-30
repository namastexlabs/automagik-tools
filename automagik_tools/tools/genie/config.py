"""
Genie Configuration

Centralized configuration management for Genie with environment variable support.
"""

import os
import json
from typing import Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _load_mcp_configs() -> Dict[str, Any]:
    """Load MCP server configurations from environment variables"""
    configs = {}

    # Check for JSON-encoded MCP configs
    if os.getenv("GENIE_MCP_CONFIGS"):
        try:
            configs = json.loads(os.getenv("GENIE_MCP_CONFIGS", "{}"))
        except json.JSONDecodeError:
            pass

    # Check for automagik-specific config
    if os.getenv("AUTOMAGIK_API_KEY") and os.getenv("AUTOMAGIK_BASE_URL"):
        # Use direct Python execution for better Agno compatibility
        configs["automagik"] = {
            "command": "python",
            "args": ["-m", "automagik_tools.tools.automagik", "--transport", "stdio"],
            "env": {
                "AUTOMAGIK_API_KEY": os.getenv("AUTOMAGIK_API_KEY"),
                "AUTOMAGIK_BASE_URL": os.getenv("AUTOMAGIK_BASE_URL"),
                "AUTOMAGIK_TIMEOUT": os.getenv("AUTOMAGIK_TIMEOUT", "600"),
                "AUTOMAGIK_ENABLE_MARKDOWN": "false",  # Disable markdown to avoid double agent execution
            },
        }

    return configs


@dataclass
class GenieConfig:
    """Configuration for Genie MCP tool orchestrator"""

    # OpenAI API configuration
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("GENIE_MODEL", "gpt-4.1"))

    # Memory and storage configuration
    memory_db_file: str = field(
        default_factory=lambda: os.getenv("GENIE_MEMORY_DB", "genie_memory.db")
    )
    storage_db_file: str = field(
        default_factory=lambda: os.getenv("GENIE_STORAGE_DB", "genie_storage.db")
    )
    shared_session_id: str = field(
        default_factory=lambda: os.getenv("GENIE_SESSION_ID", "global_genie_session")
    )

    # Agent behavior configuration
    num_history_runs: int = field(
        default_factory=lambda: int(os.getenv("GENIE_HISTORY_RUNS", "3"))
    )
    show_tool_calls: bool = field(
        default_factory=lambda: os.getenv("GENIE_SHOW_TOOL_CALLS", "true").lower()
        == "true"
    )

    # MCP server timeout and management settings
    mcp_cleanup_timeout: float = field(
        default_factory=lambda: float(os.getenv("GENIE_MCP_CLEANUP_TIMEOUT", "2.0"))
    )
    sse_cleanup_delay: float = field(
        default_factory=lambda: float(os.getenv("GENIE_SSE_CLEANUP_DELAY", "0.2"))
    )
    aggressive_cleanup: bool = field(
        default_factory=lambda: os.getenv("GENIE_AGGRESSIVE_CLEANUP", "true").lower()
        == "true"
    )

    def __post_init__(self):
        # Only validate if the genie tool is being actively used
        # Skip validation during tool discovery or when other tools are running
        self._validate_on_use = not self.openai_api_key
        
    def validate_for_use(self):
        """Validate configuration when actually using the genie tool"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for Genie tool")

    @property
    def mcp_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse MCP server configurations from environment variables.
        Supports both individual server configs and a combined JSON config.
        """
        # Use the _load_mcp_configs function which has the correct command-based configs
        return _load_mcp_configs()

    def get_server_specific_cleanup_settings(self, server_name: str) -> Dict[str, Any]:
        """Get cleanup settings specific to a server type"""
        transport_mode = os.environ.get("AUTOMAGIK_TRANSPORT", "stdio")

        # Server-specific settings
        settings = {
            "cleanup_timeout": self.mcp_cleanup_timeout,
            "aggressive_cleanup": self.aggressive_cleanup,
        }

        # Linear MCP server needs special handling due to stdout pollution
        if server_name == "linear" and transport_mode == "sse":
            settings.update(
                {
                    "cleanup_timeout": 1.0,  # Faster timeout for Linear
                    "aggressive_cleanup": True,
                    "force_kill_on_timeout": True,
                    "filter_patterns": [
                        "MCP Linear is running",
                        "Starting MCP Linear...",
                        "MCP Linear version:",
                        "Linear MCP server started",
                    ],
                }
            )

        # Other servers that might have similar issues
        elif server_name in ["filesystem", "puppeteer"] and transport_mode == "sse":
            settings.update({"cleanup_timeout": 1.5, "aggressive_cleanup": True})

        return settings


def get_config() -> GenieConfig:
    """Get Genie configuration from environment variables"""
    return GenieConfig()


def validate_config(config: GenieConfig) -> bool:
    """Validate Genie configuration"""
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for Genie")

    if config.num_history_runs < 0:
        raise ValueError("num_history_runs must be non-negative")

    return True
