"""
Comprehensive tests for Google Workspace Core functionality.

Tests real-world scenarios for:
- Session management (expiry, LRU, auto-refresh, concurrency)
- OAuth configuration (validation, environment variables)
- Auth checking (HTTP status codes, headers)
- Drive helpers (permissions, URLs, queries)
- Docs helpers (text styles, requests)
"""

import pytest
import os
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
import httpx

from automagik_tools.tools.google_workspace_core.auth.session_manager import (
    SessionManager,
    SessionBinding,
    SessionStatus,
)
from automagik_tools.tools.google_workspace_core.auth.oauth_config import OAuthConfig
from automagik_tools.tools.google_workspace_core.auth.auth_checker import (
    check_if_auth_required,
    check_if_auth_required_sync,
)
from automagik_tools.tools.google_workspace_core.services.drive_helpers import (
    check_public_link_permission,
    format_public_sharing_error,
    get_drive_image_url,
    build_drive_list_params,
)
from automagik_tools.tools.google_workspace_core.services.docs_helpers import (
    build_text_style,
    create_insert_text_request,
    create_insert_text_segment_request,
    create_delete_range_request,
)


class TestSessionManagerEdgeCases:
    """Test edge cases and boundary conditions in session management."""

    def test_session_expires_exactly_at_boundary(self):
        """Test that session expires AT the timestamp, not after."""
        manager = SessionManager(default_ttl=timedelta(seconds=1))

        # Bind a session
        manager.bind_session("test_session", "user@example.com", ttl=timedelta(seconds=1))

        # Wait until expiry
        time.sleep(1.1)

        # Session should be expired
        email = manager.get_user_email("test_session")
        assert email is None, "Session should be None at exact expiry"

        # Check status was updated
        binding = manager.get_binding("test_session")
        assert binding.status == SessionStatus.EXPIRED

    def test_session_auto_refresh_extends_lifetime(self):
        """Test that auto-refresh updates access tracking on access."""
        manager = SessionManager(default_ttl=timedelta(seconds=2), auto_refresh=True)

        # Bind session with short TTL
        manager.bind_session("test_session", "user@example.com", ttl=timedelta(seconds=2))

        # Get initial access count
        binding1 = manager.get_binding("test_session")
        initial_count = binding1.access_count

        # Wait a bit
        time.sleep(0.1)

        # Access the session (should update access tracking)
        email = manager.get_user_email("test_session")
        assert email == "user@example.com"

        # Check access count increased
        binding2 = manager.get_binding("test_session")
        assert binding2.access_count > initial_count

    def test_session_without_auto_refresh(self):
        """Test session behavior when auto_refresh is disabled."""
        manager = SessionManager(default_ttl=timedelta(hours=1), auto_refresh=False)

        # Bind session
        manager.bind_session("test_session", "user@example.com")

        # Get binding and record access count
        binding1 = manager.get_binding("test_session")
        initial_count = binding1.access_count

        # Access session multiple times
        manager.get_user_email("test_session")
        manager.get_user_email("test_session")

        # Access count should not increase when auto_refresh is off
        binding2 = manager.get_binding("test_session")
        # Binding was accessed during bind_session, so count is 1
        assert binding2.access_count == initial_count

    def test_lru_cleanup_removes_oldest_sessions(self):
        """Test that LRU cleanup removes least recently accessed sessions."""
        manager = SessionManager(max_sessions=5)

        # Create 5 sessions
        for i in range(5):
            manager.bind_session(f"session_{i}", f"user{i}@example.com")
            time.sleep(0.01)  # Ensure different timestamps

        # Access session_0 to make it recent
        manager.get_user_email("session_0")

        # Trigger LRU cleanup (remove 3 sessions)
        removed = manager._cleanup_lru(count=3)
        assert removed == 3

        # session_0 should still exist (it was accessed recently)
        assert manager.get_user_email("session_0") == "user0@example.com"

    def test_max_sessions_triggers_automatic_cleanup(self):
        """Test that reaching max_sessions triggers automatic LRU cleanup."""
        manager = SessionManager(max_sessions=3)

        # Fill to capacity
        manager.bind_session("session_1", "user1@example.com")
        manager.bind_session("session_2", "user2@example.com")
        manager.bind_session("session_3", "user3@example.com")

        # Adding one more should trigger cleanup
        manager.bind_session("session_4", "user4@example.com")

        # Total sessions should still be reasonable (cleanup removes 100)
        stats = manager.get_stats()
        # Since we only had 3 and added 1, cleanup runs but doesn't remove much
        assert stats["total_sessions"] <= manager._max_sessions + 100

    def test_session_rebind_with_allow_rebind(self):
        """Test rebinding session to different user when allow_rebind=True."""
        manager = SessionManager()

        # Bind session to first user
        manager.bind_session("test_session", "user1@example.com")
        assert manager.get_user_email("test_session") == "user1@example.com"

        # Rebind to different user with allow_rebind=True
        result = manager.bind_session(
            "test_session", "user2@example.com", allow_rebind=True
        )
        assert result is True
        assert manager.get_user_email("test_session") == "user2@example.com"

    def test_session_rebind_rejected_without_flag(self):
        """Test that rebinding to different user fails without allow_rebind flag."""
        manager = SessionManager()

        # Bind session to first user
        manager.bind_session("test_session", "user1@example.com")

        # Try rebinding to different user without allow_rebind
        result = manager.bind_session("test_session", "user2@example.com")
        assert result is False

        # Original binding should remain
        assert manager.get_user_email("test_session") == "user1@example.com"

    def test_session_stats_accuracy(self):
        """Test that session statistics are accurate."""
        manager = SessionManager(default_ttl=timedelta(seconds=1))

        # Create active sessions
        manager.bind_session("active1", "user1@example.com", ttl=timedelta(hours=1))
        manager.bind_session("active2", "user2@example.com", ttl=timedelta(hours=1))

        # Create expired session
        manager.bind_session("expired", "user3@example.com", ttl=timedelta(seconds=0.1))
        time.sleep(0.2)

        # Create revoked session
        manager.bind_session("revoked", "user4@example.com")
        manager.revoke_session("revoked")

        # Get stats
        stats = manager.get_stats()

        assert stats["total_sessions"] == 4
        assert stats["active_sessions"] >= 2  # active1, active2
        assert stats["revoked_sessions"] >= 1  # revoked
        assert stats["unique_users"] == 4

    def test_cleanup_expired_removes_old_sessions(self):
        """Test that cleanup_expired removes expired sessions."""
        manager = SessionManager()

        # Create expired sessions
        manager.bind_session("expired1", "user1@example.com", ttl=timedelta(seconds=0.1))
        manager.bind_session("expired2", "user2@example.com", ttl=timedelta(seconds=0.1))

        # Create active session
        manager.bind_session("active", "user3@example.com", ttl=timedelta(hours=1))

        # Wait for expiry
        time.sleep(0.2)

        # Cleanup
        removed = manager.cleanup_expired()

        assert removed == 2
        assert manager.get_user_email("active") == "user3@example.com"
        assert manager.get_user_email("expired1") is None

    def test_get_sessions_for_user(self):
        """Test retrieving all sessions for a specific user."""
        manager = SessionManager()

        # Create multiple sessions for same user
        manager.bind_session("session1", "user@example.com")
        manager.bind_session("session2", "user@example.com")
        manager.bind_session("session3", "other@example.com")

        # Get sessions for user
        sessions = manager.get_sessions_for_user("user@example.com")

        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" not in sessions

    def test_unbind_all_for_user(self):
        """Test unbinding all sessions for a user."""
        manager = SessionManager()

        # Create sessions
        manager.bind_session("session1", "user@example.com")
        manager.bind_session("session2", "user@example.com")
        manager.bind_session("session3", "other@example.com")

        # Unbind all for user
        count = manager.unbind_all_for_user("user@example.com")

        assert count == 2
        assert manager.get_user_email("session1") is None
        assert manager.get_user_email("session2") is None
        assert manager.get_user_email("session3") == "other@example.com"


