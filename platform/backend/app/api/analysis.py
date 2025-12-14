from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import Role, require_role
from app.db.session import get_session
from app.models.core import SecurityEvent
from app.schemas.baselines import (
    BaselineEvaluateRequest,
    BaselineEvaluateResult,
    BaselineProfileRead,
    BaselineTrainRequest,
)
from app.services.audit import record_audit
from app.services.anomaly import detect_anomalies
from app.services.baseline import evaluate_metrics_against_baseline, train_baseline_profile
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


@router.post("/baseline/train", response_model=BaselineProfileRead)
def train_baseline(
    request: BaselineTrainRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    try:
        profile = train_baseline_profile(
            session,
            asset_id=request.asset_id,
            protocol=request.protocol,
            observations_limit=request.observations_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_audit(
        session,
        actor=current_user.username,
        action="baseline_train",
        resource=str(profile.id),
        detail={"asset_id": profile.asset_id, "protocol": profile.protocol},
    )
    return profile


@router.post("/baseline/evaluate", response_model=BaselineEvaluateResult)
def evaluate_baseline(
    request: BaselineEvaluateRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(Role.analyst)),
):
    try:
        result = evaluate_metrics_against_baseline(
            session=session,
            asset_id=request.asset_id,
            protocol=request.protocol,
            metrics=request.metrics,
            threshold=request.threshold,
            create_event=request.create_event,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_audit(
        session,
        actor=current_user.username,
        action="baseline_evaluate",
        resource=f"asset:{request.asset_id}",
        detail={
            "protocol": request.protocol,
            "deviations": result["deviations"],
            "event_id": result.get("event_id"),
        },
    )
    return result
