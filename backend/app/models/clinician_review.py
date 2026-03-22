from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClinicianReview(Base):
    __tablename__ = "clinician_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_analyses.id"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)

    reviewer_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)  # DRAFT / FINAL
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)  # CONFIRMED / NOT_CONFIRMED / UNCERTAIN

    structured_note_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    free_text: Mapped[str | None] = mapped_column(Text(), nullable=True)

    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)

    signed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)