from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.core import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogRead


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogRead])
def list_logs(
    session: Session = Depends(get_session), current_user=Depends(get_current_user)
):
    return session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc())).all()


@router.post("/", response_model=AuditLogRead)
def create_log(
    log: AuditLogCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    record = AuditLog.from_orm(log)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/{log_id}", response_model=AuditLogRead)
def get_log(
    log_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)
):
    record = session.get(AuditLog, log_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record
