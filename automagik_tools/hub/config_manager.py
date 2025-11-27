"""Configuration manager for centralized config access.

Provides singleton access to runtime configuration with caching and hot-reload.
"""
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from .bootstrap import RuntimeConfig, load_runtime_config_from_db
from .database import get_db_session
from .setup import ConfigStore


class ConfigurationManager:
    """Singleton configuration manager.

    Provides cached access to runtime configuration with automatic refresh.
    """

    _instance: Optional['ConfigurationManager'] = None
    _config: Optional[RuntimeConfig] = None
    _last_loaded: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(seconds=60)
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_config(cls, force_reload: bool = False) -> RuntimeConfig:
        """Get runtime configuration (cached).

        Args:
            force_reload: Force reload from database ignoring cache

        Returns:
            Current runtime configuration
        """
        async with cls._lock:
            now = datetime.now()

            # Check if cache is valid
            if not force_reload and cls._config is not None and cls._last_loaded is not None:
                if now - cls._last_loaded < cls._cache_ttl:
                    return cls._config

            # Reload from database
            cls._config = await load_runtime_config_from_db()
            cls._last_loaded = now

            return cls._config

    @classmethod
    async def reload_config(cls) -> RuntimeConfig:
        """Force reload configuration from database.

        Returns:
            Reloaded runtime configuration
        """
        return await cls.get_config(force_reload=True)

    @classmethod
    async def update_config(cls, key: str, value: str) -> None:
        """Update configuration value in database.

        Args:
            key: Configuration key
            value: Configuration value
        """
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            await config_store.set(key, value)
            await session.commit()

        # Invalidate cache
        cls._last_loaded = None

    @classmethod
    async def update_network_config(cls, bind_address: str, port: int) -> None:
        """Update network configuration.

        Args:
            bind_address: Server bind address
            port: Server port
        """
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            await config_store.set_network_config({
                "bind_address": bind_address,
                "port": port
            })
            await session.commit()

        # Invalidate cache
        cls._last_loaded = None

    @classmethod
    async def update_super_admins(cls, emails: list[str]) -> None:
        """Update super admin emails.

        Args:
            emails: List of super admin email addresses
        """
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            emails_str = ",".join(emails)
            await config_store.set(ConfigStore.KEY_SUPER_ADMIN_EMAILS, emails_str)
            await session.commit()

        # Invalidate cache
        cls._last_loaded = None

    @classmethod
    async def update_security_settings(
        cls,
        allowed_origins: Optional[list[str]] = None,
        enable_hsts: Optional[bool] = None,
        csp_report_uri: Optional[str] = None
    ) -> None:
        """Update security settings.

        Args:
            allowed_origins: CORS allowed origins
            enable_hsts: Enable HSTS header
            csp_report_uri: CSP report URI
        """
        async with get_db_session() as session:
            config_store = ConfigStore(session)

            if allowed_origins is not None:
                await config_store.set("allowed_origins", ",".join(allowed_origins))

            if enable_hsts is not None:
                await config_store.set("enable_hsts", "true" if enable_hsts else "false")

            if csp_report_uri is not None:
                await config_store.set("csp_report_uri", csp_report_uri)

            await session.commit()

        # Invalidate cache
        cls._last_loaded = None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear configuration cache."""
        cls._config = None
        cls._last_loaded = None


# Global instance
_config_manager = ConfigurationManager()


async def get_config() -> RuntimeConfig:
    """Get current runtime configuration (convenience function).

    Returns:
        Current runtime configuration
    """
    return await _config_manager.get_config()


async def reload_config() -> RuntimeConfig:
    """Reload configuration from database (convenience function).

    Returns:
        Reloaded runtime configuration
    """
    return await _config_manager.reload_config()
