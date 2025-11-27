"""Application mode state machine.

Manages transitions between:
- UNCONFIGURED: Fresh install, redirect to setup wizard
- LOCAL: Single admin, no password, no external auth
- WORKOS: Full enterprise auth with SSO, MFA, Directory Sync
"""
import enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from .config_store import ConfigStore


class AppMode(str, enum.Enum):
    """Application mode states."""
    UNCONFIGURED = "unconfigured"
    LOCAL = "local"
    WORKOS = "workos"


class LocalModeConfig(BaseModel):
    """Configuration for local mode setup."""
    # No fields needed - API key is auto-generated
    pass


class WorkOSModeConfig(BaseModel):
    """Configuration for WorkOS mode setup."""
    client_id: str = Field(..., description="WorkOS Client ID", min_length=1)
    api_key: str = Field(..., description="WorkOS API Key", min_length=1)
    authkit_domain: str = Field(..., description="AuthKit domain URL", min_length=1)
    super_admin_emails: list[EmailStr] = Field(..., description="Super admin email addresses", min_items=1)


class ModeManager:
    """Manages application mode state machine."""

    def __init__(self, config_store: ConfigStore):
        """Initialize mode manager.

        Args:
            config_store: Configuration store instance
        """
        self.config_store = config_store

    async def get_current_mode(self) -> AppMode:
        """Get current application mode.

        Returns:
            Current AppMode
        """
        mode_str = await self.config_store.get_app_mode()
        return AppMode(mode_str)

    async def is_setup_required(self) -> bool:
        """Check if setup wizard should be shown.

        Returns:
            True if mode is UNCONFIGURED, False otherwise
        """
        mode = await self.get_current_mode()
        return mode == AppMode.UNCONFIGURED

    async def configure_local_mode(self, config: LocalModeConfig) -> str:
        """Configure local mode (single admin, no password).

        Args:
            config: Local mode configuration (empty, for consistency)

        Returns:
            Generated Omni API key

        Raises:
            ValueError: If already configured in different mode
        """
        current_mode = await self.get_current_mode()
        if current_mode not in (AppMode.UNCONFIGURED, AppMode.LOCAL):
            raise ValueError(f"Cannot configure local mode from {current_mode} state")

        # Initialize encryption if not done
        await self.config_store.initialize_encryption()

        # Generate Omni API key
        import secrets
        api_key = f"omni_local_{secrets.token_urlsafe(32)}"

        # Store API key (encrypted)
        await self.config_store.set(
            "local_omni_api_key",
            api_key,
            is_secret=True
        )

        # Set mode
        await self.config_store.set_app_mode(AppMode.LOCAL.value)
        await self.config_store.mark_setup_completed()

        return api_key  # Return for display to user

    async def configure_workos_mode(self, config: WorkOSModeConfig) -> None:
        """Configure WorkOS mode (enterprise auth).

        Args:
            config: WorkOS mode configuration

        Raises:
            ValueError: If already configured in different mode
        """
        current_mode = await self.get_current_mode()
        # Allow upgrade from LOCAL to WORKOS
        if current_mode not in (AppMode.UNCONFIGURED, AppMode.LOCAL, AppMode.WORKOS):
            raise ValueError(f"Cannot configure WorkOS mode from {current_mode} state")

        # Initialize encryption if not done
        await self.config_store.initialize_encryption()

        # Store WorkOS credentials (API key is encrypted)
        await self.config_store.set(
            ConfigStore.KEY_WORKOS_CLIENT_ID,
            config.client_id,
            is_secret=False
        )
        await self.config_store.set(
            ConfigStore.KEY_WORKOS_API_KEY,
            config.api_key,
            is_secret=True  # Encrypt API key
        )
        await self.config_store.set(
            ConfigStore.KEY_WORKOS_AUTHKIT_DOMAIN,
            config.authkit_domain,
            is_secret=False
        )

        # Store super admin emails (comma-separated)
        admin_emails = ",".join(config.super_admin_emails)
        await self.config_store.set(
            ConfigStore.KEY_SUPER_ADMIN_EMAILS,
            admin_emails,
            is_secret=False
        )

        # Set mode
        await self.config_store.set_app_mode(AppMode.WORKOS.value)
        await self.config_store.mark_setup_completed()

    async def get_workos_credentials(self) -> Optional[Dict[str, str]]:
        """Get WorkOS credentials (if configured).

        Returns:
            Dict with client_id, api_key, authkit_domain, or None
        """
        mode = await self.get_current_mode()
        if mode != AppMode.WORKOS:
            return None

        client_id = await self.config_store.get(ConfigStore.KEY_WORKOS_CLIENT_ID)
        api_key = await self.config_store.get(ConfigStore.KEY_WORKOS_API_KEY)
        authkit_domain = await self.config_store.get(ConfigStore.KEY_WORKOS_AUTHKIT_DOMAIN)

        if not all([client_id, api_key, authkit_domain]):
            return None

        return {
            "client_id": client_id,
            "api_key": api_key,
            "authkit_domain": authkit_domain,
        }


    async def get_super_admin_emails(self) -> list[str]:
        """Get super admin emails (for WorkOS mode).

        Returns:
            List of super admin emails
        """
        mode = await self.get_current_mode()
        if mode != AppMode.WORKOS:
            return []

        emails_str = await self.config_store.get(ConfigStore.KEY_SUPER_ADMIN_EMAILS)
        if not emails_str:
            return []

        return [email.strip() for email in emails_str.split(",")]

    async def upgrade_to_workos(self, config: WorkOSModeConfig) -> None:
        """Upgrade from LOCAL mode to WORKOS mode.

        Args:
            config: WorkOS mode configuration

        Raises:
            ValueError: If not in LOCAL mode
        """
        current_mode = await self.get_current_mode()
        if current_mode != AppMode.LOCAL:
            raise ValueError(f"Can only upgrade from LOCAL mode (current: {current_mode})")

        await self.configure_workos_mode(config)

    async def migrate_from_env_if_needed(self) -> bool:
        """Auto-migrate WorkOS credentials from .env to database.

        Only runs if:
        - App mode is UNCONFIGURED
        - .env has WORKOS_CLIENT_ID and WORKOS_API_KEY
        - Database doesn't have credentials yet

        Returns:
            True if migration happened, False otherwise
        """
        import os

        # Only migrate if unconfigured
        mode = await self.get_current_mode()
        if mode != AppMode.UNCONFIGURED:
            return False

        # Check if .env has credentials
        client_id = os.getenv("WORKOS_CLIENT_ID")
        api_key = os.getenv("WORKOS_API_KEY")
        authkit_domain = os.getenv("WORKOS_AUTHKIT_DOMAIN", "")
        super_admins = os.getenv("WORKOS_SUPER_ADMIN_EMAILS", "").split(",")

        if not client_id or not api_key:
            return False  # Nothing to migrate

        # Validate email list
        super_admin_emails = [e.strip() for e in super_admins if e.strip()]
        if not super_admin_emails:
            # Default to a placeholder if not set
            super_admin_emails = ["admin@example.com"]

        # Migrate to database
        config = WorkOSModeConfig(
            client_id=client_id,
            api_key=api_key,
            authkit_domain=authkit_domain or "https://veracious-shadow-68.authkit.app",
            super_admin_emails=super_admin_emails
        )

        await self.configure_workos_mode(config)

        print(f"✅ Auto-migrated WorkOS credentials from .env to database")
        print(f"   Client ID: {client_id[:20]}...")
        print(f"   Domain: {authkit_domain}")
        print(f"   Super Admins: {', '.join(super_admin_emails)}")

        return True
