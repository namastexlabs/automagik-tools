"""
Configuration for Wait Utility Tool
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class WaitConfig(BaseSettings):
    """Configuration for Wait Utility MCP Tool"""

    max_duration: int = Field(
        default=3600,  # 1 hour max
        description="Maximum wait duration in seconds",
        alias="WAIT_MAX_DURATION",
    )

    default_progress_interval: float = Field(
        default=1.0,
        description="Default progress reporting interval in seconds",
        alias="WAIT_DEFAULT_PROGRESS_INTERVAL",
    )

    model_config = {
        "env_prefix": "WAIT_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
