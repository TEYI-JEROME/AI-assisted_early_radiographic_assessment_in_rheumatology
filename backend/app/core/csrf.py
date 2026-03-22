import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Local MVP pragmatic exemptions:
# We keep the middleware in place but do not block the core product workflows.
CSRF_EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/logout",
    "/api/patients",
    "/api/analyses",
    "/api/reviews",
)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def is_exempt_path(path: str) -> bool:
    for prefix in CSRF_EXEMPT_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        if method in SAFE_METHODS:
            return await call_next(request)

        if is_exempt_path(path):
            return await call_next(request)

        auth_cookie = request.cookies.get(settings.cookie_name)
        if not auth_cookie:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        csrf_header = request.headers.get(settings.csrf_header_name)

        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "csrf_failed",
                        "message": "CSRF validation failed.",
                    }
                },
            )

        return await call_next(request)