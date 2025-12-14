from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.security import Role, require_role
from app.db.session import get_session
from app.schemas.rules import RulePackCreate, RulePackRead, RulePackUpdate
from app.services import rules as rule_service
from app.services.audit import record_audit
from app.services.rules import RuleEngine

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=List[RulePackRead])
def list_rules(
    enabled: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.viewer)),
):
    packs = rule_service.list_rule_packs(session, enabled=enabled)
    record_audit(
        session,
        actor=current_user.username,
        action="rules_list",
        resource="rules",
        detail={"count": len(packs)},
    )
    return packs


@router.post("/", response_model=RulePackRead)
def create_rule_pack(
    payload: RulePackCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    pack = rule_service.create_rule_pack(session, payload.dict())
    record_audit(
        session,
        actor=current_user.username,
        action="rule_pack_create",
        resource=str(pack.id),
        detail={"name": pack.name, "enabled": pack.enabled},
    )
    return pack


@router.patch("/{pack_id}", response_model=RulePackRead)
def update_rule_pack(
    pack_id: int,
    payload: RulePackUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    try:
        pack = rule_service.update_rule_pack(session, pack_id, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    record_audit(
        session,
        actor=current_user.username,
        action="rule_pack_update",
        resource=str(pack.id),
        detail={"enabled": pack.enabled},
    )
    return pack


@router.post("/{pack_id}/test")
def test_rule_pack(
    pack_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    try:
        rules = rule_service.load_rules_from_db(session, pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    engine = RuleEngine(rules)
    matches = engine.evaluate(payload)
    record_audit(
        session,
        actor=current_user.username,
        action="rule_pack_test",
        resource=str(pack_id),
        detail={"matches": len(matches)},
    )
    return {"matches": matches}
