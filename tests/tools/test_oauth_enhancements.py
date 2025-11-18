"""
Comprehensive tests for OAuth UX enhancements.

Tests the new FastMCP-inspired OAuth features:
- TokenStorageAdapter
- Automatic retry logic
- Enhanced error messages
- Session manager with expiry
- Auth requirement detection
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

# Import modules to test
from automagik_tools.tools.google_workspace_core.auth.token_storage_adapter import (
    OAuthToken,
    OAuthClientInfo,
    TokenStorageAdapter,
    FileTokenStorageAdapter,
    MemoryTokenStorageAdapter,
    get_token_storage_adapter,
)

from automagik_tools.tools.google_workspace_core.auth.retry_handler import (
    StaleCredentialError,
    with_automatic_retry,
    _is_stale_credential_error,
    _extract_user_email,
    configure_retry,
    get_retry_config,
)

from automagik_tools.tools.google_workspace_core.auth.error_messages import (
    AuthErrorGuidance,
    AuthErrorMessages,
    ErrorType,
)

from automagik_tools.tools.google_workspace_core.auth.session_manager import (
    SessionBinding,
    SessionManager,
    SessionStatus,
    get_session_manager,
    reset_session_manager,
)

from automagik_tools.tools.google_workspace_core.auth.auth_checker import (
    check_if_auth_required,
    check_if_auth_required_sync,
    validate_bearer_token,
    extract_bearer_token,
    AuthCheckCache,
)


# ===== OAuthToken Tests =====


def test_oauth_token_creation():
    """Test OAuthToken creation and properties"""
    token = OAuthToken(
        access_token="test_token_123",
        refresh_token="refresh_token_456",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        scopes=["email", "profile"],
    )

    assert token.access_token == "test_token_123"
    assert token.refresh_token == "refresh_token_456"
    assert token.token_type == "Bearer"
    assert token.scopes == ["email", "profile"]
    assert not token.is_expired()
    assert token.is_valid()


def test_oauth_token_expired():
    """Test expired token detection"""
    token = OAuthToken(
        access_token="test_token",
        expires_at=datetime.utcnow() - timedelta(hours=1),  # Already expired
    )

    assert token.is_expired()
    assert not token.is_valid()


def test_oauth_token_no_expiry():
    """Test token without expiry (doesn't expire)"""
    token = OAuthToken(access_token="test_token", expires_at=None)

    assert not token.is_expired()
    assert token.is_valid()


# ===== Retry Handler Tests =====


def test_extract_user_email_from_kwargs():
    """Test extracting user email from kwargs"""
    args = ()
    kwargs = {"user_email": "test@example.com", "other_param": "value"}

    email = _extract_user_email(args, kwargs)
    assert email == "test@example.com"


def test_extract_user_email_from_args():
    """Test extracting user email from positional args"""
    args = ("user@example.com", "other_arg")
    kwargs = {}

    email = _extract_user_email(args, kwargs)
    assert email == "user@example.com"


def test_extract_user_email_not_found():
    """Test when user email cannot be extracted"""
    args = ("not_an_email", 123)
    kwargs = {"other": "value"}

    email = _extract_user_email(args, kwargs)
    assert email is None


def test_is_stale_credential_error():
    """Test detection of stale credential errors"""
    # Test invalid_grant error
    error = RefreshError("invalid_grant: Token has been expired or revoked")
    assert _is_stale_credential_error(error)

    # Test other RefreshError
    error = RefreshError("Some other error")
    assert not _is_stale_credential_error(error)

    # Test non-RefreshError
    error = ValueError("Not a refresh error")
    assert not _is_stale_credential_error(error)


@pytest.mark.asyncio
async def test_with_automatic_retry_success():
    """Test successful function call with retry decorator"""

    @with_automatic_retry(max_retries=2)
    async def test_func(user_email: str):
        return f"Success for {user_email}"

    result = await test_func("test@example.com")
    assert result == "Success for test@example.com"


@pytest.mark.asyncio
async def test_with_automatic_retry_recovers():
    """Test retry decorator recovers from stale credentials"""
    call_count = 0

    @with_automatic_retry(max_retries=2, clear_cache_on_fail=False)
    async def test_func(user_email: str):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call fails with stale credential error
            raise RefreshError("invalid_grant: Token has been expired")

        # Second call succeeds
        return "Success after retry"

    result = await test_func("test@example.com")
    assert result == "Success after retry"
    assert call_count == 2  # Called twice (failed once, succeeded once)


@pytest.mark.asyncio
async def test_with_automatic_retry_exhausted():
    """Test retry decorator raises after retries exhausted"""

    @with_automatic_retry(max_retries=1)
    async def test_func(user_email: str):
        # Always fails
        raise RefreshError("invalid_grant: Token has been expired")

    with pytest.raises(StaleCredentialError) as exc_info:
        await test_func("test@example.com")

    assert "Please reauthenticate" in str(exc_info.value)


# ===== Error Messages Tests =====


def test_error_guidance_format():
    """Test error message formatting"""
    guidance = AuthErrorMessages.token_expired("user@example.com", "gmail")

    formatted = guidance.format(include_technical=False, use_emojis=True)

    assert "Authentication Error" in formatted
    assert "Token Expired" in formatted
    assert "user@example.com" in formatted
    assert "start_google_auth" in formatted


def test_error_guidance_no_emojis():
    """Test error message formatting without emojis"""
    guidance = AuthErrorMessages.token_expired("user@example.com", "gmail")

    formatted = guidance.format(use_emojis=False)

    # Should not contain emoji characters
    assert "🔐" not in formatted
    assert "✅" not in formatted


def test_error_guidance_to_dict():
    """Test converting error guidance to dictionary"""
    guidance = AuthErrorMessages.token_revoked("user@example.com", "gmail")

    data = guidance.to_dict()

    assert data["error_type"] == "token_revoked"
    assert data["title"] == "Token Revoked"
    assert "user@example.com" in data["message"]


def test_insufficient_scopes_error():
    """Test insufficient scopes error message"""
    required = ["gmail.readonly", "gmail.send"]
    current = ["gmail.readonly"]

    guidance = AuthErrorMessages.insufficient_scopes(
        "user@example.com", "gmail", required, current
    )

    formatted = guidance.format()

    assert "Insufficient Permissions" in formatted
    assert "gmail.send" in formatted  # Missing scope should be mentioned


# ===== Session Manager Tests =====


def test_session_binding_creation():
    """Test SessionBinding creation"""
    now = datetime.utcnow()
    expires = now + timedelta(hours=24)

    binding = SessionBinding(
        user_email="test@example.com",
        bound_at=now,
        expires_at=expires,
        last_accessed=now,
        access_count=1,
    )

    assert binding.user_email == "test@example.com"
    assert not binding.is_expired()
    assert binding.is_active()
    assert binding.status == SessionStatus.ACTIVE


def test_session_binding_expired():
    """Test expired session detection"""
    now = datetime.utcnow()
    expired = now - timedelta(hours=1)  # Already expired

    binding = SessionBinding(
        user_email="test@example.com",
        bound_at=expired,
        expires_at=expired,
        last_accessed=expired,
    )

    assert binding.is_expired()
    assert not binding.is_active()


def test_session_manager_bind():
    """Test binding session to user"""
    manager = SessionManager(default_ttl=timedelta(hours=1))

    result = manager.bind_session("session_123", "user@example.com")

    assert result is True
    assert manager.get_user_email("session_123") == "user@example.com"


def test_session_manager_duplicate_bind():
    """Test binding same session twice to same user"""
    manager = SessionManager()

    manager.bind_session("session_123", "user@example.com")
    result = manager.bind_session("session_123", "user@example.com")

    assert result is True  # Should succeed (same user)


def test_session_manager_different_user_bind():
    """Test binding same session to different user (should fail)"""
    manager = SessionManager()

    manager.bind_session("session_123", "user1@example.com")
    result = manager.bind_session("session_123", "user2@example.com")

    assert result is False  # Should fail (different user)
    assert (
        manager.get_user_email("session_123") == "user1@example.com"
    )  # Original binding preserved


def test_session_manager_unbind():
    """Test unbinding session"""
    manager = SessionManager()

    manager.bind_session("session_123", "user@example.com")
    result = manager.unbind_session("session_123")

    assert result is True
    assert manager.get_user_email("session_123") is None


def test_session_manager_cleanup_expired():
    """Test cleaning up expired sessions"""
    manager = SessionManager(default_ttl=timedelta(seconds=0.1))  # Very short TTL

    manager.bind_session("session_1", "user1@example.com")
    manager.bind_session("session_2", "user2@example.com")

    # Wait for expiry
    import time

    time.sleep(0.2)

    count = manager.cleanup_expired()

    assert count == 2  # Both sessions should be expired
    assert manager.get_user_email("session_1") is None
    assert manager.get_user_email("session_2") is None


def test_session_manager_stats():
    """Test session statistics"""
    manager = SessionManager()

    manager.bind_session("session_1", "user1@example.com")
    manager.bind_session("session_2", "user2@example.com")

    stats = manager.get_stats()

    assert stats["total_sessions"] == 2
    assert stats["active_sessions"] == 2
    assert stats["unique_users"] == 2


def test_session_manager_revoke():
    """Test revoking session"""
    manager = SessionManager()

    manager.bind_session("session_123", "user@example.com")
    result = manager.revoke_session("session_123")

    assert result is True

    binding = manager.get_binding("session_123")
    assert binding is not None
    assert binding.status == SessionStatus.REVOKED
    assert not binding.is_active()


# ===== Auth Checker Tests =====


@pytest.mark.asyncio
async def test_check_if_auth_required_401():
    """Test auth check with 401 response"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await check_if_auth_required("http://example.com/api")

        assert result is True


@pytest.mark.asyncio
async def test_check_if_auth_required_200():
    """Test auth check with 200 response (no auth needed)"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await check_if_auth_required("http://example.com/api")

        assert result is False


@pytest.mark.asyncio
async def test_check_if_auth_required_www_authenticate():
    """Test auth check with WWW-Authenticate header"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"www-authenticate": "Bearer realm='example'"}

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await check_if_auth_required("http://example.com/api")

        assert result is True


def test_validate_bearer_token_valid():
    """Test validating valid bearer tokens"""
    assert validate_bearer_token("Bearer abc123def456ghi789jkl012") is True
    assert validate_bearer_token("abc123def456ghi789jkl012") is True


def test_validate_bearer_token_invalid():
    """Test validating invalid bearer tokens"""
    assert validate_bearer_token("") is False
    assert validate_bearer_token("short") is False  # Too short
    assert validate_bearer_token("has spaces in it which is invalid") is False
    assert validate_bearer_token(None) is False


def test_extract_bearer_token():
    """Test extracting bearer token from header"""
    # With Bearer prefix
    token = extract_bearer_token("Bearer abc123def456ghi789jkl012")
    assert token == "abc123def456ghi789jkl012"

    # Without Bearer prefix
    token = extract_bearer_token("abc123def456ghi789jkl012")
    assert token == "abc123def456ghi789jkl012"

    # Invalid format
    token = extract_bearer_token("Basic xyz")
    assert token is None


def test_auth_check_cache():
    """Test auth check caching"""
    cache = AuthCheckCache(ttl_seconds=10)

    # Set and get
    cache.set("http://example.com", True)
    result = cache.get("http://example.com")

    assert result is True

    # Clear specific URL
    cache.clear("http://example.com")
    result = cache.get("http://example.com")

    assert result is None


def test_auth_check_cache_expiry():
    """Test cache expiry"""
    cache = AuthCheckCache(ttl_seconds=0.1)  # Very short TTL

    cache.set("http://example.com", True)

    # Wait for expiry
    import time

    time.sleep(0.2)

    result = cache.get("http://example.com")
    assert result is None  # Should be expired


# ===== Integration Tests =====


def test_retry_config_global():
    """Test global retry configuration"""
    # Save original config
    original = get_retry_config()

    # Configure new settings
    configure_retry(default_max_retries=5, enabled=True)

    config = get_retry_config()
    assert config.default_max_retries == 5
    assert config.enabled is True

    # Restore original
    configure_retry(
        default_max_retries=original.default_max_retries,
        default_clear_cache=original.default_clear_cache,
        default_backoff_base=original.default_backoff_base,
        enabled=original.enabled,
    )


def test_get_session_manager_singleton():
    """Test session manager singleton pattern"""
    reset_session_manager()  # Reset first

    manager1 = get_session_manager()
    manager2 = get_session_manager()

    assert manager1 is manager2  # Same instance


def test_session_manager_background_cleanup():
    """Test background cleanup thread"""
    reset_session_manager()

    manager = SessionManager(cleanup_interval=timedelta(seconds=0.5))

    # Start cleanup
    manager.start_background_cleanup()
    assert manager._cleanup_thread is not None
    assert manager._cleanup_thread.is_alive()

    # Stop cleanup
    manager.stop_background_cleanup()
    import time

    time.sleep(1)  # Give it time to stop
    assert manager._cleanup_thread is None or not manager._cleanup_thread.is_alive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
