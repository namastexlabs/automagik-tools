"""REST API routes for Hub UI."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastmcp.server.dependencies import get_access_token, AccessToken
from . import registry, tools as hub_tools
from .credentials import store_credential, get_credential, list_credentials, delete_credential
from .tool_instances import get_instance_manager


# Security scheme (optional - for backward compatibility with bearer tokens)
security = HTTPBearer(auto_error=False)


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


# Helper to extract user_id from session cookie (supports both modes)
async def get_current_user_id(request: Request) -> str:
    """Extract user ID from session cookie.

    Supports both WorkOS mode (wos_session cookie) and Local Mode (local_session cookie).
    Falls back to bearer token if cookies are not present (for backward compatibility).
    """
    from .auth import get_current_user

    try:
        # Try cookie-based authentication first (both WorkOS and Local Mode)
        user = await get_current_user(request)
        return user.get("id") or user.get("user_id")
    except HTTPException:
        # Fall back to bearer token (for backward compatibility)
        token = get_access_token()
        if token:
            user_id = token.claims.get("sub")
            if user_id:
                return user_id

        # No valid authentication
        raise HTTPException(status_code=401, detail="Not authenticated")


async def get_current_user_context(request: Request) -> Dict[str, Any]:
    """Get full user context including user_id and workspace_id.

    Returns the complete user object from authentication, which includes:
    - id/user_id: The user's unique identifier
    - workspace_id: The user's workspace (required for multi-tenant operations)
    - email, first_name, last_name: User profile info
    - is_super_admin: Admin status flag
    """
    from .auth import get_current_user

    try:
        # Try cookie-based authentication first (both WorkOS and Local Mode)
        return await get_current_user(request)
    except HTTPException:
        # Fall back to bearer token (for backward compatibility)
        token = get_access_token()
        if token:
            user_id = token.claims.get("sub")
            workspace_id = token.claims.get("workspace_id")
            if user_id:
                return {
                    "id": user_id,
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                }

        # No valid authentication
        raise HTTPException(status_code=401, detail="Not authenticated")


def extract_user_workspace(user: Dict[str, Any]) -> tuple[str, str]:
    """Extract user_id and workspace_id from user dict.

    Returns:
        Tuple of (user_id, workspace_id)
    """
    user_id = user.get("id") or user.get("user_id")
    workspace_id = user.get("workspace_id")
    return user_id, workspace_id


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
async def list_user_tools(user: Dict[str, Any] = Depends(get_current_user_context)) -> List[Dict[str, Any]]:
    """List all tools configured by the current user."""
    user_id, workspace_id = extract_user_workspace(user)
    return await hub_tools.list_my_tools(user_id=user_id, workspace_id=workspace_id)


@router.post("/user/tools/{tool_name}")
async def configure_tool(
    tool_name: str,
    request: ToolConfigRequest,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Add and configure a tool for the current user."""
    user_id, workspace_id = extract_user_workspace(user)
    result = await hub_tools.add_tool(tool_name, request.config, user_id=user_id, workspace_id=workspace_id)

    return {
        "status": "success",
        "message": result,
        "tool": tool_name
    }


