"""
Google Workspace MCP Tool Configuration
"""

from pathlib import Path
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


def _default_credentials_dir() -> str:
    """Return a cross-platform default directory for OAuth credentials."""
    try:
        base_dir = Path.home()
    except RuntimeError:
        # Home directory can be unavailable in some sandboxed environments
        base_dir = Path.cwd()
    return str(base_dir / ".google_workspace_mcp" / "credentials")


class GoogleWorkspaceConfig(BaseSettings):
    """Configuration for Google Workspace MCP tool"""

    # OAuth credentials (optional for now, loaded from env)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Credentials storage (per-user default, override via GOOGLE_WORKSPACE_CREDENTIALS_DIR)
    credentials_dir: str = _default_credentials_dir()

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
        env_prefix="GOOGLE_WORKSPACE_", env_file=".env", env_file_encoding="utf-8"
    )
