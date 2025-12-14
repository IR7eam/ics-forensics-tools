from app.schemas.roadmap import RoadmapItem, RoadmapSummary


def get_roadmap_summary() -> RoadmapSummary:
    delivered = [
        RoadmapItem(
            title="Protocol-aware scan registry with safety defaults",
            detail="Read-only Modbus/OPCUA/IEC104/SNMP/SSH/S7/CIP specs with rate/timeout controls and auditing",
            status="done",
            category="collection",
        ),
        RoadmapItem(
            title="RBAC, audit, and report/export flows",
            detail="Role-scoped APIs, audit trails for scans/analysis, and HTML/PDF/DOCX reporting with evidence indexes",
            status="done",
            category="platform",
        ),
        RoadmapItem(
            title="Analysis and baselines",
            detail="Rule packs, risk scoring, attack-stage summaries, baseline training and deviation alerts",
            status="done",
            category="analytics",
        ),
        RoadmapItem(
            title="Evidence chain and downloads",
            detail="Evidence graph assembly, timeline API/UI, hashed artifacts stored on disk with download endpoints",
            status="done",
            category="evidence",
        ),
    ]

    in_progress = [
        RoadmapItem(
            title="Live protocol collectors",
            detail="Deepen Modbus/SNMP/SSH/OPCUA/IEC104 parsing with structured observations while keeping opt-in safeguards",
            status="in_progress",
            category="collection",
        ),
        RoadmapItem(
            title="End-to-end integration harness",
            detail="docker-compose simulators for Modbus/OPCUA/SNMP/SSH/IEC104 plus API/UI smoke tests",
            status="in_progress",
            category="testing",
        ),
    ]

    remaining = [
        RoadmapItem(
            title="Queue/worker hardening",
            detail="External worker option (Celery/RQ) for resilient scan execution, retries, and cancellation persistence",
            status="planned",
            category="platform",
        ),
        RoadmapItem(
            title="Device fingerprint depth",
            detail="Protocol-specific parsing to populate vendor/model/firmware per device_type without overwriting curated data",
            status="planned",
            category="inventory",
        ),
        RoadmapItem(
            title="Operator docs and presets",
            detail="Expanded safety guidance, opt-in operation flags, and richer sample targets for field validation",
            status="planned",
            category="docs",
        ),
    ]

    return RoadmapSummary(
        iterations_remaining=2,
        focus_areas=[
            "Deepen live collectors while preserving read-only defaults",
            "Ship simulator-backed integration tests and CI hooks",
            "Harden worker orchestration and operational runbooks",
        ],
        delivered=delivered,
        in_progress=in_progress,
        remaining=remaining,
        blockers=[
            "Real protocol client dependencies are optional extras and must stay opt-in for safety",
            "Integration simulators increase CI time; need gated or cached runs",
        ],
    )
