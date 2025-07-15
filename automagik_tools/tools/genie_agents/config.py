from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class GenieAgentsConfig(BaseModel):
    """Configuration for Genie Agents API tool."""
    
    model_config = ConfigDict(env_prefix="GENIE_AGENTS_")
    
    api_base_url: str = Field(
        default="http://localhost:9888",
        description="Base URL for the Genie Agents API"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (if required)"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )