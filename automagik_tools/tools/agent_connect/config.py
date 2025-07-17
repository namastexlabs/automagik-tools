"""
Configuration for Agent Connect MCP tool
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AgentConnectConfig(BaseSettings):
    """Configuration for Agent Connect MCP tool"""
    
    max_queue_size: int = Field(
        default=1000,
        description="Maximum messages per channel queue",
        alias="AGENT_CONNECT_MAX_QUEUE_SIZE"
    )
    
    max_history_size: int = Field(
        default=100,
        description="Maximum messages to keep in history per channel",
        alias="AGENT_CONNECT_MAX_HISTORY_SIZE"
    )
    
    default_timeout: float = Field(
        default=300.0,  # 5 minutes
        description="Default timeout for listen operations in seconds",
        alias="AGENT_CONNECT_DEFAULT_TIMEOUT"
    )
    
    cleanup_interval: int = Field(
        default=3600,  # 1 hour
        description="Interval for cleaning up inactive channels in seconds",
        alias="AGENT_CONNECT_CLEANUP_INTERVAL"
    )
    
    inactive_channel_hours: int = Field(
        default=24,  # 24 hours
        description="Hours before an inactive channel is eligible for cleanup",
        alias="AGENT_CONNECT_INACTIVE_CHANNEL_HOURS"
    )
    
    reply_timeout_default: float = Field(
        default=30.0,
        description="Default timeout when waiting for replies in seconds",
        alias="AGENT_CONNECT_REPLY_TIMEOUT_DEFAULT"
    )
    
    storage_dir: str = Field(
        default="/tmp/agent_connect",
        description="Directory path for storing channel data and message history",
        alias="AGENT_CONNECT_STORAGE"
    )
    
    model_config = {
        "env_prefix": "AGENT_CONNECT_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }