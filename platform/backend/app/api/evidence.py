from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import RawEvidence
from app.schemas.evidence import RawEvidenceCreate, RawEvidenceRead
from app.services.audit import record_audit

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/", response_model=List[RawEvidenceRead])
def list_evidence(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(RawEvidence)).all()


@router.post("/", response_model=RawEvidenceRead)
def create_evidence(item: RawEvidenceCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_obj = RawEvidence.from_orm(item)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    record_audit(
        session,
        actor=current_user.username,
        action="evidence_create",
        resource=str(db_obj.id),
        detail={"observation_id": db_obj.observation_id},
    )
    return db_obj


@router.get("/{evidence_id}", response_model=RawEvidenceRead)
def get_evidence(evidence_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    evidence = session.get(RawEvidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence
