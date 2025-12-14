from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.core import ScanJob
from app.schemas.scan_jobs import ScanJobCreate, ScanJobRead, ScanJobUpdate
from app.services.scanner import run_scan_job

router = APIRouter(prefix="/scan-jobs", tags=["scan-jobs"])


@router.get("/", response_model=List[ScanJobRead])
def list_jobs(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    return session.exec(select(ScanJob)).all()


@router.post("/", response_model=ScanJobRead)
def create_job(job: ScanJobCreate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    db_job = ScanJob.from_orm(job)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job


@router.get("/{job_id}", response_model=ScanJobRead)
def get_job(job_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    job = session.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    return job


@router.put("/{job_id}", response_model=ScanJobRead)
def update_job(job_id: int, job: ScanJobUpdate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    db_job = session.get(ScanJob, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    for key, value in job.dict(exclude_unset=True).items():
        setattr(db_job, key, value)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job


@router.post("/{job_id}/run", response_model=ScanJobRead)
def trigger_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    db_job = session.get(ScanJob, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="ScanJob not found")
    actor = getattr(current_user, "username", "system")
    background_tasks.add_task(run_scan_job, job_id, actor)
    db_job.status = "queued"
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job
