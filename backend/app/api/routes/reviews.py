from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.services.admin_service import AuthDeps
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/{analysis_id}/draft", response_model=ReviewResponse)
def save_draft(
    analysis_id: str,
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_roles("Admin", "Rheumatologist", "Resident")),
) -> ReviewResponse:
    return ReviewService().save_draft(db, analysis_id=analysis_id, user=user, payload=payload)


@router.post("/{analysis_id}/finalize", response_model=ReviewResponse)
def finalize_review(
    analysis_id: str,
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_roles("Admin", "Rheumatologist")),
) -> ReviewResponse:
    return ReviewService().finalize(db, analysis_id=analysis_id, user=user, payload=payload)


@router.get("/{analysis_id}", response_model=ReviewResponse)
def get_current_review(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(AuthDeps.require_user),
) -> ReviewResponse:
    return ReviewService().get_current(db, analysis_id=analysis_id)