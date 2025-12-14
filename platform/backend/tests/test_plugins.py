from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import main
from app.db import session as db_session
from app.services.plugins import PLUGIN_REGISTRY


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


def test_plugin_registry_endpoint_requires_viewer_and_returns_specs():
    client = setup_test_app()
    token = client.post("/api/auth/token", data={"username": "viewer", "password": "viewer"}).json()["access_token"]

    resp = client.get("/api/plugins/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, list)
    assert len(payload) == len(PLUGIN_REGISTRY)
    # ensure dangerous operations are surfaced for UI highlighting
    modbus = next((p for p in payload if p["name"] == "modbus"), None)
    assert modbus is not None
    assert "fc5" in modbus["dangerous_operations"]
