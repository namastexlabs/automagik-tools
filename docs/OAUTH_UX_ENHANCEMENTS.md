# OAuth UX Enhancements Design Document

## Executive Summary

This document outlines comprehensive enhancements to the OAuth implementation in automagik-tools, inspired by FastMCP's OAuth patterns. The goal is to provide a seamless, secure, and user-friendly authentication experience.

## Current State Analysis

### Strengths
- ✅ Dual-mode OAuth (2.0 + 2.1) support
- ✅ Triple-storage pattern for reliability
- ✅ PKCE enforcement for security
- ✅ Thread-safe session management
- ✅ Multiple authentication paths

### Pain Points
- ❌ Complex token refresh without stored client secrets
- ❌ No automatic retry on stale credentials
- ❌ Session bindings lack expiry (potential memory leak)
- ❌ Duplicate implementations (google_workspace vs google_workspace_core)
- ❌ Inconsistent error messages
- ❌ No unified token storage interface

## Enhancement Strategy

### 1. Unified TokenStorageAdapter Pattern

**Objective**: Create a FastMCP-compatible token storage interface

**Implementation**:
```python
# File: automagik_tools/tools/google_workspace/auth/token_storage_adapter.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OAuthToken:
    """Standardized OAuth token structure"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scopes: Optional[list[str]] = None

@dataclass
class OAuthClientInfo:
    """OAuth client credentials"""
    client_id: str
    client_secret: str
    redirect_uris: list[str]
    auth_uri: str
    token_uri: str

class TokenStorageAdapter(ABC):
    """
    FastMCP-compatible token storage interface.

    Implements the adapter pattern to allow swappable storage backends
    while maintaining a consistent interface for OAuth operations.
    """

    @abstractmethod
    def get_tokens(self, user_id: str) -> Optional[OAuthToken]:
        """Retrieve tokens for a user"""
        pass

    @abstractmethod
    def set_tokens(self, user_id: str, tokens: OAuthToken) -> None:
        """Store tokens for a user"""
        pass

    @abstractmethod
    def clear_tokens(self, user_id: str) -> None:
        """Remove tokens for a user"""
        pass

    @abstractmethod
    def get_client_info(self) -> Optional[OAuthClientInfo]:
        """Get OAuth client credentials"""
        pass

    @abstractmethod
    def set_client_info(self, client_info: OAuthClientInfo) -> None:
        """Store OAuth client credentials"""
        pass

    @abstractmethod
    def list_users(self) -> list[str]:
        """List all users with stored tokens"""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired tokens, return count"""
        pass


class FileTokenStorageAdapter(TokenStorageAdapter):
    """
    File-based implementation of TokenStorageAdapter.

    Adapts existing LocalDirectoryCredentialStore to the new interface.
    """

    def __init__(self, base_dir: Optional[str] = None):
        from .credential_store import LocalDirectoryCredentialStore
        self._store = LocalDirectoryCredentialStore(base_dir)

    def get_tokens(self, user_id: str) -> Optional[OAuthToken]:
        """Load credentials from file and convert to OAuthToken"""
        creds = self._store.load_credentials(user_id)
        if not creds:
            return None

        return OAuthToken(
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_type="Bearer",
            expires_at=creds.expiry,
            scopes=list(creds.scopes) if creds.scopes else None
        )

    # ... other methods


class MemoryTokenStorageAdapter(TokenStorageAdapter):
    """
    In-memory implementation for stateless mode.

    Adapts OAuth21SessionStore to the new interface.
    """

    def __init__(self):
        from .oauth21_session_store import get_oauth_store
        self._store = get_oauth_store()

    # ... implementation
```

**Benefits**:
- ✅ Swappable storage backends (file, memory, database)
- ✅ FastMCP compatibility
- ✅ Easier testing with mock adapters
- ✅ Standardized token format across storage types

---

### 2. Automatic Stale Credential Retry Logic

**Objective**: Automatically detect and recover from stale/revoked credentials

