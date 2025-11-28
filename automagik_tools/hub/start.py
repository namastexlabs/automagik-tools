"""Hub startup wrapper - database-first configuration.

This module provides the entry point for PM2/systemd to start the Hub.
It reads configuration from the database BEFORE starting uvicorn,
enabling true zero-configuration operation.

Usage:
    python -m automagik_tools.hub.start
    # or via entry point:
    automagik-hub-start
"""
import asyncio
import sys
import signal
from typing import Optional


async def start_hub() -> None:
    """Bootstrap from database, then start uvicorn.

    This is the core startup flow:
    1. Run bootstrap_application() to initialize/read database config
    2. Extract host/port from RuntimeConfig
    3. Start uvicorn with database-provided values

    This inverts the traditional flow where PM2 passes port via environment.
    Now: PM2 just starts Python -> Python reads DB -> Python starts uvicorn.
    """
    from automagik_tools.hub.bootstrap import bootstrap_application

    # Phase 1: Bootstrap - reads config from database
    print("🚀 Starting Hub with database-first configuration...")
    config = await bootstrap_application()

    # Phase 2: Start uvicorn with database values
    import uvicorn

    print(f"🌐 Starting server on {config.host}:{config.port}")

    uvicorn_config = uvicorn.Config(
        "automagik_tools.hub_http:app",
        host=config.host,
        port=config.port,
        log_level="info",
        access_log=True,
        # Disable uvicorn's own lifespan since we handle bootstrap here
        # The app's lifespan will still run for cleanup
        lifespan="on",
    )

    server = uvicorn.Server(uvicorn_config)

    # Handle graceful shutdown
    def handle_signal(signum: int, frame: Optional[object]) -> None:
        print(f"\n📴 Received signal {signum}, shutting down...")
        server.should_exit = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    await server.serve()


def main() -> None:
    """Entry point for PM2/systemd.

    This is called by:
    - PM2: python -m automagik_tools.hub.start
    - Entry point: automagik-hub-start
    - Systemd: ExecStart=/path/to/python -m automagik_tools.hub.start
    """
    try:
        asyncio.run(start_hub())
    except KeyboardInterrupt:
        print("\n👋 Shutdown complete")
        sys.exit(0)
    except SystemExit as e:
        # Re-raise SystemExit (from bootstrap failures) as-is
        raise
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
