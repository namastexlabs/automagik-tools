"""Bootstrap manager for database-first configuration.

Handles first-run detection, database initialization, and configuration migration.
After bootstrap completes, .env is no longer read - database becomes source of truth.
"""
import os
import enum
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import text

from .database import get_db_session, run_database_migrations, engine
from .setup import ConfigStore, ModeManager


class BootstrapState(enum.Enum):
    """Bootstrap state for configuration lifecycle."""
    NO_DATABASE = "no_database"           # Database file doesn't exist
    EMPTY_DATABASE = "empty_database"     # Database exists but no tables
    MIGRATIONS_NEEDED = "migrations_needed"  # Tables exist but migrations pending
    UNCONFIGURED = "unconfigured"         # Migrations done but setup not complete
    CONFIGURED = "configured"             # Fully configured


@dataclass(frozen=True)
class RuntimeConfig:
    """Immutable runtime configuration loaded from database.

    After bootstrap completes, this is the single source of truth.
    """
    host: str
    port: int
    database_path: str
    allowed_origins: list[str]
    enable_hsts: bool
    csp_report_uri: Optional[str]
    super_admin_emails: list[str]
    workos_cookie_password: str


async def get_bootstrap_state() -> BootstrapState:
    """Detect current bootstrap state.

    Returns:
        Current bootstrap state
    """
    from .database import _is_postgresql

    # Check 1: Does database exist?
    if _is_postgresql():
        # PostgreSQL: Try to connect
        try:
            async with get_db_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            return BootstrapState.NO_DATABASE
    else:
        # SQLite: Check file exists
        db_path = Path(os.getenv("HUB_DATABASE_PATH", "./data/hub.db"))
        if not db_path.exists():
            return BootstrapState.NO_DATABASE

    # Check 2: Does database have tables?
    try:
        async with get_db_session() as session:
            if _is_postgresql():
                query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'tools_system_config'
                """)
            else:
                query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='tools_system_config'
                """)

            result = await session.execute(query)
            if result.scalar_one_or_none() is None:
                return BootstrapState.EMPTY_DATABASE
    except Exception:
        return BootstrapState.EMPTY_DATABASE

    # Check 3: Are migrations up to date?
    # Note: We'll implement migrations_are_current() in Phase 3
    # For now, assume migrations are current if tables exist

    # Check 4: Is setup completed?
    try:
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            mode = await config_store.get_app_mode()

            if mode == "unconfigured":
                return BootstrapState.UNCONFIGURED

            return BootstrapState.CONFIGURED
    except Exception:
        return BootstrapState.UNCONFIGURED


async def create_database_if_needed(db_path: str) -> None:
    """Create database directory and file if needed.

    Args:
        db_path: Path to database file
    """
    db_file = Path(db_path)
    db_dir = db_file.parent

    # Create directory if needed
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created database directory: {db_dir}")


async def run_migrations_once() -> bool:
    """Run database migrations if needed (idempotent).

    Returns:
        True if migrations were run, False if already up-to-date
    """
    try:
        # Check if migrations are needed
        async with get_db_session() as session:
            # Try to query system_config table
            result = await session.execute(
                text("SELECT COUNT(*) FROM tools_system_config")
            )
            result.scalar_one()
            # Table exists and is queryable
            print("✅ Database migrations already applied")
            return False
    except Exception:
        # Migrations needed
        print("🔄 Running database migrations...")
        await run_database_migrations()
        # Force connection pool refresh after subprocess migration
        # (subprocess creates tables, main process needs fresh connections)
        await engine.dispose()
        print("✅ Database migrations complete")
        return True


async def auto_migrate_from_env() -> bool:
    """Auto-migrate WorkOS credentials from .env to database.

    Only runs if:
    - App mode is UNCONFIGURED
    - .env has WORKOS_CLIENT_ID and WORKOS_API_KEY
    - Database doesn't have credentials yet

    Returns:
        True if migration happened, False otherwise
    """
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        mode_manager = ModeManager(config_store)

        # This function already exists in mode_manager
        return await mode_manager.migrate_from_env_if_needed()


async def load_runtime_config_from_db() -> RuntimeConfig:
    """Load runtime configuration from database.

    This is the ONLY configuration source after bootstrap.

    Returns:
        RuntimeConfig with all settings from database
    """
    async with get_db_session() as session:
        config_store = ConfigStore(session)

        # Network configuration
        network_config = await config_store.get_network_config()
        host = network_config.get("bind_address", "0.0.0.0")
        port = int(network_config.get("port", 8884))

        # Database path
        database_path = await config_store.get(
            ConfigStore.KEY_DATABASE_PATH,
            os.getenv("HUB_DATABASE_PATH", "./data/hub.db")
        )

        # Security settings (will be added in Phase 1.3)
        allowed_origins_str = await config_store.get("allowed_origins", "*")
        allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

        enable_hsts = await config_store.get("enable_hsts", "false") == "true"
        csp_report_uri = await config_store.get("csp_report_uri")

        # Super admin emails
        super_admins_str = await config_store.get(ConfigStore.KEY_SUPER_ADMIN_EMAILS, "")
        super_admin_emails = [e.strip() for e in super_admins_str.split(",") if e.strip()]

        # WorkOS cookie password (will be added in Phase 1.3)
        workos_cookie_password = await config_store.get_or_generate_cookie_password()

        return RuntimeConfig(
            host=host,
            port=port,
            database_path=database_path,
            allowed_origins=allowed_origins,
            enable_hsts=enable_hsts,
            csp_report_uri=csp_report_uri,
            super_admin_emails=super_admin_emails,
            workos_cookie_password=workos_cookie_password,
        )


async def bootstrap_application() -> RuntimeConfig:
    """Bootstrap the application and return runtime configuration.

    This is the main entry point for application configuration.

    Bootstrap phases:
    1. NO_DATABASE / EMPTY_DATABASE -> Create DB, run migrations, auto-migrate from .env
    2. UNCONFIGURED -> Wait for setup wizard
    3. CONFIGURED -> Load config from database

    Returns:
        RuntimeConfig loaded from database
    """
    import traceback
    import re
    from .database import DATABASE_URL, _is_postgresql

    # Pre-flight connectivity check - fail fast if database is unreachable
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        # Print detailed error trace for debugging
        safe_url = re.sub(r':([^@]+)@', ':****@', DATABASE_URL) if '@' in DATABASE_URL else DATABASE_URL
        print(f"""
================================================================================
TOOLS HUB DATABASE CONNECTION FAILED
================================================================================
URL: {safe_url}
Error: {type(e).__name__}: {e}

{traceback.format_exc()}

Quick fixes:
1. PostgreSQL: pg_isready -h 192.168.112.135 -p 5432
2. Check HUB_DATABASE_URL environment variable
3. Ensure database exists

Copy this block when reporting issues.
================================================================================
""")
        raise SystemExit(f"DATABASE CONNECTION FAILED: {e}")


    from dotenv import load_dotenv

    # Step 1: Detect state
    state = await get_bootstrap_state()
    print(f"🔍 Bootstrap state: {state.value}")

    if state in [BootstrapState.NO_DATABASE, BootstrapState.EMPTY_DATABASE]:
        # BOOTSTRAP PHASE - Read .env for initial setup only
        print("📝 Loading .env for initial bootstrap...")
        load_dotenv()

        db_path = os.getenv("HUB_DATABASE_PATH", "./data/hub.db")

        # Create database if needed
        if state == BootstrapState.NO_DATABASE:
            await create_database_if_needed(db_path)

        # Run migrations
        await run_migrations_once()

        # Auto-migrate from .env if WorkOS credentials present
        migrated = await auto_migrate_from_env()
        if migrated:
            print("✅ Auto-migrated WorkOS credentials from .env to database")

        # Store .env defaults in database for future use
        async with get_db_session() as session:
            config_store = ConfigStore(session)

            # Store network config from .env
            host = os.getenv("HUB_HOST", "0.0.0.0")
            port = int(os.getenv("HUB_PORT", "8884"))
            await config_store.set_network_config({"bind_address": host, "port": port})

            # Store database path
            await config_store.set(ConfigStore.KEY_DATABASE_PATH, db_path)

            # Store security settings
            allowed_origins = os.getenv("HUB_ALLOWED_ORIGINS", "*")
            await config_store.set("allowed_origins", allowed_origins)

            enable_hsts = os.getenv("HUB_ENABLE_HSTS", "true")
            await config_store.set("enable_hsts", enable_hsts)

            csp_uri = os.getenv("HUB_CSP_REPORT_URI", "")
            if csp_uri:
                await config_store.set("csp_report_uri", csp_uri)

            # Store super admin emails
            super_admins = os.getenv("SUPER_ADMIN_EMAILS", "")
            if super_admins:
                await config_store.set(ConfigStore.KEY_SUPER_ADMIN_EMAILS, super_admins)

            # Auto-migrate Google OAuth credentials from .env (Priority 4)
            google_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
            google_client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")

            if google_client_id and google_client_secret:
                # Check if already migrated
                existing = await config_store.get_google_oauth_credentials("default")
                if not existing:
                    await config_store.set_google_oauth_credentials(
                        "default", google_client_id, google_client_secret
                    )
                    print("✅ Auto-migrated Google OAuth credentials from .env to database")

            await session.commit()

        print("✅ Bootstrap complete - configuration stored in database")

    elif state == BootstrapState.UNCONFIGURED:
        # SETUP PHASE - Wait for wizard
        print("⚠️  Setup required! Navigate to /setup to configure application mode")

    elif state == BootstrapState.CONFIGURED:
        # RUNNING PHASE
        print("✅ Application configured - loading from database")

    # Load and return runtime configuration from database
    config = await load_runtime_config_from_db()

    print(f"📊 Runtime config loaded:")
    print(f"   Host: {config.host}:{config.port}")
    print(f"   Database: {config.database_path}")
    print(f"   Super Admins: {len(config.super_admin_emails)} configured")
    print(f"   CORS Origins: {', '.join(config.allowed_origins[:3])}{'...' if len(config.allowed_origins) > 3 else ''}")

    return config
