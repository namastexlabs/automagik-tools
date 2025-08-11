"""Configuration for OMNI MCP tool"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class OmniConfig(BaseSettings):
    """Configuration for OMNI multi-tenant messaging API tool"""
    
    api_key: str = Field(
        default="", 
        description="API key for OMNI authentication", 
        alias="OMNI_API_KEY"
    )
    
    base_url: str = Field(
        default="http://localhost:8882",
        description="Base URL for the OMNI API",
        alias="OMNI_BASE_URL"
    )
    
    default_instance: Optional[str] = Field(
        default=None,
        description="Default instance name for operations",
        alias="OMNI_DEFAULT_INSTANCE"
    )
    
    timeout: int = Field(
        default=30, 
        description="Request timeout in seconds", 
        alias="OMNI_TIMEOUT"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        alias="OMNI_MAX_RETRIES"
    )
    
    model_config = {
        "env_prefix": "OMNI_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
    
    def validate_for_use(self):
        """Validate configuration is ready for use"""
        if not self.api_key:
            raise ValueError("OMNI_API_KEY is required")
        if not self.base_url:
            raise ValueError("OMNI_BASE_URL is required")