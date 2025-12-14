from pathlib import Path

from app.services.rules import RuleEngine, load_rules_from_file


def test_rule_engine_matches_write_block():
    path = Path(__file__).resolve().parents[1] / "rules" / "sample_rules.yml"
    rules = load_rules_from_file(path)
    engine = RuleEngine(rules)
    payload = {"protocol": "modbus", "parsed_data": {"function_code": 5}}
    matches = engine.evaluate(payload)
    match = next((m for m in matches if m["id"] == "modbus-read-only"), None)
    assert match is not None
    assert match["attack_stage"] == "control"
    assert match["risk_score"] > 0.5


def test_rule_engine_skips_read():
    path = Path(__file__).resolve().parents[1] / "rules" / "sample_rules.yml"
    rules = load_rules_from_file(path)
    engine = RuleEngine(rules)
    payload = {"protocol": "modbus", "parsed_data": {"function_code": 3}}
    matches = engine.evaluate(payload)
    assert matches == []
