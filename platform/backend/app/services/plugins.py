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
from typing import Dict, List, Tuple


@dataclass
class PluginSpec:
    name: str
    protocol: str
    device_types: List[str]
    default_port: int
    description: str
    read_only: bool = True
    allowed_operations: List[str] = field(default_factory=list)
    notes: str = ""


PLUGIN_REGISTRY: Dict[str, PluginSpec] = {
    "modbus": PluginSpec(
        name="modbus",
        protocol="modbus/tcp",
        device_types=["plc", "rtu", "gateway"],
        default_port=502,
        description="Read-only Modbus/TCP identification and register sampling",
        allowed_operations=["fc3", "fc4", "diagnostic"],
        notes="Limited to read functions and conservative range probing with rate limits.",
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
        notes="C_IC_NA_1 total call must be opt-in via configuration.",
    ),
    "snmp": PluginSpec(
        name="snmp",
        protocol="snmp",
        device_types=["gateway", "network-security"],
        default_port=161,
        description="SNMPv2c/v3 read-only sysDescr/sysName/ifTable sampling",
        allowed_operations=["get", "getnext", "walk"],
    ),
    "ssh": PluginSpec(
        name="ssh",
        protocol="ssh",
        device_types=["server", "network-security"],
        default_port=22,
        description="SSH banner/hostkey probing with optional safe command whitelist",
        allowed_operations=["banner", "hostkey", "uname", "uptime", "ip_a"],
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


def simulate_plugin_collection(spec: PluginSpec, target: str, parameters: Dict) -> Tuple[dict, dict]:
    """Create observation/evidence payloads for a simulated plugin run.

    The payloads mirror Observation/RawEvidence fields so the scanner can persist
    them without knowing protocol specifics. Hashes are deterministic per target
    and plugin to emulate integrity tracking.
    """

    timestamp = datetime.utcnow()
    raw_payload = f"{spec.name}:{target}:{timestamp.isoformat()}".encode()
    evidence_hash = "sha256:" + sha256(raw_payload).hexdigest()
    storage_path = f"simulated://{spec.protocol}/{target}/{timestamp.isoformat()}"

    observation_payload = {
        "asset_id": None,
        "protocol": spec.protocol,
        "timestamp": timestamp,
        "parsed_data": {
            "target": target,
            "plugin": spec.name,
            "device_type": spec.device_types[0] if spec.device_types else "unknown",
            "operations": spec.allowed_operations,
            "parameters": parameters,
            "read_only": spec.read_only,
        },
        "metrics": {
            "status": "simulated",
            "latency_ms": 40 + len(target),
            "default_port": spec.default_port,
        },
        "raw_refs": [storage_path],
    }

    evidence_payload = {
        "hash": evidence_hash,
        "storage_path": storage_path,
        "context": {
            "plugin": spec.name,
            "protocol": spec.protocol,
            "notes": spec.notes or "simulated evidence placeholder",
        },
    }

    return observation_payload, evidence_payload
