"""REST API routes for Hub UI."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastmcp.server.dependencies import get_access_token, AccessToken
from . import registry, tools as hub_tools
from .credentials import store_credential, get_credential, list_credentials, delete_credential


# Security scheme
security = HTTPBearer()


# Request/Response Models
class ToolConfigRequest(BaseModel):
    """Request model for tool configuration."""
    config: Dict[str, Any]


class ToolTestRequest(BaseModel):
    """Request model for testing tool connection."""
    config: Dict[str, Any]


class CredentialRequest(BaseModel):
    """Request model for credential storage."""
    provider: str
    secrets: Dict[str, Any]


# Helper to extract user_id from token
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from access token."""
    # In production, verify token with WorkOS
    # For now, extract from token claims
    token = get_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = token.claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID")

    return user_id


# Create router (no prefix - will be mounted at /api in hub_http.py)
router = APIRouter()


# --- Tool Catalogue Endpoints ---

@router.get("/tools/catalogue")
async def get_tool_catalogue() -> List[Dict[str, Any]]:
    """
    Get complete tool catalogue with metadata.
    Public endpoint (no auth required for browsing).
    """
    return await registry.list_available_tools()


@router.get("/tools/{tool_name}/metadata")
async def get_tool_metadata_api(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed metadata for a specific tool.
    Public endpoint (no auth required).
    """
    metadata = await registry.get_tool_metadata(tool_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return metadata


@router.get("/tools/{tool_name}/schema")
async def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """
    Get configuration schema for a specific tool.
    Public endpoint (no auth required).
    """
    metadata = await registry.get_tool_metadata(tool_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return {
        "tool_name": tool_name,
        "config_schema": metadata.get("config_schema", {}),
        "auth_type": metadata.get("auth_type", "none"),
        "required_oauth": metadata.get("required_oauth", []),
    }


# --- User Tool Management Endpoints ---

@router.get("/user/tools")
async def list_user_tools(user_id: str = Depends(get_current_user_id)) -> List[Dict[str, Any]]:
    """List all tools configured by the current user."""
    # Create mock Context with user_id
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    return await hub_tools.list_my_tools(ctx)


@router.post("/user/tools/{tool_name}")
async def configure_tool(
    tool_name: str,
    request: ToolConfigRequest,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Add and configure a tool for the current user."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    result = await hub_tools.add_tool(tool_name, request.config, ctx)

    return {
        "status": "success",
        "message": result,
        "tool": tool_name
    }


@router.get("/user/tools/{tool_name}")
async def get_user_tool_config(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get current configuration for a user's tool."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    return await hub_tools.get_tool_config(tool_name, ctx)


@router.put("/user/tools/{tool_name}")
async def update_user_tool_config(
    tool_name: str,
    request: ToolConfigRequest,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Update configuration for a user's tool."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    result = await hub_tools.update_tool_config(tool_name, request.config, ctx)

    return {
        "status": "success",
        "message": result,
        "tool": tool_name
    }


@router.delete("/user/tools/{tool_name}")
async def delete_user_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Remove a tool from user's collection."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    result = await hub_tools.remove_tool(tool_name, ctx)

    return {
        "status": "success",
        "message": result,
        "tool": tool_name
    }


@router.post("/user/tools/{tool_name}/test")
async def test_tool_connection(
    tool_name: str,
    request: ToolTestRequest,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Test tool connection with provided configuration.
    Does not save the configuration.
    """
    # TODO: Implement per-tool connection testing
    # For now, just validate the config against schema

    metadata = await registry.get_tool_metadata(tool_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    config_schema = metadata.get("config_schema", {})
    required_keys = config_schema.get("required", [])

    missing_keys = [key for key in required_keys if key not in request.config]
    if missing_keys:
        return {
            "status": "error",
            "message": f"Missing required configuration keys: {', '.join(missing_keys)}",
            "valid": False
        }

    # If schema validation passes, assume connection would work
    # In production, we'd actually try to connect to the service
    return {
        "status": "success",
        "message": "Configuration is valid",
        "valid": True
    }


# --- Tool Lifecycle Endpoints ---
# TODO: Implement start/stop/refresh/logs endpoints


@router.get("/user/tools/{tool_name}/status")
async def get_tool_status(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get runtime status of a tool."""
    # TODO: Implement tool instance tracking
    # For now, return mock status

    return {
        "tool": tool_name,
        "status": "unknown",  # running, stopped, error
        "message": "Status tracking not yet implemented"
    }


@router.post("/user/tools/{tool_name}/start")
async def start_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Start a tool instance."""
    # TODO: Implement tool instance management
    return {
        "status": "success",
        "message": "Tool lifecycle management not yet implemented",
        "tool": tool_name
    }


@router.post("/user/tools/{tool_name}/stop")
async def stop_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Stop a tool instance."""
    # TODO: Implement tool instance management
    return {
        "status": "success",
        "message": "Tool lifecycle management not yet implemented",
        "tool": tool_name
    }


@router.post("/user/tools/{tool_name}/refresh")
async def refresh_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Refresh tool configuration/reload."""
    # TODO: Implement tool instance management
    return {
        "status": "success",
        "message": "Tool lifecycle management not yet implemented",
        "tool": tool_name
    }


# --- Credential Management Endpoints ---

@router.post("/user/credentials/{tool_name}")
async def store_tool_credential(
    tool_name: str,
    request: CredentialRequest,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Store encrypted credentials for a tool."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    result = await store_credential(tool_name, request.provider, request.secrets, ctx)

    return {
        "status": "success",
        "message": result
    }


@router.get("/user/credentials/{tool_name}")
async def get_tool_credential(
    tool_name: str,
    provider: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Retrieve credentials for a tool."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    return await get_credential(tool_name, provider, ctx)


@router.get("/user/credentials")
async def list_user_credentials(user_id: str = Depends(get_current_user_id)) -> List[Dict[str, Any]]:
    """List all user's credentials (metadata only)."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    return await list_credentials(ctx)


@router.delete("/user/credentials/{tool_name}")
async def delete_tool_credential(
    tool_name: str,
    provider: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Delete a tool credential."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    result = await delete_credential(tool_name, provider, ctx)

    return {
        "status": "success",
        "message": result
    }


# --- Health & Info Endpoints ---

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/info")
async def server_info() -> Dict[str, Any]:
    """Get server information."""
    return {
        "name": "Automagik Tools Hub",
        "version": "0.1.0",
        "auth_provider": "WorkOS AuthKit",
        "features": [
            "multi_tenant",
            "oauth_support",
            "encrypted_credentials",
            "dynamic_tool_loading"
        ]
    }
