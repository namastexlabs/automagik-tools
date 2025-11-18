"""
Authentication requirement detection for MCP endpoints.

Inspired by FastMCP's check_if_auth_required function. Provides utilities
to detect if an endpoint requires authentication before making requests.
"""

from typing import Optional, Dict, Any
import asyncio
import httpx
import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)


async def check_if_auth_required(
    mcp_url: str, timeout: float = 5.0, httpx_kwargs: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check if MCP endpoint requires authentication by making a test request.

    Inspired by FastMCP's check_if_auth_required function. Sends a test request
    to the endpoint and analyzes the response to determine if authentication
    is needed.

    Args:
        mcp_url: The MCP server URL to check
        timeout: Request timeout in seconds (default: 5.0)
        httpx_kwargs: Additional httpx client arguments

    Returns:
        True if auth appears to be required, False otherwise

    Example:
        >>> await check_if_auth_required("http://localhost:8000/mcp")
        True  # 401 Unauthorized received

        >>> await check_if_auth_required("http://localhost:8000/public")
        False  # 200 OK received
    """
    httpx_kwargs = httpx_kwargs or {}

    try:
        async with httpx.AsyncClient(**httpx_kwargs) as client:
            # Try a simple GET request to the MCP endpoint
            response = await client.get(
                mcp_url, timeout=timeout, follow_redirects=False
            )

            # Check status code for auth requirements
            if response.status_code == 401:
                logger.debug(f"Auth required for {mcp_url}: 401 Unauthorized")
                return True

            if response.status_code == 403:
                logger.debug(f"Auth required for {mcp_url}: 403 Forbidden")
                return True

            # Check for WWW-Authenticate header (indicates auth required)
            if "www-authenticate" in [h.lower() for h in response.headers.keys()]:
                logger.debug(
                    f"Auth required for {mcp_url}: WWW-Authenticate header present"
                )
                return True

            # Check for Proxy-Authenticate header
            if "proxy-authenticate" in [h.lower() for h in response.headers.keys()]:
                logger.debug(
                    f"Auth required for {mcp_url}: Proxy-Authenticate header present"
                )
                return True

            # Successful response, no auth needed
            logger.debug(f"No auth required for {mcp_url}: {response.status_code}")
            return False

    except httpx.TimeoutException:
        logger.warning(f"Timeout checking auth requirement for {mcp_url}")
        # Assume auth not required if server doesn't respond
        # (better to allow attempt than block)
        return False

    except httpx.ConnectError as e:
        logger.warning(f"Connection error checking auth for {mcp_url}: {e}")
        # Cannot determine, assume not required
        return False

    except Exception as e:
        logger.warning(f"Error checking auth requirement for {mcp_url}: {e}")
        # On error, assume auth not required to allow attempt
        return False


def check_if_auth_required_sync(
    mcp_url: str, timeout: float = 5.0, httpx_kwargs: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Synchronous version of check_if_auth_required.

    Args:
        mcp_url: The MCP server URL to check
        timeout: Request timeout in seconds
        httpx_kwargs: Additional httpx client arguments

    Returns:
        True if auth appears to be required, False otherwise
    """
    httpx_kwargs = httpx_kwargs or {}

    try:
        with httpx.Client(**httpx_kwargs) as client:
            response = client.get(mcp_url, timeout=timeout, follow_redirects=False)

            if response.status_code in [401, 403]:
                logger.debug(f"Auth required for {mcp_url}: {response.status_code}")
                return True

            if "www-authenticate" in [h.lower() for h in response.headers.keys()]:
                logger.debug(
                    f"Auth required for {mcp_url}: WWW-Authenticate header present"
                )
                return True

            logger.debug(f"No auth required for {mcp_url}: {response.status_code}")
            return False

    except httpx.TimeoutException:
        logger.warning(f"Timeout checking auth requirement for {mcp_url}")
        return False

    except httpx.ConnectError as e:
        logger.warning(f"Connection error checking auth for {mcp_url}: {e}")
        return False

    except Exception as e:
        logger.warning(f"Error checking auth requirement for {mcp_url}: {e}")
        return False


def require_auth_if_needed(auth_url: str, check_timeout: float = 5.0):
    """
    Decorator to conditionally require authentication based on endpoint check.

    Checks if the endpoint requires authentication before executing the function.
    If auth is required but not available, raises an appropriate error.

    Args:
        auth_url: URL to check for auth requirements
        check_timeout: Timeout for auth check request

    Example:
        @require_auth_if_needed("http://localhost:8000/mcp")
        async def my_tool_function(user_email: str):
            # Will automatically check if auth is needed
            # and prompt user if required
            return await do_something()

    Raises:
        ValueError: If auth required but user_email not provided
        GoogleAuthenticationError: If auth required but credentials invalid
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check if auth required
            auth_needed = await check_if_auth_required(auth_url, check_timeout)

            if auth_needed:
                # Extract user email from args/kwargs
                from .retry_handler import _extract_user_email

                user_email = _extract_user_email(args, kwargs)

                if not user_email:
                    raise ValueError(
                        f"Authentication required for {auth_url}, but no user_email provided"
                    )

                # Check if we have valid credentials
                from .token_storage_adapter import get_token_storage_adapter

                adapter = get_token_storage_adapter()

                if not adapter.has_valid_tokens(user_email):
                    # Prompt for authentication
                    from .error_messages import AuthErrorMessages

                    guidance = AuthErrorMessages.token_expired(
                        user_email, "MCP Service"
                    )

                    from .google_auth import GoogleAuthenticationError

                    raise GoogleAuthenticationError(guidance.format())

                logger.debug(f"Auth required and valid tokens found for {user_email}")

            # Proceed with function
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check if auth required (sync version)
            auth_needed = check_if_auth_required_sync(auth_url, check_timeout)

            if auth_needed:
                from .retry_handler import _extract_user_email

                user_email = _extract_user_email(args, kwargs)

                if not user_email:
                    raise ValueError(
                        f"Authentication required for {auth_url}, but no user_email provided"
                    )

                from .token_storage_adapter import get_token_storage_adapter

                adapter = get_token_storage_adapter()

                if not adapter.has_valid_tokens(user_email):
                    from .error_messages import AuthErrorMessages

                    guidance = AuthErrorMessages.token_expired(
                        user_email, "MCP Service"
                    )

                    from .google_auth import GoogleAuthenticationError

                    raise GoogleAuthenticationError(guidance.format())

                logger.debug(f"Auth required and valid tokens found for {user_email}")

            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def check_multiple_endpoints(
    endpoints: Dict[str, str], timeout: float = 5.0
) -> Dict[str, bool]:
    """
    Check multiple endpoints for auth requirements in parallel.

    Args:
        endpoints: Dict mapping endpoint names to URLs
        timeout: Timeout for each request (per endpoint)

    Returns:
        Dict mapping endpoint names to auth requirement (True/False)

    Example:
        >>> results = await check_multiple_endpoints({
        ...     "gmail": "http://localhost:8000/gmail",
        ...     "drive": "http://localhost:8000/drive",
        ...     "calendar": "http://localhost:8000/calendar"
        ... })
        >>> print(results)
        {'gmail': True, 'drive': True, 'calendar': False}

    Note:
        All endpoints are checked concurrently using asyncio.gather(),
        so total execution time is roughly one timeout period rather than
        timeout * number of endpoints.
    """

    async def check_with_error_handling(name: str, url: str) -> tuple[str, bool]:
        """Check a single endpoint and return (name, result) tuple."""
        try:
            result = await check_if_auth_required(url, timeout)
            return (name, result)
        except Exception as e:
            logger.error(f"Error checking {name}: {e}")
            return (name, False)

    # Create tasks for all endpoints and run them concurrently
    tasks = [check_with_error_handling(name, url) for name, url in endpoints.items()]

    # Run all checks in parallel
    endpoint_results = await asyncio.gather(*tasks)

    # Convert list of tuples to dict
    return dict(endpoint_results)


def validate_bearer_token(token: str) -> bool:
    """
    Validate Bearer token format.

    Args:
        token: Token to validate (with or without "Bearer " prefix)

    Returns:
        True if token format is valid, False otherwise
    """
    if not token:
        return False

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    # Basic validation
    # - Must be non-empty
    # - Must not contain spaces
    # - Should be reasonable length (between 20 and 2048 characters)
    if not token:
        return False

    if " " in token:
        return False

    if len(token) < 20 or len(token) > 2048:
        return False

    return True


def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Extracted token (without "Bearer " prefix), or None if invalid

    Example:
        >>> extract_bearer_token("Bearer abc123")
        'abc123'

        >>> extract_bearer_token("abc123")
        'abc123'

        >>> extract_bearer_token("Basic xyz")
        None
    """
    if not auth_header:
        return None

    # Check for Bearer scheme
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        if validate_bearer_token(token):
            return token

        return None

    # Try as raw token (no "Bearer " prefix)
    if validate_bearer_token(auth_header):
        return auth_header

    # Not a valid Bearer token
    return None


class AuthCheckCache:
    """
    Cache for auth requirement checks to avoid repeated requests.

    Caches results for a configurable TTL to improve performance.
    """

    def __init__(self, ttl_seconds: float = 300.0):
        """
        Initialize auth check cache.

        Args:
            ttl_seconds: How long to cache results (default: 5 minutes)
        """
        from datetime import datetime

        self._cache: Dict[str, tuple[bool, datetime]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def get(self, url: str) -> Optional[bool]:
        """
        Get cached result for URL.

        Args:
            url: URL to check

        Returns:
            Cached result if valid, None if expired/not found
        """
        from datetime import datetime, timedelta

        with self._lock:
            if url not in self._cache:
                return None

            result, cached_at = self._cache[url]

            # Check if expired
            if datetime.utcnow() - cached_at > timedelta(seconds=self._ttl):
                del self._cache[url]
                return None

            return result

    def set(self, url: str, auth_required: bool) -> None:
        """
        Cache auth check result.

        Args:
            url: URL that was checked
            auth_required: Whether auth is required
        """
        from datetime import datetime

        with self._lock:
            self._cache[url] = (auth_required, datetime.utcnow())

    def clear(self, url: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            url: Specific URL to clear, or None to clear all
        """
        with self._lock:
            if url:
                self._cache.pop(url, None)
            else:
                self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {"cached_urls": len(self._cache), "ttl_seconds": self._ttl}


# Global auth check cache
_auth_check_cache = AuthCheckCache()


def get_auth_check_cache() -> AuthCheckCache:
    """Get the global auth check cache"""
    return _auth_check_cache