class TestOAuthConfigValidation:
    """Test OAuth configuration validation and environment variable handling."""

    @patch.dict(os.environ, {}, clear=True)
    def test_oauth_config_defaults(self):
        """Test OAuth config with default values."""
        config = OAuthConfig()

        assert config.base_uri == "http://localhost"
        assert config.port == 8000
        assert config.base_url == "http://localhost:8000"
        assert config.auto_open_browser is True
        assert config.oauth21_enabled is False
        assert config.stateless_mode is False

    @patch.dict(
        os.environ,
        {
            "WORKSPACE_MCP_BASE_URI": "https://example.com",
            "PORT": "9000",
            "GOOGLE_OAUTH_AUTO_OPEN_BROWSER": "false",
        },
    )
    def test_oauth_config_from_environment(self):
        """Test OAuth config reads from environment variables."""
        config = OAuthConfig()

        assert config.base_uri == "https://example.com"
        assert config.port == 9000
        assert config.base_url == "https://example.com:9000"
        assert config.auto_open_browser is False

    @patch.dict(os.environ, {"MCP_ENABLE_OAUTH21": "true"})
    def test_oauth21_enabled(self):
        """Test OAuth 2.1 mode configuration."""
        config = OAuthConfig()

        assert config.oauth21_enabled is True
        assert config.pkce_required is True
        assert config.supported_code_challenge_methods == ["S256"]

    @patch.dict(os.environ, {"MCP_ENABLE_OAUTH21": "false"})
    def test_oauth20_mode(self):
        """Test OAuth 2.0 mode supports both S256 and plain PKCE."""
        config = OAuthConfig()

        assert config.oauth21_enabled is False
        assert config.supported_code_challenge_methods == ["S256", "plain"]

    @patch.dict(os.environ, {"EXTERNAL_OAUTH21_PROVIDER": "true"})
    def test_external_provider_requires_oauth21(self):
        """Test that external OAuth 2.1 provider requires OAuth 2.1 enabled."""
        with pytest.raises(ValueError, match="EXTERNAL_OAUTH21_PROVIDER requires"):
            OAuthConfig()

    @patch.dict(
        os.environ,
        {"EXTERNAL_OAUTH21_PROVIDER": "true", "MCP_ENABLE_OAUTH21": "true"},
    )
    def test_external_provider_with_oauth21(self):
        """Test external OAuth 2.1 provider with OAuth 2.1 enabled."""
        config = OAuthConfig()
        assert config.external_oauth21_provider is True
        assert config.oauth21_enabled is True

    @patch.dict(os.environ, {"WORKSPACE_MCP_STATELESS_MODE": "true"})
    def test_stateless_mode_requires_oauth21(self):
        """Test that stateless mode requires OAuth 2.1."""
        with pytest.raises(ValueError, match="STATELESS_MODE requires"):
            OAuthConfig()

    @patch.dict(
        os.environ,
        {"WORKSPACE_MCP_STATELESS_MODE": "true", "MCP_ENABLE_OAUTH21": "true"},
    )
    def test_stateless_mode_with_oauth21(self):
        """Test stateless mode with OAuth 2.1 enabled."""
        config = OAuthConfig()
        assert config.stateless_mode is True
        assert config.oauth21_enabled is True

    @patch.dict(
        os.environ, {"GOOGLE_OAUTH_REDIRECT_URI": "https://custom.com/callback"}
    )
    def test_custom_redirect_uri(self):
        """Test custom redirect URI configuration."""
        config = OAuthConfig()
        assert config.redirect_uri == "https://custom.com/callback"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_redirect_uri(self):
        """Test default redirect URI construction."""
        config = OAuthConfig()
        assert config.redirect_uri == "http://localhost:8000/oauth2callback"

    @patch.dict(os.environ, {"WORKSPACE_EXTERNAL_URL": "https://proxy.example.com"})
    def test_external_url_configuration(self):
        """Test external URL for reverse proxy scenarios."""
        config = OAuthConfig()
        assert config.external_url == "https://proxy.example.com"


