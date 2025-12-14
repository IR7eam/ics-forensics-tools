from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import Observation
from app.schemas.observations import ObservationCreate, ObservationRead

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("/", response_model=List[ObservationRead])
def list_observations(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    return session.exec(select(Observation)).all()


@router.post("/", response_model=ObservationRead)
def create_observation(observation: ObservationCreate, session: Session = Depends(get_session), current_user=Depends(require_role(Role.analyst))):
    db_obj = Observation.from_orm(observation)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


@router.get("/{observation_id}", response_model=ObservationRead)
def get_observation(observation_id: int, session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    observation = session.get(Observation, observation_id)
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation
