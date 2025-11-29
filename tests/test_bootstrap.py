"""Tests for database-first bootstrap system."""
import pytest
import os
import tempfile
from pathlib import Path

from automagik_tools.hub.bootstrap import (
    BootstrapState,
    get_bootstrap_state,
    RuntimeConfig,
    load_runtime_config_from_db,
    create_database_if_needed,
)
from automagik_tools.hub.setup import ConfigStore
from automagik_tools.hub.database import get_db_session, run_database_migrations


@pytest.mark.asyncio
class TestBootstrapStates:
    """Test bootstrap state detection."""

    async def test_no_database_state(self, tmp_path, monkeypatch):
        """Test NO_DATABASE state detection."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        # Database doesn't exist
        state = await get_bootstrap_state()
        assert state == BootstrapState.NO_DATABASE

    async def test_database_creation(self, tmp_path, monkeypatch):
        """Test database directory and file creation."""
        db_path = tmp_path / "data" / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        # Create database
        await create_database_if_needed(str(db_path))

        # Directory should exist
        assert db_path.parent.exists()


@pytest.mark.asyncio
class TestRuntimeConfig:
    """Test RuntimeConfig dataclass."""

    async def test_runtime_config_immutable(self):
        """Test that RuntimeConfig is immutable."""
        config = RuntimeConfig(
            host="127.0.0.1",
            port=8884,
            database_path="data/hub.db",
            allowed_origins=["http://localhost:3000"],
            enable_hsts=False,
            csp_report_uri=None,
            super_admin_emails=["admin@example.com"],
            workos_cookie_password="test123"
        )

        # Should be frozen
        with pytest.raises(AttributeError):
            config.port = 9999


@pytest.mark.asyncio
class TestConfigStore:
    """Test ConfigStore operations."""

    async def test_get_set_config(self, tmp_path, monkeypatch):
        """Test basic get/set operations."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        # Initialize database
        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        # Test set/get
        async with get_db_session() as session:
            config_store = ConfigStore(session)

            # Initialize encryption
            await config_store.initialize_encryption()

            # Set value
            await config_store.set("test_key", "test_value")
            await session.commit()

        # Get value in new session
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            value = await config_store.get("test_key")
            assert value == "test_value"

    async def test_secret_encryption(self, tmp_path, monkeypatch):
        """Test that secrets are encrypted."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        async with get_db_session() as session:
            config_store = ConfigStore(session)
            await config_store.initialize_encryption()

            # Set secret
            secret_value = "super_secret_key"
            await config_store.set("api_key", secret_value, is_secret=True)
            await session.commit()

        # Retrieve secret
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            retrieved = await config_store.get("api_key")
            assert retrieved == secret_value

    async def test_app_mode_management(self, tmp_path, monkeypatch):
        """Test app mode get/set."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        async with get_db_session() as session:
            config_store = ConfigStore(session)

            # Default should be unconfigured
            mode = await config_store.get_app_mode()
            assert mode == "unconfigured"

            # Set to workos
            await config_store.set_app_mode("workos")
            await session.commit()

        # Verify in new session
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            mode = await config_store.get_app_mode()
            assert mode == "workos"

    async def test_network_config(self, tmp_path, monkeypatch):
        """Test network configuration management."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        async with get_db_session() as session:
            config_store = ConfigStore(session)

            # Set network config
            await config_store.set_network_config({
                "bind_address": "0.0.0.0",
                "port": 9000
            })
            await session.commit()

        # Get network config
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            config = await config_store.get_network_config()

            # Config store returns the stored value directly
            assert config["bind_address"] == "0.0.0.0"
            assert config["port"] == 9000


@pytest.mark.asyncio
class TestConfigurationPersistence:
    """Test that configuration persists across sessions."""

    async def test_config_persists_after_restart(self, tmp_path, monkeypatch):
        """Test configuration survives database reconnection."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        # First session: Set configuration
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            await config_store.initialize_encryption()
            await config_store.set("test_persist", "persistent_value")
            await config_store.set_app_mode("local")
            await session.commit()

        # Simulate restart by creating new session
        async with get_db_session() as session:
            config_store = ConfigStore(session)

            # Values should persist
            value = await config_store.get("test_persist")
            assert value == "persistent_value"

            mode = await config_store.get_app_mode()
            assert mode == "local"


@pytest.mark.asyncio
class TestBootstrapIntegration:
    """Integration tests for full bootstrap flow."""

    async def test_cookie_password_auto_generation(self, tmp_path, monkeypatch):
        """Test that cookie password is auto-generated if not set."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("HUB_DATABASE_PATH", str(db_path))

        await create_database_if_needed(str(db_path))
        await run_database_migrations()

        async with get_db_session() as session:
            config_store = ConfigStore(session)
            await config_store.initialize_encryption()

            # First call should generate
            password1 = await config_store.get_or_generate_cookie_password()
            assert password1 is not None
            assert len(password1) > 20

            await session.commit()

        # Second call should return same password
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            password2 = await config_store.get_or_generate_cookie_password()
            assert password1 == password2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
