from fastapi.testclient import TestClient

from app.main import app
from app.db.session import init_db


client = TestClient(app)


def test_import_and_export_roundtrip(tmp_path):
    init_db()
    csv_content = "ip,hostname,device_type,protocols,tags\n10.0.0.1,plc-a,plc,modbus/snmp;opcua,critical\n"
    files = {"file": ("assets.csv", csv_content, "text/csv")}
    token = client.post(
        "/api/auth/token",
        data={"username": "analyst", "password": "analyst"},
    ).json()["access_token"]
    resp = client.post("/api/assets/import", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    created = resp.json()
    assert len(created) == 1
    assert created[0]["ip"] == "10.0.0.1"
    assert "modbus/snmp" in created[0]["protocols"]

    viewer_token = client.post(
        "/api/auth/token",
        data={"username": "viewer", "password": "viewer"},
    ).json()["access_token"]
    export_resp = client.get("/api/assets/export", headers={"Authorization": f"Bearer {viewer_token}"})
    assert export_resp.status_code == 200
    export_csv = export_resp.text
    assert "10.0.0.1" in export_csv
    assert "plc-a" in export_csv

