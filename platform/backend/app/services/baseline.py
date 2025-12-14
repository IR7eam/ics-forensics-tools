"""Baseline training and deviation evaluation utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List

from sqlmodel import Session, select

from app.models.core import BaselineProfile, Observation, SecurityEvent
from app.services.risk import compute_risk_score


def _collect_numeric_metrics(observations: Iterable[Observation]) -> Dict[str, List[float]]:
    metrics: Dict[str, List[float]] = {}
    for obs in observations:
        for key, value in (obs.metrics or {}).items():
            if isinstance(value, (int, float)):
                metrics.setdefault(key, []).append(float(value))
    return metrics


def compute_baseline_from_observations(observations: Iterable[Observation]) -> Dict[str, Dict[str, float]]:
    numeric_metrics = _collect_numeric_metrics(observations)
    baseline: Dict[str, Dict[str, float]] = {}
    for name, values in numeric_metrics.items():
        if not values:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / max(len(values), 1)
        std = variance ** 0.5
        baseline[name] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "count": len(values),
        }
    return baseline


def train_baseline_profile(
    session: Session, asset_id: int, protocol: str, observations_limit: int = 200
) -> BaselineProfile:
    observations = (
        session.exec(
            select(Observation)
            .where(Observation.asset_id == asset_id)
            .where(Observation.protocol == protocol)
            .order_by(Observation.timestamp.desc())
            .limit(observations_limit)
        )
        .all()
    )
    if not observations:
        raise ValueError("No observations available to train baseline")

    metrics_baseline = compute_baseline_from_observations(observations)
    if not metrics_baseline:
        raise ValueError("Observations missing numeric metrics for baseline training")

    profile = (
        session.exec(
            select(BaselineProfile)
            .where(BaselineProfile.asset_id == asset_id)
            .where(BaselineProfile.protocol == protocol)
        ).first()
        or BaselineProfile(asset_id=asset_id, protocol=protocol)
    )
    profile.metrics_baseline = metrics_baseline
    profile.trained_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def evaluate_metrics_against_baseline(
    *,
    session: Session,
    asset_id: int,
    protocol: str,
    metrics: Dict[str, float],
    threshold: float = 3.0,
    create_event: bool = True,
) -> Dict:
    profile = session.exec(
        select(BaselineProfile)
        .where(BaselineProfile.asset_id == asset_id)
        .where(BaselineProfile.protocol == protocol)
    ).first()
    if not profile:
        raise ValueError("Baseline profile not found")

    deviations: List[str] = []
    comparison: Dict[str, Dict[str, float | bool]] = {}
    for name, value in metrics.items():
        baseline_metric = profile.metrics_baseline.get(name)
        if not baseline_metric:
            continue
        mean = baseline_metric.get("mean", 0.0)
        std = baseline_metric.get("std", 0.0) or 0.0
        zscore = abs(value - mean) / std if std else (1.0 if value != mean else 0.0)
        anomalous = zscore >= threshold
        comparison[name] = {
            "value": value,
            "baseline_mean": mean,
            "baseline_std": std,
            "zscore": round(zscore, 4),
            "anomalous": anomalous,
        }
        if anomalous:
            deviations.append(name)

    event_id = None
    if create_event and deviations:
        severity = "high" if len(deviations) > 1 else "medium"
        confidence = 0.7 if len(deviations) > 1 else 0.55
        risk_score = compute_risk_score(severity, confidence, impact="availability")
        description = (
            f"Baseline deviation for asset {asset_id} protocol {protocol}: "
            f"metrics {', '.join(deviations)} exceed z-score {threshold}"
        )
        event = SecurityEvent(
            asset_id=asset_id,
            severity=severity,
            confidence=confidence,
            impact="availability",
            attack_stage="reconnaissance",
            category="baseline_deviation",
            risk_score=risk_score,
            tags=["baseline", "anomaly"],
            recommendations=["Validate device availability and recent changes."],
            description=description,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        event_id = event.id

    return {"comparison": comparison, "deviations": deviations, "event_id": event_id}
