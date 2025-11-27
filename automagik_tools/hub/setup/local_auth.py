"""Local mode authentication (single admin, no password).

In local mode:
- Single admin user (configured email)
- No password required
- Instant "login" by clicking button
- Full access to everything
"""
import uuid
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, Workspace, UserRole
from .mode_manager import AppMode, ModeManager


class LocalAuthSession(BaseModel):
    """Local authentication session."""
    user_id: str
    email: str
    workspace_id: str
    is_super_admin: bool = True


class LocalAuthManager:
    """Manages local mode authentication."""

    def __init__(self, session: AsyncSession, mode_manager: ModeManager):
        """Initialize local auth manager.

        Args:
            session: Database session
            mode_manager: Mode manager instance
        """
        self.session = session
        self.mode_manager = mode_manager

    async def get_or_create_local_admin(self) -> Optional[User]:
        """Get or create the local admin user.

        Returns:
            User object or None if not in local mode
        """
        # Check if in local mode
        mode = await self.mode_manager.get_current_mode()
        if mode != AppMode.LOCAL:
            return None

        # Check if user already exists (should be exactly one)
        result = await self.session.execute(
            select(User).where(User.role == UserRole.SUPER_ADMIN.value)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create user and workspace (first-time setup)
        workspace_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Create workspace first
        workspace = Workspace(
            id=workspace_id,
            name="Local Workspace",
            slug=f"local-{user_id[:8]}",
            owner_id=user_id,
            workos_org_id=None,  # No WorkOS in local mode
            settings={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(workspace)

        # Create user (no email needed)
        user = User(
            id=user_id,
            email="local@automagik.tools",  # Placeholder, not used
            first_name="Local",
            last_name="Admin",
            workspace_id=workspace_id,
            role=UserRole.SUPER_ADMIN.value,
            is_super_admin=True,
            directory_sync_id=None,
            idp_id=None,
            provisioned_via="manual",
            mfa_enabled=False,
            mfa_grace_period_end=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def authenticate_local(self) -> Optional[LocalAuthSession]:
        """Authenticate in local mode (no password required).

        Returns:
            LocalAuthSession or None if not in local mode
        """
        user = await self.get_or_create_local_admin()
        if not user:
            return None

        return LocalAuthSession(
            user_id=user.id,
            email=user.email,
            workspace_id=user.workspace_id,
            is_super_admin=user.is_super_admin,
        )

    async def authenticate_with_api_key(self, api_key: str) -> Optional[LocalAuthSession]:
        """Authenticate using Omni API key in local mode.

        Args:
            api_key: Omni API key from user

        Returns:
            LocalAuthSession or None if invalid
        """
        mode = await self.mode_manager.get_current_mode()
        if mode != AppMode.LOCAL:
            return None

        # Verify API key
        stored_key = await self.mode_manager.config_store.get("local_omni_api_key")
        if not stored_key or stored_key != api_key:
            return None

        # Get or create local admin
        user = await self.get_or_create_local_admin()
        if not user:
            return None

        return LocalAuthSession(
            user_id=user.id,
            email=user.email,
            workspace_id=user.workspace_id,
            is_super_admin=True,
        )
