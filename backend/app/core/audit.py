import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit_log(
    db: Session,
    *,
    event_type: str,
    actor_user_id: str | None,
    patient_id: str | None,
    details: dict,
) -> None:
    log = AuditLog(
        id=str(uuid4()),
        event_type=event_type,
        actor_user_id=actor_user_id,
        patient_id=patient_id,
        details_json=json.dumps(details, ensure_ascii=False),
        occurred_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()