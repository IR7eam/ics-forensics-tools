from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.core import EvidenceLink
from app.schemas.evidence_links import EvidenceLinkCreate, EvidenceLinkRead

router = APIRouter(prefix="/evidence-links", tags=["evidence-links"])


@router.get("/", response_model=List[EvidenceLinkRead])
def list_links(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    return session.exec(select(EvidenceLink)).all()


@router.post("/", response_model=EvidenceLinkRead)
def create_link(item: EvidenceLinkCreate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    db_obj = EvidenceLink.from_orm(item)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/{link_id}", response_model=EvidenceLinkRead)
def get_link(link_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    link = session.get(EvidenceLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Evidence link not found")
    return link
