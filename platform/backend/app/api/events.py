from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.core import SecurityEvent
from app.schemas.security_events import SecurityEventCreate, SecurityEventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[SecurityEventRead])
def list_events(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    return session.exec(select(SecurityEvent)).all()


@router.post("/", response_model=SecurityEventRead)
def create_event(event: SecurityEventCreate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    db_obj = SecurityEvent.from_orm(event)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/{event_id}", response_model=SecurityEventRead)
def get_event(event_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    event = session.get(SecurityEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
