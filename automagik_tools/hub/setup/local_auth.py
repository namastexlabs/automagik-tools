"""Local mode authentication (single admin, no password).

In local mode:
- Single admin user (configured email)
- No password required
- Instant "login" by clicking button
- Full access to everything
"""
import uuid
import hmac
import hashlib
import json
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, Workspace, UserRole
from .mode_manager import AppMode, ModeManager

logger = logging.getLogger(__name__)


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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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


# Session signing utilities for Local Mode HTTP-only cookies

def sign_local_session(payload: Dict[str, Any], secret: str, expires_days: int = 30) -> str:
    """Create a signed session token for Local Mode.

    Args:
        payload: Session data (user_id, email, workspace_id, etc.)
        secret: Secret key for signing (local_omni_api_key)
        expires_days: Token expiry in days (default 30)

    Returns:
        Signed token string in format: base64_data.signature
    """
    # Add expiry timestamp
    payload_copy = payload.copy()
    payload_copy["exp"] = (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat()
    payload_copy["iat"] = datetime.now(timezone.utc).isoformat()

    # Encode payload
    data = base64.urlsafe_b64encode(json.dumps(payload_copy).encode()).decode()

    # Sign with HMAC-SHA256
    signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    return f"{data}.{signature}"


def verify_local_session(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a Local Mode session token.

    Args:
        token: Signed token string
        secret: Secret key used for signing

    Returns:
        Decoded payload if valid, None if invalid/expired
    """
    try:
        # Split token into data and signature
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            logger.warning("[LocalAuth] Invalid token format - missing signature")
            return None

        data, signature = parts

        # Verify signature
        expected_signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("[LocalAuth] Invalid token signature")
            return None

        # Decode payload
        payload = json.loads(base64.urlsafe_b64decode(data))

        # Check expiry
        exp = payload.get("exp")
        if exp:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if exp_dt < datetime.now(timezone.utc):
                logger.info("[LocalAuth] Token expired")
                return None

        return payload

    except (ValueError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"[LocalAuth] Token verification failed: {e}")
        return None
