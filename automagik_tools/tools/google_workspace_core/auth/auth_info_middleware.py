"""
Authentication middleware to populate context state with user information
"""

import jwt
import logging
import os
import time
from types import SimpleNamespace
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers

from automagik_tools.tools.google_workspace_core.auth.oauth21_session_store import (
    ensure_session_from_access_token,
)

# Configure logging
logger = logging.getLogger(__name__)


class AuthInfoMiddleware(Middleware):
    """
    Middleware to extract authentication information from JWT tokens
    and populate the FastMCP context state for use in tools and prompts.
    """

    def __init__(self):
        super().__init__()
        self.auth_provider_type = "GoogleProvider"

    def _store_unverified_google_token(self, context: MiddlewareContext, token_str: str):
        """Persist minimal state for an unverified Google access token."""

        access_token = SimpleNamespace(
            token=token_str,
            client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", "google"),
            scopes=[],
            session_id=f"google_oauth_{token_str[:8]}",
            expires_at=int(time.time()) + 3600,
            sub="unknown",
            email="",
        )
        context.fastmcp_context.set_state("access_token", access_token)
        context.fastmcp_context.set_state("auth_provider_type", self.auth_provider_type)
        context.fastmcp_context.set_state("token_type", "google_oauth")

    def _decode_verified_claims(self, token_str: str):
        try:
            return jwt.decode(token_str, options={"verify_signature": False})
        except jwt.DecodeError as exc:
            logger.error(f"Failed to decode verified JWT payload: {exc}")
        except Exception as exc:
            logger.error(f"Error decoding verified JWT payload: {exc}")
        return {}

    def _store_verified_token(
        self,
        context: MiddlewareContext,
        token_str: str,
        verified_auth,
        token_type: str,
    ):
        """Populate FastMCP state from a verified token."""

        claims = {}
        if hasattr(verified_auth, "claims") and isinstance(verified_auth.claims, dict):
            claims = dict(verified_auth.claims)
        elif token_type != "google_oauth":
            claims = self._decode_verified_claims(token_str)

        user_email = claims.get("email") or getattr(verified_auth, "email", None)
        if not user_email:
            logger.warning("Verified token missing email claim; skipping authentication state")
            return

        client_id = (
            getattr(verified_auth, "client_id", None)
            or claims.get("aud")
            or claims.get("client_id")
            or os.getenv("GOOGLE_OAUTH_CLIENT_ID", "google")
        )

        scope_claim = claims.get("scope") if isinstance(claims, dict) else None
        scopes = getattr(verified_auth, "scopes", None)
        if not scopes and scope_claim:
            if isinstance(scope_claim, str):
                scopes = scope_claim.split()
            elif isinstance(scope_claim, (list, tuple, set)):
                scopes = list(scope_claim)
        if not scopes:
            scopes = []

        expires_at = (
            getattr(verified_auth, "expires_at", None)
            or claims.get("exp")
            or (int(time.time()) + 3600)
        )

        session_id = (
            getattr(verified_auth, "session_id", None)
            or claims.get("sid")
            or claims.get("jti")
            or claims.get("session_id")
            or f"{token_type}_{token_str[:8]}"
        )

        sub_claim = claims.get("sub") if isinstance(claims, dict) else None

        access_token = SimpleNamespace(
            token=token_str,
            client_id=client_id,
            scopes=scopes,
            session_id=session_id,
            expires_at=expires_at,
            sub=sub_claim or getattr(verified_auth, "sub", None) or user_email,
            email=user_email,
        )

        context.fastmcp_context.set_state("access_token", access_token)
        mcp_session_id = getattr(context.fastmcp_context, "session_id", None)
        ensure_session_from_access_token(verified_auth, user_email, mcp_session_id)
        context.fastmcp_context.set_state("access_token_obj", verified_auth)
        context.fastmcp_context.set_state("auth_provider_type", self.auth_provider_type)
        context.fastmcp_context.set_state("token_type", token_type)
        context.fastmcp_context.set_state("user_email", user_email)
        context.fastmcp_context.set_state(
            "username", claims.get("username") or user_email
        )

        if claims:
            context.fastmcp_context.set_state("user_id", claims.get("sub"))
            context.fastmcp_context.set_state("name", claims.get("name"))
            context.fastmcp_context.set_state("auth_time", claims.get("auth_time"))
            context.fastmcp_context.set_state("issuer", claims.get("iss"))
            context.fastmcp_context.set_state(
                "audience", claims.get("aud") or claims.get("client_id")
            )
            context.fastmcp_context.set_state("jti", claims.get("jti"))

        context.fastmcp_context.set_state("authenticated_user_email", user_email)
        context.fastmcp_context.set_state(
            "authenticated_via",
            "bearer_token" if token_type == "google_oauth" else "jwt_token",
        )

        logger.info(f"Authenticated via {token_type}: {user_email}")

    async def _process_request_for_auth(self, context: MiddlewareContext):
        """Helper to extract, verify, and store auth info from a request."""
        if not context.fastmcp_context:
            logger.warning("No fastmcp_context available")
            return

        # Return early if authentication state is already set
        if context.fastmcp_context.get_state("authenticated_user_email"):
            logger.info("Authentication state already set.")
            return

        # Try to get the HTTP request to extract Authorization header
        try:
            # Use the new FastMCP method to get HTTP headers
            headers = get_http_headers()
            if headers:
                logger.debug("Processing HTTP headers for authentication")

                # Get the Authorization header
                auth_header = headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    token_str = auth_header[7:]  # Remove "Bearer " prefix
                    logger.debug("Found Bearer token")

                    token_is_google = token_str.startswith("ya29.")
                    token_type = "google_oauth" if token_is_google else "jwt_token"

                    if token_is_google:
                        logger.debug("Detected Google OAuth access token format")

                    from ..core.server import get_auth_provider

                    auth_provider = get_auth_provider()
                    verified_auth = None

                    if auth_provider:
                        try:
                            verified_auth = await auth_provider.verify_token(token_str)
                        except Exception as e:
                            logger.error(f"Error verifying bearer token: {e}")
                    else:
                        logger.warning(
                            "No auth provider available to verify bearer tokens"
                        )

                    if verified_auth:
                        self._store_verified_token(
                            context, token_str, verified_auth, token_type
                        )
                    elif token_is_google:
                        logger.warning(
                            "Storing unverified Google access token; authentication not granted"
                        )
                        self._store_unverified_google_token(context, token_str)
                    else:
                        logger.warning(
                            "Rejected JWT bearer token because verification failed"
                        )
                else:
                    logger.debug("No Bearer token in Authorization header")
            else:
                logger.debug(
                    "No HTTP headers available (might be using stdio transport)"
                )
        except Exception as e:
            logger.debug(f"Could not get HTTP request: {e}")

        # After trying HTTP headers, check for other authentication methods
        # This consolidates all authentication logic in the middleware
        if not context.fastmcp_context.get_state("authenticated_user_email"):
            logger.debug(
                "No authentication found via bearer token, checking other methods"
            )

            # Check transport mode
            from ..core.config import get_transport_mode

            transport_mode = get_transport_mode()

            if transport_mode == "stdio":
                # In stdio mode, check if there's a session with credentials
                # This is ONLY safe in stdio mode because it's single-user
                logger.debug("Checking for stdio mode authentication")

                # Get the requested user from the context if available
                requested_user = None
                if hasattr(context, "request") and hasattr(context.request, "params"):
                    requested_user = context.request.params.get("user_google_email")
                elif hasattr(context, "arguments"):
                    # FastMCP may store arguments differently
                    requested_user = context.arguments.get("user_google_email")

                if requested_user:
                    try:
                        from .oauth21_session_store import get_oauth21_session_store

                        store = get_oauth21_session_store()

                        # Check if user has a recent session
                        if store.has_session(requested_user):
                            logger.debug(
                                f"Using recent stdio session for {requested_user}"
                            )
                            # In stdio mode, we can trust the user has authenticated recently
                            context.fastmcp_context.set_state(
                                "authenticated_user_email", requested_user
                            )
                            context.fastmcp_context.set_state(
                                "authenticated_via", "stdio_session"
                            )
                            context.fastmcp_context.set_state(
                                "auth_provider_type", "oauth21_stdio"
                            )
                    except Exception as e:
                        logger.debug(f"Error checking stdio session: {e}")

                # If no requested user was provided but exactly one session exists, assume it in stdio mode
                if not context.fastmcp_context.get_state("authenticated_user_email"):
                    try:
                        from .oauth21_session_store import get_oauth21_session_store

                        store = get_oauth21_session_store()
                        single_user = store.get_single_user_email()
                        if single_user:
                            logger.debug(
                                f"Defaulting to single stdio OAuth session for {single_user}"
                            )
                            context.fastmcp_context.set_state(
                                "authenticated_user_email", single_user
                            )
                            context.fastmcp_context.set_state(
                                "authenticated_via", "stdio_single_session"
                            )
                            context.fastmcp_context.set_state(
                                "auth_provider_type", "oauth21_stdio"
                            )
                            context.fastmcp_context.set_state("user_email", single_user)
                            context.fastmcp_context.set_state("username", single_user)
                    except Exception as e:
                        logger.debug(
                            f"Error determining stdio single-user session: {e}"
                        )

            # Check for MCP session binding
            if not context.fastmcp_context.get_state(
                "authenticated_user_email"
            ) and hasattr(context.fastmcp_context, "session_id"):
                mcp_session_id = context.fastmcp_context.session_id
                if mcp_session_id:
                    try:
                        from .oauth21_session_store import get_oauth21_session_store

                        store = get_oauth21_session_store()

                        # Check if this MCP session is bound to a user
                        bound_user = store.get_user_by_mcp_session(mcp_session_id)
                        if bound_user:
                            logger.debug(f"MCP session bound to {bound_user}")
                            context.fastmcp_context.set_state(
                                "authenticated_user_email", bound_user
                            )
                            context.fastmcp_context.set_state(
                                "authenticated_via", "mcp_session_binding"
                            )
                            context.fastmcp_context.set_state(
                                "auth_provider_type", "oauth21_session"
                            )
                    except Exception as e:
                        logger.debug(f"Error checking MCP session binding: {e}")

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Extract auth info from token and set in context state"""
        logger.debug("Processing tool call authentication")

        try:
            await self._process_request_for_auth(context)

            logger.debug("Passing to next handler")
            result = await call_next(context)
            logger.debug("Handler completed")
            return result

        except Exception as e:
            # Check if this is an authentication error - don't log traceback for these
            if "GoogleAuthenticationError" in str(
                type(e)
            ) or "Access denied: Cannot retrieve credentials" in str(e):
                logger.info(f"Authentication check failed: {e}")
            else:
                logger.error(f"Error in on_call_tool middleware: {e}", exc_info=True)
            raise

    async def on_get_prompt(self, context: MiddlewareContext, call_next):
        """Extract auth info for prompt requests too"""
        logger.debug("Processing prompt authentication")

        try:
            await self._process_request_for_auth(context)

            logger.debug("Passing prompt to next handler")
            result = await call_next(context)
            logger.debug("Prompt handler completed")
            return result

        except Exception as e:
            # Check if this is an authentication error - don't log traceback for these
            if "GoogleAuthenticationError" in str(
                type(e)
            ) or "Access denied: Cannot retrieve credentials" in str(e):
                logger.info(f"Authentication check failed in prompt: {e}")
            else:
                logger.error(f"Error in on_get_prompt middleware: {e}", exc_info=True)
            raise
