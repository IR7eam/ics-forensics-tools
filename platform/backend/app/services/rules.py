from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.services.risk import compute_risk_score
from app.models.core import RulePack
from sqlmodel import Session, select


class RuleEngine:
    """Simple rule matcher that evaluates condition expressions on observation dicts."""

    def __init__(self, rules: List[dict]):
        self.rules = rules

    @staticmethod
    def _resolve_path(data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current: Any = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def evaluate(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        matched = []
        for rule in self.rules:
            conditions = rule.get("conditions", [])
            if all(self._evaluate_condition(payload, cond) for cond in conditions):
                severity = rule.get("severity", "info")
                confidence = float(rule.get("confidence", 0.5))
                impact = rule.get("impact")
                risk_score = rule.get("risk_score") or compute_risk_score(severity, confidence, impact)
                matched.append(
                    {
                        "id": rule.get("id"),
                        "name": rule.get("name"),
                        "description": rule.get("description"),
                        "severity": severity,
                        "confidence": confidence,
                        "impact": impact,
                        "attack_stage": rule.get("attack_stage"),
                        "category": rule.get("category"),
                        "risk_score": risk_score,
                        "recommendations": rule.get("recommendations", []),
                        "evidence": payload,
                    }
                )
        return matched

    def _evaluate_condition(self, payload: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        field_path = condition.get("field")
        op = condition.get("op")
        value = condition.get("value")
        actual = self._resolve_path(payload, field_path) if field_path else None
        if op == "eq":
            return actual == value
        if op == "neq":
            return actual != value
        if op == "gt":
            return actual is not None and actual > value
        if op == "lt":
            return actual is not None and actual < value
        if op == "regex":
            import re

            return actual is not None and re.search(value, str(actual)) is not None
        if op == "in":
            return isinstance(value, list) and actual in value
        return False


def load_rules_from_file(path: Path) -> List[dict]:
    content = yaml.safe_load(path.read_text())
    return content.get("rules", []) if isinstance(content, dict) else []


def load_rules_from_db(session: Session, rule_pack_id: int) -> List[dict]:
    pack = session.get(RulePack, rule_pack_id)
    if not pack:
        raise ValueError("Rule pack not found")
    return pack.rules or []


def list_rule_packs(session: Session, enabled: Optional[bool] = None) -> List[RulePack]:
    query = select(RulePack)
    if enabled is not None:
        query = query.where(RulePack.enabled == enabled)
    return session.exec(query).all()


def create_rule_pack(session: Session, data: Dict[str, Any]) -> RulePack:
    pack = RulePack(**data)
    session.add(pack)
    session.commit()
    session.refresh(pack)
    return pack


def update_rule_pack(session: Session, pack_id: int, data: Dict[str, Any]) -> RulePack:
    pack = session.get(RulePack, pack_id)
    if not pack:
        raise ValueError("Rule pack not found")
    for key, value in data.items():
        if value is not None:
            setattr(pack, key, value)
    pack.updated_at = datetime.utcnow()
    session.add(pack)
    session.commit()
    session.refresh(pack)
    return pack
