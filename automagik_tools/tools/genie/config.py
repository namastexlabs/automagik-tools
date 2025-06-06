"""
Genie Configuration

Centralized configuration management for Genie with environment variable support.
"""

import os
import json
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from dataclasses import dataclass, field

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
    if os.getenv("GENIE_AUTOMAGIK_API_KEY") and os.getenv("GENIE_AUTOMAGIK_BASE_URL"):
        # Use direct Python execution for better Agno compatibility
        configs["automagik"] = {
            "command": "python",
            "args": ["-m", "automagik_tools.tools.automagik", "--transport", "stdio"],
            "env": {
                "AUTOMAGIK_AGENTS_API_KEY": os.getenv("GENIE_AUTOMAGIK_API_KEY"),
                "AUTOMAGIK_AGENTS_BASE_URL": os.getenv("GENIE_AUTOMAGIK_BASE_URL"),
                "AUTOMAGIK_AGENTS_TIMEOUT": os.getenv("GENIE_AUTOMAGIK_TIMEOUT", "600"),
                "AUTOMAGIK_AGENTS_ENABLE_MARKDOWN": "false"  # Disable markdown to avoid double agent execution
            }
        }
    
    return configs

@dataclass
class GenieConfig:
    """Configuration for Genie MCP tool orchestrator"""
    
    # OpenAI API configuration
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("GENIE_MODEL", "gpt-4o"))
    
    # Memory and storage configuration
    memory_db_file: str = field(default_factory=lambda: os.getenv("GENIE_MEMORY_DB", "genie_memory.db"))
    storage_db_file: str = field(default_factory=lambda: os.getenv("GENIE_STORAGE_DB", "genie_storage.db"))
    shared_session_id: str = field(default_factory=lambda: os.getenv("GENIE_SESSION_ID", "global_genie_session"))
    
    # Agent behavior configuration
    num_history_runs: int = field(default_factory=lambda: int(os.getenv("GENIE_HISTORY_RUNS", "3")))
    show_tool_calls: bool = field(default_factory=lambda: os.getenv("GENIE_SHOW_TOOL_CALLS", "true").lower() == "true")
    
    # MCP server timeout and management settings
    mcp_cleanup_timeout: float = field(default_factory=lambda: float(os.getenv("GENIE_MCP_CLEANUP_TIMEOUT", "2.0")))
    sse_cleanup_delay: float = field(default_factory=lambda: float(os.getenv("GENIE_SSE_CLEANUP_DELAY", "0.2")))
    aggressive_cleanup: bool = field(default_factory=lambda: os.getenv("GENIE_AGGRESSIVE_CLEANUP", "true").lower() == "true")
    
    def __post_init__(self):
        # Validate required fields
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    @property
    def mcp_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse MCP server configurations from environment variables.
        Supports both individual server configs and a combined JSON config.
        """
        configs = {}
        
        # Check for combined JSON config first
        combined_config = os.getenv("GENIE_MCP_CONFIGS")
        if combined_config:
            try:
                configs.update(json.loads(combined_config))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GENIE_MCP_CONFIGS: {e}")
        
        # Check for individual server configurations
        # Pattern: GENIE_{SERVER_NAME}_CONFIG
        for key, value in os.environ.items():
            if key.startswith("GENIE_") and key.endswith("_CONFIG"):
                server_name = key[6:-7].lower()  # Remove GENIE_ prefix and _CONFIG suffix
                try:
                    configs[server_name] = json.loads(value)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in {key}: {e}")
        
        # Legacy support for specific server environment patterns
        
        # Automagik configuration
        automagik_key = os.getenv("GENIE_AUTOMAGIK_API_KEY")
        automagik_url = os.getenv("GENIE_AUTOMAGIK_BASE_URL")
        if automagik_key and automagik_url:
            configs["automagik"] = {
                "url": f"{automagik_url}/sse" if not automagik_url.endswith("/sse") else automagik_url,
                "transport": "sse"
            }
        
        # Linear configuration
        linear_token = os.getenv("LINEAR_API_TOKEN")
        if linear_token:
            configs["linear"] = {
                "command": "npx",
                "args": ["-y", "@tacticlaunch/mcp-linear"],
                "env": {"LINEAR_API_TOKEN": linear_token}
            }
        
        # Evolution API configuration
        evolution_key = os.getenv("EVOLUTION_API_KEY")
        evolution_url = os.getenv("EVOLUTION_API_BASE_URL")
        if evolution_key and evolution_url:
            configs["evolution"] = {
                "url": f"{evolution_url}/sse" if not evolution_url.endswith("/sse") else evolution_url,
                "transport": "sse"
            }
        
        return configs
    
    def get_server_specific_cleanup_settings(self, server_name: str) -> Dict[str, Any]:
        """Get cleanup settings specific to a server type"""
        transport_mode = os.environ.get('AUTOMAGIK_TRANSPORT', 'stdio')
        
        # Server-specific settings
        settings = {
            "cleanup_timeout": self.mcp_cleanup_timeout,
            "aggressive_cleanup": self.aggressive_cleanup
        }
        
        # Linear MCP server needs special handling due to stdout pollution
        if server_name == "linear" and transport_mode == "sse":
            settings.update({
                "cleanup_timeout": 1.0,  # Faster timeout for Linear
                "aggressive_cleanup": True,
                "force_kill_on_timeout": True,
                "filter_patterns": [
                    "MCP Linear is running",
                    "Starting MCP Linear...",
                    "MCP Linear version:",
                    "Linear MCP server started"
                ]
            })
        
        # Other servers that might have similar issues
        elif server_name in ["filesystem", "puppeteer"] and transport_mode == "sse":
            settings.update({
                "cleanup_timeout": 1.5,
                "aggressive_cleanup": True
            })
        
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
        
    if config.max_memory_search_results < 1:
        raise ValueError("max_memory_search_results must be positive")
    
    return True