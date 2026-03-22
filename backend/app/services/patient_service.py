from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.patient import Patient


class PatientService:
    def create_patient(
        self,
        db: Session,
        *,
        patient_id: str,
        hospital_number: str,
        full_name: str,
        date_of_birth,
        sex: str,
        notes: str | None,
    ) -> Patient:
        existing = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if existing:
            raise AppError("Patient ID already exists.", code="patient_exists", http_status=409)

        now = datetime.utcnow()
        patient = Patient(
            id=str(uuid4()),
            patient_id=patient_id,
            hospital_number=hospital_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            sex=sex,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    def get_by_patient_id(self, db: Session, patient_id: str) -> Patient:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise AppError("Patient not found.", code="patient_not_found", http_status=404)
        return patient