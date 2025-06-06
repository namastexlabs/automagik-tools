"""
Configuration for Enhanced AutomagikAgents with AI processing
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AutomagikAgentsEnhancedConfig(BaseSettings):
    """Configuration for Enhanced AutomagikAgents MCP Tool with AI processing"""
    
    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="AUTOMAGIK_AGENTS_API_KEY"
    )
    
    base_url: str = Field(
        default="http://192.168.112.148:8881",
        description="Base URL for the API",
        alias="AUTOMAGIK_AGENTS_BASE_URL"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="AUTOMAGIK_AGENTS_TIMEOUT"
    )
    
    enable_ai_processing: bool = Field(
        default=True,
        description="Enable AI-powered response processing",
        alias="ENABLE_JSON_PROCESSING"
    )
    
    model_config = {
        "env_prefix": "AUTOMAGIK_AGENTS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }