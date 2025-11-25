"""Multi-tenant authorization module.

Provides decorators and utilities for:
- Workspace isolation (users can only access their own workspace)
- Super admin access (platform owner can access all workspaces)
- Permission checking based on roles

Usage:
    @require_workspace_owner
    async def my_tool(ctx: Context, workspace_id: str):
        # User can only access their own workspace
        pass

    @require_super_admin
    async def admin_tool(ctx: Context):
        # Only platform super admin can access
        pass
"""
import os
import re
import uuid
from functools import wraps
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

from fastapi import HTTPException
from fastmcp import Context
from sqlalchemy import select

from .database import get_db_session
from .models import User, Workspace, UserRole, ProvisioningMethod


# Load super admin emails from environment
SUPER_ADMIN_EMAILS = [
    email.strip().lower()
    for email in os.getenv("SUPER_ADMIN_EMAILS", "").split(",")
    if email.strip()
]


def is_super_admin(email: str) -> bool:
    """Check if user is a platform super admin.

    Super admins can:
    - Access all workspaces
    - Manage all users
    - View all audit logs
    - Modify platform settings

    Args:
        email: User's email address

    Returns:
        True if user is a super admin
    """
    if not email:
        return False
    return email.lower().strip() in SUPER_ADMIN_EMAILS


