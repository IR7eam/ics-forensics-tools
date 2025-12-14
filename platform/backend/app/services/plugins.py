"""Registry of read-only protocol collectors and simulation helpers.

This module provides metadata for each protocol plugin we plan to support
in the staged delivery. The current implementation simulates read-only
collection results while applying latency and hashing so the rest of the
platform can exercise normalization, audit logging, and reporting flows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Tuple

from app.core.config import get_settings


@dataclass
class PluginSpec:
    name: str
    protocol: str
    device_types: List[str]
    default_port: int
    description: str
    read_only: bool = True
    allowed_operations: List[str] = field(default_factory=list)
    dangerous_operations: List[str] = field(default_factory=list)
    enforce_opt_in: bool = True
    notes: str = ""


PLUGIN_REGISTRY: Dict[str, PluginSpec] = {
    "modbus": PluginSpec(
        name="modbus",
        protocol="modbus/tcp",
        device_types=["plc", "rtu", "gateway"],
        default_port=502,
        description="Read-only Modbus/TCP identification and register sampling",
        allowed_operations=["fc3", "fc4", "diagnostic"],
        dangerous_operations=["fc5", "fc6", "fc15", "fc16"],
        notes="Limited to read functions and conservative range probing with rate limits.",
    ),
    "s7comm": PluginSpec(
        name="s7comm",
        protocol="s7comm",
        device_types=["plc"],
        default_port=102,
        description="Siemens S7 read-only identification (S7-300/400) including run/comm status",
        allowed_operations=["cotp_connect", "szl_id", "read_data"],
        dangerous_operations=["write_data", "mode_transition"],
        notes="Run/stop transitions and writes remain disabled; only read SZL/system data blocks are allowed.",
    ),
    "cip": PluginSpec(
        name="cip",
        protocol="ethernet/ip-cip",
        device_types=["plc"],
        default_port=44818,
        description="Rockwell/AB Logix read-only identity and connection status sampling",
        allowed_operations=["list_identity", "list_services", "read_tag"],
        dangerous_operations=["write_tag", "download_program"],
        notes="Only identity and read-tag paths are permitted by default.",
    ),
    "opcua": PluginSpec(
        name="opcua",
        protocol="opc-ua",
        device_types=["plc", "rtu", "gateway"],
        default_port=4840,
        description="OPC UA endpoint discovery and ServerStatus browse (read-only)",
        allowed_operations=["endpoint_discovery", "browse", "read_status"],
    ),
    "iec104": PluginSpec(
        name="iec104",
        protocol="iec104",
        device_types=["rtu", "substation"],
        default_port=2404,
        description="IEC 60870-5-104 link bring-up with optional total call (disabled by default)",
        allowed_operations=["startdt", "testfr"],
        dangerous_operations=["total_call"],
        notes="C_IC_NA_1 total call must be opt-in via configuration.",
    ),
    "snmp": PluginSpec(
        name="snmp",
        protocol="snmp",
        device_types=["gateway", "network-security"],
        default_port=161,
        description="SNMPv2c/v3 read-only sysDescr/sysName/ifTable sampling",
        allowed_operations=["get", "getnext", "walk"],
        dangerous_operations=["set"],
    ),
    "ssh": PluginSpec(
        name="ssh",
        protocol="ssh",
        device_types=["server", "network-security"],
        default_port=22,
        description="SSH banner/hostkey probing with optional safe command whitelist",
        allowed_operations=["banner", "hostkey", "uname", "uptime", "ip_a"],
        dangerous_operations=["sudo", "shell", "configure_terminal", "reload"],
        notes="Side-effecting commands remain disabled unless explicitly allowed in config.",
    ),
    "generic": PluginSpec(
        name="generic",
        protocol="generic",
        device_types=["unknown"],
        default_port=0,
        description="Fallback collector for placeholder simulations",
        allowed_operations=["probe"],
    ),
}


def validate_operations(spec: PluginSpec, requested_ops: List[str] | None, allow_side_effects: bool) -> List[str]:
    """Return the operations to perform after enforcing read-only policy."""

    if not requested_ops:
        return spec.allowed_operations

    unsupported = [op for op in requested_ops if op not in spec.allowed_operations + spec.dangerous_operations]
    if unsupported:
        raise ValueError(f"Unsupported operations for {spec.name}: {unsupported}")

    dangerous = [op for op in requested_ops if op in spec.dangerous_operations]
    if dangerous and (spec.enforce_opt_in and not allow_side_effects):
        raise PermissionError(f"Side-effecting operations require opt-in: {dangerous}")

    return requested_ops


def _write_evidence_bytes(content: bytes, spec: PluginSpec, target: str, evidence_dir: Path) -> Path:
    """Persist evidence bytes into a structured evidence directory."""

    safe_proto = spec.protocol.replace("/", "_")
    safe_target = target.replace(":", "_").replace("/", "_")
    target_dir = evidence_dir / safe_proto / safe_target
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{datetime.utcnow().isoformat()}.bin"
    path.write_bytes(content)
    return path


def simulate_plugin_collection(
    spec: PluginSpec, target: str, parameters: Dict, evidence_dir: Path | None = None
) -> Tuple[dict, dict]:
    """Create observation/evidence payloads for a simulated plugin run.

    The payloads mirror Observation/RawEvidence fields so the scanner can persist
    them without knowing protocol specifics. Hashes are deterministic per target
    and plugin to emulate integrity tracking.
    """

    timestamp = datetime.utcnow()
    raw_payload = f"{spec.name}:{target}:{timestamp.isoformat()}".encode()
    evidence_hash = "sha256:" + sha256(raw_payload).hexdigest()
    evidence_root = Path(evidence_dir or get_settings().evidence_dir)
    evidence_root.mkdir(parents=True, exist_ok=True)
    storage_path = _write_evidence_bytes(raw_payload, spec, target, evidence_root)

    requested_ops = parameters.get("operations")
    allowed_ops = requested_ops or spec.allowed_operations

    observation_payload = {
        "asset_id": None,
        "protocol": spec.protocol,
        "timestamp": timestamp,
        "parsed_data": {
            "target": target,
            "plugin": spec.name,
            "device_type": spec.device_types[0] if spec.device_types else "unknown",
            "operations": allowed_ops,
            "parameters": parameters,
            "read_only": spec.read_only,
        },
        "metrics": {
            "status": "simulated",
            "latency_ms": 40 + len(target),
            "default_port": spec.default_port,
        },
        "raw_refs": [str(storage_path)],
    }

    evidence_payload = {
        "hash": evidence_hash,
        "storage_path": str(storage_path),
        "context": {
            "plugin": spec.name,
            "protocol": spec.protocol,
            "notes": spec.notes or "simulated evidence placeholder",
        },
    }

    return observation_payload, evidence_payload
