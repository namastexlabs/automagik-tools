"""Multi-tenant tool support for Hub.

Provides base classes and utilities for making tools multi-tenant aware.
Tools can access user-specific configuration from the database via Context.
"""
import logging
from typing import Any, Dict, Optional, TypeVar, Generic
from pydantic_settings import BaseSettings
from fastmcp import Context
from .database import get_db_session
from .models import ToolConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)

ConfigT = TypeVar("ConfigT", bound=BaseSettings)


class MultiTenantToolMixin(Generic[ConfigT]):
    """Mixin for multi-tenant tools.

    Provides methods to get user-specific configuration from Hub database.
    Tools should use this instead of global configuration.

    Usage:
        class MyTool(MultiTenantToolMixin[MyToolConfig]):
            async def get_client(self, ctx: Context) -> MyClient:
                config = await self.get_user_config(ctx, MyToolConfig)
                return MyClient(config)
    """

    tool_name: str = ""  # Override in subclass

    async def get_user_config(
        self,
        ctx: Context,
        config_class: type[ConfigT],
        use_global_fallback: bool = True
    ) -> ConfigT:
        """Get user-specific configuration from database.

        Args:
            ctx: FastMCP Context with user information
            config_class: Pydantic Settings class for configuration
            use_global_fallback: If True, fall back to environment variables when no user config found

        Returns:
            Configuration object with user-specific or global settings

        Raises:
            ValueError: If no configuration found and use_global_fallback=False
        """
        user_id = self._get_user_id(ctx)

        if not user_id:
            if use_global_fallback:
                logger.warning(f"[{self.tool_name}] No user ID in context, using global config")
                return config_class()
            raise ValueError(f"No user ID found in context for tool {self.tool_name}")

        # Try to get user-specific config from database
        config_data = await self._load_user_config_from_db(user_id)

        if config_data:
            logger.info(f"[{self.tool_name}] Loaded user config for {user_id}")
            # Merge with defaults from config_class
            return config_class(**config_data)

        # No user config found
        if use_global_fallback:
            logger.info(f"[{self.tool_name}] No user config found, using global config for {user_id}")
            return config_class()

        raise ValueError(f"No configuration found for user {user_id} and tool {self.tool_name}")

    async def _load_user_config_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load configuration from database."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(ToolConfig).where(
                        ToolConfig.user_id == user_id,
                        ToolConfig.tool_name == self.tool_name
                    )
                )
                tool_config = result.scalar_one_or_none()

                if tool_config and tool_config.config:
                    return tool_config.config

                return None

        except Exception as e:
            logger.error(f"[{self.tool_name}] Error loading config from database: {e}")
            return None

    def _get_user_id(self, ctx: Context) -> Optional[str]:
        """Extract user ID from context.

        Checks multiple possible locations:
        1. ctx.get_state("user_id")
        2. ctx.get_state("authenticated_user_email")
        3. ctx attribute
        """
        try:
            # Try state first
            user_id = ctx.get_state("user_id")
            if user_id:
                return user_id

            # Try email as user_id
            email = ctx.get_state("authenticated_user_email")
            if email:
                return email

        except Exception:
            pass

        # Try direct attribute access
        if hasattr(ctx, "user_id"):
            return getattr(ctx, "user_id")

        return None

    async def save_user_config(
        self,
        ctx: Context,
        config_data: Dict[str, Any]
    ) -> None:
        """Save user configuration to database.

        Args:
            ctx: FastMCP Context with user information
            config_data: Configuration dictionary to save

        Raises:
            ValueError: If no user ID in context
        """
        user_id = self._get_user_id(ctx)

        if not user_id:
            raise ValueError(f"No user ID found in context for tool {self.tool_name}")

        try:
            async with get_db_session() as session:
                # Check if config exists
                result = await session.execute(
                    select(ToolConfig).where(
                        ToolConfig.user_id == user_id,
                        ToolConfig.tool_name == self.tool_name
                    )
                )
                tool_config = result.scalar_one_or_none()

                if tool_config:
                    # Update existing
                    tool_config.config = config_data
                else:
                    # Create new
                    tool_config = ToolConfig(
                        user_id=user_id,
                        tool_name=self.tool_name,
                        config=config_data
                    )
                    session.add(tool_config)

                await session.commit()
                logger.info(f"[{self.tool_name}] Saved config for user {user_id}")

        except Exception as e:
            logger.error(f"[{self.tool_name}] Error saving config to database: {e}")
            raise


def get_user_config_from_context(
    ctx: Context,
    tool_name: str,
    config_class: type[ConfigT],
    use_global_fallback: bool = True
) -> Optional[ConfigT]:
    """Helper function to get user config from context.

    This is a convenience function that can be used without subclassing.

    Args:
        ctx: FastMCP Context
        tool_name: Name of the tool
        config_class: Pydantic Settings class
        use_global_fallback: Whether to fall back to env vars

    Returns:
        Configuration object or None
    """
    # Check if config was already injected into context by HubToolWrapper
    if hasattr(ctx, "tool_config") and ctx.tool_config:
        try:
            return config_class(**ctx.tool_config)
        except Exception as e:
            logger.warning(f"Failed to create config from context: {e}")

    # Fall back to global config
    if use_global_fallback:
        return config_class()

    return None


# Decorator for multi-tenant tool functions
def multi_tenant_tool(tool_name: str):
    """Decorator to make a tool function multi-tenant aware.

    Automatically injects user configuration from context.

    Usage:
        @multi_tenant_tool("my_tool")
        @mcp.tool()
        async def my_function(ctx: Context, ...):
            config = ctx.tool_config  # User-specific config available here
    """
    def decorator(func):
        async def wrapper(*args, ctx: Context = None, **kwargs):
            if ctx:
                # Try to load config if not already present
                if not hasattr(ctx, "tool_config") or not ctx.tool_config:
                    user_id = None
                    try:
                        user_id = ctx.get_state("user_id")
                    except:
                        pass

                    if user_id:
                        # Load from database
                        async with get_db_session() as session:
                            result = await session.execute(
                                select(ToolConfig).where(
                                    ToolConfig.user_id == user_id,
                                    ToolConfig.tool_name == tool_name
                                )
                            )
                            tool_config = result.scalar_one_or_none()

                            if tool_config:
                                # Inject into context
                                setattr(ctx, "tool_config", tool_config.config)

            return await func(*args, ctx=ctx, **kwargs)

        return wrapper
    return decorator
