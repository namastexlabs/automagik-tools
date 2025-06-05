"""
Configuration for EvolutionApiV2
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class EvolutionApiV2Config(BaseSettings):
    """Configuration for EvolutionApiV2 MCP Tool"""
    
    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="EVOLUTION_API_V2_API_KEY"
    )
    
    base_url: str = Field(
        default="http://localhost:8080",
        description="Base URL for the Evolution API server",
        alias="EVOLUTION_API_V2_BASE_URL"
    )
    
    openapi_url: str = Field(
        default="https://raw.githubusercontent.com/EvolutionAPI/docs-evolution/refs/heads/main/openapi/openapi-v2.json",
        description="URL to fetch OpenAPI specification",
        alias="EVOLUTION_API_V2_OPENAPI_URL"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="EVOLUTION_API_V2_TIMEOUT"
    )
    
    model_config = {
        "env_prefix": "EVOLUTION_API_V2_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
