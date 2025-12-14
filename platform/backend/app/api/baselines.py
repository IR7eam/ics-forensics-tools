from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import BaselineProfile
from app.schemas.baselines import BaselineProfileCreate, BaselineProfileRead
from app.services.audit import record_audit

router = APIRouter(prefix="/baselines", tags=["baselines"])


@router.get("/", response_model=List[BaselineProfileRead])
def list_baselines(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(BaselineProfile)).all()


@router.post("/", response_model=BaselineProfileRead)
def create_baseline(baseline: BaselineProfileCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_obj = BaselineProfile.from_orm(baseline)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    record_audit(
        session,
        actor=current_user.username,
        action="baseline_create",
        resource=str(db_obj.id),
        detail={"asset_id": db_obj.asset_id, "protocol": db_obj.protocol},
    )
    return db_obj


@router.get("/{baseline_id}", response_model=BaselineProfileRead)
def get_baseline(baseline_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    baseline = session.get(BaselineProfile, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return baseline
