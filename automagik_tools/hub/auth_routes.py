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

logger = logging.getLogger(__name__)

# Environment variables for WorkOS
WORKOS_API_KEY = os.getenv("WORKOS_API_KEY", "")
WORKOS_CLIENT_ID = os.getenv("WORKOS_CLIENT_ID", "")
WORKOS_REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8885/api/auth/callback")
WORKOS_BASE_URL = "https://api.workos.com"

router = APIRouter(prefix="/auth")
security = HTTPBearer(auto_error=False)


class AuthCallbackRequest(BaseModel):
    """Request model for auth callback."""
    code: str


@router.get("/authorize")
async def get_authorization_url() -> Dict[str, str]:
    """Get WorkOS AuthKit authorization URL.

    Returns a URL that the frontend redirects to for authentication.
    WorkOS handles the login UI, MFA, SSO, etc.
    """
    if not WORKOS_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="WorkOS not configured. Set WORKOS_CLIENT_ID environment variable."
        )

    # Build WorkOS authorization URL
    authorization_url = (
        f"{WORKOS_BASE_URL}/user_management/authorize"
        f"?client_id={WORKOS_CLIENT_ID}"
        f"&redirect_uri={WORKOS_REDIRECT_URI}"
        f"&response_type=code"
        f"&provider=authkit"  # Use AuthKit for universal login
    )

    logger.info(f"Generated authorization URL for redirect")
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
    if not WORKOS_API_KEY or not WORKOS_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="WorkOS not configured. Set WORKOS_API_KEY and WORKOS_CLIENT_ID."
        )

    # Get client IP for audit logging
    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    try:
        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKOS_BASE_URL}/user_management/authenticate",
                json={
                    "client_id": WORKOS_CLIENT_ID,
                    "client_secret": WORKOS_API_KEY,
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

    # In production, decode and verify the JWT token
    # For development, we can decode the token payload
    # The token is a JWT from WorkOS

    # TODO: Proper JWT verification with WorkOS JWKS
    # For now, we trust the token and use it to look up the user

    # This is a placeholder - in production use proper JWT verification
    # import jwt
    # payload = jwt.decode(credentials.credentials, options={"verify_signature": False})

    # For now, return a response that indicates authentication is working
    return {
        "authenticated": True,
        "message": "Token validation not implemented yet - configure JWT verification"
    }


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
