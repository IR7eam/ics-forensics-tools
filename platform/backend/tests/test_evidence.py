from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app import main
from app.db import session as db_session
from app.models.core import AuditLog, RawEvidence


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


def test_evidence_download_serves_file_and_audits(tmp_path):
    client, engine = setup_test_app()
    evidence_file = tmp_path / "evidence.bin"
    payload = b"demo-bytes"
    evidence_file.write_bytes(payload)

    with Session(engine) as session:
        evidence = RawEvidence(
            observation_id=None,
            hash="sha256:" + sha256(payload).hexdigest(),
            storage_path=str(evidence_file),
            context={"plugin": "modbus"},
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)

    token = client.post(
        "/api/auth/token", data={"username": "viewer", "password": "viewer"}
    ).json()["access_token"]

    resp = client.get(
        f"/api/evidence/{evidence.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.content == payload
    assert resp.headers["content-type"].startswith("application/octet-stream")

    with Session(engine) as session:
        audits = session.exec(select(AuditLog)).all()
        assert any(a.action == "evidence_download" for a in audits)


def test_missing_file_returns_not_found(tmp_path):
    client, engine = setup_test_app()
    missing_path = Path(tmp_path / "missing.bin")

    with Session(engine) as session:
        evidence = RawEvidence(
            hash="sha256:" + sha256(b"missing").hexdigest(),
            storage_path=str(missing_path),
            context={},
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)

    token = client.post(
        "/api/auth/token", data={"username": "viewer", "password": "viewer"}
    ).json()["access_token"]

    resp = client.get(
        f"/api/evidence/{evidence.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
