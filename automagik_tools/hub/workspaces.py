"""Workspace management module.

Provides CRUD operations for workspaces:
- Create workspace on user signup
- Get workspace details
- Update workspace settings
- List workspace members (future: team workspaces)
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import select, func
from fastmcp import Context

from .database import get_db_session
from .models import Workspace, User, UserTool, ToolConfig, OAuthToken, AuditLog
from .authorization import (
    get_user_context,
    require_workspace_owner,
    require_super_admin,
    generate_workspace_slug,
)


async def get_workspace(workspace_id: str) -> Optional[Dict[str, Any]]:
    """Get workspace details by ID.

    Args:
        workspace_id: Workspace UUID

    Returns:
        Workspace dict or None
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            return None

        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "owner_id": workspace.owner_id,
            "workos_org_id": workspace.workos_org_id,
            "settings": workspace.settings or {},
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
            "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else None,
        }


async def get_workspace_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Get workspace by URL slug.

    Args:
        slug: URL-safe workspace identifier

    Returns:
        Workspace dict or None
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.slug == slug)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            return None

        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "owner_id": workspace.owner_id,
            "workos_org_id": workspace.workos_org_id,
            "settings": workspace.settings or {},
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        }


async def update_workspace_settings(
    workspace_id: str,
    settings: Dict[str, Any],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Update workspace settings.

    Settings can include:
    - default_tools: List of tools to enable by default
    - mfa_required: Whether MFA is required for workspace members
    - theme: UI theme preference
    - notifications: Notification preferences

    Args:
        workspace_id: Workspace UUID
        settings: New settings (merged with existing)
        ctx: FastMCP context for audit logging

    Returns:
        Updated workspace dict
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        # Merge settings
        current_settings = workspace.settings or {}
        current_settings.update(settings)
        workspace.settings = current_settings
        workspace.updated_at = datetime.utcnow()

        await session.commit()

        return {
            "id": workspace.id,
            "name": workspace.name,
            "settings": workspace.settings,
            "updated_at": workspace.updated_at.isoformat(),
        }


async def update_workspace_name(
    workspace_id: str,
    name: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """Update workspace name and regenerate slug.

    Args:
        workspace_id: Workspace UUID
        name: New workspace name
        ctx: FastMCP context

    Returns:
        Updated workspace dict
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        # Get existing slugs (excluding current)
        result = await session.execute(
            select(Workspace.slug).where(Workspace.id != workspace_id)
        )
        existing_slugs = [row[0] for row in result.fetchall()]

        workspace.name = name
        workspace.slug = generate_workspace_slug(name, existing_slugs)
        workspace.updated_at = datetime.utcnow()

        await session.commit()

        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "updated_at": workspace.updated_at.isoformat(),
        }


async def get_workspace_stats(workspace_id: str) -> Dict[str, Any]:
    """Get workspace statistics.

    Returns counts of tools, configs, credentials, etc.

    Args:
        workspace_id: Workspace UUID

    Returns:
        Dict with statistics
    """
    async with get_db_session() as session:
        # Count tools
        tools_result = await session.execute(
            select(func.count(UserTool.id))
            .where(UserTool.workspace_id == workspace_id)
        )
        tools_count = tools_result.scalar() or 0

        # Count enabled tools
        enabled_tools_result = await session.execute(
            select(func.count(UserTool.id))
            .where(UserTool.workspace_id == workspace_id, UserTool.enabled == True)
        )
        enabled_tools_count = enabled_tools_result.scalar() or 0

        # Count configs
        configs_result = await session.execute(
            select(func.count(ToolConfig.id))
            .where(ToolConfig.workspace_id == workspace_id)
        )
        configs_count = configs_result.scalar() or 0

        # Count OAuth tokens
        tokens_result = await session.execute(
            select(func.count(OAuthToken.id))
            .where(OAuthToken.workspace_id == workspace_id)
        )
        tokens_count = tokens_result.scalar() or 0

        # Count audit logs (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        audit_result = await session.execute(
            select(func.count(AuditLog.id))
            .where(
                AuditLog.workspace_id == workspace_id,
                AuditLog.occurred_at >= thirty_days_ago
            )
        )
        audit_count = audit_result.scalar() or 0

        return {
            "workspace_id": workspace_id,
            "tools": {
                "total": tools_count,
                "enabled": enabled_tools_count,
            },
            "configs": configs_count,
            "credentials": tokens_count,
            "audit_events_30d": audit_count,
        }


async def list_all_workspaces(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all workspaces (super admin only).

    Args:
        limit: Max workspaces to return
        offset: Pagination offset

    Returns:
        List of workspace dicts
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace)
            .order_by(Workspace.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        workspaces = result.scalars().all()

        return [
            {
                "id": ws.id,
                "name": ws.name,
                "slug": ws.slug,
                "owner_id": ws.owner_id,
                "created_at": ws.created_at.isoformat() if ws.created_at else None,
            }
            for ws in workspaces
        ]


async def get_workspace_members(workspace_id: str) -> List[Dict[str, Any]]:
    """Get all members of a workspace.

    Args:
        workspace_id: Workspace UUID

    Returns:
        List of user dicts
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(User)
            .where(User.workspace_id == workspace_id)
            .order_by(User.created_at)
        )
        users = result.scalars().all()

        return [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_super_admin": user.is_super_admin,
                "mfa_enabled": user.mfa_enabled,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            for user in users
        ]


async def link_workos_organization(
    workspace_id: str,
    workos_org_id: str,
) -> Dict[str, Any]:
    """Link a WorkOS Organization to a workspace.

    Called when Directory Sync is set up.

    Args:
        workspace_id: Workspace UUID
        workos_org_id: WorkOS Organization ID

    Returns:
        Updated workspace dict
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        workspace.workos_org_id = workos_org_id
        workspace.updated_at = datetime.utcnow()

        await session.commit()

        return {
            "id": workspace.id,
            "name": workspace.name,
            "workos_org_id": workspace.workos_org_id,
        }
