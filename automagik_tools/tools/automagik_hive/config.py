from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class AutomagikHiveConfig(BaseModel):
    """Configuration for Automagik Hive API tool."""
    
    model_config = ConfigDict(env_prefix="HIVE_")
    
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