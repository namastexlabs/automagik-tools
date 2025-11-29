"""Authentication configuration using AuthKit (WorkOS)."""
import os
import asyncio
from typing import Optional, Dict, Any
import workos
from workos import WorkOSClient
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastmcp import Context

# Initialize WorkOS client
def get_workos_client() -> WorkOSClient:
    """Get WorkOS client (from database or .env fallback).

    This is synchronous but needs to check async database.
    Uses asyncio.run() to bridge sync/async gap.
    """
    from .setup import ConfigStore, ModeManager
    from .database import get_db_session

    async def _get_credentials():
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            mode_manager = ModeManager(config_store)
            creds = await mode_manager.get_workos_credentials()

            if creds:
                return creds["api_key"], creds["client_id"]

            # No credentials in database
            return None, None

    # Run async function in sync context
    try:
        api_key, client_id = asyncio.get_running_loop().run_until_complete(_get_credentials())
    except RuntimeError:
        # No event loop running, create one
        api_key, client_id = asyncio.run(_get_credentials())

    if not api_key or not client_id:
        raise ValueError("WorkOS not configured. Complete setup wizard at /setup")

    return WorkOSClient(api_key=api_key, client_id=client_id)

def get_cookie_password() -> str:
    """Get WorkOS cookie password from database.

    Cookie password is stored in the database (encrypted) during setup wizard.
    """
    from .setup import ConfigStore
    from .database import get_db_session

    async def _get_password():
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            return await config_store.get_or_generate_cookie_password()

    # Run async function in sync context
    try:
        password = asyncio.get_running_loop().run_until_complete(_get_password())
    except RuntimeError:
        # No event loop running, create one
        password = asyncio.run(_get_password())

    if not password:
        raise ValueError("WorkOS cookie password not configured. Complete setup wizard at /setup")
    return password

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from session cookie.

    Supports both WorkOS mode (wos_session cookie) and Local Mode (local_session cookie).
    """
    # Try WorkOS session first
    wos_session_data = request.cookies.get("wos_session")
    if wos_session_data:
        return await _validate_workos_session(wos_session_data)

    # Try Local Mode session
    local_session_data = request.cookies.get("local_session")
    if local_session_data:
        return await _validate_local_session(local_session_data)

    # No valid session found
    raise HTTPException(status_code=401, detail="Not authenticated")


async def _validate_workos_session(session_data: str) -> Dict[str, Any]:
    """Validate WorkOS session cookie and return user data."""
    try:
        cookie_password = get_cookie_password()
        client = get_workos_client()
        session = client.user_management.load_sealed_session(
            sealed_session=session_data,
            cookie_password=cookie_password,
        )

        auth_response = session.authenticate()

        if not auth_response.authenticated:
            # Try to refresh
            refresh_result = session.refresh()
            if not refresh_result.authenticated:
                raise HTTPException(status_code=401, detail="Session expired")

            # Note: In a real FastAPI dependency, we can't easily set the cookie on the response here
            # The middleware or endpoint needs to handle the refresh and cookie setting
            # For now, we assume the session is valid or return 401
            return refresh_result.user.to_dict()

        return auth_response.user.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"WorkOS authentication failed: {str(e)}")


async def _validate_local_session(session_data: str) -> Dict[str, Any]:
    """Validate Local Mode session cookie and return user data."""
    from .setup.local_auth import verify_local_session
    from .setup import ConfigStore
    from .database import get_db_session

    try:
        # Get the signing secret
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            api_key = await config_store.get("local_omni_api_key")

            if not api_key:
                raise HTTPException(status_code=401, detail="Local Mode not configured")

            # Verify the session token
            payload = verify_local_session(session_data, api_key)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid or expired local session")

            # Return user data in same format as WorkOS
            return {
                "id": payload.get("user_id"),
                "user_id": payload.get("user_id"),  # Include both for compatibility
                "email": payload.get("email"),
                "workspace_id": payload.get("workspace_id"),
                "is_super_admin": payload.get("is_super_admin", True),
                "mode": "local",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Local authentication failed: {str(e)}")

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
