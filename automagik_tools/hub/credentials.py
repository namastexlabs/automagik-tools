"""Credential management tools for handling user secrets and OAuth tokens."""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import Context
from sqlalchemy import select, delete
from .database import get_db_session
from .models import OAuthToken


async def store_credential(
    tool_name: str,
    provider: str,
    secrets: Dict[str, Any],
    ctx: Context
) -> str:
    """
    Store encrypted credentials for a specific tool and provider.
    
    Args:
        tool_name: Name of the tool (e.g., 'google_calendar')
        provider: Provider name (e.g., 'google', 'github', 'api_key')
        secrets: Dictionary containing secrets (e.g., {'access_token': '...', 'refresh_token': '...'})
        ctx: FastMCP context (provides user_id)
        
    Returns:
        Success message
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")

    # In a real implementation, we would encrypt these values before storing
    # For now, we'll store them as JSON strings, but the model field is named 'access_token' (Text)
    # We'll map the 'secrets' dict to the model fields
    
    access_token = json.dumps(secrets) # Storing the whole dict for flexibility if it's not just a token
    refresh_token = secrets.get("refresh_token")
    
    # If secrets has specific fields, use them, otherwise dump the whole thing
    if "access_token" in secrets:
        access_token = secrets["access_token"]
    
    async with get_db_session() as session:
        # Check if exists
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user_id,
                OAuthToken.tool_name == tool_name,
                OAuthToken.provider == provider
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.updated_at = datetime.utcnow()
        else:
            new_token = OAuthToken(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tool_name=tool_name,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token
            )
            session.add(new_token)
            
        await session.commit()
        
    return f"✅ Credentials for {tool_name} ({provider}) stored successfully."


async def get_credential(
    tool_name: str,
    provider: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Retrieve credentials for a specific tool.
    
    Args:
        tool_name: Name of the tool
        provider: Provider name
        ctx: FastMCP context
        
    Returns:
        Dictionary of secrets
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")
         
    async with get_db_session() as session:
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user_id,
                OAuthToken.tool_name == tool_name,
                OAuthToken.provider == provider
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            raise ValueError(f"No credentials found for {tool_name} ({provider})")
            
        # Try to parse as JSON if it was stored as a dict dump, otherwise return as access_token
        try:
            return json.loads(token.access_token)
        except json.JSONDecodeError:
            return {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token
            }


async def list_credentials(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all stored credentials (metadata only, no secrets).
    
    Args:
        ctx: FastMCP context
        
    Returns:
        List of credential metadata
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")
         
    async with get_db_session() as session:
        result = await session.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id)
        )
        tokens = result.scalars().all()
        
        return [
            {
                "tool_name": t.tool_name,
                "provider": t.provider,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in tokens
        ]


async def delete_credential(
    tool_name: str,
    provider: str,
    ctx: Context
) -> str:
    """
    Delete a stored credential.
    
    Args:
        tool_name: Name of the tool
        provider: Provider name
        ctx: FastMCP context
        
    Returns:
        Success message
    """
    # TODO: Proper user extraction
    user_id = "default_user"
    if ctx and hasattr(ctx, "session") and ctx.session.get("user_id"):
         user_id = ctx.session.get("user_id")
         
    async with get_db_session() as session:
        result = await session.execute(
            delete(OAuthToken).where(
                OAuthToken.user_id == user_id,
                OAuthToken.tool_name == tool_name,
                OAuthToken.provider == provider
            )
        )
        await session.commit()
        
    return f"✅ Credentials for {tool_name} ({provider}) deleted."
