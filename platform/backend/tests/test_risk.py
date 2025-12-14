from app.services.risk import ATTACK_STAGES, compute_risk_score, summarize_attack_stages


def test_compute_risk_score_bounds():
    assert 0 <= compute_risk_score("info", 0.2, None) <= 1
    assert compute_risk_score("high", 0.9, "integrity") > compute_risk_score("low", 0.2, None)


def test_summarize_attack_stages():
    events = [
        {"attack_stage": "reconnaissance", "risk_score": 0.3},
        {"attack_stage": "control", "risk_score": 0.8},
        {"attack_stage": "control", "risk_score": 0.4},
    ]
    summary = summarize_attack_stages(events)
    assert summary["control"]["count"] == 2
    assert summary["control"]["max_risk"] == 0.8
    assert "unknown" not in summary
    assert set(summary.keys()).issubset(set(ATTACK_STAGES + ["control"]))
