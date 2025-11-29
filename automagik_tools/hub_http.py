"""HTTP server for multi-tenant Hub."""
import os
import webbrowser
import threading
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastmcp import FastMCP, Context
from .hub import tools as hub_tools
from .hub.registry import populate_tool_registry
from .hub.database import get_db_session
from .hub.api_routes import router as api_router
from .hub.auth_routes import router as auth_router
from .hub.setup import (
    setup_router,
    add_setup_middleware,
    ConfigStore,
    ModeManager,
    AppMode,
)
from .hub.bootstrap import bootstrap_application, RuntimeConfig


# Global runtime config (set during bootstrap)
_runtime_config: Optional[RuntimeConfig] = None


def get_runtime_config() -> Optional[RuntimeConfig]:
    """Get the runtime configuration set during bootstrap."""
    return _runtime_config


# Server lifespan: bootstrap and initialize
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Bootstrap application and initialize tool registry on startup."""
    global _runtime_config

    print("🚀 Initializing Hub...")

    # Phase 1: Bootstrap application (handles first-run, migrations, .env migration)
    _runtime_config = await bootstrap_application()

    # Phase 2: Check app mode for zero-config
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        mode_manager = ModeManager(config_store)

        try:
            app_mode = await mode_manager.get_current_mode()
            print(f"📋 App Mode: {app_mode.value}")

            if app_mode == AppMode.UNCONFIGURED:
                print("⚠️  Setup required! Navigate to /setup to configure.")
            elif app_mode == AppMode.LOCAL:
                admin_email = await mode_manager.get_local_admin_email()
                print(f"🏠 Local Mode: Admin = {admin_email}")
            elif app_mode == AppMode.WORKOS:
                creds = await mode_manager.get_workos_credentials()
                print(f"🏢 WorkOS Mode: Domain = {creds.get('authkit_domain') if creds else 'N/A'}")
        except Exception as e:
            print(f"⚠️  Failed to check app mode: {e}")
            print("   Assuming UNCONFIGURED - setup required")

    # Import Google Calendar Tools
    # This registers all calendar tools onto the Hub instance
    print("📅 Importing Google Calendar tools...")
    from automagik_tools.hub.execution import HubToolWrapper

    calendar_server = create_calendar_server()

    # Wrap all tools in the calendar server before importing
    # Note: FastMCP.import_server iterates over server.tools
    # We need to intercept this or wrap them manually.
    # Since import_server just calls self.add_tool, we can iterate and add them manually with wrapping.

    # But import_server is convenient. Let's see if we can wrap them in place.
    # FastMCP tools are stored in _tool_manager._tools

    # Let's iterate and wrap
    # We need to access the private _tool_manager
    tool_manager = calendar_server._tool_manager
    if hasattr(tool_manager, "_tools"):
        for tool in tool_manager._tools.values():
            # tool is a Tool object, tool.fn is the function
            original_fn = tool.fn
            wrapped_fn = HubToolWrapper.wrap(tool.name, original_fn)
            tool.fn = wrapped_fn

    await hub.import_server(calendar_server)

    # Populate tool registry
    await populate_tool_registry()

    # Re-inject credential store to be safe
    credential_store.set_credential_store(db_store)

    print("✅ Hub ready!")

    # Auto-open browser after server is ready
    host = os.getenv("HUB_HOST", "0.0.0.0")
    port = int(os.getenv("HUB_PORT", 8884))

    # Use localhost for browser open (0.0.0.0 won't work in browser)
    browser_host = "localhost" if host == "0.0.0.0" else host
    base_url = f"http://{browser_host}:{port}"

    # Determine URL based on app mode
    # If unconfigured, open directly to setup wizard
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        mode_manager = ModeManager(config_store)
        try:
            current_mode = await mode_manager.get_current_mode()
            if current_mode == AppMode.UNCONFIGURED:
                hub_url = f"{base_url}/setup"
                print("⚙️  Setup required - opening setup wizard in browser")
            else:
                hub_url = base_url
        except Exception:
            # If mode check fails, assume unconfigured
            hub_url = f"{base_url}/setup"

    def open_browser():
        """Open browser after a short delay to ensure server is listening.

        Uses Python's webbrowser module which automatically detects the OS
        and uses the appropriate browser opening mechanism:
        - Windows: uses os.startfile() or ShellExecute
        - macOS: uses 'open' command
        - Linux: uses xdg-open, gnome-open, or kde-open
        """
        time.sleep(2)  # Wait for server to fully start
        print(f"🌐 Opening browser to {hub_url}")
        webbrowser.open(hub_url)

    # Start browser open in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    yield
    print("👋 Hub shutting down...")


# Create Hub with conditional AuthKit
from automagik_tools.tools.google_calendar import create_server as create_calendar_server
from .hub.middleware import get_hub_middleware


# Initialize FastMCP Hub
# Note: Authentication is handled by custom routes in auth_routes.py
# This allows support for dual-mode (local passwordless + WorkOS enterprise)
hub = FastMCP(
    name="Automagik Tools Hub",
    instructions="Multi-tenant MCP tool management hub. Use the available tools to manage your personal tool collection.",
    lifespan=lifespan,
    # No auth parameter - custom routes handle authentication
)

# Add multi-tenant middleware
for middleware in get_hub_middleware():
    hub.add_middleware(middleware)


# --- Hub Management Tools ---
# Note: Auth routes are automatically handled by AuthKitProvider

@hub.tool()
async def get_available_tools() -> List[Dict[str, Any]]:
    """List all tools available in the repository that you can add to your collection."""
    return await hub_tools.get_available_tools()


@hub.tool()
async def get_tool_metadata(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed metadata and configuration schema for a specific tool.

    Args:
        tool_name: Name of the tool to get metadata for
    """
    return await hub_tools.get_tool_metadata(tool_name)


