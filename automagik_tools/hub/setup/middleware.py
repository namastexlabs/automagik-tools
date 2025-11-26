"""Setup wizard middleware for zero-config startup.

Redirects to setup wizard if app is in UNCONFIGURED mode.
Allows public access to setup routes only.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from .config_store import ConfigStore
from .mode_manager import AppMode, ModeManager


class SetupRequiredMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce setup completion.

    If app is UNCONFIGURED, only allow access to:
    - /setup/* (setup API)
    - /app/setup (setup UI)
    - Static assets
    """

    ALLOWED_PATHS_UNCONFIGURED = {
        "/api/setup/",  # Setup API routes
        "/setup/",      # Legacy setup routes
        "/app/setup",   # Setup UI
        "/app/",        # App UI (all pages)
        "/static/",     # Static assets
        "/favicon.ico",
        "/api/health",  # Health check
        "/health",
        "/docs",        # API docs (root)
        "/api/docs",    # API docs (mounted)
        "/api/redoc",   # ReDoc (mounted)
        "/api/openapi.json",  # OpenAPI spec
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next):
        """Check setup status before processing request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or redirect
        """
        path = request.url.path

        # Check app mode
        try:
            async with get_db_session() as session:
                config_store = ConfigStore(session)
                mode_str = await config_store.get_app_mode()
                mode = AppMode(mode_str)

                # If configured, allow all requests
                if mode != AppMode.UNCONFIGURED:
                    return await call_next(request)

                # In UNCONFIGURED mode, only allow setup routes
                if self._is_allowed_path(path):
                    return await call_next(request)

                # Redirect to setup wizard
                if path.startswith("/api/"):
                    # API requests get 503 Service Unavailable
                    return Response(
                        content='{"error": "Setup required", "setup_url": "/app/setup"}',
                        status_code=503,
                        media_type="application/json"
                    )
                else:
                    # Browser requests get redirected
                    return RedirectResponse(url="/app/setup", status_code=307)

        except Exception as e:
            # If database not initialized yet, allow setup routes
            if self._is_allowed_path(path):
                return await call_next(request)

            # Otherwise, show error
            return Response(
                content=f'{{"error": "Setup error", "detail": "{str(e)}"}}',
                status_code=500,
                media_type="application/json"
            )

    def _is_allowed_path(self, path: str) -> bool:
        """Check if path is allowed in UNCONFIGURED mode.

        Args:
            path: Request path

        Returns:
            True if allowed
        """
        for allowed in self.ALLOWED_PATHS_UNCONFIGURED:
            if path.startswith(allowed):
                return True
        return False


def add_setup_middleware(app: FastAPI):
    """Add setup middleware to FastAPI app.

    Args:
        app: FastAPI application
    """
    app.add_middleware(SetupRequiredMiddleware)
