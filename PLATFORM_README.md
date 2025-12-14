# ICS Forensics Platform (staged delivery)

This document describes the staged roadmap for building the requested end-to-end ICS forensics platform on top of the existing tooling. This initial drop focuses on creating a backend scaffold with core domain models and REST entry points so we can iterate safely.

See `platform/docs/ROADMAP.md` for a detailed gap analysis and next-milestone checklist.

## Current scope (Milestone 1)
- Adds a FastAPI-based backend skeleton under `platform/backend` with SQLModel data models for the platform-wide normalized entities (Asset, ScanJob, Observation, RawEvidence, SecurityEvent, EvidenceLink, Report, BaselineProfile).
- Provides JWT-backed authentication with demo roles (viewer/analyst/admin) so APIs enforce least-privilege access.
- Exposes CRUD APIs for Assets, Scan Jobs, Observations, Evidence, Baselines, Security Events, and Evidence Links to unblock front-end wiring and initial data ingestion.
- Adds an audit log surface (`/api/audit`) and a background scan trigger (`POST /api/scan-jobs/{id}/run`) backed by an in-process queue that simulates read-only collections while recording per-target audit entries. CRUD, report generation, and analysis calls are also audited. Jobs can be cancelled via `POST /api/scan-jobs/{id}/cancel`.
- Adds analysis helpers: rule evaluation (YAML-driven) and anomaly detection (z-score + Isolation Forest) via `/api/analysis` endpoints.
- Introduces report generation (HTML/PDF/DOCX) via `/api/reports/generate`, storing paths in the `Report` table for download/preview.
- Includes a `Makefile` to start the backend (`make backend`), initialize the database (`make init-db`), or run backend unit tests (`make test-backend`).

## How to run (local)
```bash
cd platform
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
make init-db
make backend
# in a second terminal for the UI
cd platform/frontend
npm install
npm run dev -- --host
```
The API will listen on `http://0.0.0.0:8000` with OpenAPI docs at `/docs`.
The UI will be available at `http://127.0.0.1:5173` (configurable via Vite).

## How to run (Docker Compose)
```bash
cd platform
docker compose up --build
```
Services:
- **backend**: FastAPI app on `http://localhost:8000` using a volume-backed SQLite database at `/data/ics_platform.db`.
- **frontend**: built React UI served via `serve` at `http://localhost:4173` with API calls pointed to the backend service.

Stop with `docker compose down`. The named `backend-data` volume preserves the SQLite database between runs.

## Authentication (developer-friendly RBAC)
- Obtain a bearer token by calling `POST /api/auth/token` with OAuth2 form fields. Default demo accounts:
  - `admin` / `admin` (role: admin)
  - `analyst` / `analyst` (role: analyst)
  - `viewer` / `viewer` (role: viewer)
- Use the returned `access_token` as `Authorization: Bearer <token>` to access protected endpoints. The backend enforces roles: viewers can read, analysts can create/update jobs/assets/baselines/events, and admins can review audit logs and delete assets.

## Data model overview
The SQLModel tables mirror the normalized evidence schema:
- **Asset**: ip/hostname, device_type, vendor, model, serial, firmware, supported protocols, tags, timestamps.
- **ScanJob**: initiated_by, targets, plugin list, parameters snapshot, status lifecycle.
- **Observation**: per-asset protocol observation with parsed data, metrics, raw references.
- **RawEvidence**: binary/text pointers with hash and context for integrity.
- **SecurityEvent**: rule/anomaly hits with severity, confidence, impact, evidence references.
- **EvidenceLink**: links between evidence to construct timelines/graphs.
- **Report**: generated files and parameters (HTML/PDF/DOCX in later milestones).

## Progress update
- **Protocol registry & simulation**: Added a protocol-aware plugin registry (Modbus, OPC UA, IEC104, SNMP, SSH, and generic) with read-only operation lists and device_type hints. The scan runner now emits per-plugin observations, SHA-256–hashed raw evidence, and protocol-aware audit details.
- **Roadmap tracking**: Documented current coverage, gaps, and upcoming milestones in `platform/docs/ROADMAP.md` to clarify what remains for full delivery.
- **Safety enforcement**: Scan jobs now enforce operation allowlists and require explicit opt-in for side-effecting protocol actions, recording denied attempts in the audit log.
- **Plugin registry API + UI surfacing**: `/api/plugins` lists per-protocol allowed/dangerous operations, device types, and descriptions so the frontend can highlight read-only defaults and red-flag opt-in steps in the Settings page.
- **Baseline UX and attack-stage awareness**: Settings now offers baseline train/evaluate controls, and the dashboard visualizes attack-stage coverage using `/analysis/attack-stages` so analysts can track drift and stage trends.
- **Rule-pack management**: Analysts can upload/list/toggle rule packs via `/api/rules` with audit coverage and test them in the Settings UI to validate detection logic.