**Implementation**:
```python
# File: automagik_tools/tools/google_workspace/auth/retry_handler.py

from functools import wraps
from typing import Callable, TypeVar, ParamSpec
import asyncio
import logging
from google.auth.exceptions import RefreshError

P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)


class StaleCredentialError(Exception):
    """Raised when credentials are stale and require reauthentication"""
    pass


def with_automatic_retry(
    max_retries: int = 1,
    clear_cache_on_fail: bool = True
):
    """
    Decorator that automatically retries OAuth operations on stale credentials.

    Inspired by FastMCP's async_auth_flow with retry logic.

    Args:
        max_retries: Maximum number of retry attempts (default: 1)
        clear_cache_on_fail: Clear credential cache before retry

    Example:
        @with_automatic_retry(max_retries=2)
        async def get_gmail_service(user_email: str):
            # Will automatically retry if credentials are stale
            return await authenticate_and_build_service(user_email)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except RefreshError as e:
                    last_error = e
                    error_msg = str(e).lower()

                    # Check if error indicates stale credentials
                    if "invalid_grant" in error_msg or "expired" in error_msg or "revoked" in error_msg:
                        logger.warning(
                            f"Stale credentials detected on attempt {attempt + 1}/{max_retries + 1}: {e}"
                        )

                        if attempt < max_retries:
                            if clear_cache_on_fail:
                                # Extract user email from args/kwargs
                                user_email = _extract_user_email(args, kwargs)
                                if user_email:
                                    await _clear_user_credentials(user_email)
                                    logger.info(f"Cleared cached credentials for {user_email}, retrying...")

                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt)
                            continue

                    # Non-stale error, raise immediately
                    raise

            # All retries exhausted
            raise StaleCredentialError(
                f"Failed after {max_retries + 1} attempts. "
                f"Please reauthenticate using start_google_auth. "
                f"Last error: {last_error}"
            ) from last_error

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Sync version for non-async functions
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except RefreshError as e:
                    last_error = e
                    error_msg = str(e).lower()

                    if "invalid_grant" in error_msg or "expired" in error_msg or "revoked" in error_msg:
                        logger.warning(
                            f"Stale credentials detected on attempt {attempt + 1}/{max_retries + 1}: {e}"
                        )

                        if attempt < max_retries:
                            if clear_cache_on_fail:
                                user_email = _extract_user_email(args, kwargs)
                                if user_email:
                                    _clear_user_credentials_sync(user_email)
                                    logger.info(f"Cleared cached credentials for {user_email}, retrying...")

                            import time
                            time.sleep(2 ** attempt)
                            continue

                    raise

            raise StaleCredentialError(
                f"Failed after {max_retries + 1} attempts. "
                f"Please reauthenticate using start_google_auth. "
                f"Last error: {last_error}"
            ) from last_error

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def _extract_user_email(args: tuple, kwargs: dict) -> Optional[str]:
    """Extract user_email from function arguments"""
    # Try kwargs first
    if "user_email" in kwargs:
        return kwargs["user_email"]
    if "user_google_email" in kwargs:
        return kwargs["user_google_email"]

    # Try positional args (usually first argument)
    if args and isinstance(args[0], str) and "@" in args[0]:
        return args[0]

    return None
```

**Usage Example**:
```python
# In google_auth.py

@with_automatic_retry(max_retries=2, clear_cache_on_fail=True)
async def get_credentials(user_email: str, scopes: list[str]) -> Credentials:
    """
    Get credentials with automatic retry on stale tokens.

    Will automatically:
    1. Try to load cached credentials
    2. If stale, clear cache and retry
    3. If still failing, prompt user to reauthenticate
    """
    # Existing implementation...
```

**Benefits**:
- ✅ Automatic recovery from temporary auth failures
- ✅ Reduced user friction (fewer manual reauths)
- ✅ Exponential backoff prevents API rate limiting
- ✅ Clear error messages when retry exhausted
- ✅ Works with both async and sync code

---

### 3. Session Expiry and Cleanup Mechanism

**Objective**: Prevent memory leaks from unlimited session bindings

**Implementation**:
```python
# File: automagik_tools/tools/google_workspace/auth/session_manager.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionBinding:
    """Session-to-user binding with expiry"""
    user_email: str
    bound_at: datetime
    expires_at: datetime
    last_accessed: datetime
    access_count: int = 0


class SessionManager:
    """
    Manages session bindings with automatic expiry and cleanup.

    Features:
    - TTL-based expiry (default: 24 hours)
    - LRU cleanup when max sessions reached
    - Background cleanup thread
    - Thread-safe operations
    """

    def __init__(
        self,
        default_ttl: timedelta = timedelta(hours=24),
        max_sessions: int = 1000,
        cleanup_interval: timedelta = timedelta(hours=1)
    ):
        self._bindings: Dict[str, SessionBinding] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._max_sessions = max_sessions
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

    def bind_session(
        self,
        session_id: str,
        user_email: str,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Bind session to user with expiry.

        Returns:
            True if binding created, False if session already bound
        """
        with self._lock:
            # Check existing binding
            if session_id in self._bindings:
                binding = self._bindings[session_id]

                # Update last accessed time
                binding.last_accessed = datetime.utcnow()
                binding.access_count += 1

                # Check if bound to same user
                if binding.user_email == user_email:
                    logger.debug(f"Session {session_id} already bound to {user_email}")
                    return True
                else:
                    logger.warning(
                        f"Session {session_id} already bound to {binding.user_email}, "
                        f"cannot bind to {user_email}"
                    )
                    return False

            # Cleanup if max sessions reached
            if len(self._bindings) >= self._max_sessions:
                self._cleanup_lru()

            # Create new binding
            now = datetime.utcnow()
            ttl = ttl or self._default_ttl

            self._bindings[session_id] = SessionBinding(
                user_email=user_email,
                bound_at=now,
                expires_at=now + ttl,
                last_accessed=now,
                access_count=1
            )

            logger.info(f"Bound session {session_id} to {user_email}, expires at {now + ttl}")
            return True

    def get_user_email(self, session_id: str) -> Optional[str]:
        """Get user email for session, None if expired/not found"""
        with self._lock:
            binding = self._bindings.get(session_id)
            if not binding:
                return None

            # Check expiry
            now = datetime.utcnow()
            if now > binding.expires_at:
                logger.debug(f"Session {session_id} expired, removing binding")
                del self._bindings[session_id]
                return None

            # Update last accessed
            binding.last_accessed = now
            binding.access_count += 1

            return binding.user_email

    def unbind_session(self, session_id: str) -> bool:
        """Unbind session, return True if existed"""
        with self._lock:
            if session_id in self._bindings:
                user_email = self._bindings[session_id].user_email
                del self._bindings[session_id]
                logger.info(f"Unbound session {session_id} from {user_email}")
                return True
            return False

    def cleanup_expired(self) -> int:
        """Remove expired sessions, return count"""
        with self._lock:
            now = datetime.utcnow()
            expired = [
                sid for sid, binding in self._bindings.items()
                if now > binding.expires_at
            ]

            for sid in expired:
                del self._bindings[sid]

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

            return len(expired)

    def _cleanup_lru(self, count: int = 100) -> None:
        """Remove least recently used sessions"""
        # Sort by last accessed time
        sorted_sessions = sorted(
            self._bindings.items(),
            key=lambda x: x[1].last_accessed
        )

        # Remove oldest
        for sid, _ in sorted_sessions[:count]:
            del self._bindings[sid]

        logger.info(f"Cleaned up {count} LRU sessions")

    def start_background_cleanup(self) -> None:
        """Start background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            logger.warning("Background cleanup already running")
            return

        def cleanup_loop():
            while not self._stop_cleanup.wait(self._cleanup_interval.total_seconds()):
                try:
                    count = self.cleanup_expired()
                    if count > 0:
                        logger.debug(f"Background cleanup removed {count} sessions")
                except Exception as e:
                    logger.error(f"Error in background cleanup: {e}")

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("Started background session cleanup")

    def stop_background_cleanup(self) -> None:
        """Stop background cleanup thread"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("Stopped background session cleanup")

    def get_stats(self) -> dict:
        """Get session statistics"""
        with self._lock:
            now = datetime.utcnow()
            active = sum(1 for b in self._bindings.values() if now <= b.expires_at)

            return {
                "total_sessions": len(self._bindings),
                "active_sessions": active,
                "expired_sessions": len(self._bindings) - active,
                "unique_users": len(set(b.user_email for b in self._bindings.values()))
            }
```

