"""
FastMCP-compatible token storage adapter for OAuth credentials.

Provides a unified interface for managing OAuth tokens across different storage backends
(file-based, in-memory, database, etc.) inspired by FastMCP's TokenStorageAdapter pattern.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    """
    Standardized OAuth token structure.

    Compatible with both OAuth 2.0 and OAuth 2.1 token formats.
    """

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scopes: Optional[List[str]] = None
    id_token: Optional[str] = None  # For OpenID Connect

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (has access token and not expired)"""
        return bool(self.access_token) and not self.is_expired()


@dataclass
class OAuthClientInfo:
    """OAuth client credentials and configuration"""

    client_id: str
    client_secret: str
    redirect_uris: List[str]
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"


class TokenStorageAdapter(ABC):
    """
    Abstract interface for OAuth token storage.

    Inspired by FastMCP's TokenStorageAdapter, this provides a consistent
    interface for storing and retrieving OAuth tokens across different backends.

    Implementations must be thread-safe for production use.
    """

    @abstractmethod
    def get_tokens(self, user_id: str) -> Optional[OAuthToken]:
        """
        Retrieve tokens for a user.

        Args:
            user_id: Unique identifier for the user (typically email)

        Returns:
            OAuthToken if found and valid, None otherwise
        """
        pass

    @abstractmethod
    def set_tokens(self, user_id: str, tokens: OAuthToken) -> None:
        """
        Store tokens for a user.

        Args:
            user_id: Unique identifier for the user
            tokens: OAuth tokens to store
        """
        pass

    @abstractmethod
    def clear_tokens(self, user_id: str) -> bool:
        """
        Remove tokens for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if tokens existed and were removed, False otherwise
        """
        pass

    @abstractmethod
    def get_client_info(self) -> Optional[OAuthClientInfo]:
        """
        Get OAuth client credentials.

        Returns:
            OAuthClientInfo if configured, None otherwise
        """
        pass

    @abstractmethod
    def set_client_info(self, client_info: OAuthClientInfo) -> None:
        """
        Store OAuth client credentials.

        Args:
            client_info: OAuth client configuration
        """
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        """
        List all users with stored tokens.

        Returns:
            List of user IDs with stored credentials
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired tokens.

        Returns:
            Number of expired tokens removed
        """
        pass

    def has_valid_tokens(self, user_id: str) -> bool:
        """
        Check if user has valid (non-expired) tokens.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if valid tokens exist, False otherwise
        """
        tokens = self.get_tokens(user_id)
        return tokens is not None and tokens.is_valid()


class FileTokenStorageAdapter(TokenStorageAdapter):
    """
    File-based implementation of TokenStorageAdapter.

    Adapts the existing LocalDirectoryCredentialStore to the new interface
    while maintaining backward compatibility.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize file-based token storage.

        Args:
            base_dir: Base directory for credential storage.
                     Defaults to ~/.google_workspace_mcp/credentials/
        """
        from .credential_store import LocalDirectoryCredentialStore

        self._store = LocalDirectoryCredentialStore(base_dir)
        self._client_info: Optional[OAuthClientInfo] = None
        logger.debug(
            f"Initialized FileTokenStorageAdapter with base_dir: {self._store.base_dir}"
        )

    def get_tokens(self, user_id: str) -> Optional[OAuthToken]:
        """Load credentials from file and convert to OAuthToken"""
        try:
            creds = self._store.get_credential(user_id)
            if not creds:
                logger.debug(f"No credentials found for user: {user_id}")
                return None

            token = OAuthToken(
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                token_type="Bearer",
                expires_at=creds.expiry,
                scopes=list(creds.scopes) if creds.scopes else None,
            )

            logger.debug(
                f"Loaded tokens for {user_id}, expires: {token.expires_at}, valid: {token.is_valid()}"
            )
            return token

        except Exception as e:
            logger.error(f"Error loading tokens for {user_id}: {e}")
            return None

    def set_tokens(self, user_id: str, tokens: OAuthToken) -> None:
        """Convert OAuthToken to Credentials and save to file"""
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self._client_info.client_id if self._client_info else None,
                client_secret=(
                    self._client_info.client_secret if self._client_info else None
                ),
                scopes=tokens.scopes,
            )

            # Set expiry if provided
            if tokens.expires_at:
                creds.expiry = tokens.expires_at

            self._store.store_credential(user_id, creds)
            logger.info(f"Saved tokens for {user_id}")

        except Exception as e:
            logger.error(f"Error saving tokens for {user_id}: {e}")
            raise

    def clear_tokens(self, user_id: str) -> bool:
        """Remove credential file for user"""
        try:
            # Use the store's delete_credential method
            result = self._store.delete_credential(user_id)
            if result:
                logger.info(f"Cleared credentials for {user_id}")
            else:
                logger.debug(f"No credentials to clear for {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error clearing tokens for {user_id}: {e}")
            return False

    def get_client_info(self) -> Optional[OAuthClientInfo]:
        """Get stored client info (from memory or config)"""
        if self._client_info:
            return self._client_info

        # Try to load from config
        try:
            from .oauth_config import get_oauth_config

            config = get_oauth_config()
            if config.is_configured():
                self._client_info = OAuthClientInfo(
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    redirect_uris=[config.redirect_uri],
                    auth_uri="https://accounts.google.com/o/oauth2/auth",
                    token_uri="https://oauth2.googleapis.com/token",
                )
                return self._client_info

        except Exception as e:
            logger.error(f"Error loading client info from config: {e}")

        return None

    def set_client_info(self, client_info: OAuthClientInfo) -> None:
        """Store client info in memory"""
        self._client_info = client_info
        logger.info("Stored OAuth client info")

    def list_users(self) -> List[str]:
        """List all users with credential files"""
        try:
            # Delegate to the store's list_users method
            users = self._store.list_users()
            logger.debug(f"Found {len(users)} users with stored credentials")
            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def cleanup_expired(self) -> int:
        """Remove expired credential files"""
        try:
            users = self.list_users()
            expired_count = 0

            for user_id in users:
                tokens = self.get_tokens(user_id)
                if tokens and tokens.is_expired():
                    if self.clear_tokens(user_id):
                        expired_count += 1

            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired credential files")

            return expired_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0


class MemoryTokenStorageAdapter(TokenStorageAdapter):
    """
    In-memory implementation for stateless mode.

    Adapts OAuth21SessionStore to the TokenStorageAdapter interface.
    Tokens are stored only in memory and lost on server restart.
    """

    def __init__(self):
        """Initialize in-memory token storage"""
        from .oauth21_session_store import get_oauth21_session_store

        self._store = get_oauth21_session_store()
        self._client_info: Optional[OAuthClientInfo] = None
        logger.debug("Initialized MemoryTokenStorageAdapter")

    def get_tokens(self, user_id: str) -> Optional[OAuthToken]:
        """Get tokens from session store"""
        try:
            creds = self._store.get_credentials_for_user(user_id)
            if not creds:
                return None

            return OAuthToken(
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                token_type="Bearer",
                expires_at=creds.expiry,
                scopes=list(creds.scopes) if creds.scopes else None,
            )

        except Exception as e:
            logger.error(f"Error getting tokens from memory for {user_id}: {e}")
            return None

    def set_tokens(self, user_id: str, tokens: OAuthToken) -> None:
        """Store tokens in session store"""
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self._client_info.client_id if self._client_info else None,
                client_secret=(
                    self._client_info.client_secret if self._client_info else None
                ),
                scopes=tokens.scopes,
            )

            if tokens.expires_at:
                creds.expiry = tokens.expires_at

            # Store in OAuth21SessionStore
            # Note: We need a session_id for binding, using user_id as session_id for stateless mode
            self._store.store_credentials(user_id, creds, user_id)
            logger.info(f"Stored tokens in memory for {user_id}")

        except Exception as e:
            logger.error(f"Error storing tokens in memory for {user_id}: {e}")
            raise

    def clear_tokens(self, user_id: str) -> bool:
        """Remove tokens from memory"""
        try:
            # Clear from session store
            self._store.clear_credentials_for_user(user_id)
            logger.info(f"Cleared tokens from memory for {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing tokens from memory for {user_id}: {e}")
            return False

    def get_client_info(self) -> Optional[OAuthClientInfo]:
        """Get client info from config"""
        if self._client_info:
            return self._client_info

        try:
            from .oauth_config import get_oauth_config

            config = get_oauth_config()
            if config.is_configured():
                self._client_info = OAuthClientInfo(
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    redirect_uris=[config.redirect_uri],
                )
                return self._client_info

        except Exception as e:
            logger.error(f"Error loading client info: {e}")

        return None

    def set_client_info(self, client_info: OAuthClientInfo) -> None:
        """Store client info in memory"""
        self._client_info = client_info

    def list_users(self) -> List[str]:
        """List all users from session store"""
        try:
            # Get all users with stored credentials
            users = []
            # Note: OAuth21SessionStore doesn't have a direct list method,
            # we'll need to access internal storage
            if hasattr(self._store, "_credentials_by_user"):
                users = list(self._store._credentials_by_user.keys())

            return users

        except Exception as e:
            logger.error(f"Error listing users from memory: {e}")
            return []

    def cleanup_expired(self) -> int:
        """Remove expired tokens from memory"""
        try:
            users = self.list_users()
            expired_count = 0

            for user_id in users:
                tokens = self.get_tokens(user_id)
                if tokens and tokens.is_expired():
                    if self.clear_tokens(user_id):
                        expired_count += 1

            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired tokens from memory")

            return expired_count

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return 0


def get_token_storage_adapter(stateless: Optional[bool] = None) -> TokenStorageAdapter:
    """
    Factory function to get the appropriate token storage adapter.

    Args:
        stateless: If True, use in-memory storage. If False, use file-based storage.
                  If None (default), reads from WORKSPACE_MCP_STATELESS_MODE config.

    Returns:
        TokenStorageAdapter implementation
    """
    if stateless is None:
        from .oauth_config import is_stateless_mode

        stateless = is_stateless_mode()
        logger.debug(
            f"Stateless mode not specified, using config value: {stateless}"
        )

    if stateless:
        logger.info("Using MemoryTokenStorageAdapter (stateless mode)")
        return MemoryTokenStorageAdapter()
    else:
        logger.info("Using FileTokenStorageAdapter (stateful mode)")
        return FileTokenStorageAdapter()
