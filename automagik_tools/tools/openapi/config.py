"""
Configuration for OpenAPI Universal Bridge
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict


class OpenAPIConfig(BaseSettings):
    """Configuration for OpenAPI MCP Tool"""

    openapi_url: str = Field(
        default="",
        description="OpenAPI specification URL",
        alias="OPENAPI_OPENAPI_URL",
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
        alias="OPENAPI_API_KEY",
    )

    base_url: Optional[str] = Field(
        default=None,
        description="Base URL override for the API",
        alias="OPENAPI_BASE_URL",
    )

    name: Optional[str] = Field(
        default="OpenAPI",
        description="Name for the MCP server",
        alias="OPENAPI_NAME",
    )

    instructions: Optional[str] = Field(
        default=None,
        description="Custom instructions for the MCP server",
        alias="OPENAPI_INSTRUCTIONS",
    )

    extra_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional HTTP headers",
    )

    model_config = {
        "env_prefix": "OPENAPI_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
