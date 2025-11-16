"""
Google Workspace MCP Tool Configuration
"""

from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GoogleWorkspaceConfig(BaseSettings):
    """Configuration for Google Workspace MCP tool"""

    # OAuth credentials (optional for now, loaded from env)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Credentials storage (project-level: personal-genie)
    credentials_dir: str = "/home/namastex/.credentials/personal-genie/google-workspace"

    # Tool tier (core, extended, complete)
    tool_tier: str = "core"

    # User email (for single-user mode)
    user_email: Optional[str] = None

    # OAuth 2.1 mode
    enable_oauth21: bool = False
    single_user_mode: bool = True
    stateless_mode: bool = False

    # Server config
    base_uri: str = "http://localhost"
    port: int = 8000
    log_level: str = "INFO"

    model_config = ConfigDict(
        env_prefix="GOOGLE_WORKSPACE_",
        env_file=".env",
        env_file_encoding="utf-8"
    )
