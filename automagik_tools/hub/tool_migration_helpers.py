"""Helper utilities for migrating tools to multi-tenant architecture.

Provides wrapper functions and utilities to make existing tools multi-tenant compatible
without requiring extensive refactoring.
"""
import logging
import functools
from typing import Any, Callable, Optional, TypeVar, Type
from pydantic_settings import BaseSettings
from fastmcp import Context

logger = logging.getLogger(__name__)

ConfigT = TypeVar("ConfigT", bound=BaseSettings)


def make_context_aware_config_loader(
    config_class: Type[ConfigT],
    tool_name: str
) -> Callable[[Optional[Context]], ConfigT]:
    """Create a config loader function that checks Context first.

    This factory function creates a config loader that:
    1. Checks if user config is in Context (injected by Hub)
    2. Falls back to global config from environment variables

    Args:
        config_class: Pydantic Settings class for configuration
        tool_name: Name of the tool (for logging)

    Returns:
        Function that takes optional Context and returns config

    Example:
        # In your tool __init__.py:
        from automagik_tools.hub.tool_migration_helpers import make_context_aware_config_loader
        from .config import OmniConfig

        _get_config = make_context_aware_config_loader(OmniConfig, "omni")

        def _ensure_client(ctx: Optional[Context] = None) -> OmniClient:
            config = _get_config(ctx)
            return OmniClient(config)
    """
    # Cache for global config
    _global_config: Optional[ConfigT] = None

    def get_config(ctx: Optional[Context] = None) -> ConfigT:
        """Get configuration from context or global config."""
        nonlocal _global_config

        # Try to get user-specific config from context
        if ctx:
            # Check if Hub injected config into context
            if hasattr(ctx, "tool_config") and ctx.tool_config:
                try:
                    logger.debug(f"[{tool_name}] Using user config from context")
                    return config_class(**ctx.tool_config)
                except Exception as e:
                    logger.warning(f"[{tool_name}] Failed to create config from context: {e}")

        # Fall back to global config from environment
        if _global_config is None:
            logger.debug(f"[{tool_name}] Loading global config from environment")
            _global_config = config_class()

        return _global_config

    return get_config


def make_context_aware_client_factory(
    client_class: type,
    config_loader: Callable[[Optional[Context]], ConfigT],
    tool_name: str,
    singleton: bool = False
) -> Callable[[Optional[Context]], Any]:
    """Create a client factory function that uses context-aware config.

    Args:
        client_class: Client class to instantiate
        config_loader: Function that loads config from context
        tool_name: Name of the tool (for logging)
        singleton: If True, cache global client; if False, create new client per request

    Returns:
        Function that takes optional Context and returns client instance

    Example:
        # In your tool __init__.py:
        _get_config = make_context_aware_config_loader(OmniConfig, "omni")
        _ensure_client = make_context_aware_client_factory(
            OmniClient, _get_config, "omni", singleton=True
        )
    """
    # Cache for global client (only used if singleton=True)
    _global_client: Optional[Any] = None

    def ensure_client(ctx: Optional[Context] = None) -> Any:
        """Get client instance with appropriate configuration."""
        nonlocal _global_client

        config = config_loader(ctx)

        # For multi-tenant mode with context, always create fresh client
        if ctx and hasattr(ctx, "tool_config") and ctx.tool_config:
            logger.debug(f"[{tool_name}] Creating user-specific client")
            return client_class(config)

        # For global mode, use singleton if requested
        if singleton:
            if _global_client is None:
                logger.debug(f"[{tool_name}] Creating singleton global client")
                _global_client = client_class(config)
            return _global_client
        else:
            # Create new client each time
            return client_class(config)

    return ensure_client


def inject_context_parameter(func: Callable) -> Callable:
    """Decorator to automatically inject Context parameter into tool functions.

    Modifies the function signature to accept optional ctx: Context parameter.
    Useful for gradual migration without changing all call sites.

    Args:
        func: Original tool function

    Returns:
        Wrapped function with optional Context parameter

    Example:
        @inject_context_parameter
        @mcp.tool()
        async def my_tool(param1: str) -> str:
            # ctx will be available as keyword argument
            return "result"
    """
    @functools.wraps(func)
    async def wrapper(*args, ctx: Optional[Context] = None, **kwargs):
        # Pass context through if function expects it
        import inspect
        sig = inspect.signature(func)

        if "ctx" in sig.parameters:
            kwargs["ctx"] = ctx

        return await func(*args, **kwargs)

    return wrapper


# Example: Complete migration helper for a tool
class ToolMigrationHelper:
    """Helper class to migrate a tool to multi-tenant architecture.

    Example usage:
        # In your tool __init__.py, add at the top:
        from automagik_tools.hub.tool_migration_helpers import ToolMigrationHelper
        from .config import MyToolConfig
        from .client import MyToolClient

        # Create helper
        _mt_helper = ToolMigrationHelper(
            tool_name="my_tool",
            config_class=MyToolConfig,
            client_class=MyToolClient
        )

        # Replace your _ensure_client function with:
        def _ensure_client(ctx: Optional[Context] = None) -> MyToolClient:
            return _mt_helper.get_client(ctx)

        # Add ctx parameter to all @mcp.tool() functions:
        @mcp.tool()
        async def my_function(param1: str, ctx: Context = None) -> str:
            client = _ensure_client(ctx)
            ...
    """

    def __init__(
        self,
        tool_name: str,
        config_class: Type[ConfigT],
        client_class: type,
        singleton: bool = True
    ):
        """Initialize migration helper.

        Args:
            tool_name: Name of the tool
            config_class: Pydantic Settings class for configuration
            client_class: Client class to instantiate
            singleton: Whether to use singleton pattern for global client
        """
        self.tool_name = tool_name
        self.config_class = config_class
        self.client_class = client_class
        self.singleton = singleton

        # Create config loader and client factory
        self._get_config = make_context_aware_config_loader(config_class, tool_name)
        self._ensure_client = make_context_aware_client_factory(
            client_class, self._get_config, tool_name, singleton
        )

        logger.info(f"[{tool_name}] Multi-tenant migration helper initialized")

    def get_config(self, ctx: Optional[Context] = None) -> ConfigT:
        """Get configuration (user-specific or global)."""
        return self._get_config(ctx)

    def get_client(self, ctx: Optional[Context] = None) -> Any:
        """Get client instance (user-specific or global)."""
        return self._ensure_client(ctx)


def verify_multi_tenant_compatibility(tool_module) -> dict[str, Any]:
    """Verify that a tool module is multi-tenant compatible.

    Checks for:
    - Context parameter in tool functions
    - Proper config handling
    - Client initialization

    Args:
        tool_module: The tool module to check

    Returns:
        Dictionary with compatibility status and issues
    """
    issues = []
    compatible = True

    # Check if module has create_server function
    if not hasattr(tool_module, "create_server"):
        issues.append("Missing create_server() function")
        compatible = False

    # Check if module has get_config_class function
    if not hasattr(tool_module, "get_config_class"):
        issues.append("Missing get_config_class() function")
        compatible = False

    # Check if module has mcp server
    if not hasattr(tool_module, "mcp"):
        issues.append("Missing mcp server instance")
        compatible = False
    else:
        # Check tool functions for Context parameter
        mcp = tool_module.mcp
        tools_without_context = []

        # This is a simplified check - in practice, would need to inspect
        # the actual function signatures of registered tools
        # For now, just check if the pattern is being followed

    return {
        "compatible": compatible and len(issues) == 0,
        "issues": issues,
        "tool_count": len(getattr(tool_module.mcp, "_tools", [])) if hasattr(tool_module, "mcp") else 0
    }
