from collections import defaultdict
from typing import Dict, Iterable, List, Optional


ATTACK_STAGES = [
    "reconnaissance",
    "intrusion",
    "lateral_movement",
    "control",
    "impact",
    "recovery",
]


_SEVERITY_WEIGHTS: Dict[str, float] = {
    "critical": 1.0,
    "high": 0.9,
    "medium": 0.6,
    "low": 0.3,
    "info": 0.1,
}

_IMPACT_WEIGHTS: Dict[str, float] = {
    "safety": 1.0,
    "availability": 0.8,
    "integrity": 0.7,
    "confidentiality": 0.5,
}


def compute_risk_score(severity: str, confidence: float, impact: Optional[str] = None) -> float:
    """Derive a bounded risk score from severity/confidence/impact metadata."""

    sev_weight = _SEVERITY_WEIGHTS.get(severity, 0.1)
    impact_weight = _IMPACT_WEIGHTS.get(impact, 0.2 if impact else 0.0)
    score = (sev_weight * 0.6) + (max(min(confidence, 1.0), 0.0) * 0.3) + (impact_weight * 0.1)
    return round(min(max(score, 0.0), 1.0), 3)


def summarize_attack_stages(events: Iterable[Dict]) -> Dict[str, Dict[str, float]]:
    """Return per-stage counts and maximum risk to drive UI timelines."""

    summary: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "max_risk": 0.0})
    for event in events:
        stage = event.get("attack_stage") or "unknown"
        stage_entry = summary[stage]
        stage_entry["count"] += 1
        stage_entry["max_risk"] = max(stage_entry["max_risk"], float(event.get("risk_score", 0.0)))
    return summary
