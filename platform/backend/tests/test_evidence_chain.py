from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import main
from app.db import session as db_session
from app.models.core import Asset, EvidenceLink, Observation, RawEvidence, SecurityEvent


def setup_test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    main.app.dependency_overrides[db_session.get_session] = override_get_session
    return TestClient(main.app), engine


def get_token(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_evidence_chain_orders_entries_and_summarizes():
    client, engine = setup_test_app()

    with Session(engine) as session:
        asset = Asset(ip="10.1.1.10", hostname="plc")
        session.add(asset)
        session.commit()
        session.refresh(asset)
        asset_id = asset.id

        obs = Observation(
            asset_id=asset_id,
            protocol="modbus",
            parsed_data={"summary": "Holding registers"},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )
        event = SecurityEvent(
            asset_id=asset_id,
            attack_stage="control",
            risk_score=0.72,
            severity="high",
            description="Unexpected write attempt",
            created_at=datetime(2024, 1, 1, 12, 5, 0),
        )
        session.add_all([obs, event])
        session.commit()
        session.refresh(obs)
        session.refresh(event)

        raw = RawEvidence(
            observation_id=obs.id,
            hash="abc123",
            storage_path="/tmp/raw.bin",
            context={"summary": "pcap capture"},
            created_at=datetime(2024, 1, 1, 12, 10, 0),
        )
        link = EvidenceLink(
            from_ref=f"observation:{obs.id}",
            to_ref=f"event:{event.id}",
            relation="supports",
            created_at=datetime(2024, 1, 1, 12, 15, 0),
        )
        session.add_all([raw, link])
        session.commit()

    viewer_token = get_token(client, "viewer", "viewer")
    resp = client.get(
        "/api/analysis/evidence-chain",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()

    refs = [entry["ref"] for entry in body["entries"]]
    assert refs[0].startswith("observation:")
    assert refs[1].startswith("event:")
    assert refs[-1].startswith("link:")

    assert body["summary"]["total_entries"] == 4
    assert body["summary"]["stage_counts"].get("control") == 1
    assert body["summary"]["max_risk"] == 0.72

    filtered = client.get(
        "/api/analysis/evidence-chain",
        params={"asset_id": asset_id, "attack_stage": "impact"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert filtered.status_code == 200
    filtered_body = filtered.json()
    assert filtered_body["summary"]["stage_counts"] == {}
    assert filtered_body["summary"]["total_entries"] == 3  # observation, raw evidence, link
