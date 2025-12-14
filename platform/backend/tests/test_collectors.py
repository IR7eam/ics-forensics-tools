import socket
from pathlib import Path

import pytest

from app.services.collectors import collect_with_plugin
from app.services.plugins import PLUGIN_REGISTRY


class FakeSocket:
    def __init__(self, responses):
        self.responses = responses
        self.sent = []
        self.connected = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, addr):
        self.connected = addr

    def sendall(self, payload: bytes):
        self.sent.append(payload)

    def recv(self, size: int) -> bytes:
        return self.responses.pop(0) if self.responses else b""

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


@pytest.fixture
def fake_socket(monkeypatch):
    responses = [b"\x68\x04\x0b\x00\x00\x00", b"\x68\x04\x83\x00\x00\x00"]

    def _factory(*args, **kwargs):
        return FakeSocket(responses.copy())

    monkeypatch.setattr(socket, "socket", _factory)
    return responses


def test_iec104_collector_records_raw_evidence(tmp_path, fake_socket, monkeypatch):
    spec = PLUGIN_REGISTRY["iec104"]

    obs, evidence = collect_with_plugin(
        spec,
        target="127.0.0.1:2404",
        parameters={"timeouts": {"connect_s": 0.5, "read_s": 0.5}},
        evidence_dir=Path(tmp_path),
    )

    assert obs["protocol"] == "iec104"
    assert obs["parsed_data"]["link_status"] == "ok"
    assert obs["parsed_data"]["startdt"]["response_hex"]
    assert obs["raw_refs"], "raw evidence reference missing"
    assert evidence["hash"].startswith("sha256:")
    assert Path(evidence["storage_path"]).exists()


@pytest.mark.parametrize("frame_resp", [b"", b"\x68\x04\x83\x00\x00\x00"])
def test_iec104_handles_missing_frames(tmp_path, monkeypatch, frame_resp):
    responses = [frame_resp]

    def _factory(*args, **kwargs):
        return FakeSocket(responses.copy())

    monkeypatch.setattr(socket, "socket", _factory)

    spec = PLUGIN_REGISTRY["iec104"]
    obs, evidence = collect_with_plugin(
        spec,
        target="10.0.0.5",
        parameters={"timeouts": {"connect_s": 0.1, "read_s": 0.1}},
        evidence_dir=Path(tmp_path),
    )

    assert obs["metrics"]["status"] == "ok"
    assert evidence["hash"].startswith("sha256:")
    assert Path(evidence["storage_path"]).exists()
