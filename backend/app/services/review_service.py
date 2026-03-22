import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.ai_analysis import AIAnalysis
from app.models.clinician_review import ClinicianReview
from app.models.user import User
from app.schemas.review import ReviewCreateRequest, ReviewResponse


class ReviewService:
    def _get_analysis(self, db: Session, analysis_id: str) -> AIAnalysis:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        if not analysis:
            raise AppError("Analysis not found.", code="analysis_not_found", http_status=404)
        return analysis

    def _current_review(self, db: Session, analysis_id: str) -> ClinicianReview | None:
        return (
            db.query(ClinicianReview)
            .filter(
                ClinicianReview.analysis_id == analysis_id,
                ClinicianReview.is_current == True,  # noqa: E712
            )
            .first()
        )

    def save_draft(self, db: Session, *, analysis_id: str, user: User, payload: ReviewCreateRequest) -> ReviewResponse:
        analysis = self._get_analysis(db, analysis_id)
        current = self._current_review(db, analysis_id)

        now = datetime.utcnow()
        version = 1

        if current:
            current.is_current = False
            db.add(current)
            db.commit()
            version = current.version + 1

        review = ClinicianReview(
            id=str(uuid4()),
            analysis_id=analysis.id,
            patient_id=analysis.patient_id,
            reviewer_user_id=user.id,
            status="DRAFT",
            decision=payload.decision,
            structured_note_json=json.dumps(payload.structured_note or {}, ensure_ascii=False),
            free_text=payload.free_text,
            version=version,
            is_current=True,
            signed_at=None,
            created_at=now,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        return self._to_response(review)

    def finalize(self, db: Session, *, analysis_id: str, user: User, payload: ReviewCreateRequest) -> ReviewResponse:
        analysis = self._get_analysis(db, analysis_id)
        current = self._current_review(db, analysis_id)

        now = datetime.utcnow()
        version = 1

        if current:
            current.is_current = False
            db.add(current)
            db.commit()
            version = current.version + 1

        review = ClinicianReview(
            id=str(uuid4()),
            analysis_id=analysis.id,
            patient_id=analysis.patient_id,
            reviewer_user_id=user.id,
            status="FINAL",
            decision=payload.decision,
            structured_note_json=json.dumps(payload.structured_note or {}, ensure_ascii=False),
            free_text=payload.free_text,
            version=version,
            is_current=True,
            signed_at=now,
            created_at=now,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        return self._to_response(review)

    def get_current(self, db: Session, *, analysis_id: str) -> ReviewResponse:
        self._get_analysis(db, analysis_id)
        current = self._current_review(db, analysis_id)
        if not current:
            raise AppError("No clinician review found for this analysis.", code="review_not_found", http_status=404)
        return self._to_response(current)

    def _to_response(self, review: ClinicianReview) -> ReviewResponse:
        return ReviewResponse(
            id=review.id,
            analysis_id=review.analysis_id,
            patient_id=review.patient_id,
            reviewer_user_id=review.reviewer_user_id,
            status=review.status,
            decision=review.decision,
            structured_note=json.loads(review.structured_note_json or "{}"),
            free_text=review.free_text,
            version=review.version,
            is_current=review.is_current,
            signed_at=review.signed_at,
            created_at=review.created_at,
        )