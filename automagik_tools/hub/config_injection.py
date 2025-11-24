"""Runtime configuration injection for multi-tenant tools.

This module provides a mechanism to inject user-specific configuration
into tools at runtime through environment variable manipulation and
context access, WITHOUT requiring tools to be refactored.

Works by:
1. Intercepting tool function calls
2. Temporarily setting environment variables from user config
3. Calling the tool function
4. Restoring original environment

This is a transitional solution until all tools are properly multi-tenant aware.
"""
import os
import logging
import asyncio
from typing import Any, Dict, Optional, Callable
from contextvars import ContextVar
from fastmcp import Context
from .database import get_db_session
from .models import ToolConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Context variable to hold current user's config
current_user_config: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "current_user_config", default=None
)


async def load_user_config_for_tool(user_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Load user configuration for a tool from database.

    Args:
        user_id: User identifier
        tool_name: Tool name

    Returns:
        Configuration dictionary or None
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(ToolConfig).where(
                    ToolConfig.user_id == user_id,
                    ToolConfig.tool_name == tool_name
                )
            )
            tool_config = result.scalar_one_or_none()

            if tool_config and tool_config.config:
                logger.debug(f"[{tool_name}] Loaded config for user {user_id}")
                return tool_config.config

            return None

    except Exception as e:
        logger.error(f"[{tool_name}] Error loading config for {user_id}: {e}")
        return None


def config_to_env_vars(config: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    """Convert configuration dict to environment variable format.

    Args:
        config: Configuration dictionary
        prefix: Prefix for environment variables

    Returns:
        Dictionary of environment variables

    Example:
        config = {"api_key": "secret", "base_url": "http://api"}
        prefix = "OMNI_"
        returns: {"OMNI_API_KEY": "secret", "OMNI_BASE_URL": "http://api"}
    """
    env_vars = {}

    for key, value in config.items():
        # Convert snake_case to UPPER_SNAKE_CASE
        env_key = key.upper()
        if prefix:
            env_key = f"{prefix.upper().rstrip('_')}_{env_key}"

        # Convert value to string
        if isinstance(value, (str, int, float, bool)):
            env_vars[env_key] = str(value)
        elif value is not None:
            env_vars[env_key] = str(value)

    return env_vars


class EnvironmentInjector:
    """Context manager for temporarily injecting environment variables."""

    def __init__(self, env_vars: Dict[str, str]):
        self.env_vars = env_vars
        self.original_vars = {}

    def __enter__(self):
        """Inject environment variables."""
        for key, value in self.env_vars.items():
            # Save original value
            self.original_vars[key] = os.environ.get(key)
            # Set new value
            os.environ[key] = value
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original environment variables."""
        for key in self.env_vars:
            original = self.original_vars[key]
            if original is None:
                # Key didn't exist before, remove it
                os.environ.pop(key, None)
            else:
                # Restore original value
                os.environ[key] = original


async def with_user_config(
    func: Callable,
    tool_name: str,
    ctx: Optional[Context] = None,
    *args,
    **kwargs
) -> Any:
    """Execute a function with user-specific configuration injected.

    This is a wrapper that:
    1. Extracts user_id from context
    2. Loads user config from database
    3. Injects config as environment variables
    4. Calls the function
    5. Restores environment

    Args:
        func: Function to call
        tool_name: Name of the tool
        ctx: FastMCP Context
        *args, **kwargs: Arguments to pass to function

    Returns:
        Result of function call
    """
    # Try to get user ID from context
    user_id = None
    if ctx:
        try:
            user_id = ctx.get_state("user_id")
        except:
            pass

        if not user_id:
            try:
                user_id = ctx.get_state("authenticated_user_email")
            except:
                pass

    # No user ID, just call function normally
    if not user_id:
        logger.debug(f"[{tool_name}] No user ID in context, using global config")
        return await func(*args, **kwargs)

    # Load user config
    config = await load_user_config_for_tool(user_id, tool_name)

    if not config:
        logger.debug(f"[{tool_name}] No user config found for {user_id}, using global config")
        return await func(*args, **kwargs)

    # Determine env var prefix for this tool
    # Most tools use TOOL_NAME_ prefix
    prefix = f"{tool_name.upper().replace('-', '_')}_"

    # Convert config to env vars
    env_vars = config_to_env_vars(config, prefix)

    # Inject env vars and call function
    logger.info(f"[{tool_name}] Injecting config for user {user_id}")

    with EnvironmentInjector(env_vars):
        result = await func(*args, **kwargs)

    return result


# Alternative: Pydantic Settings-aware injection
def create_user_config_instance(
    config_class: type,
    user_config: Dict[str, Any]
) -> Any:
    """Create a Pydantic Settings instance from user config.

    Args:
        config_class: Pydantic Settings class
        user_config: User configuration dictionary

    Returns:
        Instance of config_class with user config applied
    """
    # Pydantic Settings can accept dict directly
    try:
        return config_class(**user_config)
    except Exception as e:
        logger.warning(f"Failed to create config from user data: {e}")
        # Fall back to default config
        return config_class()


# For tools that use global _config pattern
def get_or_create_user_config(
    ctx: Optional[Context],
    config_class: type,
    tool_name: str
) -> Any:
    """Get user-specific config or create from global config.

    This function can be used by tools to get configuration:

    Example:
        from automagik_tools.hub.config_injection import get_or_create_user_config

        def _ensure_client(ctx: Optional[Context] = None) -> Client:
            config = get_or_create_user_config(ctx, MyConfig, "my_tool")
            return Client(config)

    Args:
        ctx: FastMCP Context (may be None)
        config_class: Pydantic Settings class
        tool_name: Tool name

    Returns:
        Configuration instance
    """
    # Check if user config is in context (injected by Hub)
    if ctx and hasattr(ctx, "tool_config") and ctx.tool_config:
        try:
            return create_user_config_instance(config_class, ctx.tool_config)
        except Exception as e:
            logger.warning(f"[{tool_name}] Failed to use context config: {e}")

    # Fall back to global config from environment
    return config_class()
