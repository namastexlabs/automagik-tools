"""Hub multi-tenant middleware.

Provides middleware for:
- User authentication and authorization
- Per-user config injection via Context state
- Request logging and audit trails
- Rate limiting (future)
- Tool access control (future)

Based on FastMCP middleware patterns:
docs/fastmcp/20251123_123729/servers/middleware.md
"""
import logging
import time
from typing import Optional, Dict, Any
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_access_token, AccessToken
from fastmcp.exceptions import ToolError
from .database import get_db_session
from .models import ToolConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)


class UserConfigInjectionMiddleware(Middleware):
    """Inject user-specific tool configuration into Context state.

    This middleware loads user configuration from the database and makes it
    available to tools via ctx.get_state("tool_config") or ctx.tool_config.

    Tools already check for this pattern in their _get_config() helpers.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Inject user config before tool execution."""
        # Get authenticated user from access token
        user_id = await self._get_user_id(context)

        if user_id:
            # Store user_id in context state (tools check this)
            context.fastmcp_context.set_state("user_id", user_id)

            # Load user's tool configuration
            tool_name = context.message.name
            tool_config = await self._load_user_tool_config(user_id, tool_name)

            if tool_config:
                # Inject into context state (for ctx.get_state("tool_config"))
                context.fastmcp_context.set_state("tool_config", tool_config)

                # Also set as attribute (for hasattr(ctx, "tool_config") checks)
                context.fastmcp_context.tool_config = tool_config

                logger.debug(f"Injected config for user {user_id} tool {tool_name}")

        return await call_next(context)

    async def _get_user_id(self, context: MiddlewareContext) -> Optional[str]:
        """Extract user ID from access token or context."""
        try:
            # Try to get from FastMCP access token
            token: Optional[AccessToken] = get_access_token()

            if token:
                # Extract user ID from token claims
                # WorkOS tokens typically have 'sub' (subject) claim
                if "sub" in token.claims:
                    return token.claims["sub"]

                # Check for email
                if "email" in token.claims:
                    return token.claims["email"]

                # Use client_id as fallback
                if token.client_id:
                    return token.client_id

        except Exception as e:
            logger.debug(f"Could not extract user from token: {e}")

        # Fallback: check context state
        if context.fastmcp_context:
            user_id = context.fastmcp_context.get_state("user_id")
            if user_id:
                return user_id

        return None

    async def _load_user_tool_config(
        self,
        user_id: str,
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """Load user's tool configuration from database."""
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
                    return tool_config.config

                return None

        except Exception as e:
            logger.error(f"Error loading config for {user_id}/{tool_name}: {e}")
            return None


class RequestLoggingMiddleware(Middleware):
    """Log all MCP requests for audit and debugging.

    Logs tool calls with user ID, timing, and success/failure status.
    Useful for monitoring usage patterns and debugging issues.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log tool execution."""
        tool_name = context.message.name
        user_id = context.fastmcp_context.get_state("user_id") if context.fastmcp_context else "anonymous"
        start_time = time.time()

        logger.info(
            f"[TOOL_CALL] user={user_id} tool={tool_name} "
            f"method={context.method}"
        )

        try:
            result = await call_next(context)
            duration = time.time() - start_time

            logger.info(
                f"[TOOL_SUCCESS] user={user_id} tool={tool_name} "
                f"duration={duration:.3f}s"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"[TOOL_ERROR] user={user_id} tool={tool_name} "
                f"duration={duration:.3f}s error={str(e)}"
            )

            raise


class SessionAwareMiddleware(Middleware):
    """Handle MCP session initialization and track session info.

    Logs client connections and stores session metadata in context state.
    Useful for debugging connection issues and tracking client info.
    """

    async def on_initialize(self, context: MiddlewareContext, call_next):
        """Log client initialization."""
        # Check if MCP request context is available
        if context.fastmcp_context and context.fastmcp_context.request_context:
            session_id = context.fastmcp_context.session_id
            client_id = context.fastmcp_context.client_id

            logger.info(
                f"[SESSION_INIT] session_id={session_id} "
                f"client_id={client_id or 'unknown'}"
            )
        else:
            # MCP session not available yet - use HTTP helpers for request data
            from fastmcp.server.dependencies import get_http_headers
            headers = get_http_headers()
            user_agent = headers.get("user-agent", "unknown")

            logger.info(
                f"[SESSION_INIT] MCP session pending, "
                f"user_agent={user_agent}"
            )

        # Note: on_initialize returns None per FastMCP docs
        return await call_next(context)

    async def on_request(self, context: MiddlewareContext, call_next):
        """Store session info in context state."""
        ctx = context.fastmcp_context

        if ctx and ctx.request_context:
            # MCP session available - store session metadata
            ctx.set_state("session_id", ctx.session_id)
            ctx.set_state("client_id", ctx.client_id)

        return await call_next(context)


class RateLimitMiddleware(Middleware):
    """Rate limit tool calls per user.

    TODO: Implement actual rate limiting logic with:
    - Redis/in-memory counter per user
    - Configurable limits (requests per minute/hour)
    - Different limits for different tools
    - Graceful degradation

    For now, this is a placeholder showing the pattern.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        # TODO: Add actual rate limit tracking
        self._rate_limits: Dict[str, Any] = {}

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Check rate limit before executing tool."""
        user_id = context.fastmcp_context.get_state("user_id") if context.fastmcp_context else None

        if user_id:
            # TODO: Implement actual rate limit checking
            # For now, just pass through
            pass

        return await call_next(context)


class ToolAccessControlMiddleware(Middleware):
    """Control access to tools based on user permissions.

    TODO: Implement access control logic:
    - Check if user has access to specific tool
    - Enforce subscription-based tool access
    - Block private/restricted tools

    For now, this is a placeholder showing the pattern.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Check tool access permissions."""
        tool_name = context.message.name
        user_id = context.fastmcp_context.get_state("user_id") if context.fastmcp_context else None

        # TODO: Implement actual access control
        # Example from docs:
        # if context.fastmcp_context:
        #     try:
        #         tool = await context.fastmcp_context.fastmcp.get_tool(tool_name)
        #         if "restricted" in tool.tags:
        #             # Check user permissions
        #             if not await self._has_permission(user_id, tool_name):
        #                 raise ToolError("Access denied: insufficient permissions")
        #     except Exception:
        #         pass

        return await call_next(context)


def get_hub_middleware() -> list[Middleware]:
    """Get all Hub middleware in execution order.

    Middleware execution order (from general to specific):
    1. SessionAwareMiddleware - Track sessions
    2. UserConfigInjectionMiddleware - Load user config
    3. RequestLoggingMiddleware - Log all requests
    4. RateLimitMiddleware - Rate limit (future)
    5. ToolAccessControlMiddleware - Access control (future)

    Returns:
        List of middleware instances to add to Hub
    """
    return [
        SessionAwareMiddleware(),
        UserConfigInjectionMiddleware(),
        RequestLoggingMiddleware(),
        # Uncomment when implementing:
        # RateLimitMiddleware(requests_per_minute=60),
        # ToolAccessControlMiddleware(),
    ]
