from pathlib import Path
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import SecurityEvent
from app.services.audit import record_audit
from app.services.anomaly import detect_anomalies
from app.services.rules import RuleEngine, load_rules_from_file
from app.services.risk import summarize_attack_stages

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/rules/evaluate")
def evaluate_rules(
    payload: Dict,
    rule_file: str = "rules/sample_rules.yml",
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    path = Path(rule_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rule file not found")
    rules = load_rules_from_file(path)
    engine = RuleEngine(rules)
    matches = engine.evaluate(payload)
    record_audit(
        session,
        actor=current_user.username,
        action="rules_evaluate",
        resource=path.name,
        detail={"match_count": len(matches)},
    )
    return {"matches": matches}


@router.post("/anomaly")
def run_anomaly_detection(
    metrics: Dict[str, List[float]],
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    result = detect_anomalies(metrics)
    record_audit(
        session,
        actor=current_user.username,
        action="anomaly_detection",
        resource="metrics",
        detail={"metric_keys": list(metrics.keys())},
    )
    return result


@router.get("/attack-stages")
def summarize_stages(session: Session = Depends(get_session), current_user=Depends(require_role(Role.viewer))):
    events = session.exec(select(SecurityEvent)).all()
    summary = summarize_attack_stages([e.dict() for e in events])
    record_audit(
        session,
        actor=current_user.username,
        action="attack_stage_summary",
        resource="events",
        detail={"stages": list(summary.keys())},
    )
    return summary
