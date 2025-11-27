"""
Database-backed Credential Store for Google Workspace MCP.
Adapts the existing CredentialStore interface to use the Hub's OAuthToken table.
"""
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from sqlalchemy import select, delete

from automagik_tools.hub.auth.google.credential_store import CredentialStore
from automagik_tools.hub.database import get_db_session_sync, get_db_session
from automagik_tools.hub.models import OAuthToken

logger = logging.getLogger(__name__)

class DatabaseCredentialStore(CredentialStore):
    """Credential store that uses the Hub's database (OAuthToken table)."""

    def __init__(self, user_id_map: Optional[dict] = None):
        """
        Initialize the database credential store.
        
        Args:
            user_id_map: Optional mapping of email -> user_id. 
                        If not provided, we might need a way to resolve user_id from email 
                        or assume email IS the user identifier for legacy compatibility.
        """
        self.user_id_map = user_id_map or {}
        logger.info("DatabaseCredentialStore initialized")

    def _get_user_id(self, user_email: str) -> str:
        """
        Resolve user_email to user_id.
        For now, we'll assume the user_email IS the user_id if not found in map,
        or we need to look it up in the Users table.
        
        TODO: robust user lookup.
        """
        return self.user_id_map.get(user_email, user_email)

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from database."""
        # Note: This method is synchronous in the interface, but our DB is async.
        # We need a sync wrapper or the interface needs to be async.
        # Existing google_auth.py calls this synchronously.
        # We'll use a sync session wrapper if available, or run_until_complete.
        
        # For simplicity in this adaptation, we'll use a sync-compatible approach 
        # or rely on the fact that we might be running in an async context where we can't block.
        # However, `google_auth.py` calls this in sync functions.
        # We will use `get_db_session_sync` (which we need to implement or simulate).
        
        # CRITICAL: The existing `database.py` is async only. 
        # We must bridge this. For now, we'll use a hacky `asyncio.run` wrapper 
        # if there's no running loop, or error if there is.
        # BUT `google_auth.py` functions are often async (e.g. handle_auth_callback is NOT async? Wait, let me check).
        
        # Checked google_auth.py: handle_auth_callback IS NOT async def.
        # Wait, `handle_auth_callback` in `google_auth.py` line 428 is `def`, not `async def`.
        # So we need synchronous DB access.
        
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We are in an async loop but called synchronously. 
            # Use the synchronous implementation.
            return self._get_credential_sync(user_email)
        
        return asyncio.run(self._get_credential_async(user_email))

    def _get_credential_sync(self, user_email: str) -> Optional[Credentials]:
        """Synchronous implementation using get_db_session_sync."""
        from automagik_tools.hub.database import get_db_session_sync
        
        user_id = self._get_user_id(user_email)
        session = get_db_session_sync()
        try:
            result = session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google"
                )
            )
            token_row = result.scalar_one_or_none()
            
            if not token_row:
                return None
            
            try:
                creds_data = json.loads(token_row.access_token)
                expiry = None
                if creds_data.get("expiry"):
                    try:
                        expiry = datetime.fromisoformat(creds_data["expiry"])
                        if expiry.tzinfo is not None:
                            expiry = expiry.replace(tzinfo=None)
                    except (ValueError, TypeError):
                        pass

                return Credentials(
                    token=creds_data.get("token"),
                    refresh_token=creds_data.get("refresh_token"),
                    token_uri=creds_data.get("token_uri"),
                    client_id=creds_data.get("client_id"),
                    client_secret=creds_data.get("client_secret"),
                    scopes=creds_data.get("scopes"),
                    expiry=expiry,
                )
            except Exception as e:
                logger.error(f"Error parsing credentials for {user_email}: {e}")
                return None
        finally:
            session.close()

    async def _get_credential_async(self, user_email: str) -> Optional[Credentials]:
        user_id = self._get_user_id(user_email)
        async with get_db_session() as session:
            result = await session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google" # Assuming google provider
                )
            )
            token_row = result.scalar_one_or_none()
            
            if not token_row:
                return None
            
            try:
                # Parse JSON stored in access_token (if we stored full dict) or reconstruct
                # For this implementation, let's assume we store the full credentials dict in access_token
                # to match LocalDirectoryCredentialStore's behavior of storing full JSON.
                creds_data = json.loads(token_row.access_token)
                
                expiry = None
                if creds_data.get("expiry"):
                    try:
                        expiry = datetime.fromisoformat(creds_data["expiry"])
                        if expiry.tzinfo is not None:
                            expiry = expiry.replace(tzinfo=None)
                    except (ValueError, TypeError):
                        pass

                return Credentials(
                    token=creds_data.get("token"),
                    refresh_token=creds_data.get("refresh_token"),
                    token_uri=creds_data.get("token_uri"),
                    client_id=creds_data.get("client_id"),
                    client_secret=creds_data.get("client_secret"),
                    scopes=creds_data.get("scopes"),
                    expiry=expiry,
                )
            except Exception as e:
                logger.error(f"Error parsing credentials for {user_email}: {e}")
                return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to database."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We are in an async loop, so we cannot use asyncio.run()
            # We must use the synchronous session wrapper we created
            return self._store_credential_sync(user_email, credentials)
        else:
            return asyncio.run(self._store_credential_async(user_email, credentials))

    def _store_credential_sync(self, user_email: str, credentials: Credentials) -> bool:
        """Synchronous implementation using get_db_session_sync."""
        from automagik_tools.hub.database import get_db_session_sync
        
        user_id = self._get_user_id(user_email)
        
        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        creds_json = json.dumps(creds_data)
        
        session = get_db_session_sync()
        try:
            # Check if exists
            existing = session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google"
                )
            ).scalar_one_or_none()
            
            if existing:
                existing.access_token = creds_json
                existing.refresh_token = credentials.refresh_token
                existing.updated_at = datetime.now(timezone.utc)
            else:
                import uuid
                new_token = OAuthToken(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tool_name="google_workspace",
                    provider="google",
                    access_token=creds_json,
                    refresh_token=credentials.refresh_token
                )
                session.add(new_token)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Sync store_credential failed: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def _store_credential_async(self, user_email: str, credentials: Credentials) -> bool:
        user_id = self._get_user_id(user_email)
        
        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        
        # Store as JSON string in access_token field for now to preserve structure
        # In a stricter schema, we'd map fields individually
        creds_json = json.dumps(creds_data)
        
        async with get_db_session() as session:
            # Check if exists
            result = await session.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google"
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.access_token = creds_json
                existing.refresh_token = credentials.refresh_token
                existing.updated_at = datetime.now(timezone.utc)
            else:
                import uuid
                new_token = OAuthToken(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tool_name="google_workspace", # Generic name for the suite
                    provider="google",
                    access_token=creds_json,
                    refresh_token=credentials.refresh_token
                )
                session.add(new_token)
            
            await session.commit()
            return True

    def delete_credential(self, user_email: str) -> bool:
        """Delete credential from database."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self._delete_credential_sync(user_email)
            
        try:
            return asyncio.run(self._delete_credential_async(user_email))
        except Exception:
            return False

    def _delete_credential_sync(self, user_email: str) -> bool:
        from automagik_tools.hub.database import get_db_session_sync
        user_id = self._get_user_id(user_email)
        session = get_db_session_sync()
        try:
            session.execute(
                delete(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google"
                )
            )
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    async def _delete_credential_async(self, user_email: str) -> bool:
        user_id = self._get_user_id(user_email)
        async with get_db_session() as session:
            await session.execute(
                delete(OAuthToken).where(
                    OAuthToken.user_id == user_id,
                    OAuthToken.provider == "google"
                )
            )
            await session.commit()
            return True

    def list_users(self) -> List[str]:
        """List all users with google credentials."""
        import asyncio
        try:
            return asyncio.run(self._list_users_async())
        except Exception:
            return []

    async def _list_users_async(self) -> List[str]:
        async with get_db_session() as session:
            result = await session.execute(
                select(OAuthToken.user_id).where(OAuthToken.provider == "google")
            )
            return list(result.scalars().all())
