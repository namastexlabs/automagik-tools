
from typing import Optional, Callable, Awaitable, Any
from fastmcp.server.middleware import Middleware, MiddlewareContext
from starlette.requests import Request
from . import get_current_user

class AuthMiddleware(Middleware):
    """
    Middleware to authenticate users and set context state.
    """
    async def on_call_tool(
        self, 
        context: MiddlewareContext, 
        call_next: Callable[[MiddlewareContext], Awaitable[Any]]
    ) -> Any:
        # Extract request from context if available
        request = getattr(context, "request", None)
        user = None
        
        if request and isinstance(request, Request):
            try:
                user = await get_current_user(request)
            except Exception:
                # Allow unauthenticated access for now (e.g. for login tools)
                pass
        
        if user:
            # Set state in context
            # We assume context has a state dict or similar mechanism
            # Based on service_decorator.py usage of ctx.get_state(), we need to populate it.
            # FastMCP's Context object (which MiddlewareContext likely wraps or is related to)
            # usually has a state attribute.
            
            if hasattr(context, "state") and isinstance(context.state, dict):
                 context.state["authenticated_user_email"] = user.get("email")
                 context.state["authenticated_via"] = "session"
                 context.state["user"] = user
            elif hasattr(context, "session") and hasattr(context.session, "state"):
                 # Some implementations might put state in session
                 context.session.state["authenticated_user_email"] = user.get("email")
                 context.session.state["authenticated_via"] = "session"
                 context.session.state["user"] = user
        
        return await call_next(context)
