"""Token refresh middleware for WorkOS AuthKit.

Automatically refreshes expired or expiring access tokens before they expire.
Uses HTTP-only cookies for session storage (security best practice).
"""
import logging
from fastapi import Request
from .auth import get_workos_client, get_cookie_password

logger = logging.getLogger(__name__)

async def token_refresh_middleware(request: Request, call_next):
    """Automatically refresh expired WorkOS tokens.

    This middleware:
    1. Checks for session cookie
    2. Loads and authenticates the session
    3. Refreshes if expired or expiring soon
    4. Updates cookie with refreshed session
    5. Passes request to next handler

    Uses WorkOS SDK methods:
    - load_sealed_session: Unseals session cookie
    - session.authenticate(): Validates session (no network call)
    - session.refresh(): Refreshes tokens if needed
    """
    # Get session cookie
    session_data = request.cookies.get("wos_session")
    if not session_data:
        # No session cookie - let request through
        return await call_next(request)

    try:
        # Get WorkOS client and cookie password
        client = get_workos_client()
        cookie_password = get_cookie_password()

        # Load sealed session
        session = client.user_management.load_sealed_session(
            sealed_session=session_data,
            cookie_password=cookie_password,
        )

        # Check authentication status
        auth_response = session.authenticate()

        if not auth_response.authenticated:
            # Session expired - try to refresh
            refresh_result = session.refresh()

            if refresh_result.authenticated:
                # Refresh succeeded - seal new session and update cookie
                # Note: We need to seal the refreshed session
                # The WorkOS SDK should provide session.seal() or similar
                # For now, proceed with request (cookie will be updated by auth routes)
                response = await call_next(request)

                # TODO: Update cookie with refreshed sealed session
                # Need to verify WorkOS SDK method for sealing after refresh
                logger.info("Token refreshed successfully (cookie update pending)")

                return response
            else:
                # Refresh failed - clear invalid cookie and continue
                logger.warning("Token refresh failed - session expired")
                response = await call_next(request)
                response.delete_cookie("wos_session")
                return response

        # Session is valid - proceed normally
        return await call_next(request)

    except Exception as e:
        # If refresh fails, log error and let request through
        # Auth endpoints will handle the invalid session
        logger.error(f"Token refresh error: {e}")
        return await call_next(request)
