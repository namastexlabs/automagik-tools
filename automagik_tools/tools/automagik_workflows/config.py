"""
Configuration for AutoMagik Workflows
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AutomagikWorkflowsConfig(BaseSettings):
    """Configuration for AutoMagik Workflows MCP Tool"""

    api_key: str = Field(
        default="",
        description="API key for authentication",
        alias="AUTOMAGIK_WORKFLOWS_API_KEY",
    )

    base_url: str = Field(
        default="http://localhost:28881",
        description="Base URL for the Claude Code API",
        alias="AUTOMAGIK_WORKFLOWS_BASE_URL",
    )

    timeout: int = Field(
        default=7200,
        description="Request timeout in seconds (default: 2 hours)",
        alias="AUTOMAGIK_WORKFLOWS_TIMEOUT",
    )

    polling_interval: int = Field(
        default=8,
        description="Polling interval in seconds for workflow status",
        alias="AUTOMAGIK_WORKFLOWS_POLLING_INTERVAL",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests",
        alias="AUTOMAGIK_WORKFLOWS_MAX_RETRIES",
    )

    model_config = {
        "env_prefix": "AUTOMAGIK_WORKFLOWS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
