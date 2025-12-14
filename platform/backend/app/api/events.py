from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import SecurityEvent
from app.schemas.security_events import SecurityEventCreate, SecurityEventRead
from app.services.audit import record_audit
from app.services.risk import compute_risk_score

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[SecurityEventRead])
def list_events(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(SecurityEvent)).all()


@router.post("/", response_model=SecurityEventRead)
def create_event(event: SecurityEventCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    payload = event.dict()
    if payload.get("risk_score") in (None, 0):
        payload["risk_score"] = compute_risk_score(payload.get("severity", "info"), float(payload.get("confidence", 0.5)), payload.get("impact"))
    if not payload.get("attack_stage"):
        payload["attack_stage"] = "unknown"
    db_obj = SecurityEvent(**payload)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    record_audit(
        session,
        actor=current_user.username,
        action="security_event_create",
        resource=str(db_obj.id),
        detail={"severity": db_obj.severity, "asset_id": db_obj.asset_id, "risk_score": db_obj.risk_score},
    )
    return db_obj


@router.get("/{event_id}", response_model=SecurityEventRead)
def get_event(event_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    event = session.get(SecurityEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
