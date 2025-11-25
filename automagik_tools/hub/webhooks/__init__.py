"""WorkOS Webhook handlers.

This module provides webhook endpoints for:
- Directory Sync (Google Workspace user provisioning)
- Authentication events (login, MFA, etc.)
- Audit Log events
"""
from .directory_sync import router as directory_sync_router

__all__ = ["directory_sync_router"]