## Next milestones (suggested breakdown)
1. **Protocol plugins + collectors**: integrate Modbus/S7/CIP/OPC UA/IEC104/SNMP/SSH collectors with timeouts, concurrency, and rate limits; map outputs into `Observation` and `RawEvidence`.
2. **Task orchestration & audit**: background workers, per-request audit logs, role-based permissions, and job state machine.
3. **Analysis layer**: rule engine, baseline modeling, anomaly detection utilities producing `SecurityEvent` rows.
4. **Evidence graph & reporting**: evidence linkage APIs, attack-stage mapping, and multi-format report generation.
5. **Frontend**: React-based dashboard consuming the APIs (assets, jobs, events, evidence chains, reports, settings).
6. **Packaging & tests**: docker-compose, integration fixtures (simulated protocol servers), unit tests for rule engine/anomaly detection, and documentation updates.

Each milestone will preserve the safety constraints (read-only defaults, explicit opt-in for side-effecting operations) and extend the schema where necessary to capture audit details.

## Backend API surface (early draft)
- `POST /api/auth/token` — obtain a JWT.
- CRUD under `/api/assets`, `/api/scan-jobs`, `/api/observations`, `/api/evidence`, `/api/events`, `/api/baselines`, `/api/evidence-links`.
- `POST /api/reports/generate` — generate HTML/PDF/DOCX reports summarizing assets/events/observations within a scope.
- `POST /api/analysis/rules/evaluate` — evaluate YAML rules or stored rule packs (via `rule_pack_id`) against an observation-like payload.
- CRUD under `/api/rules` — upload/list/toggle/test rule packs.
- `POST /api/analysis/anomaly` — run z-score and IsolationForest anomaly detection over metric arrays.
- `POST /api/analysis/baseline/train` — compute and store per-asset/per-protocol baselines from stored observations.
- `POST /api/analysis/baseline/evaluate` — compare live metrics to a baseline, optionally emitting `SecurityEvent` rows.
- `GET /api/analysis/attack-stages` — aggregate stored security events by ICS attack stage with max risk per stage for timeline views.
- `POST /api/scan-jobs/{id}/run` — queue a scan job and execute it in the background with audit logging and simulated observations/evidence.
- `POST /api/scan-jobs/{id}/cancel` — request cancellation; the queued/active job marks itself cancelled and records an audit entry.
- `GET /api/evidence/{id}/download` — stream stored evidence bytes from `ICS_EVIDENCE_DIR` (default `./evidence`) and audit the download.
- `GET /api/plugins` — enumerate plugin specs (protocol, allowed vs. dangerous operations, device types) for UI validation and operator review.
- `/api/audit` — list or insert audit trail entries.

## Next-phase plan (Milestone 2 goals)
- **Collector integration**: wire existing forensic plugins into the platform scan pipeline, and add read-only collectors for IEC104/OPC UA/SNMP/SSH with rate-limit/timeout defaults mapped into `Observation` and `RawEvidence` records.
- **Background execution & audit**: add a job runner (e.g., FastAPI BackgroundTasks or Celery-ready hooks) with per-request audit logs and RBAC checks on sensitive endpoints.
- **Evidence delivery & UI hooks**: expose report download endpoints, attach evidence-link traversal helpers, and start the frontend scaffold (React + AntD) with pages for dashboard, assets, scan jobs, events, and report preview.
- **Frontend skeleton (delivered in this step)**: a Vite + React + Ant Design single-page app with navigation, JWT login helper, and pages for dashboard, assets, scan jobs, events, evidence chains, reports, and settings.

## Testing
```bash
cd platform
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
make test-backend
```

Sample job payloads for manual testing live in `platform/docs/sample_targets.yaml`; each entry corresponds to `name`, `target_range`, and `plugins` fields you can paste into the Scan Jobs form. All presets stick to read-only operations.
