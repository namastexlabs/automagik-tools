"""Authentication configuration using AuthKit (WorkOS).

WorkOS credentials are loaded from database after bootstrap.
During bootstrap phase, credentials are auto-migrated from .env if present.
"""
from typing import Optional, Dict, Any
import asyncio
import workos
from workos import WorkOSClient
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastmcp import Context

from ..database import get_db_session
from ..setup import ConfigStore

# Cache for WorkOS client to avoid repeated database queries
_workos_client: Optional[WorkOSClient] = None
_cookie_password: Optional[str] = None


async def _load_workos_credentials() -> tuple[str, str, str]:
    """Load WorkOS credentials from database.

    Returns:
        Tuple of (api_key, client_id, cookie_password)

    Raises:
        ValueError: If credentials not configured
    """
    async with get_db_session() as session:
        config_store = ConfigStore(session)

        api_key = await config_store.get(ConfigStore.KEY_WORKOS_API_KEY)
        client_id = await config_store.get(ConfigStore.KEY_WORKOS_CLIENT_ID)
        cookie_password = await config_store.get_or_generate_cookie_password()

        if not api_key or not client_id:
            raise ValueError(
                "WorkOS not configured. Please complete setup wizard at /setup"
            )

        return api_key, client_id, cookie_password


def get_workos_client() -> WorkOSClient:
    """Get WorkOS client (cached).

    For sync contexts. Loads credentials from database on first call.
    """
    global _workos_client

    if _workos_client is None:
        # Load from database (blocking call)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run async in running loop - this shouldn't happen
                raise ValueError(
                    "Cannot initialize WorkOS client from running event loop"
                )
            api_key, client_id, _ = loop.run_until_complete(
                _load_workos_credentials()
            )
        except Exception:
            # Fallback during bootstrap
            raise ValueError("WorkOS not configured")

        _workos_client = WorkOSClient(api_key=api_key, client_id=client_id)

    return _workos_client


async def get_workos_client_async() -> WorkOSClient:
    """Get WorkOS client (async version, preferred)."""
    global _workos_client

    if _workos_client is None:
        api_key, client_id, _ = await _load_workos_credentials()
        _workos_client = WorkOSClient(api_key=api_key, client_id=client_id)

    return _workos_client


def get_cookie_password() -> str:
    """Get WorkOS cookie password (cached).

    For sync contexts. Loads from database on first call.
    """
    global _cookie_password

    if _cookie_password is None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise ValueError(
                    "Cannot initialize cookie password from running event loop"
                )
            _, _, password = loop.run_until_complete(_load_workos_credentials())
        except Exception:
            raise ValueError("WorkOS not configured")

        _cookie_password = password

    return _cookie_password


async def get_cookie_password_async() -> str:
    """Get WorkOS cookie password (async version, preferred)."""
    global _cookie_password

    if _cookie_password is None:
        _, _, password = await _load_workos_credentials()
        _cookie_password = password

    return _cookie_password

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from the session cookie.
    Supports both LOCAL mode (signed session) and WorkOS mode (sealed session).
    """
    from ..setup.local_auth import verify_local_session

    # Check app mode first
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        try:
            app_mode = await config_store.get_app_mode()
        except Exception:
            raise HTTPException(status_code=500, detail="Configuration not available")

    # LOCAL Mode: Use local_session cookie with signed token
    if app_mode == "local":
        session_data = request.cookies.get("local_session")
        if not session_data:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Get API key to verify signature
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            api_key = await config_store.get("local_omni_api_key")

        if not api_key:
            raise HTTPException(status_code=500, detail="Local auth not configured")

        payload = verify_local_session(session_data, api_key)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return {
            "id": payload.get("user_id"),
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "first_name": payload.get("first_name", "Local"),
            "last_name": payload.get("last_name", "User"),
            "workspace_id": payload.get("workspace_id"),
            "is_super_admin": payload.get("is_super_admin", False),
        }

    # WorkOS Mode: Use wos_session cookie with sealed encryption
    elif app_mode == "workos":
        cookie_password = get_cookie_password()
        session_data = request.cookies.get("wos_session")

        if not session_data:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            client = get_workos_client()
            wos_session = client.user_management.load_sealed_session(
                sealed_session=session_data,
                cookie_password=cookie_password,
            )

            auth_response = wos_session.authenticate()

            if not auth_response.authenticated:
                # Try to refresh
                refresh_result = wos_session.refresh()
                if not refresh_result.authenticated:
                    raise HTTPException(status_code=401, detail="Session expired")

                return refresh_result.user.to_dict()

            return auth_response.user.to_dict()

        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    # Unconfigured
    else:
        raise HTTPException(status_code=503, detail="Application not configured")

def get_auth_url(redirect_uri: str) -> str:
    """Generate AuthKit authorization URL."""
    client = get_workos_client()
    return client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=redirect_uri,
    )

async def authenticate_with_code(code: str) -> Dict[str, Any]:
    """Exchange code for session."""
    client = get_workos_client()
    cookie_password = get_cookie_password()
    
    response = client.user_management.authenticate_with_code(
        code=code,
        session={
            "seal_session": True,
            "cookie_password": cookie_password,
        }
    )
    
    return {
        "user": response.user.to_dict(),
        "sealed_session": response.sealed_session,
    }

async def get_logout_url(session_data: str) -> str:
    """Get logout URL."""
    client = get_workos_client()
    cookie_password = get_cookie_password()
    
    session = client.user_management.load_sealed_session(
        sealed_session=session_data,
        cookie_password=cookie_password,
    )
    
    return session.get_logout_url()
