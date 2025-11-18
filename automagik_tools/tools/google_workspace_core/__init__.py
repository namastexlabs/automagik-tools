"""
Google Workspace Core - Shared authentication and utilities for Google Workspace tools

This package provides shared functionality for all Google Workspace tools:
- OAuth authentication and credential management
- Service account support
- Multi-tenant credential storage
- Scope management
- Tool registry and filtering

NOT a standalone MCP tool - use individual Google tools:
- google_gmail, google_drive, google_calendar, google_docs, google_sheets, etc.
"""

__version__ = "2.0.0"

# Mark as non-tool for automagik-tools discovery
__AUTOMAGIK_NOT_A_TOOL__ = True

# NOTE: This is NOT a public API module - it provides shared utilities for Google Workspace tools.
# Individual Google tools (google_gmail, google_drive, etc.) import directly from submodules:
#   - from .auth.scopes import SCOPES, set_enabled_tools
#   - from .config import GoogleWorkspaceBaseConfig
#   - from .auth.google_auth import get_authenticated_google_service
# Do not import from this top-level package.
