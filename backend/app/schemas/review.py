from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
    decision: str = Field(pattern="^(CONFIRMED|NOT_CONFIRMED|UNCERTAIN)$")
    structured_note: dict = Field(default_factory=dict)
    free_text: str | None = Field(default=None, max_length=5000)


class ReviewResponse(BaseModel):
    id: str
    analysis_id: str
    patient_id: str
    reviewer_user_id: str
    status: str
    decision: str | None
    structured_note: dict
    free_text: str | None
    version: int
    is_current: bool
    signed_at: datetime | None
    created_at: datetime