@router.get("/user/tools/{tool_name}")
async def get_user_tool_config(
    tool_name: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Get current configuration for a user's tool."""
    user_id, workspace_id = extract_user_workspace(user)
    return await hub_tools.get_tool_config(tool_name, user_id=user_id, workspace_id=workspace_id)


@router.put("/user/tools/{tool_name}")
async def update_user_tool_config(
    tool_name: str,
    request: ToolConfigRequest,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Update configuration for a user's tool."""
    user_id, workspace_id = extract_user_workspace(user)
    result = await hub_tools.update_tool_config(tool_name, request.config, user_id=user_id, workspace_id=workspace_id)

    return {
        "status": "success",
        "message": result,
        "tool": tool_name
    }


@router.delete("/user/tools/{tool_name}")
async def delete_user_tool(
    tool_name: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Remove a tool from user's collection."""
    user_id, workspace_id = extract_user_workspace(user)
    result = await hub_tools.remove_tool(tool_name, user_id=user_id, workspace_id=workspace_id)

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


@router.get("/user/tools/{tool_name}/status")
async def get_tool_status(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get runtime status of a tool."""
    manager = get_instance_manager()
    return await manager.get_tool_status(user_id, tool_name)


@router.post("/user/tools/{tool_name}/start")
async def start_tool(
    tool_name: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Start a tool instance."""
    user_id, workspace_id = extract_user_workspace(user)

    # Get user's tool configuration
    try:
        config = await hub_tools.get_tool_config(tool_name, user_id=user_id, workspace_id=workspace_id)
    except Exception:
        # No config found, use empty config
        config = {}

    manager = get_instance_manager()
    return await manager.start_tool(user_id, tool_name, config)


@router.post("/user/tools/{tool_name}/stop")
async def stop_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Stop a tool instance."""
    manager = get_instance_manager()
    return await manager.stop_tool(user_id, tool_name)


@router.post("/user/tools/{tool_name}/refresh")
async def refresh_tool(
    tool_name: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Refresh tool configuration/reload."""
    user_id, workspace_id = extract_user_workspace(user)

    # Get user's latest tool configuration
    try:
        config = await hub_tools.get_tool_config(tool_name, user_id=user_id, workspace_id=workspace_id)
    except Exception:
        config = {}

    manager = get_instance_manager()
    return await manager.refresh_tool(user_id, tool_name, config)


# --- Credential Management Endpoints ---

@router.post("/user/credentials/{tool_name}")
async def store_tool_credential(
    tool_name: str,
    request: CredentialRequest,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Store encrypted credentials for a tool."""
    user_id, _ = extract_user_workspace(user)
    result = await store_credential(tool_name, request.provider, request.secrets, user_id=user_id)

    return {
        "status": "success",
        "message": result
    }


@router.get("/user/credentials/{tool_name}")
async def get_tool_credential(
    tool_name: str,
    provider: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Retrieve credentials for a tool."""
    user_id, _ = extract_user_workspace(user)
    return await get_credential(tool_name, provider, user_id=user_id)


@router.get("/user/credentials")
async def list_user_credentials(user: Dict[str, Any] = Depends(get_current_user_context)) -> List[Dict[str, Any]]:
    """List all user's credentials (metadata only)."""
    user_id, _ = extract_user_workspace(user)
    return await list_credentials(user_id=user_id)


@router.delete("/user/credentials/{tool_name}")
async def delete_tool_credential(
    tool_name: str,
    provider: str,
    user: Dict[str, Any] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Delete a tool credential."""
    user_id, _ = extract_user_workspace(user)
    result = await delete_credential(tool_name, provider, user_id=user_id)

    return {
        "status": "success",
        "message": result
    }


# --- Workspace Endpoints ---

@router.get("/workspace")
async def get_my_workspace(user_id: str = Depends(get_current_user_id)) -> Dict[str, Any]:
    """Get current user's workspace details."""
    from .database import get_db_session
    from .models import User
    from .workspaces import get_workspace, get_workspace_stats
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(User.workspace_id).where(User.id == user_id)
        )
        workspace_id = result.scalar_one_or_none()

    if not workspace_id:
        raise HTTPException(status_code=404, detail="No workspace found")

    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    stats = await get_workspace_stats(workspace_id)

    return {
        **workspace,
        "stats": stats,
    }


@router.put("/workspace/settings")
async def update_my_workspace_settings(
    settings: Dict[str, Any],
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Update workspace settings."""
    from .database import get_db_session
    from .models import User
    from .workspaces import update_workspace_settings
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(User.workspace_id).where(User.id == user_id)
        )
        workspace_id = result.scalar_one_or_none()

    if not workspace_id:
        raise HTTPException(status_code=404, detail="No workspace found")

    return await update_workspace_settings(workspace_id, settings)


# --- Audit Log Endpoints ---

@router.get("/audit-logs")
async def get_audit_logs_api(
    category: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """Get audit logs for user's workspace."""
    from .database import get_db_session
    from .models import User, AuditEventCategory
    from .audit import logger as audit_module
    from sqlalchemy import select

    async with get_db_session() as session:
        result = await session.execute(
            select(User.workspace_id).where(User.id == user_id)
        )
        workspace_id = result.scalar_one_or_none()

    if not workspace_id:
        raise HTTPException(status_code=404, detail="No workspace found")

    # Parse category if provided
    category_enum = None
    if category:
        try:
            category_enum = AuditEventCategory(category)
        except ValueError:
            pass  # Invalid category, ignore filter

    return await audit_module.get_audit_logs(
        workspace_id=workspace_id,
        category=category_enum,
        action=action,
        limit=limit,
        offset=offset,
    )


# --- Admin Endpoints (Super Admin Only) ---

@router.get("/admin/workspaces")
async def list_all_workspaces_api(
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """List all workspaces (super admin only)."""
    from .authorization import is_super_admin
    from .database import get_db_session
    from .models import User
    from .workspaces import list_all_workspaces
    from sqlalchemy import select

    # Check if user is super admin
    async with get_db_session() as session:
        result = await session.execute(
            select(User.email, User.is_super_admin).where(User.id == user_id)
        )
        row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    email, db_is_super_admin = row
    if not (db_is_super_admin or is_super_admin(email)):
        raise HTTPException(status_code=403, detail="Super admin access required")

    return await list_all_workspaces(limit=limit, offset=offset)


@router.get("/admin/audit-logs")
async def get_all_audit_logs_api(
    workspace_id: Optional[str] = None,
    category: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """Get all audit logs (super admin only)."""
    from .authorization import is_super_admin
    from .database import get_db_session
    from .models import User, AuditEventCategory
    from .audit import logger as audit_module
    from sqlalchemy import select

    # Check if user is super admin
    async with get_db_session() as session:
        result = await session.execute(
            select(User.email, User.is_super_admin).where(User.id == user_id)
        )
        row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    email, db_is_super_admin = row
    if not (db_is_super_admin or is_super_admin(email)):
        raise HTTPException(status_code=403, detail="Super admin access required")

    # Parse category if provided
    category_enum = None
    if category:
        try:
            category_enum = AuditEventCategory(category)
        except ValueError:
            pass

    return await audit_module.get_audit_logs(
        workspace_id=workspace_id,
        category=category_enum,
        action=action,
        limit=limit,
        offset=offset,
    )


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
            "workspace_isolation",
            "oauth_support",
            "encrypted_credentials",
            "dynamic_tool_loading",
            "audit_logging",
            "directory_sync",
        ]
    }
