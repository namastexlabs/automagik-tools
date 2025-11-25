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

        # Get configured admin email
        admin_email = await self.mode_manager.get_local_admin_email()
        if not admin_email:
            return None

        # Check if user exists
        result = await self.session.execute(
            select(User).where(User.email == admin_email)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create user and workspace
        workspace_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Create workspace first
        workspace = Workspace(
            id=workspace_id,
            name=f"{admin_email}'s Workspace",
            slug=f"local-{user_id[:8]}",
            owner_id=user_id,
            workos_org_id=None,  # No WorkOS in local mode
            settings={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(workspace)

        # Create user
        user = User(
            id=user_id,
            email=admin_email,
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

    async def is_local_admin(self, email: str) -> bool:
        """Check if email is the local admin.

        Args:
            email: Email to check

        Returns:
            True if email is local admin
        """
        mode = await self.mode_manager.get_current_mode()
        if mode != AppMode.LOCAL:
            return False

        admin_email = await self.mode_manager.get_local_admin_email()
        return email.lower() == admin_email.lower() if admin_email else False
