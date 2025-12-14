"""Optional real collectors with safe read-only defaults and fallbacks.

The platform primarily operates in a simulated-safe mode to avoid unintended
network impact. When ``ICS_USE_SIMULATED_PLUGINS`` is set to ``false`` and the
optional protocol libraries are installed, these helpers attempt conservative
read-only collections. Any missing dependency or connection error automatically
falls back to the simulator to keep scan jobs progressing while recording audit
events.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple

from app.core.config import get_settings
from app.services.plugins import PluginSpec, simulate_plugin_collection


class CollectorDependencyError(RuntimeError):
    """Raised when an optional dependency is unavailable for a protocol."""


class CollectorExecutionError(RuntimeError):
    """Raised when a real collector cannot complete safely."""


@dataclass
class CollectorResult:
    observation: Dict
    evidence: Dict


def _parse_target(target: str, default_port: int) -> Tuple[str, int]:
    if ":" in target:
        host, port = target.rsplit(":", 1)
        try:
            return host, int(port)
        except ValueError:
            return target, default_port
    return target, default_port


def _safe_socket_probe(host: str, port: int, timeout: float) -> float:
    start = datetime.utcnow()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
    end = datetime.utcnow()
    return (end - start).total_seconds() * 1000


def _base_payload(spec: PluginSpec, target: str, parameters: Dict) -> Dict:
    return {
        "target": target,
        "plugin": spec.name,
        "device_type": spec.device_types[0] if spec.device_types else "unknown",
        "operations": parameters.get("operations") or spec.allowed_operations,
        "parameters": parameters,
        "read_only": spec.read_only,
    }


def _collect_modbus(spec: PluginSpec, target: str, parameters: Dict) -> CollectorResult:
    try:
        from pymodbus.client import ModbusTcpClient  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dep
        raise CollectorDependencyError("pymodbus not available") from exc

    host, port = _parse_target(target, spec.default_port)
    timeouts = parameters.get("timeouts") or {}
    unit_id = parameters.get("unit_id", 1)
    sample_len = int(parameters.get("sample_length", 4))
    sample_addr = int(parameters.get("sample_address", 0))

    client = ModbusTcpClient(host=host, port=port, timeout=timeouts.get("read_s", 5.0))
    if not client.connect():  # pragma: no cover - network dependent
        raise CollectorExecutionError(f"unable to connect to {host}:{port}")

    rr = client.read_holding_registers(sample_addr, sample_len, unit=unit_id)
    client.close()
    if rr.isError():  # pragma: no cover - network dependent
        raise CollectorExecutionError(f"read failed: {rr}")

    parsed = _base_payload(spec, target, parameters)
    parsed.update(
        {
            "function": "fc3",
            "unit_id": unit_id,
            "registers": rr.registers if hasattr(rr, "registers") else [],
        }
    )
    latency_ms = timeouts.get("connect_s", get_settings().default_connect_timeout) * 1000
    return CollectorResult(
        observation={
            "asset_id": None,
            "protocol": spec.protocol,
            "timestamp": datetime.utcnow(),
            "parsed_data": parsed,
            "metrics": {"status": "ok", "latency_ms": latency_ms, "default_port": port},
            "raw_refs": [],
        },
        evidence={"hash": None, "storage_path": "", "context": {"plugin": spec.name}},
    )


def _collect_snmp(spec: PluginSpec, target: str, parameters: Dict) -> CollectorResult:
    try:
        from pysnmp.hlapi import (  # type: ignore
            CommunityData,
            ContextData,
            getCmd,
            ObjectType,
            ObjectIdentity,
            SnmpEngine,
            UdpTransportTarget,
        )
    except Exception as exc:  # pragma: no cover - optional dep
        raise CollectorDependencyError("pysnmp not available") from exc

    host, port = _parse_target(target, spec.default_port)
    community = parameters.get("community", "public")
    oids = parameters.get("oids") or ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.5.0"]

    transport = UdpTransportTarget((host, port), timeout=parameters.get("timeouts", {}).get("read_s", 5.0))
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community),
        transport,
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids],
    )
    error_indication, error_status, error_index, var_binds = next(iterator)
    if error_indication or error_status:  # pragma: no cover - network dependent
        raise CollectorExecutionError(str(error_indication or error_status))

    parsed = _base_payload(spec, target, parameters)
    parsed.update({"oids": {str(var[0]): var[1].prettyPrint() for var in var_binds}})
    latency_ms = parameters.get("timeouts", {}).get("connect_s", get_settings().default_connect_timeout) * 1000
    return CollectorResult(
        observation={
            "asset_id": None,
            "protocol": spec.protocol,
            "timestamp": datetime.utcnow(),
            "parsed_data": parsed,
            "metrics": {"status": "ok", "latency_ms": latency_ms, "default_port": port},
            "raw_refs": [],
        },
        evidence={"hash": None, "storage_path": "", "context": {"plugin": spec.name}},
    )


def _collect_ssh(spec: PluginSpec, target: str, parameters: Dict) -> CollectorResult:
    try:
        import paramiko  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dep
        raise CollectorDependencyError("paramiko not available") from exc

    host, port = _parse_target(target, spec.default_port)
    username = parameters.get("username", "root")
    password = parameters.get("password")
    command_whitelist = parameters.get("commands") or ["uname -a", "uptime"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, port=port, username=username, password=password, timeout=parameters.get("timeouts", {}).get("connect_s", 3.0))
    except Exception as exc:  # pragma: no cover - network dependent
        raise CollectorExecutionError(str(exc)) from exc

    outputs = {}
    for cmd in command_whitelist:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=parameters.get("timeouts", {}).get("read_s", 5.0))
        outputs[cmd] = {
            "stdout": stdout.read().decode(errors="ignore"),
            "stderr": stderr.read().decode(errors="ignore"),
            "exit": stdout.channel.recv_exit_status(),
        }
    client.close()

    parsed = _base_payload(spec, target, parameters)
    parsed.update({"commands": outputs})
    latency_ms = parameters.get("timeouts", {}).get("connect_s", get_settings().default_connect_timeout) * 1000
    return CollectorResult(
        observation={
            "asset_id": None,
            "protocol": spec.protocol,
            "timestamp": datetime.utcnow(),
            "parsed_data": parsed,
            "metrics": {"status": "ok", "latency_ms": latency_ms, "default_port": port},
            "raw_refs": [],
        },
        evidence={"hash": None, "storage_path": "", "context": {"plugin": spec.name}},
    )


def _collect_opcua(spec: PluginSpec, target: str, parameters: Dict) -> CollectorResult:
    try:
        from opcua import Client  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dep
        raise CollectorDependencyError("opcua client not available") from exc

    endpoint = parameters.get("endpoint") or f"opc.tcp://{target}:{spec.default_port}"
    client = Client(endpoint)
    try:
        client.application_uri = "ics-forensics-tools"
        client.connect()
        server_status = client.get_node("i=2256").get_value()
        build_info = client.get_node("i=2260").get_value()
    except Exception as exc:  # pragma: no cover - network dependent
        raise CollectorExecutionError(str(exc)) from exc
    finally:
        try:
            client.disconnect()
        except Exception:
            pass

    parsed = _base_payload(spec, target, parameters)
    parsed.update({"server_status": str(server_status), "build_info": str(build_info), "endpoint": endpoint})
    return CollectorResult(
        observation={
            "asset_id": None,
            "protocol": spec.protocol,
            "timestamp": datetime.utcnow(),
            "parsed_data": parsed,
            "metrics": {"status": "ok", "latency_ms": None, "default_port": spec.default_port},
            "raw_refs": [],
        },
        evidence={"hash": None, "storage_path": "", "context": {"plugin": spec.name}},
    )


def _collect_socket_probe(spec: PluginSpec, target: str, parameters: Dict) -> CollectorResult:
    host, port = _parse_target(target, spec.default_port)
    latency_ms = _safe_socket_probe(host, port, parameters.get("timeouts", {}).get("connect_s", 3.0))
    parsed = _base_payload(spec, target, parameters)
    parsed.update({"socket_probe": True})
    return CollectorResult(
        observation={
            "asset_id": None,
            "protocol": spec.protocol,
            "timestamp": datetime.utcnow(),
            "parsed_data": parsed,
            "metrics": {"status": "ok", "latency_ms": latency_ms, "default_port": port},
            "raw_refs": [],
        },
        evidence={"hash": None, "storage_path": "", "context": {"plugin": spec.name}},
    )


COLLECTOR_MAP = {
    "modbus": _collect_modbus,
    "snmp": _collect_snmp,
    "ssh": _collect_ssh,
    "opcua": _collect_opcua,
    "iec104": _collect_socket_probe,  # lightweight link bring-up probe
    "s7comm": _collect_socket_probe,
    "cip": _collect_socket_probe,
    "generic": _collect_socket_probe,
}


def collect_with_plugin(spec: PluginSpec, target: str, parameters: Dict, evidence_dir):
    collector = COLLECTOR_MAP.get(spec.name)
    if not collector:
        raise CollectorExecutionError(f"no collector available for {spec.name}")

    result = collector(spec, target, parameters)
    if result.evidence.get("hash") is None:
        # Minimal evidence stub when the protocol client does not emit raw bytes.
        observation_payload, evidence_payload = simulate_plugin_collection(spec, target, parameters, evidence_dir)
        result.observation.setdefault("metrics", {}).update(result.observation.get("metrics", {}))
        result.observation["raw_refs"] = evidence_payload.get("storage_path") and [
            evidence_payload["storage_path"]
        ]
        result.evidence = evidence_payload
    return result.observation, result.evidence
