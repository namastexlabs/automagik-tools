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
            redirect_uri = "https://tools.genieos.namastex.io/api/auth/callback"
            return {
                "client_id": creds["client_id"],
                "api_key": creds["api_key"],
                "authkit_domain": creds["authkit_domain"],
                "redirect_uri": redirect_uri,
            }

        # No credentials in database - setup required
        raise HTTPException(
            status_code=500,
            detail="WorkOS not configured. Complete setup wizard at /setup"
        )


class AuthCallbackRequest(BaseModel):
    """Request model for auth callback."""
    code: str


@router.get("/authorize")
async def get_authorization_url() -> Dict[str, str]:
    """Get WorkOS AuthKit authorization URL.

    Returns a URL that the frontend redirects to for authentication.
    WorkOS handles the login UI, MFA, SSO, etc.
    """
    from workos import WorkOSClient

    config = await get_workos_config()

    # Create WorkOS client with credentials we already have (async-safe)
    client = WorkOSClient(api_key=config['api_key'], client_id=config['client_id'])

    # Use SDK to generate authorization URL (required for AuthKit)
    authorization_url = client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=config['redirect_uri'],
    )

    logger.info(f"Generated authorization URL with redirect_uri={config['redirect_uri']}")
    return {"authorization_url": authorization_url}


@router.get("/callback")
async def auth_callback(code: str, req: Request):
    """Handle OAuth callback and exchange code for session.

    This endpoint:
    1. Exchanges authorization code for sealed session
    2. Creates user in database if they don't exist
    3. Creates workspace for new users
    4. Sets HTTP-only session cookie (secure)
    5. Logs authentication event for audit

    Returns user data (session stored in HTTP-only cookie).
    """
    from .auth import get_workos_client, get_cookie_password
    from fastapi.responses import JSONResponse

    # Get client IP for audit logging
    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    try:
        # Get WorkOS client and cookie password
        workos_client = get_workos_client()
        cookie_password = get_cookie_password()

        # Exchange authorization code for sealed session using WorkOS SDK
        auth_response = workos_client.user_management.authenticate_with_code(
            code=code,
            session={
                "seal_session": True,
                "cookie_password": cookie_password,
            }
        )

        # Extract user info from WorkOS response
        workos_user = auth_response.user
        user_id = workos_user.id
        email = workos_user.email
        first_name = workos_user.first_name or ""
        last_name = workos_user.last_name or ""
        sealed_session = auth_response.sealed_session

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

        # Create response with user info (NO tokens in JSON - security best practice)
        response_data = {
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

        # Set HTTP-only session cookie (prevents XSS attacks)
        response = JSONResponse(response_data)
        response.set_cookie(
            key="wos_session",
            value=sealed_session,
            httponly=True,  # Cannot be accessed by JavaScript
            secure=req.url.scheme == "https",  # HTTPS only in production
            samesite="lax",  # CSRF protection
            max_age=3600 * 24 * 7,  # 7 days
        )

        return response

    except ValueError as e:
        # WorkOS not configured or cookie password missing
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Authentication error: {e}")

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


@router.post("/local-login")
async def local_login(req: Request) -> Dict[str, Any]:
    """Authenticate in Local Mode and set session cookie.

    This endpoint:
    1. Verifies app is in Local Mode
    2. Gets/creates local admin user
    3. Creates signed session token
    4. Sets HTTP-only session cookie
    5. Returns user info (same format as WorkOS callback)

    Only available when app is configured in Local Mode.
    """
    from fastapi.responses import JSONResponse
    from .setup.local_auth import LocalAuthManager, sign_local_session

    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    try:
        async with get_db_session() as session:
            config_store = ConfigStore(session)
            mode_manager = ModeManager(config_store)

            # Verify we're in Local Mode
            mode = await mode_manager.get_current_mode()
            if mode != AppMode.LOCAL:
                raise HTTPException(
                    status_code=403,
                    detail="Local login only available in Local Mode. Use WorkOS authentication."
                )

            # Get local admin user
            local_auth = LocalAuthManager(session, mode_manager)
            auth_session = await local_auth.authenticate_local()

            if not auth_session:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create local admin user"
                )

            # Get the user and workspace objects for full info
            user = await local_auth.get_or_create_local_admin()
            if not user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get local admin user"
                )

            # Get workspace
            from sqlalchemy import select
            from .models import Workspace
            workspace_result = await session.execute(
                select(Workspace).where(Workspace.id == user.workspace_id)
            )
            workspace = workspace_result.scalar_one_or_none()

            if not workspace:
                raise HTTPException(
                    status_code=500,
                    detail="Workspace not found for local admin"
                )

            # Get secret for signing (local_omni_api_key)
            api_key = await config_store.get("local_omni_api_key")
            if not api_key:
                # Generate a fallback secret if API key not set
                import secrets
                api_key = secrets.token_urlsafe(32)

            # Create session payload
            session_payload = {
                "user_id": user.id,
                "email": user.email,
                "workspace_id": workspace.id,
                "is_super_admin": user.is_super_admin,
                "mode": "local",
            }

            # Sign the session
            signed_session = sign_local_session(session_payload, api_key)

            # Log successful login
            await audit_logger.log_auth(
                action="auth.local_login_succeeded",
                user_id=user.id,
                email=user.email,
                workspace_id=workspace.id,
                success=True,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={"mode": "local"}
            )

            logger.info(f"[LocalAuth] User authenticated: {user.email} (workspace: {workspace.slug})")

            # Create response with user info
            response_data = {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "workspace_id": workspace.id,
                    "workspace_name": workspace.name,
                    "workspace_slug": workspace.slug,
                    "is_super_admin": user.is_super_admin,
                    "mfa_enabled": user.mfa_enabled,
                },
            }

            # Set HTTP-only session cookie
            response = JSONResponse(response_data)
            response.set_cookie(
                key="local_session",
                value=signed_session,
                httponly=True,  # Cannot be accessed by JavaScript
                secure=False,   # Local dev is typically HTTP
                samesite="strict",  # Maximum CSRF protection for local
                max_age=3600 * 24 * 30,  # 30 days for convenience
            )

            return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[LocalAuth] Login error: {e}")

        await audit_logger.log_auth(
            action="auth.local_login_failed",
            success=False,
            error_message=str(e),
            ip_address=client_ip,
            user_agent=user_agent,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Local authentication failed: {str(e)}"
        )


