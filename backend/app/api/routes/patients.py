from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientListResponse, PatientResponse
from app.services.admin_service import AuthDeps
from app.services.patient_service import PatientService

router = APIRouter()


@router.get("", response_model=PatientListResponse)
def list_patients(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_user),
) -> PatientListResponse:
    query = db.query(Patient)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (Patient.patient_id.ilike(like)) |
            (Patient.hospital_number.ilike(like)) |
            (Patient.full_name.ilike(like))
        )

    total = query.count()
    items = (
        query.order_by(Patient.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PatientListResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=[
            PatientResponse(
                id=p.id,
                patient_id=p.patient_id,
                hospital_number=p.hospital_number,
                full_name=p.full_name,
                date_of_birth=p.date_of_birth,
                sex=p.sex,
                notes=p.notes,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in items
        ],
    )


@router.post("", response_model=PatientResponse)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_roles("Admin", "Rheumatologist", "Resident")),
) -> PatientResponse:
    patient = PatientService().create_patient(
        db,
        patient_id=payload.patient_id,
        hospital_number=payload.hospital_number,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        sex=payload.sex,
        notes=payload.notes,
    )

    return PatientResponse(
        id=patient.id,
        patient_id=patient.patient_id,
        hospital_number=patient.hospital_number,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex,
        notes=patient.notes,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_user),
) -> PatientResponse:
    patient = PatientService().get_by_patient_id(db, patient_id)

    return PatientResponse(
        id=patient.id,
        patient_id=patient.patient_id,
        hospital_number=patient.hospital_number,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex,
        notes=patient.notes,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )