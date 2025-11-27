"""Database connection and session management.

After bootstrap, database path comes from RuntimeConfig.
Module-level initialization is lazy to avoid premature database access.
"""
import os
import subprocess
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import Base


def _get_database_url() -> str:
    """Get database URL from environment (bootstrap phase only).

    After bootstrap, connection is already established.
    This is only called during initial module import.
    """
    database_path = Path(os.getenv("HUB_DATABASE_PATH", "./data/hub.db"))
    return f"sqlite+aiosqlite:///{database_path}"


DATABASE_URL = _get_database_url()

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQL logging disabled for production
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def run_database_migrations() -> bool:
    """Run Alembic migrations to head (idempotent).

    This is called by bootstrap system during first-run setup.
    Safe to call multiple times - Alembic will skip if already up-to-date.

    Returns:
        True if migrations were applied, False if already current
    """
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # Project root
        )

        # Check if migrations were actually applied
        applied_migrations = "Running upgrade" in result.stdout

        if result.returncode == 0:
            if applied_migrations:
                print("✅ Migrations applied successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print("✅ Database already up-to-date")
                return False
        else:
            print(f"⚠️  Migration warning: {result.stderr}")
            # Don't fail - might be first run or no migrations needed
            return False
    except Exception as e:
        print(f"❌ Migration error (continuing anyway): {e}")
        return False


async def migrations_are_current() -> bool:
    """Check if all migrations are applied (for health checks).

    Returns:
        True if database is up-to-date
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        if result.returncode == 0 and result.stdout:
            # Check if we're at head
            result_head = subprocess.run(
                [sys.executable, "-m", "alembic", "heads"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )

            current = result.stdout.strip().split()[0] if result.stdout.strip() else ""
            head = result_head.stdout.strip().split()[0] if result_head.stdout.strip() else ""

            return current == head

        return False
    except Exception:
        return False


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session_sync():
    """
    Get a synchronous database session (via aiosqlite run_sync or similar).
    WARNING: This is a hack to support legacy sync code.
    Ideally, we should refactor everything to be async.
    For now, we will use a separate synchronous engine for these specific calls.
    """
    # Create a sync engine just for this purpose
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # We need the sync URL (sqlite:/// instead of sqlite+aiosqlite:///)
    sync_url = DATABASE_URL.replace("+aiosqlite", "")
    sync_engine = create_engine(sync_url)
    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

    return SyncSessionLocal()
