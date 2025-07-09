"""
Evolution API Configuration
"""

from pydantic import BaseSettings, Field
from typing import Optional


class EvolutionAPIConfig(BaseSettings):
    """Configuration for Evolution API tool"""
    
    api_key: str = Field(
        default="",
        description="Evolution API authentication key"
    )
    
    base_url: str = Field(
        default="https://api.evolution.com",
        description="Evolution API base URL"
    )
    
    instance: str = Field(
        default="",
        description="Evolution API instance name"
    )
    
    fixed_recipient: Optional[str] = Field(
        default="",
        description="Fixed recipient for security (removes number parameter from tools)"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    
    class Config:
        env_prefix = "EVOLUTION_API_"
        env_file = ".env"
        case_sensitive = False