def generate_workspace_slug(name: str, existing_slugs: list[str] = None) -> str:
    """Generate a URL-safe slug from workspace name.

    Args:
        name: The workspace name
        existing_slugs: List of existing slugs to avoid collisions

    Returns:
        URL-safe slug (lowercase, alphanumeric with hyphens)
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    slug = slug[:50]

    # Ensure uniqueness if existing slugs provided
    if existing_slugs:
        base_slug = slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

    return slug or f"workspace-{uuid.uuid4().hex[:8]}"


async def get_or_create_workspace(user: User, session) -> Workspace:
    """Get user's workspace or create one if it doesn't exist.

    Each user owns exactly one workspace (created on first login).

    Args:
        user: The user model
        session: Database session

    Returns:
        The user's workspace
    """
    # Check if user already has a workspace
    if user.workspace_id:
        result = await session.execute(
            select(Workspace).where(Workspace.id == user.workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            return workspace

    # Check if user owns a workspace
    if user.owned_workspace:
        return user.owned_workspace

    # Create new workspace
    workspace_name = f"{user.first_name or user.email.split('@')[0]}'s Workspace"

    # Get existing slugs to avoid collision
    result = await session.execute(select(Workspace.slug))
    existing_slugs = [row[0] for row in result.fetchall()]
    slug = generate_workspace_slug(workspace_name, existing_slugs)

    workspace = Workspace(
        id=str(uuid.uuid4()),
        name=workspace_name,
        slug=slug,
        owner_id=user.id,
        settings={"default_tools": [], "mfa_required": True}
    )
    session.add(workspace)

    # Update user's workspace reference
    user.workspace_id = workspace.id

    await session.flush()
    return workspace


async def get_or_create_user(
    workos_user_id: str,
    email: str,
    first_name: str = None,
    last_name: str = None,
    provisioned_via: ProvisioningMethod = ProvisioningMethod.MANUAL,
) -> tuple[User, Workspace]:
    """Get or create a user and their workspace.

    Called during authentication to ensure user exists in database.

    Args:
        workos_user_id: WorkOS user ID
        email: User's email
        first_name: User's first name
        last_name: User's last name
        provisioned_via: How the user was created

    Returns:
        Tuple of (User, Workspace)
    """
    async with get_db_session() as session:
        # Try to find existing user
        result = await session.execute(
            select(User).where(User.id == workos_user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Try by email (in case of ID change)
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

        if user:
            # Update user info if changed
            user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                id=workos_user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.WORKSPACE_OWNER.value,
                is_super_admin=is_super_admin(email),
                provisioned_via=provisioned_via.value,
                mfa_grace_period_end=datetime.utcnow() + timedelta(days=7),  # 7-day grace period
            )
            session.add(user)
            await session.flush()

        # Ensure user has a workspace
        workspace = await get_or_create_workspace(user, session)

        await session.commit()
        return user, workspace


async def get_user_context(ctx: Context) -> dict:
    """Extract user context from FastMCP Context.

    Returns dict with:
    - user_id: WorkOS user ID
    - email: User's email
    - workspace_id: User's workspace ID
    - is_super_admin: Whether user is super admin

    Args:
        ctx: FastMCP Context

    Returns:
        Dict with user context
    """
    user_id = ctx.get_state("user_id") if ctx else None
    email = ctx.get_state("email") if ctx else None
    workspace_id = ctx.get_state("workspace_id") if ctx else None

    return {
        "user_id": user_id,
        "email": email,
        "workspace_id": workspace_id,
        "is_super_admin": is_super_admin(email) if email else False,
    }


def require_workspace_owner(func: Callable) -> Callable:
    """Decorator to ensure user owns the workspace they're accessing.

    Super admins can access any workspace.
    Regular users can only access their own workspace.

    Usage:
        @require_workspace_owner
        async def my_tool(ctx: Context, workspace_id: str = None):
            # workspace_id is validated
            pass
    """
    @wraps(func)
    async def wrapper(*args, ctx: Context = None, workspace_id: str = None, **kwargs):
        if not ctx:
            raise HTTPException(401, "Authentication required")

        user_context = await get_user_context(ctx)

        if not user_context["user_id"]:
            raise HTTPException(401, "Authentication required")

        # Super admins can access any workspace
        if user_context["is_super_admin"]:
            return await func(*args, ctx=ctx, workspace_id=workspace_id, **kwargs)

        # If no workspace_id specified, use user's own workspace
        if workspace_id is None:
            workspace_id = user_context["workspace_id"]

        # Users can only access their own workspace
        if workspace_id != user_context["workspace_id"]:
            raise HTTPException(403, "Cannot access other workspaces")

        return await func(*args, ctx=ctx, workspace_id=workspace_id, **kwargs)

    return wrapper


def require_super_admin(func: Callable) -> Callable:
    """Decorator for platform-level operations.

    Only super admins can access these endpoints.

    Usage:
        @require_super_admin
        async def admin_only_tool(ctx: Context):
            # Only super admin can access
            pass
    """
    @wraps(func)
    async def wrapper(*args, ctx: Context = None, **kwargs):
        if not ctx:
            raise HTTPException(401, "Authentication required")

        user_context = await get_user_context(ctx)

        if not user_context["is_super_admin"]:
            raise HTTPException(403, "Super admin access required")

        return await func(*args, ctx=ctx, **kwargs)

    return wrapper


def require_permission(permission: str) -> Callable:
    """Decorator to check specific permission.

    Permissions are defined in the plan:
    - platform:admin, platform:users, platform:audit, platform:settings, platform:billing
    - workspace:admin, tools:read, tools:add, tools:configure, tools:delete, tools:execute
    - credentials:manage, workspace:audit

    Usage:
        @require_permission("tools:add")
        async def add_tool(ctx: Context):
            pass
    """
    # Permission mapping to roles
    PERMISSION_ROLES = {
        # Platform permissions - super admin only
        "platform:admin": [UserRole.SUPER_ADMIN],
        "platform:users": [UserRole.SUPER_ADMIN],
        "platform:audit": [UserRole.SUPER_ADMIN],
        "platform:settings": [UserRole.SUPER_ADMIN],
        "platform:billing": [UserRole.SUPER_ADMIN],

        # Workspace permissions
        "workspace:admin": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
        "tools:read": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER, UserRole.WORKSPACE_MEMBER, UserRole.WORKSPACE_VIEWER],
        "tools:add": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
        "tools:configure": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
        "tools:delete": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
        "tools:execute": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER, UserRole.WORKSPACE_MEMBER],
        "credentials:manage": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
        "workspace:audit": [UserRole.SUPER_ADMIN, UserRole.WORKSPACE_OWNER],
    }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, ctx: Context = None, **kwargs):
            if not ctx:
                raise HTTPException(401, "Authentication required")

            user_context = await get_user_context(ctx)

            if not user_context["user_id"]:
                raise HTTPException(401, "Authentication required")

            # Super admins have all permissions
            if user_context["is_super_admin"]:
                return await func(*args, ctx=ctx, **kwargs)

            # Check permission
            allowed_roles = PERMISSION_ROLES.get(permission, [])

            # Get user's role from database
            async with get_db_session() as session:
                result = await session.execute(
                    select(User.role).where(User.id == user_context["user_id"])
                )
                user_role = result.scalar_one_or_none()

            if not user_role or UserRole(user_role) not in allowed_roles:
                raise HTTPException(403, f"Permission denied: {permission}")

            return await func(*args, ctx=ctx, **kwargs)

        return wrapper

    return decorator


async def inject_workspace_context(ctx: Context) -> None:
    """Inject workspace_id into context state.

    Called by middleware to ensure workspace_id is available
    for all workspace-scoped operations.

    Args:
        ctx: FastMCP Context
    """
    user_id = ctx.get_state("user_id")
    if not user_id:
        return

    # Get user's workspace
    async with get_db_session() as session:
        result = await session.execute(
            select(User.workspace_id, User.email, User.is_super_admin)
            .where(User.id == user_id)
        )
        row = result.one_or_none()

        if row:
            workspace_id, email, db_is_super_admin = row
            ctx.set_state("workspace_id", workspace_id)
            ctx.set_state("email", email)
            ctx.set_state("is_super_admin", db_is_super_admin or is_super_admin(email))
