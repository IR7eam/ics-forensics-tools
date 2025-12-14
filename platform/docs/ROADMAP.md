# Platform Delivery Roadmap and Gap Analysis

This document tracks the staged delivery toward the full ICS forensics platform
requirements and highlights what is already implemented versus what remains.

## Current coverage (what works today)
- **Backend scaffolding**: FastAPI app with normalized entities (Asset, ScanJob,
  Observation, RawEvidence, SecurityEvent, EvidenceLink, Report, BaselineProfile,
  AuditLog) exposed via REST endpoints.
- **Authentication**: Developer-friendly JWT issuance helper to enable protected
  routes (RBAC tightening planned).
- **Analysis utilities**: Rule evaluation (YAML) and anomaly detection (z-score,
  IsolationForest) services and APIs.
- **Reporting**: HTML/PDF/DOCX generation endpoints that ingest observations,
  events, and assets to produce downloadable files.
- **Evidence graph**: CRUD for evidence links, observations, raw evidence, and
  audit logs to build a traceable chain.
- **Scan execution stub**: Background scan trigger that simulates read-only
  collections, now enriched with protocol-aware plugin metadata and deterministic
  evidence hashing.
- **Frontend scaffold**: Vite + React + Ant Design shell with pages for dashboard,
  assets, scan jobs, events, evidence chains, reports, and settings.

## Newly added in this drop
- **Protocol-aware scan simulation**: Registry entries for Modbus/TCP, OPC UA,
  IEC104, SNMP, SSH, S7Comm, and CIP (plus a generic fallback), including
  device_type hints, allowed read-only operations, and latency defaults. The
  scanner now emits per-plugin observations, raw evidence with SHA-256 hashes,
  and audit detail about protocol/read-only posture.
- **Retry/backoff and timeouts**: Scan jobs include connect/read timeouts,
  retry counts, and exponential backoff so collection remains conservative and
  aligns with the read-only safety posture.
- **Safety defaults**: All simulated plugins are read-only, with explicit notes
  around opt-in operations (e.g., IEC104 total call, SSH command whitelist).
- **RBAC and audit expansion**: API routes now enforce viewer/analyst/admin
  roles with demo credentials and create audit entries for CRUD, analysis, and
  scan operations.
- **Queued scans and cancellation**: Scan triggers now enqueue work onto an
  in-process worker so multiple jobs can queue safely, and analysts can request
  cancellation with per-target audit logs and status updates.
- **Baseline training & deviations**: Analysts can train per-asset baselines
  from existing observations and evaluate new metric snapshots against those
  baselines, automatically emitting security events for significant drift.
- **Progress tracking**: This roadmap documents gaps vs. the full requirement set
  and proposes the next milestone targets below.
- **Collector toggle + fallback**: Runtime switch (`ICS_USE_SIMULATED_PLUGINS`)
  to attempt real read-only collectors (Modbus/SNMP/SSH/OPC UA) when optional
  dependencies are installed, with automatic audited fallback to simulation on
  missing deps or connection failures. IEC104 now performs a conservative
  StartDT/TestFR handshake and persists captured APDUs as evidence.
- **Evidence-chain timeline**: `/analysis/evidence-chain` aggregates
  observations, events, raw evidence, and links into a time-ordered set with
  attack-stage counts and max risk summaries, and the UI renders a filterable
  timeline plus evidence downloads.
- **Roadmap API**: `/api/roadmap` exposes delivered, in-progress, and remaining
  items with iteration estimates so operators can track what is left.

## Gaps toward the full requirements
- **Real protocol collectors** (in progress): Implement deeper parsing and
  coverage for Modbus/TCP, OPC UA, IEC104, SNMP, SSH (plus S7/CIP wiring)
  beyond the current socket probes and optional client integrations, with
  structured raw captures and adaptive limits.
- **Integration harness** (in progress): docker-compose fixtures for protocol
  simulators (Modbus, OPC UA, SNMP, SSH, IEC104) plus end-to-end API/UI smoke
  tests.
- **Queue/worker hardening** (planned): Swap the inline worker for Celery/RQ or
  pluggable queues so retries/cancellation persist across processes.
- **Device fingerprint depth** (planned): Protocol-specific parsing to populate
  vendor/model/firmware per device_type without overwriting curated data.
- **Operator docs and presets** (planned): Expanded safety guidance, opt-in
  operation flags, and richer sample targets for field validation.

**Remaining workload estimate**: ~2 development iterations to deepen live
collectors, deliver simulator-backed integration tests, and finalize worker
hardening plus operator docs.

## Next milestone (proposed)
- Finish live collectors for Modbus/OPCUA/SNMP/SSH/IEC104 with structured
  observations and conservative opt-in gates.
- Ship simulator-backed integration tests and wire them into `make test-int`
  (optionally gated for CI runtime).
- Add Celery/RQ-ready hooks so scan execution can move to an external worker
  while keeping the in-process queue for lightweight demos.
- Expand operator docs with opt-in action guidance, sample targets, and
  checklist for air-gapped deployments.

## Acceptance checkpoints
- **Safety**: All collectors remain read-only by default; any opt-in action must
  be explicitly configured and highlighted in UI/API responses.
- **Observability**: Every scan request produces audit entries with actor, target,
  plugin, and result summaries; raw evidence is hashed for integrity.
- **Reporting**: PDF/DOCX/HTML generation remains functional as collectors and
  events expand, including evidence indexes and timelines.