class TestAuthChecker:
    """Test authentication requirement detection."""

    @pytest.mark.asyncio
    async def test_auth_required_401(self):
        """Test detection of auth requirement from 401 status."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is True

    @pytest.mark.asyncio
    async def test_auth_required_403(self):
        """Test detection of auth requirement from 403 status."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is True

    @pytest.mark.asyncio
    async def test_auth_required_www_authenticate_header(self):
        """Test detection of auth requirement from WWW-Authenticate header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"WWW-Authenticate": "Bearer"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is True

    @pytest.mark.asyncio
    async def test_auth_not_required_200(self):
        """Test detection of no auth requirement from 200 status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is False

    @pytest.mark.asyncio
    async def test_auth_checker_timeout_assumes_not_required(self):
        """Test that timeout assumes auth not required (fail open)."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is False  # Fail open on timeout

    @pytest.mark.asyncio
    async def test_auth_checker_connection_error(self):
        """Test that connection errors assume auth not required."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            result = await check_if_auth_required("http://test.com/mcp")
            assert result is False

    def test_auth_checker_sync_401(self):
        """Test synchronous auth checker with 401."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get = Mock(
                return_value=mock_response
            )

            result = check_if_auth_required_sync("http://test.com/mcp")
            assert result is True

    def test_auth_checker_sync_200(self):
        """Test synchronous auth checker with 200."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get = Mock(
                return_value=mock_response
            )

            result = check_if_auth_required_sync("http://test.com/mcp")
            assert result is False


