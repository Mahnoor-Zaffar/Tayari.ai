"""Security headers middleware (CSP, HSTS, X-Frame-Options, etc.)."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from core.config import settings


async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Apply security headers to every response."""
    origin = request.headers.get("origin", "")
    csp_directives = _build_csp(origin)

    response: Response = await call_next(request)

    # Strip Server header
    for header in ("server", "x-powered-by"):
        if header in response.headers:
            del response.headers[header]

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"  # deprecated but still scanned by scanners
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = csp_directives

    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response


def _build_csp(origin: str) -> str:
    """Build a restrictive CSP.

    In development the frontend origin is allowed as a connect-src
    and frame-ancestor so the Swagger UI / dev tools work.
    """
    dev_src = origin if "localhost" in origin or "127.0.0.1" in origin else ""

    directives = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'", "data:"],
        "connect-src": ["'self'", *([dev_src] if dev_src else [])],
        "frame-ancestors": ["'none'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
        "object-src": ["'none'"],
    }

    return "; ".join(f"{key} {' '.join(values)}" for key, values in directives.items() if values)
