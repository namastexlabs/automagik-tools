"""
Automatic retry handler for OAuth operations with stale credential detection.

Inspired by FastMCP's async_auth_flow with automatic retry on stale credentials.
Provides decorators and utilities for gracefully handling expired/revoked tokens.
"""

from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Optional, Any
import asyncio
import logging
from google.auth.exceptions import RefreshError

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


class StaleCredentialError(Exception):
    """
    Raised when credentials are stale and require reauthentication.

    This error is raised after all retry attempts have been exhausted
    and indicates that the user must manually reauthenticate.
    """

    def __init__(self, message: str, user_email: Optional[str] = None, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.user_email = user_email
        self.last_error = last_error


def _extract_user_email(args: tuple, kwargs: dict) -> Optional[str]:
    """
    Extract user email from function arguments.

    Checks both kwargs and positional args for user identification.
    """
    # Try kwargs first (most common)
    for key in ["user_email", "user_google_email", "email"]:
        if key in kwargs and kwargs[key]:
            return kwargs[key]

    # Try positional args (usually first argument)
    if args:
        # Check first arg
        if isinstance(args[0], str) and "@" in args[0]:
            return args[0]

        # Check second arg (sometimes service comes first)
        if len(args) > 1 and isinstance(args[1], str) and "@" in args[1]:
            return args[1]

    return None


async def _clear_user_credentials(user_email: str) -> None:
    """
    Clear cached credentials for a user (async version).

    This forces fresh authentication on the next attempt.
    """
    try:
        from .token_storage_adapter import get_token_storage_adapter

        adapter = get_token_storage_adapter()
        if adapter.clear_tokens(user_email):
            logger.info(f"Cleared cached credentials for {user_email}")
        else:
            logger.warning(f"No cached credentials found to clear for {user_email}")

    except Exception as e:
        logger.error(f"Error clearing credentials for {user_email}: {e}")


def _clear_user_credentials_sync(user_email: str) -> None:
    """
    Clear cached credentials for a user (sync version).

    This forces fresh authentication on the next attempt.
    """
    try:
        from .token_storage_adapter import get_token_storage_adapter

        adapter = get_token_storage_adapter()
        if adapter.clear_tokens(user_email):
            logger.info(f"Cleared cached credentials for {user_email}")
        else:
            logger.warning(f"No cached credentials found to clear for {user_email}")

    except Exception as e:
        logger.error(f"Error clearing credentials for {user_email}: {e}")


def _is_stale_credential_error(error: Exception) -> bool:
    """
    Check if error indicates stale/revoked credentials.

    Args:
        error: Exception to check

    Returns:
        True if error suggests credentials need refresh/reauthentication
    """
    if not isinstance(error, RefreshError):
        return False

    error_msg = str(error).lower()

    # Common indicators of stale credentials
    stale_indicators = [
        "invalid_grant",
        "token has been expired or revoked",
        "token expired",
        "refresh token is invalid",
        "authorization code has already been used",
        "invalid refresh token",
    ]

    return any(indicator in error_msg for indicator in stale_indicators)


def with_automatic_retry(max_retries: int = 1, clear_cache_on_fail: bool = True, backoff_base: float = 2.0):
    """
    Decorator that automatically retries OAuth operations on stale credentials.

    Inspired by FastMCP's async_auth_flow with retry logic. This decorator:
    1. Catches RefreshError exceptions
    2. Detects if error indicates stale credentials
    3. Optionally clears credential cache
    4. Retries with exponential backoff
    5. Raises StaleCredentialError if all retries exhausted

    Args:
        max_retries: Maximum number of retry attempts (default: 1)
        clear_cache_on_fail: Clear credential cache before retry (default: True)
        backoff_base: Base for exponential backoff calculation (default: 2.0)

    Example:
        @with_automatic_retry(max_retries=2, clear_cache_on_fail=True)
        async def get_gmail_service(user_email: str):
            # Will automatically retry if credentials are stale
            return await authenticate_and_build_service(user_email)

        # Usage
        try:
            service = await get_gmail_service("user@example.com")
        except StaleCredentialError as e:
            print(f"Please reauthenticate: {e}")
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Optional[Exception] = None
            user_email: Optional[str] = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except RefreshError as e:
                    last_error = e

                    # Check if error indicates stale credentials
                    if not _is_stale_credential_error(e):
                        # Non-stale error, raise immediately
                        logger.error(f"Non-stale RefreshError in {func.__name__}: {e}")
                        raise

                    # Extract user email for cache clearing
                    if user_email is None:
                        user_email = _extract_user_email(args, kwargs)

                    logger.warning(
                        f"Stale credentials detected in {func.__name__} "
                        f"(attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )

                    # Check if we have retries left
                    if attempt < max_retries:
                        # Clear cache if requested
                        if clear_cache_on_fail and user_email:
                            await _clear_user_credentials(user_email)
                            logger.info(f"Cleared cached credentials for {user_email}, retrying...")

                        # Exponential backoff
                        backoff_seconds = backoff_base**attempt
                        logger.debug(f"Waiting {backoff_seconds}s before retry...")
                        await asyncio.sleep(backoff_seconds)
                        continue

                    # No more retries, raise StaleCredentialError
                    break

                except Exception as e:
                    # Non-RefreshError, raise immediately
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise

            # All retries exhausted
            error_msg = (
                f"Failed after {max_retries + 1} attempts in {func.__name__}. "
                f"Please reauthenticate using start_google_auth."
            )

            if user_email:
                error_msg += f" User: {user_email}"

            if last_error:
                error_msg += f" Last error: {last_error}"

            raise StaleCredentialError(error_msg, user_email=user_email, last_error=last_error)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Synchronous version of retry wrapper"""
            last_error: Optional[Exception] = None
            user_email: Optional[str] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except RefreshError as e:
                    last_error = e

                    if not _is_stale_credential_error(e):
                        logger.error(f"Non-stale RefreshError in {func.__name__}: {e}")
                        raise

                    if user_email is None:
                        user_email = _extract_user_email(args, kwargs)

                    logger.warning(
                        f"Stale credentials detected in {func.__name__} "
                        f"(attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )

                    if attempt < max_retries:
                        if clear_cache_on_fail and user_email:
                            _clear_user_credentials_sync(user_email)
                            logger.info(f"Cleared cached credentials for {user_email}, retrying...")

                        import time

                        backoff_seconds = backoff_base**attempt
                        logger.debug(f"Waiting {backoff_seconds}s before retry...")
                        time.sleep(backoff_seconds)
                        continue

                    break

                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise

            # All retries exhausted
            error_msg = (
                f"Failed after {max_retries + 1} attempts in {func.__name__}. "
                f"Please reauthenticate using start_google_auth."
            )

            if user_email:
                error_msg += f" User: {user_email}"

            if last_error:
                error_msg += f" Last error: {last_error}"

            raise StaleCredentialError(error_msg, user_email=user_email, last_error=last_error)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def with_retry_context(user_email: str, max_retries: int = 1, clear_cache_on_fail: bool = True):
    """
    Context manager for retry logic without decorator.

    Useful for wrapping specific code blocks that need retry behavior.

    Example:
        async def my_function(user_email: str):
            async with with_retry_context(user_email, max_retries=2):
                # This code will be retried on stale credentials
                service = await build_service(user_email)
                return service.users().list()
    """

    class RetryContext:
        def __init__(self, user_email: str, max_retries: int, clear_cache: bool):
            self.user_email = user_email
            self.max_retries = max_retries
            self.clear_cache = clear_cache
            self.attempt = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                return False

            # Only handle RefreshError
            if not isinstance(exc_val, RefreshError):
                return False

            # Check if stale credentials
            if not _is_stale_credential_error(exc_val):
                return False

            # Check if we have retries left
            if self.attempt >= self.max_retries:
                # No more retries, raise StaleCredentialError
                raise StaleCredentialError(
                    f"Failed after {self.max_retries + 1} attempts. " f"Please reauthenticate.",
                    user_email=self.user_email,
                    last_error=exc_val,
                )

            # Clear cache and retry
            if self.clear_cache:
                await _clear_user_credentials(self.user_email)

            # Exponential backoff
            backoff_seconds = 2.0**self.attempt
            await asyncio.sleep(backoff_seconds)

            self.attempt += 1
            logger.info(f"Retrying after stale credential error (attempt {self.attempt + 1}/{self.max_retries + 1})")

            # Suppress exception to retry
            return True

    return RetryContext(user_email, max_retries, clear_cache_on_fail)


class RetryConfig:
    """
    Global retry configuration.

    Allows customizing retry behavior across the entire application.
    """

    def __init__(
        self,
        default_max_retries: int = 1,
        default_clear_cache: bool = True,
        default_backoff_base: float = 2.0,
        enabled: bool = True,
    ):
        self.default_max_retries = default_max_retries
        self.default_clear_cache = default_clear_cache
        self.default_backoff_base = default_backoff_base
        self.enabled = enabled

    def create_decorator(self, max_retries: Optional[int] = None, clear_cache_on_fail: Optional[bool] = None):
        """
        Create a retry decorator with configured defaults.

        Args:
            max_retries: Override default max retries
            clear_cache_on_fail: Override default cache clearing behavior

        Returns:
            Configured retry decorator
        """
        if not self.enabled:
            # Return no-op decorator if retries disabled
            def noop_decorator(func):
                return func

            return noop_decorator

        return with_automatic_retry(
            max_retries=max_retries if max_retries is not None else self.default_max_retries,
            clear_cache_on_fail=clear_cache_on_fail
            if clear_cache_on_fail is not None
            else self.default_clear_cache,
            backoff_base=self.default_backoff_base,
        )


# Global retry configuration
_global_retry_config = RetryConfig()


def get_retry_config() -> RetryConfig:
    """Get the global retry configuration"""
    return _global_retry_config


def configure_retry(
    default_max_retries: Optional[int] = None,
    default_clear_cache: Optional[bool] = None,
    default_backoff_base: Optional[float] = None,
    enabled: Optional[bool] = None,
):
    """
    Configure global retry behavior.

    Example:
        # Disable retries globally
        configure_retry(enabled=False)

        # Increase retry attempts
        configure_retry(default_max_retries=3)

        # Faster backoff
        configure_retry(default_backoff_base=1.5)
    """
    global _global_retry_config

    if default_max_retries is not None:
        _global_retry_config.default_max_retries = default_max_retries

    if default_clear_cache is not None:
        _global_retry_config.default_clear_cache = default_clear_cache

    if default_backoff_base is not None:
        _global_retry_config.default_backoff_base = default_backoff_base

    if enabled is not None:
        _global_retry_config.enabled = enabled

    logger.info(f"Updated global retry config: {_global_retry_config.__dict__}")
