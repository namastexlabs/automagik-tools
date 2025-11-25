"""HTTP server for multi-tenant Hub."""
import os
import webbrowser
import threading
import time
from typing import Dict, Any, List
from contextlib import asynccontextmanager

# Load environment variables before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastmcp import FastMCP, Context
from fastmcp.server.auth.providers.workos import AuthKitProvider
from .hub import tools as hub_tools
from .hub.registry import populate_tool_registry
from .hub.database import init_database, get_db_session
from .hub.api_routes import router as api_router
from .hub.auth_routes import router as auth_router
from .hub.setup import (
    setup_router,
    add_setup_middleware,
    ConfigStore,
    ModeManager,
    AppMode,
)


# Server lifespan: populate tool registry on startup
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize tool registry on server startup."""
    print("🚀 Initializing Hub...")

    # Initialize database tables
    await init_database()

    # Check app mode for zero-config
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        mode_manager = ModeManager(config_store)

        try:
            app_mode = await mode_manager.get_current_mode()
            print(f"📋 App Mode: {app_mode.value}")

            if app_mode == AppMode.UNCONFIGURED:
                print("⚠️  Setup required! Navigate to /app/setup to configure.")
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
                hub_url = f"{base_url}/app/setup"
                print("⚙️  Setup required - opening setup wizard in browser")
            else:
                hub_url = base_url
        except Exception:
            # If mode check fails, assume unconfigured
            hub_url = f"{base_url}/app/setup"

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


def get_auth_provider():
    """Get auth provider based on app mode.

    Returns None if UNCONFIGURED or LOCAL mode.
    Returns AuthKitProvider if WORKOS mode.
    """
    try:
        # Try to read mode from database
        import asyncio
        from .hub.database import AsyncSessionLocal

        async def check_mode():
            async with AsyncSessionLocal() as session:
                config_store = ConfigStore(session)
                mode_str = await config_store.get_app_mode()
                mode = AppMode(mode_str)

                if mode == AppMode.WORKOS:
                    # Get WorkOS credentials from database
                    mode_manager = ModeManager(config_store)
                    creds = await mode_manager.get_workos_credentials()
                    if creds:
                        return AuthKitProvider(
                            authkit_domain=creds["authkit_domain"],
                            base_url=os.getenv("HUB_BASE_URL", "http://localhost:8884")
                        )
                return None

        # Run async check
        return asyncio.run(check_mode())
    except Exception as e:
        # If database not ready or mode check fails, return None
        print(f"⚠️  Auth provider check failed: {e}")
        return None


# Initialize auth provider (None for UNCONFIGURED/LOCAL, AuthKitProvider for WORKOS)
auth_provider = get_auth_provider()

hub = FastMCP(
    name="Automagik Tools Hub",
    instructions="Multi-tenant MCP tool management hub. Use the available tools to manage your personal tool collection.",
    lifespan=lifespan,
    auth=auth_provider,  # Conditional auth: None for local mode, AuthKit for WorkOS
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
db_store = DatabaseCredentialStore()
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

    host = os.getenv("HUB_HOST", "0.0.0.0")
    port = int(os.getenv("HUB_PORT", 8884))

    print(f"🚀 Starting Hub HTTP server on http://{host}:{port}")

    # Direct HTTP deployment (recommended)
    hub.run(transport="http", host=host, port=port, lifespan="on")

# Expose app for Uvicorn CLI
app = hub.http_app()

# Add security headers middleware (must be added before CORS)
from .hub.security_middleware import SecurityHeadersMiddleware, RequestIDMiddleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS configuration - SECURITY: Do not use wildcard origins with credentials
ALLOWED_ORIGINS = os.getenv(
    "HUB_ALLOWED_ORIGINS",
    "http://localhost:8885,http://localhost:3000,http://127.0.0.1:8885"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=600,  # Cache preflight for 10 minutes
)

# Mount REST API routes at /api
# api_router is FastAPI, but app is Starlette - need to mount as sub-app
from fastapi import FastAPI
from starlette.routing import Mount

api_app = FastAPI()
api_app.include_router(api_router)
api_app.include_router(auth_router)
api_app.include_router(setup_router)  # Zero-config setup wizard API

# Add discovery routes
from .hub.discovery_routes import router as discovery_router
api_app.include_router(discovery_router)

# Add webhook routes
from .hub.webhooks import directory_sync_router
api_app.include_router(directory_sync_router)

app.mount("/api", api_app)

# Add setup middleware (must be after app creation)
add_setup_middleware(app)

# Serve static UI files at /app
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette.routing import Route
from pathlib import Path

ui_dist = Path(__file__).parent / "hub_ui" / "dist"
if ui_dist.exists():
    app.mount("/app", StaticFiles(directory=str(ui_dist), html=True), name="ui")

    # Redirect root to /app
    async def root(request):
        return RedirectResponse(url="/app")

    app.routes.append(Route("/", root))
else:
    # UI not built - serve placeholder
    from starlette.responses import JSONResponse

    async def ui_placeholder(request):
        return JSONResponse({
            "message": "Hub UI not built yet",
            "instructions": "Run: cd automagik_tools/hub_ui && npm install && npm run build",
            "mcp_endpoint": "/mcp",
            "api_endpoint": "/api"
        })

    app.routes.append(Route("/", ui_placeholder))
    app.routes.append(Route("/app", ui_placeholder))
