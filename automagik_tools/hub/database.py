"""Database connection and session management."""
import os
import subprocess
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import Base


# Database configuration
DATABASE_PATH = Path(os.getenv("HUB_DATABASE_PATH", "./data/hub.db"))
# Ensure directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

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


def run_migrations():
    """Run Alembic migrations to head."""
    print("Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # Project root
        )
        if result.returncode == 0:
            print("Migrations completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Migration warning: {result.stderr}")
            # Don't fail - might be first run or no migrations needed
    except Exception as e:
        print(f"Migration error (continuing anyway): {e}")


async def init_database():
    """Initialize database with auto-migration support."""
    # Run Alembic migrations first
    run_migrations()

    # Fallback: create any missing tables (for development)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
