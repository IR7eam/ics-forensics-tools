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
  IEC104, SNMP, and SSH (plus a generic fallback), including device_type hints,
  allowed read-only operations, and latency defaults. The scanner now emits
  per-plugin observations, raw evidence with SHA-256 hashes, and audit detail
  about protocol/read-only posture.
- **Safety defaults**: All simulated plugins are read-only, with explicit notes
  around opt-in operations (e.g., IEC104 total call, SSH command whitelist).
- **RBAC and audit expansion**: API routes now enforce viewer/analyst/admin
  roles with demo credentials and create audit entries for CRUD, analysis, and
  scan operations.
- **Progress tracking**: This roadmap documents gaps vs. the full requirement set
  and proposes the next milestone targets below.

## Gaps toward the full requirements
- **Real protocol collectors**: Need functional read-only collectors for
  Modbus/TCP, OPC UA, IEC104, SNMP, SSH (plus S7/CIP wiring), with timeouts,
  concurrency, and rate limits enforced in network calls.
- **Device coverage & fingerprinting**: Per-device-type enrichment (vendor,
  model, firmware) from protocol responses and mapping into assets/observations.
- **RBAC and audit depth**: Harden role checks (custom user store, configurable
  roles) and broaden per-request audit metadata/filters.
- **Background orchestration**: Replace the inline scan loop with a worker/queue
  (e.g., Celery/RQ) and cancellation controls for long-running jobs.
- **Baseline learning**: Persist baseline training runs per asset/protocol and
  surface deviations automatically into SecurityEvents.
- **Evidence chain visualization**: UI rendering for evidence timelines/graphs
  and attack-stage tagging across observations and events.
- **Integration tests**: docker-compose fixtures for protocol simulators
  (Modbus, OPC UA, SNMP, SSH, IEC104) plus end-to-end API/UI smoke tests.
- **Documentation**: Expanded operator guide (safety defaults, opt-in actions,
  report templates), and sample scan configs (targets.yaml/ips.csv).

## Next milestone (proposed)
- Implement a plugin runner abstraction that can call real collectors (keeping
  read-only operations as defaults) with rate-limit + timeout controls.
- Introduce RBAC enforcement (admin/analyst/viewer) on sensitive endpoints and
  broaden audit logging to cover CRUD and analysis actions.
- Add queue-backed job execution (background worker or Celery-ready hooks) with
  status polling and cancellation.
- Wire frontend pages to live API data for assets, jobs, events, and reports,
  including evidence download links and progress indicators.
- Provide docker-compose integration fixtures for at least Modbus, OPC UA, SNMP,
  and SSH simulators to validate collectors and reporting flows.

## Acceptance checkpoints
- **Safety**: All collectors remain read-only by default; any opt-in action must
  be explicitly configured and highlighted in UI/API responses.
- **Observability**: Every scan request produces audit entries with actor, target,
  plugin, and result summaries; raw evidence is hashed for integrity.
- **Reporting**: PDF/DOCX/HTML generation remains functional as collectors and
  events expand, including evidence indexes and timelines.
