from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import EvidenceLink
from app.schemas.evidence_links import EvidenceLinkCreate, EvidenceLinkRead
from app.services.audit import record_audit

router = APIRouter(prefix="/evidence-links", tags=["evidence-links"])


@router.get("/", response_model=List[EvidenceLinkRead])
def list_links(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(EvidenceLink)).all()


@router.post("/", response_model=EvidenceLinkRead)
def create_link(item: EvidenceLinkCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_obj = EvidenceLink.from_orm(item)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    record_audit(
        session,
        actor=current_user.username,
        action="evidence_link_create",
        resource=str(db_obj.id),
        detail={"from": db_obj.from_ref, "to": db_obj.to_ref},
    )
    return db_obj


@router.get("/{link_id}", response_model=EvidenceLinkRead)
def get_link(link_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    link = session.get(EvidenceLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Evidence link not found")
    return link
