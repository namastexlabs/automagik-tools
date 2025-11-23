"""Authentication configuration using AuthKit (WorkOS)."""
import os
from typing import Optional, Dict, Any
import workos
from workos import WorkOSClient
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastmcp import Context

# Initialize WorkOS client
def get_workos_client() -> WorkOSClient:
    api_key = os.getenv("WORKOS_API_KEY")
    client_id = os.getenv("WORKOS_CLIENT_ID")
    
    if not api_key or not client_id:
        raise ValueError("WORKOS_API_KEY and WORKOS_CLIENT_ID must be set")
        
    return WorkOSClient(api_key=api_key, client_id=client_id)

def get_cookie_password() -> str:
    password = os.getenv("WORKOS_COOKIE_PASSWORD")
    if not password:
        raise ValueError("WORKOS_COOKIE_PASSWORD must be set")
    return password

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from the session cookie.
    """
    cookie_password = get_cookie_password()
    session_data = request.cookies.get("wos_session")
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
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
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

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
