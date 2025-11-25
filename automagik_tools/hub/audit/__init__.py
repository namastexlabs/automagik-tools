"""Audit logging module.

Provides compliance-ready audit logging for:
- Authentication events (login, logout, MFA)
- Tool events (add, remove, configure, execute)
- Credential events (create, access, delete)
- Admin events (user management, settings changes)
"""
from .logger import (
    AuditLogger,
    AuditActor,
    AuditTarget,
    AuditContext,
    audit_logger,
    log_audit_event,
    audit_tool_call,
    get_audit_logs,
)
from ..models import AuditEventCategory

__all__ = [
    "AuditLogger",
    "AuditActor",
    "AuditTarget",
    "AuditContext",
    "AuditEventCategory",
    "audit_logger",
    "log_audit_event",
    "audit_tool_call",
    "get_audit_logs",
]
