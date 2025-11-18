"""
Google Workspace Core Configuration

Base configuration class inherited by all Google Workspace tools.
"""

from pathlib import Path
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GoogleWorkspaceBaseConfig(BaseSettings):
    """
    Base configuration for Google Workspace tools.

    All Google Workspace tools inherit from this base config.
    Individual tools can add service-specific settings.
    """

    # OAuth credentials
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Credentials storage (for multi-user OAuth hub)
    # Default to project-local directory, not user-specific home directory
    # NOTE: This field is currently not used by the credential storage system.
    # The actual implementation uses GOOGLE_MCP_CREDENTIALS_DIR environment variable.
    # Override with GOOGLE_WORKSPACE_CREDENTIALS_DIR environment variable (if this field is used in future).
    credentials_dir: str = ".credentials/google-workspace"

    # User settings
    user_email: Optional[str] = None

    # Authentication modes
    enable_oauth21: bool = False
    single_user_mode: bool = True
    stateless_mode: bool = False

    # Server settings (for OAuth callback)
    base_uri: str = "http://localhost"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    model_config = ConfigDict(
        env_prefix="GOOGLE_WORKSPACE_", env_file=".env", env_file_encoding="utf-8"
    )
