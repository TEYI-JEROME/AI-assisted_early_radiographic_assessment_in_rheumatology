from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="RheumaAssist API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(CSRFMiddleware)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/api/docs")

    app.include_router(api_router, prefix="/api")
    register_exception_handlers(app)
    return app


app = create_app()