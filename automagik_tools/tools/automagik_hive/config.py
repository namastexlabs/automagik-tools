from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class AutomagikHiveConfig(BaseSettings):
    """Configuration for Automagik Hive API tool."""
    
    model_config = {
        "env_prefix": "HIVE_",
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    api_base_url: str = Field(
        default="http://localhost:8886",
        description="Base URL for the Automagik Hive API"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (if required)"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )