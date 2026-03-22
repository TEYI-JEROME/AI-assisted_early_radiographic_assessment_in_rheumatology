from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exams.id"), nullable=False)

    roi_image_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("uploaded_images.id"), nullable=True)
    full_image_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("uploaded_images.id"), nullable=True)
    roi_selection_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("roi_selections.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)  # PENDING/RUNNING/SUCCESS/FAILED

    erosion_probability: Mapped[float | None] = mapped_column(Float(), nullable=True)
    threshold: Mapped[float | None] = mapped_column(Float(), nullable=True)
    predicted_class: Mapped[int | None] = mapped_column(Integer(), nullable=True)

    model_version: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)

    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    metadata_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")