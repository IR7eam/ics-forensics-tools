from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.security import Role, require_role
from app.db.session import get_session
from app.schemas.roadmap import RoadmapSummary
from app.services.roadmap import get_roadmap_summary
from app.services.audit import record_audit

router = APIRouter(tags=["roadmap"])


@router.get("/roadmap", response_model=RoadmapSummary)
def read_roadmap(
    session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))
):
    summary = get_roadmap_summary()
    record_audit(
        session,
        actor=current_user.username,
        action="roadmap.view",
        resource="roadmap",
        detail={"iterations_remaining": summary.iterations_remaining},
    )
    return summary