**Integration**:
```python
# Update oauth21_session_store.py to use SessionManager

# Replace simple dict with SessionManager
_session_manager = SessionManager(
    default_ttl=timedelta(hours=24),
    max_sessions=1000
)

# Start background cleanup on module load
_session_manager.start_background_cleanup()


def bind_session_to_user(session_id: str, user_email: str) -> bool:
    """Bind session with automatic expiry"""
    return _session_manager.bind_session(session_id, user_email)


def get_user_from_session(session_id: str) -> Optional[str]:
    """Get user with expiry check"""
    return _session_manager.get_user_email(session_id)
```

**Benefits**:
- ✅ Prevents memory leaks from unlimited bindings
- ✅ Automatic cleanup of expired sessions
- ✅ LRU eviction when max sessions reached
- ✅ Configurable TTL per session or global default
- ✅ Statistics for monitoring

---

### 4. Enhanced Error Messages and User Guidance

**Objective**: Provide actionable, user-friendly error messages

**Implementation**:
```python
# File: automagik_tools/tools/google_workspace/auth/error_messages.py

from typing import Optional
from dataclasses import dataclass


@dataclass
class AuthErrorGuidance:
    """Structured error message with actionable guidance"""
    error_type: str
    message: str
    user_action: str
    technical_details: Optional[str] = None
    help_url: Optional[str] = None

    def format(self, include_technical: bool = False) -> str:
        """Format as user-friendly message"""
        lines = [
            f"🔐 Authentication Error: {self.error_type}",
            "",
            f"Message: {self.message}",
            "",
            f"✅ Action Required:",
            f"   {self.user_action}",
        ]

        if include_technical and self.technical_details:
            lines.extend([
                "",
                f"🔧 Technical Details:",
                f"   {self.technical_details}"
            ])

        if self.help_url:
            lines.extend([
                "",
                f"📚 Documentation: {self.help_url}"
            ])

        return "\n".join(lines)


class AuthErrorMessages:
    """Centralized error message templates with guidance"""

    @staticmethod
    def token_expired(user_email: str, service_name: str) -> AuthErrorGuidance:
        return AuthErrorGuidance(
            error_type="Token Expired",
            message=f"Your authentication token for {service_name} has expired.",
            user_action=(
                f"Please reauthenticate by calling:\n"
                f"   start_google_auth(user_google_email=\"{user_email}\", service_name=\"{service_name}\")\n\n"
                f"Then follow the browser link to grant permissions."
            ),
            help_url="https://automagik-tools.readthedocs.io/oauth/reauthentication"
        )

    @staticmethod
    def token_revoked(user_email: str, service_name: str) -> AuthErrorGuidance:
        return AuthErrorGuidance(
            error_type="Token Revoked",
            message=(
                f"Your authentication token has been revoked. "
                f"This may happen if you changed your Google password or revoked access."
            ),
            user_action=(
                f"Please reauthenticate by calling:\n"
                f"   start_google_auth(user_google_email=\"{user_email}\", service_name=\"{service_name}\")\n\n"
                f"You will need to grant permissions again."
            ),
            help_url="https://automagik-tools.readthedocs.io/oauth/revoked-tokens"
        )

    @staticmethod
    def insufficient_scopes(user_email: str, required_scopes: list[str], current_scopes: list[str]) -> AuthErrorGuidance:
        missing = set(required_scopes) - set(current_scopes)

        return AuthErrorGuidance(
            error_type="Insufficient Permissions",
            message="Your current authentication does not have all required permissions.",
            user_action=(
                f"Please reauthenticate with additional permissions:\n"
                f"   start_google_auth(user_google_email=\"{user_email}\", service_name=...)\n\n"
                f"You will be asked to grant these additional permissions:\n" +
                "\n".join(f"   - {scope}" for scope in missing)
            ),
            technical_details=f"Missing scopes: {', '.join(missing)}",
            help_url="https://automagik-tools.readthedocs.io/oauth/scopes"
        )

    @staticmethod
    def client_secrets_not_configured() -> AuthErrorGuidance:
        return AuthErrorGuidance(
            error_type="OAuth Client Not Configured",
            message="OAuth client credentials are not configured.",
            user_action=(
                "Please configure OAuth credentials using one of these methods:\n\n"
                "1. Environment Variables (Recommended):\n"
                "   export GOOGLE_OAUTH_CLIENT_ID='your-client-id'\n"
                "   export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'\n"
                "   export GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/oauth2callback'\n\n"
                "2. Client Secrets File:\n"
                "   export GOOGLE_CLIENT_SECRET_PATH='/path/to/client_secret.json'\n\n"
                "3. Default Location:\n"
                "   Place client_secret.json in the auth directory"
            ),
            help_url="https://automagik-tools.readthedocs.io/oauth/setup"
        )

    @staticmethod
    def session_already_bound(session_id: str, current_user: str, requested_user: str) -> AuthErrorGuidance:
        return AuthErrorGuidance(
            error_type="Session Already Authenticated",
            message=f"This session is already authenticated as {current_user}.",
            user_action=(
                f"To authenticate as {requested_user}, please:\n\n"
                f"1. Start a new session, OR\n"
                f"2. Log out first by calling:\n"
                f"   logout_google_auth(session_id=\"{session_id}\")\n\n"
                f"Then authenticate again."
            ),
            technical_details=f"Session {session_id} bound to {current_user}, cannot bind to {requested_user}"
        )

    @staticmethod
    def generic_auth_error(error: Exception, user_email: str) -> AuthErrorGuidance:
        return AuthErrorGuidance(
            error_type="Authentication Error",
            message="An unexpected error occurred during authentication.",
            user_action=(
                f"Please try these steps:\n\n"
                f"1. Clear cached credentials:\n"
                f"   clear_google_auth(user_google_email=\"{user_email}\")\n\n"
                f"2. Reauthenticate:\n"
                f"   start_google_auth(user_google_email=\"{user_email}\", service_name=...)\n\n"
                f"If the problem persists, check your OAuth client configuration."
            ),
            technical_details=str(error),
            help_url="https://automagik-tools.readthedocs.io/oauth/troubleshooting"
        )
```

