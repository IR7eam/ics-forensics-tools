from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogRead


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogRead])
def list_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    query = select(AuditLog)
    if actor:
        query = query.where(AuditLog.actor.contains(actor))
    if action:
        query = query.where(AuditLog.action.contains(action))
    if resource:
        query = query.where(AuditLog.resource.contains(resource))
    if status:
        query = query.where(AuditLog.status == status)

    query = query.order_by(AuditLog.timestamp.desc()).limit(min(limit, 1000))
    return session.exec(query).all()


@router.post("/", response_model=AuditLogRead)
def create_log(
    log: AuditLogCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.admin)),
):
    record = AuditLog.from_orm(log)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/{log_id}", response_model=AuditLogRead)
def get_log(
    log_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.admin))
):
    record = session.get(AuditLog, log_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record
