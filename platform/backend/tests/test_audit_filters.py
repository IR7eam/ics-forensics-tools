from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import main
from app.db import session as db_session
from app.models.core import AuditLog


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


def seed_audit_entries(engine):
    with Session(engine) as session:
        session.add_all(
            [
                AuditLog(actor="analyst", action="asset_read", resource="asset:1", status="success"),
                AuditLog(actor="analyst", action="asset_create", resource="asset:2", status="success"),
                AuditLog(actor="viewer", action="asset_read", resource="asset:2", status="success"),
                AuditLog(actor="viewer", action="asset_read", resource="asset:3", status="denied"),
            ]
        )
        session.commit()


def test_audit_filters_require_role_and_filter():
    client, engine = setup_test_app()
    seed_audit_entries(engine)

    viewer_token = get_token(client, "viewer", "viewer")
    analyst_token = get_token(client, "analyst", "analyst")
    admin_token = get_token(client, "admin", "admin")

    # viewer is blocked
    denied = client.get("/api/audit", headers={"Authorization": f"Bearer {viewer_token}"})
    assert denied.status_code == 403

    # analyst can filter by actor and status
    resp = client.get(
        "/api/audit",
        params={"actor": "analyst", "status": "success"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert all(entry["actor"] == "analyst" for entry in entries)
    assert all(entry["status"] == "success" for entry in entries)

    # admin can limit results
    limited = client.get(
        "/api/audit", params={"limit": 2}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert limited.status_code == 200
    assert len(limited.json()) == 2
