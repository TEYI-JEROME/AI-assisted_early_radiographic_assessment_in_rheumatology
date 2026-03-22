from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.patients import router as patients_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.images import router as images_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(patients_router, prefix="/patients", tags=["patients"])
api_router.include_router(analyses_router, prefix="/analyses", tags=["analyses"])
api_router.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
api_router.include_router(images_router, prefix="/images", tags=["images"])