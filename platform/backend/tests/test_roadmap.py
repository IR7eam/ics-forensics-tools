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


def test_roadmap_endpoint_returns_progress_and_audits():
    client = setup_test_app()
    token = client.post("/api/auth/token", data={"username": "viewer", "password": "viewer"}).json()[
        "access_token"
    ]

    resp = client.get("/api/roadmap", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["iterations_remaining"] >= 1
    assert payload["delivered"] and payload["remaining"]
    assert any(item["category"] == "collection" for item in payload["in_progress"])

    audit_resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert audit_resp.status_code == 403

    admin_token = client.post("/api/auth/token", data={"username": "admin", "password": "admin"}).json()[
        "access_token"
    ]
    audit_resp = client.get("/api/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_resp.status_code == 200
    assert any(log["action"] == "roadmap.view" for log in audit_resp.json())
