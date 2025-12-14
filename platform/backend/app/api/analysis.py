from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.services.anomaly import detect_anomalies
from app.services.rules import RuleEngine, load_rules_from_file

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/rules/evaluate")
def evaluate_rules(
    payload: Dict,
    rule_file: str = "rules/sample_rules.yml",
    current_user=Depends(get_current_user),
):
    path = Path(rule_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rule file not found")
    rules = load_rules_from_file(path)
    engine = RuleEngine(rules)
    return {"matches": engine.evaluate(payload)}


@router.post("/anomaly")
def run_anomaly_detection(metrics: Dict[str, List[float]], current_user=Depends(get_current_user)):
    return detect_anomalies(metrics)
