"""Compliance Audit Logger.

Provides comprehensive audit logging for security and compliance:
- Logs to local database (immediate)
- Optionally syncs to WorkOS Audit Logs API (deferred)

Event Schema follows WorkOS Audit Logs format for compatibility:
- action: What happened (e.g., "tool.added", "auth.login_succeeded")
- actor: Who did it (user, system, api_key)
- target: What was affected (user, tool, credential, workspace)
- context: Additional metadata (IP, user agent, request ID)

Retention Policies (configurable):
- Security events (auth, credential): 1 year
- PII access events: 6 years (GDPR)
- Operational events: 90 days
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
from functools import wraps
from dataclasses import dataclass, field, asdict

from fastmcp import Context
from sqlalchemy import select

from ..database import get_db_session
from ..models import AuditLog, AuditEventCategory

logger = logging.getLogger(__name__)


@dataclass
class AuditActor:
    """Who performed the action."""
    id: Optional[str] = None
    email: Optional[str] = None
    type: str = "user"  # user, system, api_key

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuditTarget:
    """What was affected by the action."""
    type: str  # user, tool, credential, workspace
    id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuditContext:
    """Additional context for the audit event."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.ip_address:
            result["ip_address"] = self.ip_address
        if self.user_agent:
            result["user_agent"] = self.user_agent
        if self.request_id:
            result["request_id"] = self.request_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class AuditLogger:
    """Compliance audit logger for Hub events.

    Logs events to local database and optionally to WorkOS Audit Logs API.

    Usage:
        # Direct logging
        await audit_logger.log(
            action="tool.added",
            actor=AuditActor(id=user_id, email=email),
            target=AuditTarget(type="tool", name="google_calendar"),
            workspace_id=workspace_id,
        )

        # Using decorator
        @audit_tool_call("tool.executed")
        async def my_tool(ctx: Context):
            pass
    """

    def __init__(self, workos_org_id: Optional[str] = None):
        """Initialize audit logger.

        Args:
            workos_org_id: WorkOS Organization ID for API logging (optional)
        """
        self.workos_org_id = workos_org_id or os.getenv("WORKOS_ORG_ID")
        self.workos_api_key = os.getenv("WORKOS_API_KEY")

    async def log(
        self,
        action: str,
        category: AuditEventCategory,
        actor: Optional[AuditActor] = None,
        target: Optional[AuditTarget] = None,
        workspace_id: Optional[str] = None,
        context: Optional[AuditContext] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """Log an audit event.

        Args:
            action: Event action (e.g., "tool.added")
            category: Event category
            actor: Who performed the action
            target: What was affected
            workspace_id: Workspace ID (for scoping)
            context: Additional context (IP, user agent, etc.)
            success: Whether the action succeeded
            error_message: Error message if action failed

        Returns:
            Audit log entry ID
        """
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        actor = actor or AuditActor(type="system")
        context = context or AuditContext()

        async with get_db_session() as session:
            audit_entry = AuditLog(
                id=event_id,
                workspace_id=workspace_id,
                action=action,
                category=category.value if isinstance(category, AuditEventCategory) else category,
                actor_id=actor.id,
                actor_email=actor.email,
                actor_type=actor.type,
                target_type=target.type if target else None,
                target_id=target.id if target else None,
                target_name=target.name if target else None,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                request_id=context.request_id,
                event_metadata=context.metadata if context.metadata else None,
                success=success,
                error_message=error_message,
                occurred_at=now,
            )
            session.add(audit_entry)
            await session.commit()

        logger.info(
            f"Audit: {action} by {actor.email or actor.type} "
            f"on {target.type if target else 'N/A'}:{target.name if target else 'N/A'} "
            f"success={success}"
        )

        return event_id

    async def log_auth(
        self,
        action: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        workspace_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log authentication event.

        Actions: auth.login_succeeded, auth.login_failed, auth.logout,
                 auth.mfa_enabled, auth.mfa_verified, auth.mfa_failed,
                 auth.password_changed, auth.session_expired
        """
        return await self.log(
            action=action,
            category=AuditEventCategory.AUTH,
            actor=AuditActor(id=user_id, email=email, type="user"),
            target=AuditTarget(type="user", id=user_id, name=email),
            workspace_id=workspace_id,
            context=AuditContext(
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
            ),
            success=success,
            error_message=error_message,
        )

    async def log_tool(
        self,
        action: str,
        tool_name: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        workspace_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Log tool event.

        Actions: tool.added, tool.removed, tool.configured,
                 tool.executed, tool.execution_failed
        """
        return await self.log(
            action=action,
            category=AuditEventCategory.TOOL,
            actor=AuditActor(id=user_id, email=email, type="user"),
            target=AuditTarget(type="tool", name=tool_name),
            workspace_id=workspace_id,
            context=AuditContext(
                request_id=request_id,
                metadata=metadata or {},
            ),
            success=success,
            error_message=error_message,
        )

    async def log_credential(
        self,
        action: str,
        tool_name: str,
        provider: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        workspace_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """Log credential event.

        Actions: credential.created, credential.accessed, credential.deleted,
                 credential.rotated, credential.expired
        """
        return await self.log(
            action=action,
            category=AuditEventCategory.CREDENTIAL,
            actor=AuditActor(id=user_id, email=email, type="user"),
            target=AuditTarget(type="credential", name=f"{tool_name}:{provider}"),
            workspace_id=workspace_id,
            context=AuditContext(
                metadata={"tool_name": tool_name, "provider": provider},
            ),
            success=success,
            error_message=error_message,
        )

    async def log_admin(
        self,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        workspace_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log admin event.

        Actions: admin.user_created, admin.user_deleted, admin.user_updated,
                 admin.role_granted, admin.role_revoked, admin.settings_changed,
                 admin.user_provisioned, admin.user_deprovisioned
        """
        return await self.log(
            action=action,
            category=AuditEventCategory.ADMIN,
            actor=AuditActor(id=user_id, email=email, type="user"),
            target=AuditTarget(type=target_type, id=target_id, name=target_name),
            workspace_id=workspace_id,
            context=AuditContext(metadata=metadata or {}),
            success=success,
            error_message=error_message,
        )

    async def log_workspace(
        self,
        action: str,
        workspace_id: str,
        workspace_name: Optional[str] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log workspace event.

        Actions: workspace.created, workspace.settings_changed,
                 workspace.member_added, workspace.member_removed
        """
        return await self.log(
            action=action,
            category=AuditEventCategory.WORKSPACE,
            actor=AuditActor(id=user_id, email=email, type="user"),
            target=AuditTarget(type="workspace", id=workspace_id, name=workspace_name),
            workspace_id=workspace_id,
            context=AuditContext(metadata=metadata or {}),
            success=success,
            error_message=error_message,
        )


# Singleton instance
audit_logger = AuditLogger()


async def log_audit_event(
    action: str,
    category: AuditEventCategory,
    ctx: Optional[Context] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function to log audit event from context.

    Extracts user_id, email, workspace_id from FastMCP context.
    """
    user_id = ctx.get_state("user_id") if ctx else None
    email = ctx.get_state("email") if ctx else None
    workspace_id = ctx.get_state("workspace_id") if ctx else None
    request_id = ctx.get_state("request_id") if ctx else None

    return await audit_logger.log(
        action=action,
        category=category,
        actor=AuditActor(id=user_id, email=email, type="user" if user_id else "system"),
        target=AuditTarget(type=target_type, id=target_id, name=target_name) if target_type else None,
        workspace_id=workspace_id,
        context=AuditContext(
            request_id=request_id,
            metadata=metadata or {},
        ),
        success=success,
        error_message=error_message,
    )


def audit_tool_call(action: str = "tool.executed") -> Callable:
    """Decorator to automatically audit tool calls.

    Usage:
        @audit_tool_call("tool.executed")
        async def my_tool(ctx: Context):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, ctx: Context = None, **kwargs):
            tool_name = func.__name__
            user_id = ctx.get_state("user_id") if ctx else None
            email = ctx.get_state("email") if ctx else None
            workspace_id = ctx.get_state("workspace_id") if ctx else None
            request_id = ctx.get_state("request_id") if ctx else None

            try:
                result = await func(*args, ctx=ctx, **kwargs)

                # Log successful execution
                await audit_logger.log_tool(
                    action=action,
                    tool_name=tool_name,
                    user_id=user_id,
                    email=email,
                    workspace_id=workspace_id,
                    success=True,
                    request_id=request_id,
                )

                return result

            except Exception as e:
                # Log failed execution
                await audit_logger.log_tool(
                    action=f"{action}_failed" if not action.endswith("_failed") else action,
                    tool_name=tool_name,
                    user_id=user_id,
                    email=email,
                    workspace_id=workspace_id,
                    success=False,
                    error_message=str(e),
                    request_id=request_id,
                )
                raise

        return wrapper
    return decorator


async def get_audit_logs(
    workspace_id: Optional[str] = None,
    category: Optional[AuditEventCategory] = None,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Dict[str, Any]]:
    """Query audit logs with filters.

    Args:
        workspace_id: Filter by workspace
        category: Filter by category
        action: Filter by action (exact match)
        actor_id: Filter by actor
        start_date: Filter events after this date
        end_date: Filter events before this date
        limit: Max results
        offset: Pagination offset

    Returns:
        List of audit log entries
    """
    async with get_db_session() as session:
        query = select(AuditLog).order_by(AuditLog.occurred_at.desc())

        if workspace_id:
            query = query.where(AuditLog.workspace_id == workspace_id)
        if category:
            cat_value = category.value if isinstance(category, AuditEventCategory) else category
            query = query.where(AuditLog.category == cat_value)
        if action:
            query = query.where(AuditLog.action == action)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if start_date:
            query = query.where(AuditLog.occurred_at >= start_date)
        if end_date:
            query = query.where(AuditLog.occurred_at <= end_date)

        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "action": log.action,
                "category": log.category,
                "actor": {
                    "id": log.actor_id,
                    "email": log.actor_email,
                    "type": log.actor_type,
                },
                "target": {
                    "type": log.target_type,
                    "id": log.target_id,
                    "name": log.target_name,
                } if log.target_type else None,
                "workspace_id": log.workspace_id,
                "success": log.success,
                "error_message": log.error_message,
                "occurred_at": log.occurred_at.isoformat() if log.occurred_at else None,
                "metadata": log.event_metadata,
            }
            for log in logs
        ]
