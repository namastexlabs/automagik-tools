"""
Session manager with automatic expiry and cleanup for OAuth sessions.

Prevents memory leaks from unlimited session bindings and provides
automatic cleanup of expired sessions with LRU eviction.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import threading
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of a session binding"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class SessionBinding:
    """
    Session-to-user binding with expiry and usage tracking.

    Tracks when a session was created, last accessed, and when it expires.
    """

    user_email: str
    bound_at: datetime
    expires_at: datetime
    last_accessed: datetime
    access_count: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, any] = None  # Additional session data

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() >= self.expires_at

    def is_active(self) -> bool:
        """Check if session is active (not expired and not revoked)"""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    def refresh(self, ttl: Optional[timedelta] = None) -> None:
        """
        Refresh session expiry.

        Args:
            ttl: New TTL for the session. If None, uses default from manager.
        """
        if ttl:
            self.expires_at = datetime.utcnow() + ttl
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

        # Reactivate if was previously expired
        if self.status == SessionStatus.EXPIRED:
            self.status = SessionStatus.ACTIVE


class SessionManager:
    """
    Manages session bindings with automatic expiry and cleanup.

    Features:
    - TTL-based expiry (default: 24 hours)
    - LRU cleanup when max sessions reached
    - Background cleanup thread
    - Thread-safe operations
    - Session refresh on access
    - Statistics and monitoring
    """

    def __init__(
        self,
        default_ttl: timedelta = timedelta(hours=24),
        max_sessions: int = 1000,
        cleanup_interval: timedelta = timedelta(hours=1),
        auto_refresh: bool = True,
    ):
        """
        Initialize session manager.

        Args:
            default_ttl: Default time-to-live for sessions
            max_sessions: Maximum number of concurrent sessions
            cleanup_interval: How often to run background cleanup
            auto_refresh: Automatically refresh session TTL on access
        """
        self._bindings: Dict[str, SessionBinding] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._max_sessions = max_sessions
        self._cleanup_interval = cleanup_interval
        self._auto_refresh = auto_refresh
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

        logger.info(
            f"Initialized SessionManager: ttl={default_ttl}, max_sessions={max_sessions}, "
            f"cleanup_interval={cleanup_interval}, auto_refresh={auto_refresh}"
        )

    def bind_session(
        self,
        session_id: str,
        user_email: str,
        ttl: Optional[timedelta] = None,
        metadata: Optional[Dict] = None,
        allow_rebind: bool = False,
    ) -> bool:
        """
        Bind session to user with expiry.

        Args:
            session_id: Unique session identifier
            user_email: Email of the authenticated user
            ttl: Custom TTL for this session (uses default if None)
            metadata: Additional session metadata
            allow_rebind: Allow rebinding if session exists (default: False)

        Returns:
            True if binding created/updated, False if session already bound to different user
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

                    # Refresh if expired
                    if binding.is_expired():
                        binding.refresh(ttl or self._default_ttl)
                        logger.info(f"Refreshed expired session {session_id}")

                    return True

                # Different user
                if not allow_rebind:
                    logger.warning(
                        f"Session {session_id} already bound to {binding.user_email}, "
                        f"cannot bind to {user_email}"
                    )
                    return False

                # Rebind to new user
                logger.info(
                    f"Rebinding session {session_id} from {binding.user_email} to {user_email}"
                )

            # Cleanup if max sessions reached
            if len(self._bindings) >= self._max_sessions:
                self._cleanup_lru(count=100)
                logger.info(
                    f"Reached max sessions ({self._max_sessions}), cleaned up LRU entries"
                )

            # Create new binding
            now = datetime.utcnow()
            ttl = ttl or self._default_ttl

            self._bindings[session_id] = SessionBinding(
                user_email=user_email,
                bound_at=now,
                expires_at=now + ttl,
                last_accessed=now,
                access_count=1,
                status=SessionStatus.ACTIVE,
                metadata=metadata or {},
            )

            logger.info(
                f"Bound session {session_id} to {user_email}, expires at {now + ttl}"
            )
            return True

    def get_user_email(self, session_id: str) -> Optional[str]:
        """
        Get user email for session.

        Args:
            session_id: Session identifier

        Returns:
            User email if session active, None if expired/not found
        """
        with self._lock:
            binding = self._bindings.get(session_id)
            if not binding:
                return None

            # Check expiry
            now = datetime.utcnow()
            if now >= binding.expires_at:
                logger.debug(f"Session {session_id} expired at {binding.expires_at}")
                binding.status = SessionStatus.EXPIRED
                return None

            # Auto-refresh if enabled
            if self._auto_refresh:
                binding.last_accessed = now
                binding.access_count += 1

            return binding.user_email

    def get_binding(self, session_id: str) -> Optional[SessionBinding]:
        """
        Get full session binding.

        Args:
            session_id: Session identifier

        Returns:
            SessionBinding if found, None otherwise
        """
        with self._lock:
            return self._bindings.get(session_id)

    def unbind_session(self, session_id: str) -> bool:
        """
        Unbind session.

        Args:
            session_id: Session identifier

        Returns:
            True if session existed and was removed, False otherwise
        """
        with self._lock:
            if session_id in self._bindings:
                binding = self._bindings[session_id]
                user_email = binding.user_email
                del self._bindings[session_id]
                logger.info(f"Unbound session {session_id} from {user_email}")
                return True

            logger.debug(f"Session {session_id} not found for unbinding")
            return False

    def revoke_session(self, session_id: str) -> bool:
        """
        Revoke session (mark as revoked without removing).

        Args:
            session_id: Session identifier

        Returns:
            True if session existed and was revoked, False otherwise
        """
        with self._lock:
            if session_id in self._bindings:
                binding = self._bindings[session_id]
                binding.status = SessionStatus.REVOKED
                logger.info(f"Revoked session {session_id} for {binding.user_email}")
                return True

            return False

    def refresh_session(self, session_id: str, ttl: Optional[timedelta] = None) -> bool:
        """
        Refresh session expiry.

        Args:
            session_id: Session identifier
            ttl: New TTL (uses default if None)

        Returns:
            True if session was refreshed, False if not found
        """
        with self._lock:
            binding = self._bindings.get(session_id)
            if not binding:
                return False

            binding.refresh(ttl or self._default_ttl)
            logger.debug(
                f"Refreshed session {session_id}, new expiry: {binding.expires_at}"
            )
            return True

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of expired sessions removed
        """
        with self._lock:
            now = datetime.utcnow()
            expired = [
                sid
                for sid, binding in self._bindings.items()
                if now >= binding.expires_at
            ]

            for sid in expired:
                binding = self._bindings[sid]
                binding.status = SessionStatus.EXPIRED
                del self._bindings[sid]

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

            return len(expired)

    def cleanup_revoked(self) -> int:
        """
        Remove revoked sessions.

        Returns:
            Number of revoked sessions removed
        """
        with self._lock:
            revoked = [
                sid
                for sid, binding in self._bindings.items()
                if binding.status == SessionStatus.REVOKED
            ]

            for sid in revoked:
                del self._bindings[sid]

            if revoked:
                logger.info(f"Cleaned up {len(revoked)} revoked sessions")

            return len(revoked)

    def _cleanup_lru(self, count: int = 100) -> int:
        """
        Remove least recently used sessions.

        Args:
            count: Number of sessions to remove

        Returns:
            Number of sessions actually removed
        """
        # Sort by last accessed time (oldest first)
        sorted_sessions = sorted(
            self._bindings.items(), key=lambda x: x[1].last_accessed
        )

        # Remove oldest (up to count)
        removed = 0
        for sid, binding in sorted_sessions[:count]:
            del self._bindings[sid]
            removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} LRU sessions")

        return removed

    def start_background_cleanup(self) -> None:
        """Start background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            logger.warning("Background cleanup already running")
            return

        def cleanup_loop():
            logger.info("Starting background session cleanup loop")

            while not self._stop_cleanup.wait(self._cleanup_interval.total_seconds()):
                try:
                    expired_count = self.cleanup_expired()
                    revoked_count = self.cleanup_revoked()

                    if expired_count > 0 or revoked_count > 0:
                        logger.debug(
                            f"Background cleanup: {expired_count} expired, {revoked_count} revoked"
                        )

                    # Log stats periodically
                    stats = self.get_stats()
                    if stats["total_sessions"] > 0:
                        logger.debug(f"Session stats: {stats}")

                except Exception as e:
                    logger.error(f"Error in background cleanup: {e}", exc_info=True)

            logger.info("Background session cleanup loop stopped")

        self._cleanup_thread = threading.Thread(
            target=cleanup_loop, daemon=True, name="SessionCleanup"
        )
        self._cleanup_thread.start()
        logger.info(
            f"Started background session cleanup thread (interval: {self._cleanup_interval})"
        )

    def stop_background_cleanup(self) -> None:
        """Stop background cleanup thread"""
        if not self._cleanup_thread:
            logger.debug("No cleanup thread to stop")
            return

        logger.info("Stopping background session cleanup...")
        self._stop_cleanup.set()

        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

            if self._cleanup_thread.is_alive():
                logger.warning("Cleanup thread did not stop within timeout")
            else:
                logger.info("Background session cleanup stopped successfully")

        self._cleanup_thread = None
        self._stop_cleanup.clear()

    def get_stats(self) -> Dict[str, any]:
        """
        Get session statistics.

        Returns:
            Dictionary with session metrics
        """
        with self._lock:
            now = datetime.utcnow()

            active = 0
            expired = 0
            revoked = 0
            users = set()

            for binding in self._bindings.values():
                users.add(binding.user_email)

                if binding.status == SessionStatus.REVOKED:
                    revoked += 1
                elif now >= binding.expires_at:
                    expired += 1
                else:
                    active += 1

            return {
                "total_sessions": len(self._bindings),
                "active_sessions": active,
                "expired_sessions": expired,
                "revoked_sessions": revoked,
                "unique_users": len(users),
                "max_sessions": self._max_sessions,
                "default_ttl_hours": self._default_ttl.total_seconds() / 3600,
                "auto_refresh": self._auto_refresh,
            }

    def get_sessions_for_user(self, user_email: str) -> List[str]:
        """
        Get all session IDs for a user.

        Args:
            user_email: User email to search for

        Returns:
            List of session IDs bound to this user
        """
        with self._lock:
            return [
                sid
                for sid, binding in self._bindings.items()
                if binding.user_email == user_email
            ]

    def unbind_all_for_user(self, user_email: str) -> int:
        """
        Unbind all sessions for a user.

        Args:
            user_email: User email

        Returns:
            Number of sessions unbound
        """
        with self._lock:
            sessions = self.get_sessions_for_user(user_email)

            for sid in sessions:
                del self._bindings[sid]

            if sessions:
                logger.info(f"Unbound {len(sessions)} sessions for {user_email}")

            return len(sessions)

    def clear_all(self) -> int:
        """
        Clear all sessions.

        Returns:
            Number of sessions cleared
        """
        with self._lock:
            count = len(self._bindings)
            self._bindings.clear()

            if count > 0:
                logger.warning(f"Cleared all {count} sessions")

            return count


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None
_manager_lock = threading.Lock()


def get_session_manager(
    default_ttl: timedelta = timedelta(hours=24),
    max_sessions: int = 1000,
    cleanup_interval: timedelta = timedelta(hours=1),
    auto_refresh: bool = True,
) -> SessionManager:
    """
    Get the global session manager instance (singleton).

    Args:
        default_ttl: Default session TTL
        max_sessions: Maximum concurrent sessions
        cleanup_interval: Background cleanup interval
        auto_refresh: Auto-refresh sessions on access

    Returns:
        Global SessionManager instance
    """
    global _global_session_manager

    if _global_session_manager is None:
        with _manager_lock:
            if _global_session_manager is None:
                _global_session_manager = SessionManager(
                    default_ttl=default_ttl,
                    max_sessions=max_sessions,
                    cleanup_interval=cleanup_interval,
                    auto_refresh=auto_refresh,
                )

                # Start background cleanup
                _global_session_manager.start_background_cleanup()

    return _global_session_manager


def reset_session_manager() -> None:
    """
    Reset the global session manager.

    Useful for testing or reconfiguration.
    """
    global _global_session_manager

    with _manager_lock:
        if _global_session_manager:
            _global_session_manager.stop_background_cleanup()
            _global_session_manager = None

        logger.info("Reset global session manager")