@hub.tool()
async def add_tool(tool_name: str, config: Dict[str, Any], ctx: Context) -> str:
    """
    Add a tool to your personal collection.

    Args:
        tool_name: Name of the tool to add (use get_available_tools to see options)
        config: Configuration dictionary with required keys (use get_tool_metadata to see schema)
    """
    # User authentication is handled by AuthKitProvider
    # ctx.get_state("user_id") will be available
    return await hub_tools.add_tool(tool_name, config, ctx)


@hub.tool()
async def remove_tool(tool_name: str, ctx: Context) -> str:
    """
    Remove a tool from your personal collection.

    Args:
        tool_name: Name of the tool to remove
    """
    return await hub_tools.remove_tool(tool_name, ctx)


@hub.tool()
async def list_my_tools(ctx: Context) -> List[Dict[str, Any]]:
    """List all tools currently in your personal collection."""
    return await hub_tools.list_my_tools(ctx)


@hub.tool()
async def get_tool_config(tool_name: str, ctx: Context) -> Dict[str, Any]:
    """
    Get current configuration for a tool in your collection.

    Args:
        tool_name: Name of the tool
    """
    return await hub_tools.get_tool_config(tool_name, ctx)


@hub.tool()
async def update_tool_config(tool_name: str, config: Dict[str, Any], ctx: Context) -> str:
    """
    Update configuration for a tool in your collection.

    Args:
        tool_name: Name of the tool
        config: New configuration values (partial updates allowed)
    """
    return await hub_tools.update_tool_config(tool_name, config, ctx)


@hub.tool()
async def get_missing_config(tool_name: str, ctx: Context) -> List[str]:
    """
    Identify missing required configuration keys for a tool.
    
    Args:
        tool_name: Name of the tool
    """
    return await hub_tools.get_missing_config(tool_name, ctx)


# --- Credential Management Tools ---

from .hub import credentials
from .hub.google_credential_store import DatabaseCredentialStore
from .hub.auth.google import google_auth, credential_store

# Initialize and inject DatabaseCredentialStore
# This ensures Google tools use our DB instead of local files
# TODO: Make workspace-aware for multi-tenant support
# For now, use "default" workspace for single-tenant setups
db_store = DatabaseCredentialStore(workspace_id="default")
credential_store.set_credential_store(db_store)


@hub.custom_route("/auth/google/callback", methods=["GET"])
async def google_auth_callback(request: Request):
    """Handle Google OAuth callback."""
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    scope = request.query_params.get("scope")
    
    if not state or not code or not scope:
        return JSONResponse({"error": "Missing required parameters"}, status_code=400)

    # Get configured redirect URI
    from .hub.auth.google.oauth_config import get_oauth_redirect_uri
    redirect_uri = get_oauth_redirect_uri()
    
    # Reconstruct full authorization response URL
    # In production, this should be the full URL captured from the request
    # For now, we construct a mock one sufficient for the flow
    authorization_response = f"{redirect_uri}?state={state}&code={code}&scope={scope}"
    
    try:
        email, creds = google_auth.handle_auth_callback(
            scopes=scope.split(),
            authorization_response=authorization_response,
            redirect_uri=redirect_uri
        )
        return JSONResponse({"message": "Google Authentication Successful", "email": email})
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=400)


@hub.tool()
async def store_credential(
    tool_name: str,
    provider: str,
    secrets: Dict[str, Any],
    ctx: Context
) -> str:
    """
    Store encrypted credentials for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., 'google_calendar')
        provider: Provider name (e.g., 'google', 'github', 'api_key')
        secrets: Dictionary containing secrets (e.g., {'access_token': '...'})
    """
    return await credentials.store_credential(tool_name, provider, secrets, ctx)


