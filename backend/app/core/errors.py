from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, code: str = "app_error", http_status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


class AuthError(AppError):
    def __init__(self, message: str = "Authentication failed", code: str = "auth_failed", http_status: int = 401):
        super().__init__(message, code, http_status)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", code: str = "forbidden", http_status: int = 403):
        super().__init__(message, code, http_status)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", code: str = "not_found", http_status: int = 404):
        super().__init__(message, code, http_status)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", code: str = "conflict", http_status: int = 409):
        super().__init__(message, code, http_status)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
        )