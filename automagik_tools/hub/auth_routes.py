"""Authentication routes for WorkOS AuthKit integration."""
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx


# Environment variables for WorkOS
WORKOS_API_KEY = os.getenv("WORKOS_API_KEY", "")
WORKOS_CLIENT_ID = os.getenv("WORKOS_CLIENT_ID", "")
WORKOS_REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8884/api/auth/callback")
WORKOS_BASE_URL = "https://api.workos.com"


router = APIRouter(prefix="/auth")


class AuthCallbackRequest(BaseModel):
    """Request model for auth callback."""
    code: str


@router.get("/authorize")
async def get_authorization_url() -> Dict[str, str]:
    """Get WorkOS AuthKit authorization URL."""
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
    )

    return {"authorization_url": authorization_url}


@router.post("/callback")
async def auth_callback(request: AuthCallbackRequest) -> Dict[str, Any]:
    """Handle OAuth callback and exchange code for token."""
    if not WORKOS_API_KEY or not WORKOS_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="WorkOS not configured. Set WORKOS_API_KEY and WORKOS_CLIENT_ID."
        )

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
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WorkOS authentication failed: {response.text}"
                )

            auth_data = response.json()

            # Return access token and user info
            return {
                "access_token": auth_data.get("access_token"),
                "user": auth_data.get("user"),
                "refresh_token": auth_data.get("refresh_token"),
            }

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to authenticate with WorkOS: {str(e)}"
        )


@router.get("/user")
async def get_current_user() -> Dict[str, Any]:
    """Get current authenticated user info."""
    # TODO: Extract user from JWT token in Authorization header
    # For now, return mock data for development
    return {
        "id": "user_dev_001",
        "email": "dev@example.com",
        "first_name": "Developer",
        "last_name": "User"
    }
