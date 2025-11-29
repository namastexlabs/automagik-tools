"""System configuration store for zero-config setup.

Stores app mode, secrets, and setup status in database.
Secrets are encrypted using Fernet with machine-derived keys.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SystemConfig  # Use the one from models.py to avoid duplicate
from ..database import get_db_session
from .encryption import get_encryption_manager


class ConfigStore:
    """Configuration store with encryption support."""

    # Configuration keys
    KEY_APP_MODE = "app_mode"
    KEY_SETUP_COMPLETED = "setup_completed"
    KEY_ENCRYPTION_SALT = "encryption_key_salt"
    KEY_WORKOS_CLIENT_ID = "workos_client_id"
    KEY_WORKOS_API_KEY = "workos_api_key"
    KEY_WORKOS_AUTHKIT_DOMAIN = "workos_authkit_domain"
    KEY_WORKOS_SETUP_TYPE = "workos_setup_type"  # 'quick' or 'custom'
    KEY_SUPER_ADMIN_EMAILS = "super_admin_emails"
    KEY_LOCAL_ADMIN_EMAIL = "local_admin_email"
    KEY_DATABASE_PATH = "database_path"
    KEY_BIND_ADDRESS = "bind_address"
    KEY_PORT = "port"

    def __init__(self, session: AsyncSession):
        """Initialize config store.

        Args:
            session: Async database session
        """
        self.session = session
        self._encryption_manager = None

    async def _get_encryption_manager(self):
        """Get or initialize encryption manager with salt from database."""
        if self._encryption_manager is None:
            salt_b64 = await self.get(self.KEY_ENCRYPTION_SALT)
            self._encryption_manager = get_encryption_manager(salt_b64)
        return self._encryption_manager

    async def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value (decrypted if secret), or default
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.config_key == key)
        )
        config = result.scalar_one_or_none()

        if config is None:
            return default

        value = config.config_value

        # Decrypt if secret
        if config.is_secret:
            encryption = await self._get_encryption_manager()
            value = encryption.decrypt(value)

        return value

    async def set(self, key: str, value: str, is_secret: bool = False) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            is_secret: Whether to encrypt the value
        """
        # Encrypt if secret
        if is_secret:
            encryption = await self._get_encryption_manager()
            value = encryption.encrypt(value)

        # Check if exists
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.config_key == key)
        )
        config = result.scalar_one_or_none()

        if config:
            # Update existing
            config.config_value = value
            config.is_secret = is_secret
            config.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            config = SystemConfig(
                id=str(uuid.uuid4()),
                config_key=key,
                config_value=value,
                is_secret=is_secret,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(config)

        await self.session.commit()

    async def get_json(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get JSON configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Parsed JSON dict, or default
        """
        value = await self.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    async def set_json(self, key: str, value: Dict[str, Any], is_secret: bool = False) -> None:
        """Set JSON configuration value.

        Args:
            key: Configuration key
            value: Dict to serialize as JSON
            is_secret: Whether to encrypt the value
        """
        await self.set(key, json.dumps(value), is_secret=is_secret)

    async def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.config_key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            await self.session.delete(config)
            await self.session.commit()

    async def initialize_encryption(self) -> str:
        """Initialize encryption salt if not exists.

        Returns:
            Base64-encoded salt
        """
        salt_b64 = await self.get(self.KEY_ENCRYPTION_SALT)
        if salt_b64 is None:
            # Generate new salt
            encryption = get_encryption_manager()
            salt_b64 = encryption.get_salt_b64()
            await self.set(self.KEY_ENCRYPTION_SALT, salt_b64, is_secret=False)
            self._encryption_manager = encryption

        return salt_b64

    async def is_setup_completed(self) -> bool:
        """Check if initial setup is completed.

        Returns:
            True if setup completed, False otherwise
        """
        value = await self.get(self.KEY_SETUP_COMPLETED, "false")
        return value.lower() == "true"

    async def mark_setup_completed(self) -> None:
        """Mark initial setup as completed."""
        await self.set(self.KEY_SETUP_COMPLETED, "true")

    async def get_app_mode(self) -> str:
        """Get application mode.

        Returns:
            "unconfigured", "local", or "workos"
        """
        return await self.get(self.KEY_APP_MODE, "unconfigured")

    async def set_app_mode(self, mode: str) -> None:
        """Set application mode.

        Args:
            mode: "unconfigured", "local", or "workos"
        """
        if mode not in ("unconfigured", "local", "workos"):
            raise ValueError(f"Invalid app mode: {mode}")
        await self.set(self.KEY_APP_MODE, mode)

    async def get_database_path(self) -> str:
        """Get database path.

        Returns:
            Database path (default: data/hub.db)
        """
        return await self.get(self.KEY_DATABASE_PATH, "data/hub.db")

    async def set_database_path(self, path: str) -> None:
        """Set database path.

        Args:
            path: Database file path
        """
        await self.set(self.KEY_DATABASE_PATH, path)

    async def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration with fallback to env vars.

        Returns:
            Dict with bind_address and port
        """
        import os

        bind_address = await self.get(self.KEY_BIND_ADDRESS)
        port = await self.get(self.KEY_PORT)

        # Fallback to environment variables
        if not bind_address:
            bind_address = os.getenv("HUB_HOST", "127.0.0.1")
            # Normalize 0.0.0.0 to 'network', 127.0.0.1 to 'localhost'
            bind_address = "network" if bind_address == "0.0.0.0" else "localhost"

        if not port:
            port = int(os.getenv("HUB_PORT", "8000"))

        return {
            "bind_address": bind_address,
            "port": int(port) if isinstance(port, str) else port
        }

    async def set_network_config(self, config: Dict[str, Any]) -> None:
        """Set network configuration.

        Args:
            config: Dict with bind_address and port
        """
        bind_address = config.get("bind_address", "127.0.0.1")
        port = config.get("port", 8000)

        # Validate
        if not isinstance(port, int) or not (1024 <= port <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {port}")

        await self.set(self.KEY_BIND_ADDRESS, bind_address)
        await self.set(self.KEY_PORT, str(port))

    async def get_or_generate_cookie_password(self) -> str:
        """Get or generate WorkOS cookie password.

        Cookie password is used for session encryption. If not set,
        a secure random password is generated and stored.

        Returns:
            Cookie password string
        """
        import secrets

        password = await self.get("workos_cookie_password")

        if not password:
            # Generate secure random password
            password = secrets.token_urlsafe(32)
            await self.set("workos_cookie_password", password, is_secret=True)

        return password

    async def get_runtime_config(self) -> Dict[str, Any]:
        """Get complete runtime configuration from database.

        Returns:
            Dict with all runtime configuration values
        """
        import os

        # Network
        network = await self.get_network_config()

        # Database
        database_path = await self.get(
            self.KEY_DATABASE_PATH,
            os.getenv("HUB_DATABASE_PATH", "./data/hub.db")
        )

        # Security
        allowed_origins = await self.get("allowed_origins", "*")
        enable_hsts = await self.get("enable_hsts", "true") == "true"
        csp_report_uri = await self.get("csp_report_uri")

        # Super admins
        super_admins = await self.get(self.KEY_SUPER_ADMIN_EMAILS, "")

        # WorkOS
        cookie_password = await self.get_or_generate_cookie_password()

        return {
            "host": network["bind_address"],
            "port": network["port"],
            "database_path": database_path,
            "allowed_origins": allowed_origins,
            "enable_hsts": enable_hsts,
            "csp_report_uri": csp_report_uri,
            "super_admin_emails": super_admins,
            "workos_cookie_password": cookie_password,
        }

    async def get_google_oauth_credentials(self, workspace_id: str) -> Optional[Dict[str, str]]:
        """Get Google OAuth credentials for a workspace.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Dict with client_id and client_secret, or None if not configured
        """
        key_prefix = f"google_oauth.{workspace_id}"
        client_id = await self.get(f"{key_prefix}.client_id")
        client_secret = await self.get(f"{key_prefix}.client_secret")

        if not client_id or not client_secret:
            return None

        return {
            "client_id": client_id,
            "client_secret": client_secret,
        }

    async def set_google_oauth_credentials(
        self, workspace_id: str, client_id: str, client_secret: str
    ) -> None:
        """Set Google OAuth credentials for a workspace.

        Args:
            workspace_id: Workspace identifier
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret (will be encrypted)
        """
        key_prefix = f"google_oauth.{workspace_id}"
        await self.set(f"{key_prefix}.client_id", client_id, is_secret=False)
        await self.set(f"{key_prefix}.client_secret", client_secret, is_secret=True)


async def get_config_store() -> ConfigStore:
    """Get config store with database session.

    Returns:
        ConfigStore instance

    Usage:
        async with get_db_session() as session:
            store = ConfigStore(session)
            mode = await store.get_app_mode()
    """
    async with get_db_session() as session:
        return ConfigStore(session)
