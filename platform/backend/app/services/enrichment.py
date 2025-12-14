from __future__ import annotations

"""Asset enrichment helpers from observation payloads.

These utilities apply conservative heuristics to populate vendor/model/firmware
fields based on read-only protocol responses. They are intentionally simple to
avoid false positives and only fill fields that are currently empty.
"""

from typing import Dict, Iterable

from app.models.core import Asset

_VENDOR_KEYWORDS = {
    "siemens": "Siemens",
    "simatic": "Siemens",
    "rockwell": "Rockwell Automation",
    "allen-bradley": "Rockwell Automation",
    "logix": "Rockwell Automation",
    "abb": "ABB",
    "schneider": "Schneider Electric",
    "cisco": "Cisco",
    "juniper": "Juniper",
    "huawei": "Huawei",
}

_MODEL_PATTERNS = {
    "s7-300": "S7-300",
    "s7-400": "S7-400",
    "logix": "Logix",
    "guardlogix": "GuardLogix",
    "compactlogix": "CompactLogix",
}


def _flatten_strings(values: Iterable) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            parts.append(_flatten_strings(value.values()))
        elif isinstance(value, (list, tuple, set)):
            parts.append(_flatten_strings(value))
        else:
            parts.append(str(value))
    return " ".join([p for p in parts if p])


def _guess_vendor(text: str) -> str | None:
    lower = text.lower()
    for keyword, vendor in _VENDOR_KEYWORDS.items():
        if keyword in lower:
            return vendor
    return None


def _guess_model(text: str) -> str | None:
    lower = text.lower()
    for keyword, model in _MODEL_PATTERNS.items():
        if keyword in lower:
            return model
    return None


def enrich_asset_from_observation(asset: Asset, parsed_data: Dict, protocol: str | None = None) -> bool:
    """Update asset metadata from observation content.

    Only fills missing fields to avoid overwriting curated inventory data.
    Returns ``True`` when the asset was updated.
    """

    updated = False
    aggregate = _flatten_strings(parsed_data.values())
    if aggregate:
        if not asset.vendor:
            vendor = _guess_vendor(aggregate)
            if vendor:
                asset.vendor = vendor
                updated = True
        if not asset.model:
            model = _guess_model(aggregate)
            if model:
                asset.model = model
                updated = True
        if not asset.hostname and "hostname" in parsed_data:
            hostname = str(parsed_data.get("hostname"))
            if hostname:
                asset.hostname = hostname
                updated = True
        if not asset.firmware:
            for key in ("softwareVersion", "firmware", "buildNumber"):
                if key in parsed_data and parsed_data.get(key):
                    asset.firmware = str(parsed_data[key])
                    updated = True
                    break
    if protocol and protocol not in (asset.protocols or []):
        asset.protocols = list(asset.protocols or []) + [protocol]
        updated = True
    if parsed_data.get("device_type") and not asset.device_type:
        asset.device_type = parsed_data["device_type"]
        updated = True
    return updated
