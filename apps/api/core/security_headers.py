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
    # Voice interviews need the microphone; camera and geolocation stay disabled.
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    response.headers["Content-Security-Policy"] = csp_directives

    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response


def _build_csp(origin: str) -> str:
    """Build a restrictive CSP.

    The API origin is taken from ``settings.PUBLIC_API_URL`` (defaults to
    ``http://localhost:8000`` for local dev, set to the public https URL in
    production) so ``connect-src`` matches the real backend and no ``localhost``
    leaks into production headers. The WebSocket origin is derived from it
    (http→ws, https→wss). In non-production a localhost request origin is also
    allowed so Swagger UI / dev tools work.
    """
    is_prod = settings.is_production
    dev_src = "" if is_prod else (origin if "localhost" in origin or "127.0.0.1" in origin else "")

    api_origin = settings.PUBLIC_API_URL.rstrip("/")  # Backend API origin
    if api_origin.startswith("https://"):
        ws_origin = "wss://" + api_origin[len("https://") :]
    elif api_origin.startswith("http://"):
        ws_origin = "ws://" + api_origin[len("http://") :]
    else:
        ws_origin = api_origin

    directives = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'", "data:"],
        "connect-src": ["'self'", api_origin, ws_origin, *([dev_src] if dev_src and dev_src != api_origin else [])],
        "frame-ancestors": ["'none'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
        "object-src": ["'none'"],
    }

    return "; ".join(f"{key} {' '.join(values)}" for key, values in directives.items() if values)
