import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.deps import get_db
from app.models.uploaded_image import UploadedImage
from app.services.admin_service import AuthDeps

router = APIRouter()


@router.get("/{image_id}")
def get_image(
    image_id: str,
    db: Session = Depends(get_db),
    user=Depends(AuthDeps.require_user),
):
    img = db.query(UploadedImage).filter(UploadedImage.id == image_id).first()

    if not img or not os.path.exists(img.storage_path):
        raise NotFoundError("Image not found.", http_status=404)

    return FileResponse(
        img.storage_path,
        media_type=img.mime_type,
        filename=img.original_filename,
    )