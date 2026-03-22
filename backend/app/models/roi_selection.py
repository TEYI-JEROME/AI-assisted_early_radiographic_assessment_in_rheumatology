from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ROISelection(Base):
    __tablename__ = "roi_selections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    source_image_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploaded_images.id"), nullable=False)
    roi_image_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploaded_images.id"), nullable=False)

    x: Mapped[int] = mapped_column(Integer(), nullable=False)
    y: Mapped[int] = mapped_column(Integer(), nullable=False)
    width: Mapped[int] = mapped_column(Integer(), nullable=False)
    height: Mapped[int] = mapped_column(Integer(), nullable=False)

    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)