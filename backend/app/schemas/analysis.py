from datetime import datetime
from pydantic import BaseModel


class AnalysisCreateResponse(BaseModel):
    analysis_id: str


class AnalysisItem(BaseModel):
    id: str
    status: str
    exam_date: str | None
    erosion_probability: float | None
    predicted_class: int | None
    model_version: str | None
    created_at: datetime
    latest_review_status: str | None
    latest_review_decision: str | None
    latest_review_signed_at: datetime | None


class AnalysisListResponse(BaseModel):
    patient_id: str
    items: list[AnalysisItem]


class AnalysisPatient(BaseModel):
    id: str
    patient_id: str
    full_name: str


class AnalysisExam(BaseModel):
    id: str
    exam_date: str


class AnalysisLatestReview(BaseModel):
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


class AnalysisDetailResponse(BaseModel):
    id: str
    status: str

    patient: AnalysisPatient | None
    exam: AnalysisExam | None

    erosion_probability: float | None
    threshold: float | None
    predicted_class: int | None
    model_version: str | None

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    roi_image_id: str | None
    full_image_id: str | None
    roi_selection_id: str | None

    error_message: str | None
    metadata: dict
    latest_review: AnalysisLatestReview | None