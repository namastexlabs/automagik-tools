"""HTTP Security Headers Middleware.

Implements OWASP recommended security headers for the Hub HTTP API.
These are applied at the Starlette/ASGI level, not the FastMCP middleware level.

Security Headers:
- X-Frame-Options: Prevent clickjacking
- X-Content-Type-Options: Prevent MIME sniffing
- X-XSS-Protection: Legacy XSS protection (for older browsers)
- Referrer-Policy: Control referrer information
- Content-Security-Policy: Prevent XSS and injection attacks
- Strict-Transport-Security: Enforce HTTPS (production only)
- Permissions-Policy: Control browser features
"""
import os
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses.

    Configurable via environment variables:
    - HUB_ENABLE_HSTS: Enable HSTS header (default: false, set to 'true' in production)
    - HUB_CSP_REPORT_URI: URI for CSP violation reports (optional)
    """

    def __init__(
        self,
        app: Callable,
        enable_hsts: bool = None,
        csp_report_uri: str = None
    ):
        super().__init__(app)
        # Auto-detect HSTS from environment (fallback for bootstrap phase)
        if enable_hsts is None:
            enable_hsts = os.getenv("HUB_ENABLE_HSTS", "false").lower() == "true"
        self.enable_hsts = enable_hsts

        # Auto-detect CSP report URI from environment (fallback for bootstrap phase)
        if csp_report_uri is None:
            csp_report_uri = os.getenv("HUB_CSP_REPORT_URI", "")
        self.csp_report_uri = csp_report_uri

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Prevent clickjacking - frame embedding blocked
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Legacy XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy - restrict dangerous browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Required for some UI frameworks
            "style-src 'self' 'unsafe-inline'",  # Required for inline styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https://*.workos.com https://*.authkit.app",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
        ]

        if self.csp_report_uri:
            csp_directives.append(f"report-uri {self.csp_report_uri}")

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS - only enable in production with HTTPS
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to all requests for tracing.

    Generates or propagates a request ID for distributed tracing:
    - Uses X-Request-ID header if provided by client/load balancer
    - Generates UUID if not provided
    - Returns X-Request-ID in response for correlation
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers."""
        import uuid

        # Get from header or generate new
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for use in logs/audit
        request.state.request_id = request_id

        response = await call_next(request)

        # Return in response for client correlation
        response.headers["X-Request-ID"] = request_id

        return response


def get_security_middleware():
    """Get all HTTP security middleware.

    Returns middleware classes (not instances) for adding to Starlette app.
    Add them in this order for proper header application.

    Usage in hub_http.py:
        from automagik_tools.hub.security_middleware import get_security_middleware

        for middleware_class in get_security_middleware():
            app.add_middleware(middleware_class)

    Returns:
        List of middleware classes to add to the app
    """
    return [
        RequestIDMiddleware,
        SecurityHeadersMiddleware,
    ]
