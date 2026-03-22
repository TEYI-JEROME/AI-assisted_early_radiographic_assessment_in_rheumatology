import json
from datetime import datetime, date
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai.inference import infer_erosion
from app.core.errors import AppError, NotFoundError
from app.models.ai_analysis import AIAnalysis
from app.models.clinician_review import ClinicianReview
from app.models.exam import Exam
from app.models.patient import Patient
from app.models.roi_selection import ROISelection
from app.models.uploaded_image import UploadedImage
from app.models.user import User
from app.services.storage_service import StorageService


class AnalysisService:
    def create_and_run(
        self,
        db: Session,
        *,
        actor_user: User,
        patient_public_id: str,
        exam_date_iso: str,
        mode: str,
        roi_image: UploadFile,
        full_image: UploadFile | None,
        roi_meta: dict,
    ) -> AIAnalysis:
        patient = db.query(Patient).filter(Patient.patient_id == patient_public_id).first()
        if not patient:
            raise NotFoundError("Patient not found.", http_status=404)

        try:
            exam_date_obj = date.fromisoformat(exam_date_iso)
        except Exception:
            raise AppError("Invalid exam_date. Use YYYY-MM-DD.", code="invalid_exam_date", http_status=400)

        if mode not in {"ROI_DIRECT", "FULL_WITH_MANUAL_ROI"}:
            raise AppError("Invalid mode.", code="invalid_mode", http_status=400)

        if mode == "FULL_WITH_MANUAL_ROI" and full_image is None:
            raise AppError(
                "Full radiograph image is required for FULL_WITH_MANUAL_ROI.",
                code="missing_full_image",
                http_status=400,
            )

        now = datetime.utcnow()

        exam = Exam(
            id=str(uuid4()),
            patient_id=patient.id,
            exam_date=exam_date_obj,
            created_by_user_id=actor_user.id,
            notes=None,
            created_at=now,
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        storage = StorageService()

        roi_bytes = roi_image.file.read()
        roi_store = storage.store_image_bytes(original_filename=roi_image.filename or "roi", data=roi_bytes)

        roi_rec = UploadedImage(
            id=str(uuid4()),
            patient_id=patient.id,
            exam_id=exam.id,
            image_kind="ROI_DIRECT" if mode == "ROI_DIRECT" else "ROI_CROPPED",
            original_filename=roi_image.filename or "roi",
            stored_filename=roi_store.stored_filename,
            storage_path=roi_store.storage_path,
            sha256=roi_store.sha256,
            mime_type=roi_store.mime_type,
            size_bytes=roi_store.size_bytes,
            width=roi_store.width,
            height=roi_store.height,
            uploaded_by_user_id=actor_user.id,
            uploaded_at=now,
        )
        db.add(roi_rec)
        db.commit()
        db.refresh(roi_rec)

        full_rec = None
        roi_sel = None

        if mode == "FULL_WITH_MANUAL_ROI" and full_image is not None:
            full_bytes = full_image.file.read()
            full_store = storage.store_image_bytes(original_filename=full_image.filename or "full", data=full_bytes)

            full_rec = UploadedImage(
                id=str(uuid4()),
                patient_id=patient.id,
                exam_id=exam.id,
                image_kind="FULL_RADIOGRAPH",
                original_filename=full_image.filename or "full",
                stored_filename=full_store.stored_filename,
                storage_path=full_store.storage_path,
                sha256=full_store.sha256,
                mime_type=full_store.mime_type,
                size_bytes=full_store.size_bytes,
                width=full_store.width,
                height=full_store.height,
                uploaded_by_user_id=actor_user.id,
                uploaded_at=now,
            )
            db.add(full_rec)
            db.commit()
            db.refresh(full_rec)

            if all(roi_meta.get(k) is not None for k in ["x", "y", "width", "height"]):
                roi_sel = ROISelection(
                    id=str(uuid4()),
                    source_image_id=full_rec.id,
                    roi_image_id=roi_rec.id,
                    x=int(roi_meta["x"]),
                    y=int(roi_meta["y"]),
                    width=int(roi_meta["width"]),
                    height=int(roi_meta["height"]),
                    created_by_user_id=actor_user.id,
                    created_at=now,
                )
                db.add(roi_sel)
                db.commit()
                db.refresh(roi_sel)

        analysis = AIAnalysis(
            id=str(uuid4()),
            patient_id=patient.id,
            exam_id=exam.id,
            roi_image_id=roi_rec.id,
            full_image_id=full_rec.id if full_rec else None,
            roi_selection_id=roi_sel.id if roi_sel else None,
            status="RUNNING",
            erosion_probability=None,
            threshold=None,
            predicted_class=None,
            model_version=None,
            error_message=None,
            created_by_user_id=actor_user.id,
            created_at=now,
            started_at=now,
            completed_at=None,
            metadata_json=json.dumps(
                {
                    "mode": mode,
                    "warnings": ["Prediction quality depends on image quality and ROI selection."]
                    if mode == "FULL_WITH_MANUAL_ROI"
                    else [],
                }
            ),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        try:
            res = infer_erosion(roi_rec.storage_path)
            analysis.status = "SUCCESS"
            analysis.erosion_probability = float(res["probability"])
            analysis.threshold = float(res["threshold"])
            analysis.predicted_class = int(res["predicted_class"])
            analysis.model_version = str(res["model_version"])
            analysis.completed_at = datetime.utcnow()
            analysis.metadata_json = json.dumps(
                {
                    **json.loads(analysis.metadata_json),
                    "preprocess": res["preprocess"],
                }
            )
            db.add(analysis)
            db.commit()
        except AppError as e:
            analysis.status = "FAILED"
            analysis.error_message = e.message
            analysis.completed_at = datetime.utcnow()
            db.add(analysis)
            db.commit()
            raise
        except Exception:
            analysis.status = "FAILED"
            analysis.error_message = "Inference failed. Verify model artifacts and image validity."
            analysis.completed_at = datetime.utcnow()
            db.add(analysis)
            db.commit()
            raise AppError(analysis.error_message, code="inference_failed", http_status=500)

        return analysis

    def get_detail(self, db: Session, *, analysis_id: str):
        a = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        if not a:
            raise NotFoundError("Analysis not found.", http_status=404)

        exam = db.query(Exam).filter(Exam.id == a.exam_id).first()
        patient = db.query(Patient).filter(Patient.id == a.patient_id).first()
        latest_review = (
            db.query(ClinicianReview)
            .filter(
                ClinicianReview.analysis_id == a.id,
                ClinicianReview.is_current == True,  # noqa: E712
            )
            .first()
        )

        return {
            "id": a.id,
            "status": a.status,
            "patient": {
                "id": patient.id,
                "patient_id": patient.patient_id,
                "full_name": patient.full_name,
            } if patient else None,
            "exam": {
                "id": exam.id,
                "exam_date": str(exam.exam_date),
            } if exam else None,
            "erosion_probability": a.erosion_probability,
            "threshold": a.threshold,
            "predicted_class": a.predicted_class,
            "model_version": a.model_version,
            "created_at": a.created_at,
            "started_at": a.started_at,
            "completed_at": a.completed_at,
            "roi_image_id": a.roi_image_id,
            "full_image_id": a.full_image_id,
            "roi_selection_id": a.roi_selection_id,
            "error_message": a.error_message,
            "metadata": json.loads(a.metadata_json or "{}"),
            "latest_review": {
                "id": latest_review.id,
                "analysis_id": latest_review.analysis_id,
                "patient_id": latest_review.patient_id,
                "reviewer_user_id": latest_review.reviewer_user_id,
                "status": latest_review.status,
                "decision": latest_review.decision,
                "structured_note": json.loads(latest_review.structured_note_json or "{}"),
                "free_text": latest_review.free_text,
                "version": latest_review.version,
                "is_current": latest_review.is_current,
                "signed_at": latest_review.signed_at,
                "created_at": latest_review.created_at,
            } if latest_review else None,
        }

    def list_by_patient_public_id(self, db: Session, *, patient_public_id: str):
        p = db.query(Patient).filter(Patient.patient_id == patient_public_id).first()
        if not p:
            raise NotFoundError("Patient not found.", http_status=404)

        items = (
            db.query(AIAnalysis)
            .filter(AIAnalysis.patient_id == p.id)
            .order_by(AIAnalysis.created_at.desc())
            .all()
        )

        out = []
        for a in items:
            exam = db.query(Exam).filter(Exam.id == a.exam_id).first()
            latest_review = (
                db.query(ClinicianReview)
                .filter(
                    ClinicianReview.analysis_id == a.id,
                    ClinicianReview.is_current == True,  # noqa: E712
                )
                .first()
            )

            out.append(
                {
                    "id": a.id,
                    "status": a.status,
                    "exam_date": str(exam.exam_date) if exam else None,
                    "erosion_probability": a.erosion_probability,
                    "predicted_class": a.predicted_class,
                    "model_version": a.model_version,
                    "created_at": a.created_at,
                    "latest_review_status": latest_review.status if latest_review else None,
                    "latest_review_decision": latest_review.decision if latest_review else None,
                    "latest_review_signed_at": latest_review.signed_at if latest_review else None,
                }
            )

        return {"patient_id": p.patient_id, "items": out}