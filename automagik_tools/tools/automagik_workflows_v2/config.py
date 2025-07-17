"""
Configuration management for automagik-workflows-v2
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class AutomagikWorkflowsV2Config(BaseSettings):
    """Configuration for Automagik Workflows V2 tool."""
    
    # API Configuration
    api_base_url: str = Field(
        default="http://localhost:28881",
        description="Base URL for the Automagik Workflows API"
    )
    
    api_key: str = Field(
        description="API key for authentication with Automagik Workflows API",
        alias="AUTOMAGIK_WORKFLOWS_V2_API_KEY"
    )
    
    # User Configuration
    user_id: str = Field(
        description="User identifier for workflow tracking and attribution",
        alias="AUTOMAGIK_WORKFLOWS_V2_USER_ID"
    )
    
    # Execution Configuration  
    timeout: int = Field(
        default=14400,  # 4 hours
        description="Default execution timeout in seconds (4 hours max)"
    )
    
    polling_interval: int = Field(
        default=8,
        description="Progress polling interval in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for API calls"
    )
    
    # Health Check Configuration
    health_check_interval: int = Field(
        default=60,
        description="Health check interval in seconds for self-healing"
    )
    
    health_check_timeout: int = Field(
        default=10,
        description="Health check request timeout in seconds"
    )
    
    # Tool Behavior Configuration
    auto_discover_workflows: bool = Field(
        default=True,
        description="Automatically discover available workflows on startup"
    )
    
    enable_elicitation: bool = Field(
        default=True,
        description="Enable elicitation for dynamic parameter collection"
    )
    
    model_config = ConfigDict(
        env_prefix="AUTOMAGIK_WORKFLOWS_V2_",
        case_sensitive=False
    )