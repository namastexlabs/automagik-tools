
import functools
import logging
from typing import Any, Callable, Dict, Optional, List
from fastmcp import Context
from .database import get_db_session
from .models import ToolConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)

class HubToolWrapper:
    """
    Wraps tool functions to inject user-specific configuration from the database.
    """
    
    @staticmethod
    def wrap(tool_name: str, tool_func: Callable) -> Callable:
        """
        Wrap a tool function with configuration injection logic.
        
        Args:
            tool_name: Name of the tool (used to look up config)
            tool_func: The original tool function
            
        Returns:
            Wrapped function
        """
        @functools.wraps(tool_func)
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs if present (FastMCP passes it if type hinted)
            # Or use get_context() if available
            from fastmcp.server.dependencies import get_context
            
            ctx = None
            try:
                ctx = get_context()
            except Exception:
                pass
                
            # Also check if 'ctx' is in kwargs
            if not ctx and "ctx" in kwargs and isinstance(kwargs["ctx"], Context):
                ctx = kwargs["ctx"]

            user_email = None
            if ctx:
                # Try to get user from context state (set by AuthMiddleware)
                # Note: FastMCP context state access might vary
                try:
                    user_email = ctx.get_state("authenticated_user_email")
                except Exception:
                    pass

            if not user_email:
                logger.warning(f"[{tool_name}] No authenticated user found in context. Proceeding without config injection.")
                return await tool_func(*args, **kwargs)

            # Fetch config for this user and tool
            config_data = {}
            try:
                async with get_db_session() as session:
                    result = await session.execute(
                        select(ToolConfig).where(
                            ToolConfig.user_id == user_email, # Using email as user_id for now
                            ToolConfig.tool_name == tool_name
                        )
                    )
                    tool_config = result.scalar_one_or_none()
                    if tool_config and tool_config.config:
                        config_data = tool_config.config
                        logger.info(f"[{tool_name}] Loaded configuration for {user_email}")
            except Exception as e:
                logger.error(f"[{tool_name}] Error fetching config: {e}")

            # Inject config into kwargs? 
            # Or set environment variables temporarily?
            # Setting env vars is risky in async/threaded env.
            # Better to pass as arguments if the tool accepts them.
            
            # For now, let's try to inject into kwargs if the tool accepts 'config' or specific keys
            # But many tools (like google-calendar) don't accept a 'config' dict.
            # They rely on internal state or env vars.
            
            # STRATEGY: ContextVar or temporary env var modification (with lock?)
            # Since we are async, env vars are global to the process, so modifying them is bad.
            
            # However, for 'evolution-api', we might need to patch the global 'client' or 'config' object.
            # For 'google-calendar', it uses 'service' injected by decorator, which uses context.
            
            # If the tool is designed to be context-aware (like we plan), it should look into Context.
            # So we should inject the config into the Context!
            
            if ctx and config_data:
                # Inject config into context state
                # We assume the context object has a 'request' or 'state' we can attach to.
                # FastMCP Context exposes get_state(), but maybe not set_state().
                # However, we can try to attach it to the underlying request if available.
                
                try:
                    # Try to set it on the context object itself if it allows dynamic attributes
                    setattr(ctx, "tool_config", config_data)
                    logger.debug(f"[{tool_name}] Injected tool_config into Context object")
                    
                    # Also try to set it in the state dict if accessible
                    # This depends on FastMCP internals, but usually there's a way.
                    # For now, setting it on ctx should be enough if our tools look for ctx.tool_config
                except Exception as e:
                    logger.warning(f"[{tool_name}] Could not inject config into context: {e}")

            return await tool_func(*args, **kwargs)
            
        return wrapper
