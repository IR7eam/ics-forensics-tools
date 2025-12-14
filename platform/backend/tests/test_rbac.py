from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import main
from app.db import session as db_session
from app.models.core import AuditLog, Asset


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


def test_rbac_enforces_roles_and_audits_actions():
    client, engine = setup_test_app()

    viewer_token = get_token(client, "viewer", "viewer")
    analyst_token = get_token(client, "analyst", "analyst")
    admin_token = get_token(client, "admin", "admin")

    # viewer can read but not create
    resp = client.get("/api/assets", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 200

    resp = client.post(
        "/api/assets",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"ip": "10.0.0.10", "hostname": "viewer-host"},
    )
    assert resp.status_code == 403

    # analyst can create assets and triggers audit
    create_resp = client.post(
        "/api/assets",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"ip": "10.0.0.11", "hostname": "plc"},
    )
    assert create_resp.status_code == 200
    asset_id = create_resp.json()["id"]

    # admin can review audit trail and see asset_create entry
    audit_resp = client.get("/api/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_resp.status_code == 200
    audit_entries = audit_resp.json()
    assert any(entry["action"] == "asset_create" for entry in audit_entries)

    # ensure asset persisted in test database
    with Session(engine) as session:
        stored = session.get(Asset, asset_id)
        assert stored is not None
        assert session.query(AuditLog).count() >= 1
