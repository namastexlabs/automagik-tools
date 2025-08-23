"""Configuration for Spark MCP tool"""

from pydantic import Field
from pydantic_settings import BaseSettings


class SparkConfig(BaseSettings):
    """Configuration for Spark workflow orchestration tool"""

    api_key: str = Field(
        default="namastex888",
        description="API key for Spark authentication",
        alias="SPARK_API_KEY",
    )

    base_url: str = Field(
        default="http://localhost:8883",
        description="Base URL for Spark API",
        alias="SPARK_BASE_URL",
    )

    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="SPARK_TIMEOUT",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        alias="SPARK_MAX_RETRIES",
    )

    model_config = {
        "env_prefix": "SPARK_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }