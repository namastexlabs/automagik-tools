"""Authentication routes for WorkOS AuthKit integration.

Handles:
- OAuth authorization URL generation
- Authorization code exchange for tokens
- User creation and workspace provisioning on first login
- Current user info retrieval
"""
import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx

from .authorization import get_or_create_user, is_super_admin
from .models import ProvisioningMethod
from .audit import audit_logger, AuditEventCategory
from .setup import ConfigStore, ModeManager, AppMode
from .database import get_db_session

logger = logging.getLogger(__name__)

# WorkOS API base URL (not a secret)
WORKOS_BASE_URL = "https://api.workos.com"

router = APIRouter(prefix="/auth")
security = HTTPBearer(auto_error=False)


async def get_workos_config() -> Dict[str, str]:
    """Get WorkOS configuration from database (or fallback to .env).

    Returns:
        Dict with client_id, api_key, authkit_domain, redirect_uri

    Raises:
        HTTPException: If WorkOS not configured
    """
    async with get_db_session() as session:
        config_store = ConfigStore(session)
        mode_manager = ModeManager(config_store)

        # Get from database
        creds = await mode_manager.get_workos_credentials()

        if creds:
            # Database has credentials
            redirect_uri = os.getenv(
                "WORKOS_REDIRECT_URI",
                "https://tools.genieos.namastex.io/api/auth/callback"
            )
            return {
                "client_id": creds["client_id"],
                "api_key": creds["api_key"],
                "authkit_domain": creds["authkit_domain"],
                "redirect_uri": redirect_uri,
            }

        # Fallback to .env (backwards compatibility)
        client_id = os.getenv("WORKOS_CLIENT_ID")
        api_key = os.getenv("WORKOS_API_KEY")

        if not client_id or not api_key:
            raise HTTPException(
                status_code=500,
                detail="WorkOS not configured. Complete setup wizard at /setup"
            )

        return {
            "client_id": client_id,
            "api_key": api_key,
            "authkit_domain": os.getenv(
                "WORKOS_AUTHKIT_DOMAIN",
                "https://veracious-shadow-68.authkit.app"
            ),
            "redirect_uri": os.getenv(
                "WORKOS_REDIRECT_URI",
                "https://tools.genieos.namastex.io/api/auth/callback"
            ),
        }


class AuthCallbackRequest(BaseModel):
    """Request model for auth callback."""
    code: str


@router.get("/authorize")
async def get_authorization_url() -> Dict[str, str]:
    """Get WorkOS AuthKit authorization URL.

    Returns a URL that the frontend redirects to for authentication.
    WorkOS handles the login UI, MFA, SSO, etc.
    """
    config = await get_workos_config()

    # Build WorkOS authorization URL - use AuthKit OAuth endpoint directly
    authorization_url = (
        f"{config['authkit_domain']}/oauth2/authorize"
        f"?client_id={config['client_id']}"
        f"&redirect_uri={config['redirect_uri']}"
        f"&response_type=code"
    )

    logger.info(f"Generated authorization URL with redirect_uri={config['redirect_uri']}")
    return {"authorization_url": authorization_url}


@router.post("/callback")
async def auth_callback(request: AuthCallbackRequest, req: Request) -> Dict[str, Any]:
    """Handle OAuth callback and exchange code for token.

    This endpoint:
    1. Exchanges authorization code for access token
    2. Creates user in database if they don't exist
    3. Creates workspace for new users
    4. Logs authentication event for audit
    """
    config = await get_workos_config()

    # Get client IP for audit logging
    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    try:
        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKOS_BASE_URL}/user_management/authenticate",
                json={
                    "client_id": config["client_id"],
                    "client_secret": config["api_key"],
                    "grant_type": "authorization_code",
                    "code": request.code,
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"WorkOS authentication failed: {response.status_code} - {response.text}")

                # Log failed login attempt
                await audit_logger.log_auth(
                    action="auth.login_failed",
                    success=False,
                    error_message=f"WorkOS error: {response.status_code}",
                    ip_address=client_ip,
                    user_agent=user_agent,
                )

                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WorkOS authentication failed: {response.text}"
                )

            auth_data = response.json()

        # Extract user info from WorkOS response
        workos_user = auth_data.get("user", {})
        user_id = workos_user.get("id")
        email = workos_user.get("email")
        first_name = workos_user.get("first_name")
        last_name = workos_user.get("last_name")

        if not user_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Invalid user data from WorkOS"
            )

        # Create or update user in database with workspace
        user, workspace = await get_or_create_user(
            workos_user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            provisioned_via=ProvisioningMethod.MANUAL,
        )

        # Log successful login
        await audit_logger.log_auth(
            action="auth.login_succeeded",
            user_id=user.id,
            email=email,
            workspace_id=workspace.id,
            success=True,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={
                "workos_user_id": user_id,
                "first_login": user.created_at == user.updated_at,
            }
        )

        logger.info(f"User authenticated: {email} (workspace: {workspace.slug})")

        # Return access token and enriched user info
        return {
            "access_token": auth_data.get("access_token"),
            "refresh_token": auth_data.get("refresh_token"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "workspace_id": workspace.id,
                "workspace_name": workspace.name,
                "workspace_slug": workspace.slug,
                "is_super_admin": user.is_super_admin or is_super_admin(email),
                "mfa_enabled": user.mfa_enabled,
            },
        }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during WorkOS authentication: {e}")

        await audit_logger.log_auth(
            action="auth.login_failed",
            success=False,
            error_message=str(e),
            ip_address=client_ip,
            user_agent=user_agent,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to authenticate with WorkOS: {str(e)}"
        )


@router.get("/user")
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    Returns user details including workspace info and permissions.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    token = credentials.credentials
    config = await get_workos_config()

    try:
        # Verify token via WorkOS userinfo endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config['authkit_domain']}/oauth2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )

            user_data = response.json()

            # Get user from database
            from .database import get_db_session
            from sqlalchemy import select
            from .models import User

            async with get_db_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_data.get("sub"))
                )
                user = result.scalar_one_or_none()

                if not user:
                    raise HTTPException(
                        status_code=404,
                        detail="User not found in database"
                    )

                return {
                    "authenticated": True,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "workspace_id": user.workspace_id,
                        "is_super_admin": user.is_super_admin,
                        "mfa_enabled": user.mfa_enabled,
                    }
                }

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify token: {str(e)}"
        )


@router.post("/logout")
async def logout(
    req: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, str]:
    """Log out the current user.

    Logs the logout event for audit purposes.
    The frontend should also clear the stored token.
    """
    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    # Log logout event
    # Note: Without proper JWT verification, we can't get user details
    await audit_logger.log_auth(
        action="auth.logout",
        success=True,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return {"message": "Logged out successfully"}
