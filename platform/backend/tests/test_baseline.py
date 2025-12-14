from sqlmodel import SQLModel, Session, create_engine, select

from app.models.core import Asset, Observation, SecurityEvent
from app.services.baseline import evaluate_metrics_against_baseline, train_baseline_profile


def _seed_observations(session: Session, asset_id: int, protocol: str):
    for latency in [20.0, 22.0, 24.0, 20.0]:
        session.add(
            Observation(
                asset_id=asset_id,
                protocol=protocol,
                metrics={"latency_ms": latency, "errors": 0},
            )
        )
    session.commit()


def test_train_baseline_profile_builds_stats():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        asset = Asset(ip="10.0.0.1", device_type="plc")
        session.add(asset)
        session.commit()
        session.refresh(asset)

        _seed_observations(session, asset.id, "modbus/tcp")

        profile = train_baseline_profile(session, asset_id=asset.id, protocol="modbus/tcp")
        assert "latency_ms" in profile.metrics_baseline
        stats = profile.metrics_baseline["latency_ms"]
        assert stats["count"] == 4
        assert stats["mean"] > 0


def test_evaluate_metrics_against_baseline_creates_event():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        asset = Asset(ip="10.0.0.2", device_type="gateway")
        session.add(asset)
        session.commit()
        session.refresh(asset)

        _seed_observations(session, asset.id, "opc-ua")
        train_baseline_profile(session, asset_id=asset.id, protocol="opc-ua")

        result = evaluate_metrics_against_baseline(
            session=session,
            asset_id=asset.id,
            protocol="opc-ua",
            metrics={"latency_ms": 50.0},
            threshold=2.0,
        )

        assert result["deviations"] == ["latency_ms"]
        events = session.exec(select(SecurityEvent)).all()
        assert len(events) == 1
        assert events[0].category == "baseline_deviation"
        assert events[0].risk_score > 0
