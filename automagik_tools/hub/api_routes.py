"""REST API routes for Hub UI."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastmcp.server.dependencies import get_access_token, AccessToken
from . import registry, tools as hub_tools
from .credentials import store_credential, get_credential, list_credentials, delete_credential
from .tool_instances import get_instance_manager


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
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Start a tool instance."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    # Get user's tool configuration
    try:
        config = await hub_tools.get_tool_config(tool_name, ctx)
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
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Refresh tool configuration/reload."""
    from fastmcp import Context

    ctx = Context()
    ctx.set_state("user_id", user_id)

    # Get user's latest tool configuration
    try:
        config = await hub_tools.get_tool_config(tool_name, ctx)
    except Exception:
        config = {}

    manager = get_instance_manager()
    return await manager.refresh_tool(user_id, tool_name, config)


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
