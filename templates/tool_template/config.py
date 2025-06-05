"""
Configuration for {TOOL_NAME} Tool
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class {TOOL_NAME_CLASS}Config(BaseSettings):
    """Configuration for {TOOL_NAME}"""
    api_key: str = Field(
        default="",
        alias="{TOOL_NAME_LOWER}_api_key",
        description="API key for {TOOL_NAME} service"
    )
    base_url: str = Field(
        default="https://api.example.com",
        alias="{TOOL_NAME_LOWER}_base_url",
        description="Base URL for {TOOL_NAME} API"
    )
    timeout: int = Field(
        default=30,
        alias="{TOOL_NAME_LOWER}_timeout",
        description="Request timeout in seconds"
    )
    # Add more configuration fields as needed
    # rate_limit: int = Field(
    #     default=100,
    #     alias="{TOOL_NAME_LOWER}_rate_limit",
    #     description="Maximum requests per minute"
    # )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields in .env
    }