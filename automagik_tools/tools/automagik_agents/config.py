"""
Configuration for AutomagikAgents
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AutomagikAgentsConfig(BaseSettings):
    """Configuration for AutomagikAgents MCP Tool"""

    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="AUTOMAGIK_AGENTS_API_KEY",
    )

    base_url: str = Field(
        default="http://192.168.112.148:8881",
        description="Base URL for the API",
        alias="AUTOMAGIK_AGENTS_BASE_URL",
    )

    openapi_url: str = Field(
        default="http://192.168.112.148:8881/api/v1/openapi.json",
        description="URL to fetch OpenAPI specification",
        alias="AUTOMAGIK_AGENTS_OPENAPI_URL",
    )

    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="AUTOMAGIK_AGENTS_TIMEOUT",
    )

    max_component_name_length: int = Field(
        default=56,
        description="Maximum length for MCP component names (FastMCP limit is 56)",
        alias="AUTOMAGIK_AGENTS_MAX_NAME_LENGTH",
    )

    auto_truncate_names: bool = Field(
        default=True,
        description="Automatically truncate long component names",
        alias="AUTOMAGIK_AGENTS_AUTO_TRUNCATE",
    )

    exclude_health_endpoints: bool = Field(
        default=True,
        description="Exclude health check endpoints from MCP server",
        alias="AUTOMAGIK_AGENTS_EXCLUDE_HEALTH",
    )

    model_config = {
        "env_prefix": "AUTOMAGIK_AGENTS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
