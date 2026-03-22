from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import write_audit_log
from app.db.deps import get_db
from app.schemas.analysis import AnalysisCreateResponse, AnalysisDetailResponse, AnalysisListResponse
from app.services.analysis_service import AnalysisService
from app.services.admin_service import AuthDeps
from app.models.user import User

router = APIRouter()


@router.post("", response_model=AnalysisCreateResponse)
def create_analysis(
    patient_id: str = Form(..., description="Patient public ID (e.g., P-0001)"),
    exam_date: str = Form(..., description="YYYY-MM-DD"),
    mode: str = Form(..., description="ROI_DIRECT or FULL_WITH_MANUAL_ROI"),
    roi_image: UploadFile = File(...),
    full_image: UploadFile | None = File(default=None),
    roi_x: int | None = Form(default=None),
    roi_y: int | None = Form(default=None),
    roi_width: int | None = Form(default=None),
    roi_height: int | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_roles("Admin", "Rheumatologist", "Resident")),
) -> AnalysisCreateResponse:
    svc = AnalysisService()
    analysis = svc.create_and_run(
        db,
        actor_user=user,
        patient_public_id=patient_id,
        exam_date_iso=exam_date,
        mode=mode,
        roi_image=roi_image,
        full_image=full_image,
        roi_meta={
            "x": roi_x,
            "y": roi_y,
            "width": roi_width,
            "height": roi_height,
        },
    )

    write_audit_log(
        db,
        event_type="analysis.create",
        actor_user_id=user.id,
        patient_id=analysis.patient_id,
        details={"analysis_id": analysis.id, "mode": mode},
    )

    return AnalysisCreateResponse(analysis_id=analysis.id)


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_user),
) -> AnalysisDetailResponse:
    return AnalysisService().get_detail(db, analysis_id=analysis_id)


@router.get("/by-patient/{patient_id}", response_model=AnalysisListResponse)
def list_analyses_by_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_user),
) -> AnalysisListResponse:
    return AnalysisService().list_by_patient_public_id(db, patient_public_id=patient_id)