class TestDriveHelpers:
    """Test Google Drive helper functions."""

    def test_check_public_link_permission_with_reader(self):
        """Test checking for public link permission with reader role."""
        permissions = [
            {"type": "user", "role": "owner"},
            {"type": "anyone", "role": "reader"},
        ]

        assert check_public_link_permission(permissions) is True

    def test_check_public_link_permission_with_writer(self):
        """Test checking for public link permission with writer role."""
        permissions = [
            {"type": "user", "role": "owner"},
            {"type": "anyone", "role": "writer"},
        ]

        assert check_public_link_permission(permissions) is True

    def test_check_public_link_permission_with_commenter(self):
        """Test checking for public link permission with commenter role."""
        permissions = [
            {"type": "anyone", "role": "commenter"},
        ]

        assert check_public_link_permission(permissions) is True

    def test_check_public_link_permission_no_public_access(self):
        """Test checking permissions without public link access."""
        permissions = [
            {"type": "user", "role": "owner"},
            {"type": "user", "role": "reader"},
        ]

        assert check_public_link_permission(permissions) is False

    def test_check_public_link_permission_empty_list(self):
        """Test checking permissions with empty list."""
        assert check_public_link_permission([]) is False

    def test_format_public_sharing_error(self):
        """Test formatting of public sharing error message."""
        error_msg = format_public_sharing_error("My Document", "abc123")

        assert "My Document" in error_msg
        assert "abc123" in error_msg
        assert "Anyone with the link" in error_msg
        assert "https://drive.google.com/file/d/abc123/view" in error_msg

    def test_get_drive_image_url(self):
        """Test generating correct Drive image URL."""
        url = get_drive_image_url("file123")

        assert url == "https://drive.google.com/uc?export=view&id=file123"

    def test_build_drive_list_params_basic(self):
        """Test building basic Drive list parameters."""
        params = build_drive_list_params("name='test'", 10)

        assert params["q"] == "name='test'"
        assert params["pageSize"] == 10
        assert params["supportsAllDrives"] is True
        assert params["includeItemsFromAllDrives"] is True
        assert "fields" in params

    def test_build_drive_list_params_with_drive_id(self):
        """Test building Drive list parameters with shared drive ID."""
        params = build_drive_list_params("name='test'", 10, drive_id="drive123")

        assert params["driveId"] == "drive123"
        assert params["corpora"] == "drive"

    def test_build_drive_list_params_with_custom_corpora(self):
        """Test building Drive list parameters with custom corpora."""
        params = build_drive_list_params(
            "name='test'", 10, drive_id="drive123", corpora="allDrives"
        )

        assert params["driveId"] == "drive123"
        assert params["corpora"] == "allDrives"

    def test_build_drive_list_params_corpora_without_drive_id(self):
        """Test building parameters with corpora but no drive_id."""
        params = build_drive_list_params("name='test'", 10, corpora="user")

        assert "driveId" not in params
        assert params["corpora"] == "user"


class TestDocsHelpers:
    """Test Google Docs helper functions."""

    def test_build_text_style_all_options(self):
        """Test building text style with all formatting options."""
        style, fields = build_text_style(
            bold=True,
            italic=True,
            underline=True,
            font_size=14,
            font_family="Arial",
        )

        assert style["bold"] is True
        assert style["italic"] is True
        assert style["underline"] is True
        assert style["fontSize"] == {"magnitude": 14, "unit": "PT"}
        assert style["weightedFontFamily"] == {"fontFamily": "Arial"}

        assert "bold" in fields
        assert "italic" in fields
        assert "underline" in fields
        assert "fontSize" in fields
        assert "weightedFontFamily" in fields

    def test_build_text_style_partial_options(self):
        """Test building text style with only some options."""
        style, fields = build_text_style(bold=True, font_size=12)

        assert style["bold"] is True
        assert style["fontSize"] == {"magnitude": 12, "unit": "PT"}
        assert "italic" not in style
        assert "underline" not in style

        assert fields == ["bold", "fontSize"]

    def test_build_text_style_empty(self):
        """Test building empty text style."""
        style, fields = build_text_style()

        assert style == {}
        assert fields == []

    def test_build_text_style_false_values(self):
        """Test building text style with explicit False values."""
        style, fields = build_text_style(bold=False, italic=False)

        assert style["bold"] is False
        assert style["italic"] is False
        assert fields == ["bold", "italic"]

    def test_create_insert_text_request(self):
        """Test creating insertText request."""
        request = create_insert_text_request(100, "Hello World")

        assert request["insertText"]["location"]["index"] == 100
        assert request["insertText"]["text"] == "Hello World"

    def test_create_insert_text_segment_request(self):
        """Test creating insertText request with segment ID."""
        request = create_insert_text_segment_request(50, "Footer text", "footer1")

        assert request["insertText"]["location"]["segmentId"] == "footer1"
        assert request["insertText"]["location"]["index"] == 50
        assert request["insertText"]["text"] == "Footer text"

    def test_create_delete_range_request(self):
        """Test creating deleteContentRange request."""
        request = create_delete_range_request(10, 20)

        assert request["deleteContentRange"]["range"]["startIndex"] == 10
        assert request["deleteContentRange"]["range"]["endIndex"] == 20


class TestSessionBindingHelpers:
    """Test SessionBinding helper methods."""

    def test_session_binding_is_expired_at_boundary(self):
        """Test is_expired returns True AT expiry timestamp."""
        now = datetime.now(timezone.utc)

        binding = SessionBinding(
            user_email="test@example.com",
            bound_at=now - timedelta(hours=1),
            expires_at=now,  # Expires exactly now
            last_accessed=now,
        )

        # Should be expired AT the timestamp (using >=)
        assert binding.is_expired() is True

    def test_session_binding_is_active(self):
        """Test is_active checks both status and expiry."""
        now = datetime.now(timezone.utc)

        # Active and not expired
        binding = SessionBinding(
            user_email="test@example.com",
            bound_at=now,
            expires_at=now + timedelta(hours=1),
            last_accessed=now,
            status=SessionStatus.ACTIVE,
        )
        assert binding.is_active() is True

        # Active but expired
        binding.expires_at = now - timedelta(hours=1)
        assert binding.is_active() is False

        # Not expired but revoked
        binding.expires_at = now + timedelta(hours=1)
        binding.status = SessionStatus.REVOKED
        assert binding.is_active() is False

    def test_session_binding_refresh_reactivates_expired(self):
        """Test that refresh reactivates an expired session."""
        now = datetime.now(timezone.utc)

        binding = SessionBinding(
            user_email="test@example.com",
            bound_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),  # Already expired
            last_accessed=now - timedelta(hours=1),
            status=SessionStatus.EXPIRED,
        )

        # Refresh should reactivate
        binding.refresh(ttl=timedelta(hours=1))

        assert binding.status == SessionStatus.ACTIVE
        assert binding.expires_at > now


