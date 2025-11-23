"""HTTP server for multi-tenant Hub."""
import os
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from fastmcp import FastMCP, Context
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from .hub.auth import get_current_user, get_auth_url, authenticate_with_code, get_logout_url
from .hub import tools as hub_tools
from .hub.registry import populate_tool_registry
from .hub.database import init_database


# Server lifespan: populate tool registry on startup
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize tool registry on server startup."""
    print("🚀 Initializing Hub...")

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
    yield
    print("👋 Hub shutting down...")


# Create Hub
from .hub.auth.middleware import AuthMiddleware
from automagik_tools.tools.google_calendar import create_server as create_calendar_server

hub = FastMCP(
    name="Automagik Tools Hub",
    instructions="Multi-tenant MCP tool management hub. Use the available tools to manage your personal tool collection.",
    lifespan=lifespan,
    middleware=[AuthMiddleware()],
)


# --- Auth Routes ---

@hub.custom_route("/login", methods=["GET"])
async def login(request: Request):
    """Redirect to AuthKit login."""
    redirect_uri = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8000/auth/callback")
    return JSONResponse({"url": get_auth_url(redirect_uri)})

@hub.custom_route("/auth/callback", methods=["GET"])
async def auth_callback(request: Request):
    """Handle AuthKit callback."""
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "Missing code parameter"}, status_code=400)
        
    try:
        result = await authenticate_with_code(code)
        # In a real app, you'd set the cookie here using FastAPI's Response
        # For this simple example, we return the session data
        # The client needs to handle setting the cookie 'wos_session'
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=400)

@hub.custom_route("/logout", methods=["GET"])
async def logout(request: Request):
    """Logout user."""
    try:
        # Manually call get_current_user dependency
        user = await get_current_user(request)
        # If successful, we can proceed with logout logic if any
        # For now, just return success
        return JSONResponse({"message": "Logged out"})
    except HTTPException as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


# --- Hub Management Tools ---

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
    # Verify auth
    # user = await get_current_user(ctx.request) # This requires ctx to have request
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
    port = int(os.getenv("HUB_PORT", 8000))

    print(f"🚀 Starting Hub HTTP server on http://{host}:{port}")

    # Direct HTTP deployment (recommended)
    hub.run(transport="http", host=host, port=port, lifespan="on")

# Expose app for Uvicorn CLI
app = hub.http_app
