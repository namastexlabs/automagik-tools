"""
Genie Configuration

Centralized configuration management for Genie with environment variable support.
"""

import os
import json
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings

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

class GenieConfig(BaseSettings):
    """Configuration settings for Genie"""
    
    # AI Model Configuration
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key for the agent model"
    )
    model: str = Field(
        default=os.getenv("GENIE_MODEL", "gpt-4.1-mini"),
        description="OpenAI model to use for the agent"
    )
    
    # Memory and Storage Configuration  
    memory_db_file: str = Field(
        default=os.getenv("GENIE_MEMORY_DB", "genie_memory.db"),
        description="SQLite database file for persistent memory"
    )
    storage_db_file: str = Field(
        default=os.getenv("GENIE_STORAGE_DB", "genie_storage.db"), 
        description="SQLite database file for chat history storage"
    )
    shared_session_id: str = Field(
        default=os.getenv("GENIE_SESSION_ID", "global_genie_session"),
        description="Shared session ID for all users (single evolving agent)"
    )
    
    # Agent Behavior Configuration
    enable_streaming: bool = Field(
        default=os.getenv("GENIE_STREAMING", "true").lower() == "true",
        description="Enable streaming responses"
    )
    enable_debug: bool = Field(
        default=os.getenv("GENIE_DEBUG", "true").lower() == "true", 
        description="Enable debug mode with verbose logging"
    )
    show_tool_calls: bool = Field(
        default=os.getenv("GENIE_SHOW_TOOLS", "true").lower() == "true",
        description="Show tool calls in responses"
    )
    
    # Memory Management Configuration
    num_history_runs: int = Field(
        default=int(os.getenv("GENIE_HISTORY_RUNS", "5")),
        description="Number of previous conversation runs to include in context"
    )
    max_memory_search_results: int = Field(
        default=int(os.getenv("GENIE_MAX_MEMORIES", "10")),
        description="Maximum number of memories to retrieve in searches"
    )
    enable_agentic_memory: bool = Field(
        default=os.getenv("GENIE_AGENTIC_MEMORY", "true").lower() == "true",
        description="Enable agent-managed memory creation/deletion"
    )
    enable_user_memories: bool = Field(
        default=os.getenv("GENIE_USER_MEMORIES", "true").lower() == "true",
        description="Enable automatic memory creation after each interaction"
    )
    
    # MCP Server Configurations
    # Each MCP server will have its own session/instance
    mcp_server_configs: Dict[str, Any] = Field(
        default_factory=lambda: _load_mcp_configs(),
        description="MCP server configurations. Each key is a server name, value is the server config dict"
    )
    
    # Automagik MCP Server Configuration (specific support)
    automagik_command: str = Field(
        default=os.getenv("GENIE_AUTOMAGIK_COMMAND", "uvx"),
        description="Command to run automagik MCP server"
    )
    automagik_args: str = Field(
        default=os.getenv("GENIE_AUTOMAGIK_ARGS", "automagik-tools@0.3.0,serve,--tool,automagik,--transport,stdio"),
        description="Arguments for automagik MCP server (comma-separated)"
    )
    automagik_api_key: str = Field(
        default=os.getenv("GENIE_AUTOMAGIK_API_KEY", ""),
        description="API key for automagik agents"
    )
    automagik_base_url: str = Field(
        default=os.getenv("GENIE_AUTOMAGIK_BASE_URL", ""),
        description="Base URL for automagik API"
    )
    automagik_timeout: str = Field(
        default=os.getenv("GENIE_AUTOMAGIK_TIMEOUT", "600"),
        description="Timeout for automagik operations"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default=os.getenv("GENIE_LOG_LEVEL", "INFO"),
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_file: Optional[str] = Field(
        default=os.getenv("GENIE_LOG_FILE"),
        description="Optional log file path"
    )
    
    # Performance Configuration
    max_concurrent_tools: int = Field(
        default=int(os.getenv("GENIE_MAX_CONCURRENT", "5")),
        description="Maximum number of concurrent tool executions"
    )
    tool_timeout_seconds: int = Field(
        default=int(os.getenv("GENIE_TIMEOUT", "300")),
        description="Timeout for individual tool executions"
    )
    
    model_config = {
        "env_prefix": "GENIE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

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