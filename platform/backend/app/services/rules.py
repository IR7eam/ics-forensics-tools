from pathlib import Path
from typing import Any, Dict, List

import yaml

from app.services.risk import compute_risk_score


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
