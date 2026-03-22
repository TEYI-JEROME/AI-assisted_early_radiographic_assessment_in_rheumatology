from datetime import date, datetime
from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    patient_id: str = Field(min_length=2, max_length=50)
    hospital_number: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=200)
    date_of_birth: date
    sex: str = Field(pattern="^(female|male|other)$")
    notes: str | None = Field(default=None, max_length=5000)


class PatientResponse(BaseModel):
    id: str
    patient_id: str
    hospital_number: str
    full_name: str
    date_of_birth: date
    sex: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[PatientResponse]