@router.get("/user")
async def get_user_info(req: Request) -> Dict[str, Any]:
    """Get current authenticated user info.

    Reads session from HTTP-only cookie (secure).
    Returns user details including workspace info and permissions.
    """
    from .auth import get_current_user as get_user_from_cookie

    try:
        # Get user from cookie-based dependency
        user_data = await get_user_from_cookie(req)

        return {
            "authenticated": True,
            "user": user_data
        }

    except HTTPException:
        # Re-raise HTTP exceptions (401, etc.)
        raise

    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.post("/logout")
async def logout(req: Request):
    """Log out the current user.

    This endpoint:
    1. Gets session ID from cookie
    2. Deletes session cookie
    3. Redirects to WorkOS logout URL (ends session at WorkOS)
    4. Logs logout event for audit

    WorkOS will redirect user to app homepage after logout.
    """
    from .auth import get_logout_url as get_workos_logout_url
    from fastapi.responses import RedirectResponse

    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    # Get session cookie
    session_data = req.cookies.get("wos_session")

    if session_data:
        try:
            # Get WorkOS logout URL
            logout_url = await get_workos_logout_url(session_data)

            # Log logout event
            await audit_logger.log_auth(
                action="auth.logout",
                success=True,
                ip_address=client_ip,
                user_agent=user_agent,
            )

            # Delete session cookie and redirect to WorkOS logout
            response = RedirectResponse(url=logout_url, status_code=302)
            response.delete_cookie("wos_session")
            return response

        except Exception as e:
            logger.error(f"Logout error: {e}")
            # Continue to fallback logout

    # Fallback: No session or error - just delete cookie
    await audit_logger.log_auth(
        action="auth.logout",
        success=True,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("wos_session")
    return response
