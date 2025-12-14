from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.models.core import EvidenceLink, Observation, RawEvidence, SecurityEvent


def _safe_timestamp(value: Optional[datetime]) -> datetime:
    return value or datetime.utcnow()


def build_evidence_chain(
    session: Session, asset_id: Optional[int] = None, attack_stage: Optional[str] = None
) -> Dict:
    """Aggregate observations, events, evidence, and links into a timeline-friendly shape."""

    entries: List[Dict] = []

    obs_by_id: Dict[int, Observation] = {}
    obs_query = select(Observation)
    if asset_id is not None:
        obs_query = obs_query.where(Observation.asset_id == asset_id)
    for obs in session.exec(obs_query):
        obs_by_id[obs.id] = obs
        entries.append(
            {
                "ref": f"observation:{obs.id}",
                "type": "observation",
                "timestamp": _safe_timestamp(obs.timestamp),
                "description": obs.parsed_data.get("summary")
                or obs.parsed_data.get("description")
                or f"Observation via {obs.protocol}",
                "protocol": obs.protocol,
                "asset_id": obs.asset_id,
                "attack_stage": None,
                "risk_score": None,
                "relation": None,
            }
        )

    event_query = select(SecurityEvent)
    if asset_id is not None:
        event_query = event_query.where(SecurityEvent.asset_id == asset_id)
    events = session.exec(event_query).all()
    if attack_stage:
        events = [evt for evt in events if evt.attack_stage == attack_stage]

    for event in events:
        entries.append(
            {
                "ref": f"event:{event.id}",
                "type": "security_event",
                "timestamp": _safe_timestamp(event.created_at),
                "description": event.description,
                "protocol": None,
                "asset_id": event.asset_id,
                "attack_stage": event.attack_stage,
                "risk_score": float(event.risk_score or 0.0),
                "relation": None,
            }
        )

    raw_evidence = session.exec(select(RawEvidence)).all()
    for evidence in raw_evidence:
        obs = obs_by_id.get(evidence.observation_id) if evidence.observation_id else None
        if asset_id is not None and (not obs or obs.asset_id != asset_id):
            continue
        entries.append(
            {
                "ref": f"evidence:{evidence.id}",
                "type": "raw_evidence",
                "timestamp": _safe_timestamp(evidence.created_at),
                "description": evidence.context.get("summary")
                or evidence.context.get("path")
                or evidence.storage_path,
                "protocol": getattr(obs, "protocol", None),
                "asset_id": getattr(obs, "asset_id", None),
                "attack_stage": None,
                "risk_score": None,
                "relation": None,
            }
        )

    links = session.exec(select(EvidenceLink)).all()
    for link in links:
        if asset_id is not None:
            # Only include links that reference the asset-specific observations or events
            if str(asset_id) not in (link.from_ref + link.to_ref):
                continue
        entries.append(
            {
                "ref": f"link:{link.id}",
                "type": "link",
                "timestamp": _safe_timestamp(link.created_at),
                "description": f"{link.from_ref} -> {link.to_ref}",
                "protocol": None,
                "asset_id": asset_id,
                "attack_stage": None,
                "risk_score": None,
                "relation": link.relation,
            }
        )

    entries.sort(key=lambda entry: entry["timestamp"])
    stage_counts = Counter(evt.attack_stage or "unknown" for evt in events)
    max_risk = max((float(evt.risk_score or 0.0) for evt in events), default=0.0)

    return {
        "entries": entries,
        "summary": {
            "stage_counts": dict(stage_counts),
            "max_risk": round(max_risk, 3),
            "total_entries": len(entries),
        },
    }
