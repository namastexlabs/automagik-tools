"""
Configuration for Automagik
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AutomagikConfig(BaseSettings):
    """Configuration for Automagik MCP Tool"""
    
    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="AUTOMAGIK_AGENTS_API_KEY"
    )
    
    base_url: str = Field(
        default="https://api.example.com",
        description="Base URL for the API",
        alias="AUTOMAGIK_AGENTS_BASE_URL"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="AUTOMAGIK_AGENTS_TIMEOUT"
    )
    
    enable_markdown: bool = Field(
        default=True,
        description="Enable AI-powered markdown enhancement of responses",
        alias="AUTOMAGIK_AGENTS_ENABLE_MARKDOWN"
    )
    
    model_config = {
        "env_prefix": "AUTOMAGIK_AGENTS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