@hub.tool()
async def get_credential(
    tool_name: str,
    provider: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Retrieve credentials for a specific tool.
    
    Args:
        tool_name: Name of the tool
        provider: Provider name
    """
    return await credentials.get_credential(tool_name, provider, ctx)


@hub.tool()
async def list_credentials(ctx: Context) -> List[Dict[str, Any]]:
    """List all stored credentials (metadata only, no secrets)."""
    return await credentials.list_credentials(ctx)


@hub.tool()
async def delete_credential(
    tool_name: str,
    provider: str,
    ctx: Context
) -> str:
    """
    Delete a stored credential.
    
    Args:
        tool_name: Name of the tool
        provider: Provider name
    """
    return await credentials.delete_credential(tool_name, provider, ctx)





# Run server
if __name__ == "__main__":
    import uvicorn
    import asyncio

    # Bootstrap to get runtime config
    config = asyncio.run(bootstrap_application())

    print(f"🚀 Starting Hub HTTP server on http://{config.host}:{config.port}")

    # Use uvicorn to run the full app (not hub.run which only starts MCP server)
    uvicorn.run(
        "automagik_tools.hub_http:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info"
    )

# Expose app for Uvicorn CLI
app = hub.http_app()

# Add security headers middleware (must be added before CORS)
# Security settings will be loaded from RuntimeConfig during lifespan
from .hub.security_middleware import SecurityHeadersMiddleware, RequestIDMiddleware

# Middleware initialization happens before lifespan, so we use a factory function
def create_security_middleware():
    """Create security middleware with settings from RuntimeConfig."""
    if _runtime_config is not None:
        return SecurityHeadersMiddleware(
            app,
            enable_hsts=_runtime_config.enable_hsts,
            csp_report_uri=_runtime_config.csp_report_uri
        )
    # Fallback during initialization (will be reconfigured in lifespan)
    return SecurityHeadersMiddleware(app, enable_hsts=False, csp_report_uri="")

# Note: Middleware is added at module level, before bootstrap runs
# The middleware __init__ will read from env as fallback
# This is acceptable as middleware settings are low-risk compared to credentials
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS configuration - SECURITY: Do not use wildcard origins with credentials
# Get CORS origins from runtime config (loaded from database)
def get_cors_origins():
    """Get CORS origins from runtime config, with fallback for startup."""
    if _runtime_config is not None:
        return _runtime_config.allowed_origins
    # Fallback during app initialization before lifespan runs
    return ["http://localhost:8885", "http://localhost:3000", "http://127.0.0.1:8885"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=600,  # Cache preflight for 10 minutes
)

# Mount REST API routes at /api
# api_router is FastAPI, but app is Starlette - need to mount as sub-app
from fastapi import FastAPI, HTTPException
from starlette.routing import Mount

api_app = FastAPI()

# Add WorkOS token refresh middleware (automatic session refresh)
from .hub.auth_middleware import token_refresh_middleware
api_app.middleware("http")(token_refresh_middleware)

api_app.include_router(api_router)
api_app.include_router(auth_router)
api_app.include_router(setup_router)  # Zero-config setup wizard API

# Add discovery routes
from .hub.discovery_routes import router as discovery_router
api_app.include_router(discovery_router)

# Add webhook routes
from .hub.webhooks import directory_sync_router
api_app.include_router(directory_sync_router)

# Add setup wizard support routes
from .hub.filesystem_routes import router as filesystem_router
from .hub.network_routes import router as network_router
from .hub.server_control import router as server_control_router
api_app.include_router(filesystem_router)
api_app.include_router(network_router)
api_app.include_router(server_control_router)

app.mount("/api", api_app)

# Serve static UI files at /app BEFORE adding middleware
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, HTMLResponse, FileResponse
from starlette.routing import Route, Mount
from pathlib import Path
import os

ui_dist = Path(__file__).parent / "hub_ui" / "dist"
if ui_dist.exists():
    # Production SPA handler with proper cache headers
    class ProductionSPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            # Check if file exists
            full_path = os.path.join(self.directory, path)

            # If path has no extension and file doesn't exist, it's a client-side route
            if "." not in path.split("/")[-1] and not os.path.exists(full_path):
                # Serve index.html for SPA routing
                response = FileResponse(
                    os.path.join(self.directory, "index.html"),
                    media_type="text/html"
                )
                # Never cache HTML
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            # Otherwise, try to serve the file normally
            try:
                response = await super().get_response(path, scope)
                return self._add_cache_headers(response, path)
            except (FileNotFoundError, IsADirectoryError, HTTPException):
                # If it's a directory or missing file with extension, try index.html fallback
                if "." not in path.split("/")[-1]:
                    response = FileResponse(
                        os.path.join(self.directory, "index.html"),
                        media_type="text/html"
                    )
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                raise

        def _add_cache_headers(self, response, path):
            # HTML: never cache
            if path.endswith('.html'):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            # Hashed assets (Vite pattern): cache forever
            elif self._is_hashed_asset(path):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            # Other assets: short cache
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
            return response

        def _is_hashed_asset(self, path):
            # Vite pattern: index-RPesmEwX.js
            filename = path.split("/")[-1]
            if any(path.endswith(e) for e in ['.js', '.css', '.woff2', '.woff', '.ttf']):
                name_parts = filename.rsplit('.', 1)[0].split('-')
                return len(name_parts) >= 2 and len(name_parts[-1]) >= 8
            return False

    # Mount SPA at root
    app.mount("/", ProductionSPAStaticFiles(directory=str(ui_dist), html=True), name="ui")

else:
    # UI not built - serve configuration-aware placeholder
    from .hub.setup.config_store import ConfigStore
    from .hub.database import get_db_session

    async def ui_placeholder(request):
        # Check if app is configured
        try:
            async with get_db_session() as session:
                config_store = ConfigStore(session)
                app_mode = await config_store.get_app_mode()
        except Exception:
            app_mode = "unconfigured"

        path = request.url.path

        # If configured and visiting /setup, redirect to home
        if app_mode != "unconfigured" and path == "/setup":
            return RedirectResponse(url="/", status_code=307)

        # Common styles for all placeholder pages
        common_styles = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 48px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 { color: #2d3748; font-size: 2rem; margin-bottom: 16px; }
        p { color: #4a5568; margin-bottom: 12px; line-height: 1.6; }
        code {
            background: #edf2f7;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        a { color: #667eea; }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 24px;
        }
        .status-configured { background: #c6f6d5; color: #276749; }
        .status-unconfigured { background: #feebc8; color: #c05621; }
        .link-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 24px;
        }
        .link-card {
            background: #f7fafc;
            padding: 16px;
            border-radius: 8px;
            text-decoration: none;
            color: #2d3748;
            border: 2px solid #e2e8f0;
            transition: all 0.2s;
        }
        .link-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        .link-card strong { display: block; color: #667eea; margin-bottom: 4px; }
        """

        if app_mode == "unconfigured":
            # Unconfigured - show setup instructions
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup Required - Automagik Tools</title>
    <style>{common_styles}</style>
</head>
<body>
    <div class="container">
        <h1>Automagik Tools Hub</h1>
        <div class="status status-unconfigured">Setup Required</div>
        <p>The frontend UI has not been built yet.</p>
        <p>To complete setup, build the UI first:</p>
        <p><code>cd automagik_tools/hub_ui && pnpm install && pnpm build</code></p>
        <p>Then restart the hub and visit this page again.</p>
        <div class="link-grid">
            <a href="/docs" class="link-card">
                <strong>API Docs</strong>
                <span>Swagger UI</span>
            </a>
            <a href="/api/health" class="link-card">
                <strong>Health Check</strong>
                <span>System Status</span>
            </a>
        </div>
    </div>
</body>
</html>"""
        else:
            # Configured but UI not built - show status with actual mode
            mode_display = app_mode.upper() if app_mode else "UNKNOWN"
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automagik Tools Hub</title>
    <style>{common_styles}</style>
</head>
<body>
    <div class="container">
        <h1>Automagik Tools Hub</h1>
        <div class="status status-configured">Mode: {mode_display}</div>
        <p>The hub is configured and running.</p>
        <p>The frontend UI is not built. For the full experience, build it:</p>
        <p><code>cd automagik_tools/hub_ui && pnpm install && pnpm build</code></p>
        <div class="link-grid">
            <a href="/docs" class="link-card">
                <strong>API Docs</strong>
                <span>Swagger UI</span>
            </a>
            <a href="/redoc" class="link-card">
                <strong>ReDoc</strong>
                <span>API Reference</span>
            </a>
            <a href="/api/health" class="link-card">
                <strong>Health Check</strong>
                <span>System Status</span>
            </a>
            <a href="/mcp" class="link-card">
                <strong>MCP Endpoint</strong>
                <span>Model Context Protocol</span>
            </a>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html)

    # Register placeholder routes
    app.add_route("/", ui_placeholder, methods=["GET"])
    app.add_route("/setup", ui_placeholder, methods=["GET"])

# Add setup middleware AFTER routes are registered
add_setup_middleware(app)
