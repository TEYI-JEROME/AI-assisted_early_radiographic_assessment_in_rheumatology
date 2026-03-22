import hashlib
import io
from pathlib import Path
from uuid import uuid4

from PIL import Image as PILImage

from app.core.config import settings
from app.core.errors import AppError


class StoredFile:
    def __init__(self, *, stored_filename: str, storage_path: str, sha256: str, mime_type: str, size_bytes: int, width: int, height: int):
        self.stored_filename = stored_filename
        self.storage_path = storage_path
        self.sha256 = sha256
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.width = width
        self.height = height


class StorageService:
    def __init__(self) -> None:
        self._uploads_dir = settings.resolve_path(settings.uploads_dir)
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    def store_image_bytes(self, *, original_filename: str, data: bytes) -> StoredFile:
        try:
            img = PILImage.open(io.BytesIO(data))
            img.verify()
        except Exception:
            raise AppError("Invalid image file.", code="invalid_image", http_status=400)

        img = PILImage.open(io.BytesIO(data))
        fmt = (img.format or "").upper()

        if fmt not in {"PNG", "JPEG", "JPG", "BMP"}:
            raise AppError("Only PNG, JPEG, and BMP are supported.", code="unsupported_format", http_status=400)

        if fmt == "PNG":
            mime_type = "image/png"
            ext = "png"
        elif fmt in {"JPEG", "JPG"}:
            mime_type = "image/jpeg"
            ext = "jpg"
        elif fmt == "BMP":
            mime_type = "image/bmp"
            ext = "bmp"
        else:
            raise AppError("Unsupported image format.", code="unsupported_format", http_status=400)

        width, height = img.size
        sha256 = hashlib.sha256(data).hexdigest()

        stored_filename = f"{uuid4()}.{ext}"
        destination = (self._uploads_dir / stored_filename).resolve()
        destination.write_bytes(data)

        return StoredFile(
            stored_filename=stored_filename,
            storage_path=str(destination),
            sha256=sha256,
            mime_type=mime_type,
            size_bytes=len(data),
            width=width,
            height=height,
        )