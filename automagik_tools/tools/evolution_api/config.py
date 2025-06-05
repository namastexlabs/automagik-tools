"""Configuration for Evolution API tool"""

from pydantic import Field
from pydantic_settings import BaseSettings


class EvolutionAPIConfig(BaseSettings):
    """Configuration for Evolution API"""

    base_url: str = Field(
        default="https://your-evolution-api-server.com",
        description="Evolution API base URL",
    )
    api_key: str = Field(default="", description="Evolution API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")

    model_config = {
        "env_prefix": "EVOLUTION_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