**Usage**:
```python
# In service_decorator.py

except RefreshError as e:
    if "invalid_grant" in str(e).lower():
        guidance = AuthErrorMessages.token_revoked(user_email, service_name)
        raise GoogleAuthenticationError(guidance.format(include_technical=True))

    guidance = AuthErrorMessages.token_expired(user_email, service_name)
    raise GoogleAuthenticationError(guidance.format())
```

**Benefits**:
- ✅ Consistent, actionable error messages
- ✅ Step-by-step resolution guidance
- ✅ Links to relevant documentation
- ✅ Technical details for debugging
- ✅ User-friendly formatting with emojis

---

### 5. Auth Requirement Detection

**Objective**: Automatically detect when authentication is required

**Implementation**:
```python
# File: automagik_tools/tools/google_workspace/auth/auth_checker.py

from typing import Optional
import httpx
import logging

logger = logging.getLogger(__name__)


async def check_if_auth_required(
    mcp_url: str,
    timeout: float = 5.0,
    httpx_kwargs: Optional[dict] = None
) -> bool:
    """
    Check if MCP endpoint requires authentication by making a test request.

    Inspired by FastMCP's check_if_auth_required function.

    Args:
        mcp_url: The MCP server URL to check
        timeout: Request timeout in seconds
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
                mcp_url,
                timeout=timeout,
                follow_redirects=False
            )

            # Check status code
            if response.status_code == 401:
                logger.debug(f"Auth required for {mcp_url}: 401 Unauthorized")
                return True

            if response.status_code == 403:
                logger.debug(f"Auth required for {mcp_url}: 403 Forbidden")
                return True

            # Check for WWW-Authenticate header
            if "www-authenticate" in response.headers:
                logger.debug(f"Auth required for {mcp_url}: WWW-Authenticate header present")
                return True

            # Successful response, no auth needed
            logger.debug(f"No auth required for {mcp_url}: {response.status_code}")
            return False

    except httpx.TimeoutException:
        logger.warning(f"Timeout checking auth requirement for {mcp_url}")
        # Assume auth not required if server doesn't respond
        return False

    except Exception as e:
        logger.warning(f"Error checking auth requirement for {mcp_url}: {e}")
        # Assume auth not required on error
        return False


def require_auth_if_needed(auth_url: str, check_timeout: float = 5.0):
    """
    Decorator to conditionally require authentication based on endpoint check.

    Example:
        @require_auth_if_needed("http://localhost:8000/mcp")
        async def my_tool_function():
            # Will automatically check if auth is needed
            # and prompt user if required
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if auth required
            auth_needed = await check_if_auth_required(auth_url, check_timeout)

            if auth_needed:
                # Extract user email from args/kwargs
                user_email = _extract_user_email(args, kwargs)

                if not user_email:
                    raise ValueError(
                        f"Authentication required for {auth_url}, "
                        f"but no user_email provided"
                    )

                # Check if we have valid credentials
                from .google_auth import get_credentials
                creds = await get_credentials(user_email, scopes=["openid", "email"])

                if not creds or not creds.valid:
                    # Prompt for authentication
                    guidance = AuthErrorMessages.token_expired(
                        user_email,
                        "unknown_service"
                    )
                    raise GoogleAuthenticationError(guidance.format())

            # Proceed with function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**Benefits**:
- ✅ Automatic detection of auth requirements
- ✅ Reduces unnecessary auth prompts
- ✅ Works with any HTTP endpoint
- ✅ Graceful fallback on errors
- ✅ Decorator for easy integration

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Implement TokenStorageAdapter interface
- [ ] Create FileTokenStorageAdapter
- [ ] Create MemoryTokenStorageAdapter
- [ ] Add comprehensive unit tests

### Phase 2: Retry Logic (Week 1)
- [ ] Implement with_automatic_retry decorator
- [ ] Add exponential backoff
- [ ] Integrate with existing error handling
- [ ] Test with various failure scenarios

### Phase 3: Session Management (Week 2)
- [ ] Implement SessionManager with expiry
- [ ] Add background cleanup thread
- [ ] Replace existing session binding logic
- [ ] Add session statistics endpoint

### Phase 4: User Experience (Week 2)
- [ ] Implement AuthErrorMessages
- [ ] Update all error handling to use new messages
- [ ] Add check_if_auth_required function
- [ ] Create require_auth_if_needed decorator

### Phase 5: Testing & Documentation (Week 3)
- [ ] Comprehensive integration tests
- [ ] Load testing for session manager
- [ ] Update user documentation
- [ ] Create migration guide
- [ ] Add troubleshooting guide

### Phase 6: Consolidation (Week 3)
- [ ] Merge google_workspace and google_workspace_core
- [ ] Remove duplicate code
- [ ] Update all imports
- [ ] Final testing

---

## Success Metrics

- **Reduced Reauthentication**: < 5% of users need to reauth within 24 hours
- **Error Resolution Time**: 80% of auth errors resolved within 2 minutes
- **Session Memory Usage**: < 10MB for 1000 active sessions
- **Retry Success Rate**: > 90% of stale credential errors auto-resolved
- **User Satisfaction**: NPS > 50 for authentication experience

---

## Risk Mitigation

### Risk 1: Breaking Changes
- **Mitigation**: Implement alongside existing code, gradual rollout
- **Fallback**: Feature flag to disable new logic

### Risk 2: Performance Impact
- **Mitigation**: Benchmark before/after, optimize hot paths
- **Monitoring**: Add metrics for auth operation latency

### Risk 3: Session Expiry Too Aggressive
- **Mitigation**: Configurable TTL with sensible defaults
- **User Control**: Allow per-tool TTL override

---

## Appendix: FastMCP Pattern Comparison

| Feature | FastMCP Pattern | Current Implementation | Enhancement |
|---------|----------------|------------------------|-------------|
| Token Storage | TokenStorageAdapter | LocalDirectoryCredentialStore | ✅ Implement adapter |
| Automatic Retry | async_auth_flow with retry | Manual RefreshError handling | ✅ Add decorator |
| Auth Check | check_if_auth_required() | N/A | ✅ Add function |
| Client Info Storage | set_client_info() | Environment variables | ✅ Add to adapter |
| Session Management | Built-in expiry | Unlimited bindings | ✅ Add SessionManager |
| Error Messages | Generic exceptions | Mix of custom/generic | ✅ Structured guidance |

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Author**: Claude Code
**Status**: Design Complete, Ready for Implementation
