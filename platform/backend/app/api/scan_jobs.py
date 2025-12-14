from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import ScanJob
from app.schemas.scan_jobs import ScanJobCreate, ScanJobRead, ScanJobUpdate
from app.services.audit import record_audit
from app.services.scanner import cancel_scan_job, enqueue_scan_job

router = APIRouter(prefix="/scan-jobs", tags=["scan-jobs"])


@router.get("/", response_model=List[ScanJobRead])
def list_jobs(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(ScanJob)).all()


@router.post("/", response_model=ScanJobRead)
def create_job(job: ScanJobCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    settings = get_settings()
    payload = job.dict()
    payload.setdefault("connect_timeout_s", settings.default_connect_timeout)
    payload.setdefault("read_timeout_s", settings.default_read_timeout)
    payload.setdefault("rate_limit_rps", settings.default_rate_limit_rps)
    payload.setdefault("max_retries", settings.max_retry_attempts)
    payload.setdefault("retry_backoff_s", settings.retry_backoff_seconds)
    db_job = ScanJob.from_orm(ScanJobCreate(**payload))
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    record_audit(
        session,
        actor=current_user.username,
        action="scan_job_create",
        resource=str(db_job.id),
        detail={"plugins": db_job.plugins, "targets": db_job.target_range},
    )
    return db_job


@router.get("/{job_id}", response_model=ScanJobRead)
def get_job(job_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    job = session.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    return job


@router.put("/{job_id}", response_model=ScanJobRead)
def update_job(job_id: int, job: ScanJobUpdate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_job = session.get(ScanJob, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    for key, value in job.dict(exclude_unset=True).items():
        setattr(db_job, key, value)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    record_audit(
        session,
        actor=current_user.username,
        action="scan_job_update",
        resource=str(db_job.id),
        detail=job.dict(exclude_unset=True),
    )
    return db_job


@router.post("/{job_id}/run", response_model=ScanJobRead)
def trigger_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    db_job = session.get(ScanJob, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    actor = getattr(current_user, "username", "system")
    background_tasks.add_task(enqueue_scan_job, job_id, actor)
    db_job.status = "queued"
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    record_audit(
        session,
        actor=actor,
        action="scan_job_queue",
        resource=str(job_id),
        detail={"plugins": db_job.plugins, "targets": db_job.target_range},
    )
    return db_job


@router.post("/{job_id}/cancel", response_model=ScanJobRead)
def cancel_job(job_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    job = session.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    actor = getattr(current_user, "username", "system")
    success = cancel_scan_job(job_id, actor)
    if not success:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    session.refresh(job)
    record_audit(
        session,
        actor=actor,
        action="scan_job_cancelled",
        resource=str(job_id),
        detail={"status": job.status},
    )
    return job
