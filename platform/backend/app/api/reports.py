from typing import List

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import Report
from app.schemas.reports import ReportCreate, ReportRead
from app.services.reports import generate_report
from app.services.audit import record_audit

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


@router.get("/", response_model=List[ReportRead])
def list_reports(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(Report)).all()


@router.post("/generate", response_model=ReportRead)
def create_report(payload: ReportCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    fmt = payload.format.lower()
    if fmt not in {"html", "pdf", "docx"}:
        raise HTTPException(status_code=400, detail="Unsupported format")
    report = generate_report(
        session=session,
        scope=payload.scope,
        parameters=payload.parameters,
        fmt=fmt,
        title=payload.title,
        output_dir=Path(settings.report_dir),
    )
    record_audit(
        session,
        actor=current_user.username,
        action="report_generate",
        resource=str(report.id),
        detail={"format": report.format},
    )
    return report


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