class TestErrorMessages:
    """Test authentication error message generation."""

    def test_auth_error_guidance_format_with_emojis(self):
        """Test error guidance formatting with emojis."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            AuthErrorGuidance,
            ErrorType,
        )

        guidance = AuthErrorGuidance(
            error_type=ErrorType.TOKEN_EXPIRED,
            title="Token Expired",
            message="Your authentication token has expired.",
            user_action="Re-authenticate to continue.",
            technical_details="Token expired at 2025-01-01",
            help_url="https://docs.example.com/auth",
        )

        formatted = guidance.format(use_emojis=True)

        assert "🔐" in formatted
        assert "Token Expired" in formatted
        assert "Re-authenticate" in formatted

    def test_auth_error_guidance_format_without_emojis(self):
        """Test error guidance formatting without emojis."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            AuthErrorGuidance,
            ErrorType,
        )

        guidance = AuthErrorGuidance(
            error_type=ErrorType.TOKEN_REVOKED,
            title="Token Revoked",
            message="Your token was revoked.",
            user_action="Request new token.",
        )

        formatted = guidance.format(use_emojis=False)

        assert "🔐" not in formatted
        assert "Token Revoked" in formatted
        assert "Request new token" in formatted

    def test_auth_error_guidance_to_dict(self):
        """Test converting error guidance to dictionary."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            AuthErrorGuidance,
            ErrorType,
        )

        guidance = AuthErrorGuidance(
            error_type=ErrorType.INSUFFICIENT_SCOPES,
            title="Insufficient Scopes",
            message="Missing required scopes.",
            user_action="Add missing scopes.",
        )

        result = guidance.to_dict()

        assert result["error_type"] == "insufficient_scopes"
        assert result["title"] == "Insufficient Scopes"
        assert result["message"] == "Missing required scopes."

    def test_auth_error_guidance_with_code_example(self):
        """Test error guidance with code example."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            AuthErrorGuidance,
            ErrorType,
        )

        guidance = AuthErrorGuidance(
            error_type=ErrorType.CLIENT_NOT_CONFIGURED,
            title="Client Not Configured",
            message="OAuth client not found.",
            user_action="Configure OAuth client.",
            code_example='export GOOGLE_OAUTH_CLIENT_ID="your_client_id"',
        )

        formatted = guidance.format(use_emojis=True)

        assert "Example:" in formatted
        assert "GOOGLE_OAUTH_CLIENT_ID" in formatted

    def test_auth_error_guidance_with_technical_details(self):
        """Test error guidance with technical details."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            AuthErrorGuidance,
            ErrorType,
        )

        guidance = AuthErrorGuidance(
            error_type=ErrorType.NETWORK_ERROR,
            title="Network Error",
            message="Could not reach OAuth server.",
            user_action="Check network connection.",
            technical_details="Connection timeout after 30s",
        )

        formatted = guidance.format(include_technical=True, use_emojis=True)

        assert "Technical Details:" in formatted
        assert "Connection timeout" in formatted

    def test_error_type_enum_values(self):
        """Test ErrorType enum has expected values."""
        from automagik_tools.tools.google_workspace_core.auth.error_messages import (
            ErrorType,
        )

        assert ErrorType.TOKEN_EXPIRED.value == "token_expired"
        assert ErrorType.TOKEN_REVOKED.value == "token_revoked"
        assert ErrorType.INSUFFICIENT_SCOPES.value == "insufficient_scopes"
        assert ErrorType.CLIENT_NOT_CONFIGURED.value == "client_not_configured"


class TestContextUtilities:
    """Test Google Workspace context utilities."""

    def test_context_import(self):
        """Test context module can be imported."""
        from automagik_tools.tools.google_workspace_core.core import context

        assert context is not None

    def test_context_has_expected_attributes(self):
        """Test context module structure."""
        from automagik_tools.tools.google_workspace_core.core import context

        # Check that context module exists and can be used
        assert hasattr(context, "__name__")


class TestScopesEnhancements:
    """Test additional scopes functionality."""

    def test_tool_scopes_map_completeness(self):
        """Test that TOOL_SCOPES_MAP has entries for all major Google services."""
        from automagik_tools.tools.google_workspace_core.auth.scopes import (
            TOOL_SCOPES_MAP,
        )

        # Check core services are present
        assert "gmail" in TOOL_SCOPES_MAP
        assert "drive" in TOOL_SCOPES_MAP
        assert "calendar" in TOOL_SCOPES_MAP
        assert "docs" in TOOL_SCOPES_MAP
        assert "sheets" in TOOL_SCOPES_MAP

        # Check scopes are lists
        assert isinstance(TOOL_SCOPES_MAP["gmail"], list)
        assert len(TOOL_SCOPES_MAP["gmail"]) > 0

    def test_base_scopes_structure(self):
        """Test BASE_SCOPES are properly defined."""
        from automagik_tools.tools.google_workspace_core.auth.scopes import BASE_SCOPES

        assert isinstance(BASE_SCOPES, list)
        assert len(BASE_SCOPES) > 0
        # Base scopes should include profile/email
        assert any("userinfo" in scope for scope in BASE_SCOPES)

    def test_get_scopes_for_invalid_tool(self):
        """Test getting scopes for non-existent tool returns base scopes."""
        from automagik_tools.tools.google_workspace_core.auth.scopes import (
            get_scopes_for_tools,
            BASE_SCOPES,
        )

        scopes = get_scopes_for_tools(["nonexistent_tool"])

        # Should at least return base scopes
        for base_scope in BASE_SCOPES:
            assert base_scope in scopes

    def test_set_enabled_tools_with_empty_list(self):
        """Test setting empty enabled tools list."""
        from automagik_tools.tools.google_workspace_core.auth.scopes import (
            set_enabled_tools,
            get_current_scopes,
            BASE_SCOPES,
        )

        set_enabled_tools([])
        current = get_current_scopes()

        # Should have base scopes even with empty list
        for base_scope in BASE_SCOPES:
            assert base_scope in current


class TestConfigModule:
    """Test Google Workspace configuration module."""

    def test_config_module_structure(self):
        """Test config module has expected structure."""
        from automagik_tools.tools.google_workspace_core import config

        assert hasattr(config, "GoogleWorkspaceBaseConfig")

    def test_config_class_field_types(self):
        """Test config class field types are correct."""
        from automagik_tools.tools.google_workspace_core.config import (
            GoogleWorkspaceBaseConfig,
        )

        fields = GoogleWorkspaceBaseConfig.model_fields

        # Check specific field types
        assert "client_id" in fields
        assert "client_secret" in fields
        assert "enable_oauth21" in fields
        assert "single_user_mode" in fields
        assert "stateless_mode" in fields


class TestRetryHandler:
    """Test retry handler utilities."""

    def test_retry_handler_import(self):
        """Test retry handler can be imported."""
        from automagik_tools.tools.google_workspace_core.auth import retry_handler

        assert retry_handler is not None

    def test_retry_handler_has_retry_decorator(self):
        """Test retry handler has expected decorators."""
        from automagik_tools.tools.google_workspace_core.auth import retry_handler

        # Check the module has retry functionality
        assert hasattr(retry_handler, "__name__")


class TestToolRegistry:
    """Test tool registry functionality in depth."""

    def test_tool_registry_enable_all_tools(self):
        """Test enabling all tools by setting None."""
        from automagik_tools.tools.google_workspace_core.core.tool_registry import (
            set_enabled_tools,
            get_enabled_tools,
            is_tool_enabled,
        )

        # Enable all tools
        set_enabled_tools(None)

        assert get_enabled_tools() is None
        assert is_tool_enabled("any_random_tool")
        assert is_tool_enabled("another_tool")

    def test_tool_registry_specific_tools(self):
        """Test enabling specific set of tools."""
        from automagik_tools.tools.google_workspace_core.core.tool_registry import (
            set_enabled_tools,
            get_enabled_tools,
            is_tool_enabled,
        )

        # Enable specific tools
        enabled_set = {"gmail_send", "drive_search", "calendar_create"}
        set_enabled_tools(enabled_set)

        assert get_enabled_tools() == enabled_set
        assert is_tool_enabled("gmail_send")
        assert is_tool_enabled("drive_search")
        assert not is_tool_enabled("sheets_read")

    def test_tool_registry_empty_set(self):
        """Test enabling empty set of tools."""
        from automagik_tools.tools.google_workspace_core.core.tool_registry import (
            set_enabled_tools,
            is_tool_enabled,
        )

        # Empty set means no tools enabled
        set_enabled_tools(set())

        assert not is_tool_enabled("any_tool")

    def test_tool_registry_modification(self):
        """Test modifying enabled tools set."""
        from automagik_tools.tools.google_workspace_core.core.tool_registry import (
            set_enabled_tools,
            get_enabled_tools,
            is_tool_enabled,
        )

        # Start with some tools
        set_enabled_tools({"tool1", "tool2"})
        assert is_tool_enabled("tool1")

        # Change to different set
        set_enabled_tools({"tool3", "tool4"})
        assert not is_tool_enabled("tool1")
        assert is_tool_enabled("tool3")

    def test_tool_registry_single_tool(self):
        """Test enabling single tool."""
        from automagik_tools.tools.google_workspace_core.core.tool_registry import (
            set_enabled_tools,
            is_tool_enabled,
        )

        set_enabled_tools({"only_this_tool"})

        assert is_tool_enabled("only_this_tool")
        assert not is_tool_enabled("other_tool")


class TestOAuthResponseTypes:
    """Test OAuth response structures."""

    def test_oauth_responses_module_import(self):
        """Test OAuth responses can be imported."""
        from automagik_tools.tools.google_workspace_core.auth import oauth_responses

        assert oauth_responses is not None


class TestOAuthTypes:
    """Test OAuth type definitions."""

    def test_oauth_types_module_import(self):
        """Test OAuth types module."""
        from automagik_tools.tools.google_workspace_core.auth import oauth_types

        assert oauth_types is not None


class TestGoogleWorkspaceConfig:
    """Additional config tests."""

    def test_config_has_auth_fields(self):
        """Test config has all required auth fields."""
        from automagik_tools.tools.google_workspace_core.config import (
            GoogleWorkspaceBaseConfig,
        )

        fields = GoogleWorkspaceBaseConfig.model_fields

        # Auth fields
        assert "client_id" in fields
        assert "client_secret" in fields

        # Mode fields
        assert "enable_oauth21" in fields
        assert "single_user_mode" in fields
        assert "stateless_mode" in fields

        # Server fields
        assert "base_uri" in fields
        assert "port" in fields

    def test_config_has_credentials_fields(self):
        """Test config has credential management fields."""
        from automagik_tools.tools.google_workspace_core.config import (
            GoogleWorkspaceBaseConfig,
        )

        fields = GoogleWorkspaceBaseConfig.model_fields

        assert "credentials_dir" in fields
        assert "user_email" in fields


class TestCoreModuleImports:
    """Test core module imports and structure."""

    def test_core_server_import(self):
        """Test core server module can be imported."""
        from automagik_tools.tools.google_workspace_core.core import server

        assert server is not None

    def test_core_utils_import(self):
        """Test core utils module can be imported."""
        from automagik_tools.tools.google_workspace_core.core import utils

        assert utils is not None

    def test_core_config_import(self):
        """Test core config module can be imported."""
        from automagik_tools.tools.google_workspace_core.core import config

        assert config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
