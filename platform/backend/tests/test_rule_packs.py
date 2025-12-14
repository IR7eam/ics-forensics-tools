from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import main
from app.db import session as db_session


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
    return TestClient(main.app)


def test_rule_pack_lifecycle():
    client = setup_test_app()
    token = client.post(
        "/api/auth/token", data={"username": "analyst", "password": "analyst"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_payload = {
        "name": "modbus-block-writes",
        "description": "Detect Modbus writes",
        "tags": ["modbus", "write"],
        "enabled": True,
        "rules": [
            {
                "id": "modbus-write",
                "name": "Modbus write detected",
                "conditions": [
                    {"field": "protocol", "op": "eq", "value": "modbus"},
                    {"field": "parsed_data.function_code", "op": "gt", "value": 4},
                ],
                "severity": "high",
            }
        ],
    }

    created = client.post("/api/rules/", json=create_payload, headers=headers)
    assert created.status_code == 200
    pack_id = created.json()["id"]

    listed = client.get("/api/rules/", headers=headers)
    assert listed.status_code == 200
    assert any(p["id"] == pack_id for p in listed.json())

    test_payload = {"protocol": "modbus", "parsed_data": {"function_code": 5}}
    test_resp = client.post(f"/api/rules/{pack_id}/test", json=test_payload, headers=headers)
    assert test_resp.status_code == 200
    assert test_resp.json()["matches"], "Expected rule match for modbus write"

    update_resp = client.patch(f"/api/rules/{pack_id}", json={"enabled": False}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["enabled"] is False
