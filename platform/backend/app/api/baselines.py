from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.core import BaselineProfile
from app.schemas.baselines import BaselineProfileCreate, BaselineProfileRead

router = APIRouter(prefix="/baselines", tags=["baselines"])


@router.get("/", response_model=List[BaselineProfileRead])
def list_baselines(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    return session.exec(select(BaselineProfile)).all()


@router.post("/", response_model=BaselineProfileRead)
def create_baseline(baseline: BaselineProfileCreate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    db_obj = BaselineProfile.from_orm(baseline)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/{baseline_id}", response_model=BaselineProfileRead)
def get_baseline(baseline_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    baseline = session.get(BaselineProfile, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return baseline
