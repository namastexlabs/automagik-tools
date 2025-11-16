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

# Lazy imports - only load when needed to avoid circular dependencies
__all__ = [
    "get_google_service",
    "SCOPES",
    "set_enabled_tools",
    "GoogleWorkspaceBaseConfig",
]
