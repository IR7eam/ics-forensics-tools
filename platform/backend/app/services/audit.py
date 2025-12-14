from typing import Optional

from sqlmodel import Session

from app.models.core import AuditLog


def record_audit(
    session: Session,
    actor: str,
    action: str,
    resource: str,
    detail: Optional[dict] = None,
    status: str = "success",
) -> AuditLog:
    entry = AuditLog(actor=actor, action=action, resource=resource, status=status, detail=detail or {})
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
