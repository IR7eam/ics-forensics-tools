from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine, select

from app.models.core import Asset, AuditLog, Observation, RawEvidence, ScanJob
from app.core.config import get_settings
from app.services import scanner
from app.services.scanner import cancel_scan_job, run_scan_job
from app.services.plugins import simulate_plugin_collection
from app.services.collectors import CollectorDependencyError


def test_run_scan_job_creates_observations_and_audit():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        job = ScanJob(
            name="demo",
            initiated_by="tester",
            target_range=["10.0.0.1", "10.0.0.2"],
            plugins=["modbus", "opcua"],
            parameters={},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    run_scan_job(job_id, actor="tester", rate_limit_rps=0, session_factory=lambda: Session(engine))

    with Session(engine) as session:
        job = session.get(ScanJob, job_id)
        assert job.status == "completed"
        assert job.started_at is not None
        assert job.finished_at is not None

        observations = session.exec(select(Observation)).all()
        assert len(observations) == 4  # 2 targets * 2 plugins
        assert {obs.protocol for obs in observations} == {"modbus/tcp", "opc-ua"}
        assert all(obs.parsed_data.get("read_only") for obs in observations)

        evidence = session.exec(select(RawEvidence)).all()
        assert len(evidence) == 4
        assert all(ev.hash.startswith("sha256:") for ev in evidence)

        audits = session.exec(select(AuditLog)).all()
        assert any(a.action == "scan_job_completed" for a in audits)
        assert len(audits) >= 3

        for ev in evidence:
            assert Path(ev.storage_path).exists()


def test_side_effect_operations_are_denied():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        job = ScanJob(
            name="sensitive",
            initiated_by="tester",
            target_range=["10.0.0.1"],
            plugins=["modbus"],
            parameters={"operations": ["fc6"]},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    run_scan_job(job_id, actor="tester", rate_limit_rps=0, session_factory=lambda: Session(engine))

    with Session(engine) as session:
        observations = session.exec(select(Observation)).all()
        assert observations == []

        evidence = session.exec(select(RawEvidence)).all()
        assert evidence == []

        audits = session.exec(select(AuditLog)).all()
        assert any(a.action == "scan_target_denied" for a in audits)
        assert session.get(ScanJob, job_id).status == "completed"


def test_cancel_scan_job_marks_state_and_halts_collection():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        job = ScanJob(
            name="cancel-me",
            initiated_by="tester",
            target_range=["10.0.0.1", "10.0.0.2"],
            plugins=["modbus"],
            parameters={},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    cancel_scan_job(job_id, actor="tester", session_factory=lambda: Session(engine))
    run_scan_job(
        job_id,
        actor="tester",
        rate_limit_rps=0,
        session_factory=lambda: Session(engine),
        cancelled=lambda: True,
    )

    with Session(engine) as session:
        job = session.get(ScanJob, job_id)
        assert job.status == "cancelled"
        assert job.finished_at is not None
        observations = session.exec(select(Observation)).all()
        assert observations == []
        evidence = session.exec(select(RawEvidence)).all()
        assert evidence == []
    scanner._cancellations.clear()


def test_run_scan_job_links_assets_and_updates_protocols():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        asset = Asset(ip="10.0.0.1", hostname="plc1")
        session.add(asset)
        session.commit()
        session.refresh(asset)

        job = ScanJob(
            name="enrich",
            initiated_by="tester",
            target_range=["10.0.0.1", "10.0.0.2"],
            plugins=["modbus", "snmp"],
            parameters={},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id
        asset_id = asset.id

    run_scan_job(job_id, actor="tester", rate_limit_rps=0, session_factory=lambda: Session(engine))

    with Session(engine) as session:
        observations = session.exec(select(Observation)).all()
        assert any(obs.asset_id == asset_id for obs in observations)

        updated_asset = session.get(Asset, asset_id)
        assert updated_asset.device_type == "plc"
        assert set(updated_asset.protocols) >= {"modbus/tcp", "snmp"}


def test_scan_job_retries_on_timeout(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    calls = {"count": 0}

    def flaky_collector(spec, target, params, evidence_dir):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("simulated timeout")
        return simulate_plugin_collection(spec, target, params, evidence_dir)

    with Session(engine) as session:
        job = ScanJob(
            name="retry-job",
            initiated_by="tester",
            target_range=["10.0.0.9"],
            plugins=["modbus"],
            parameters={},
            max_retries=1,
            retry_backoff_s=0,
            rate_limit_rps=0,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    run_scan_job(job_id, actor="tester", session_factory=lambda: Session(engine), collector_func=flaky_collector)

    with Session(engine) as session:
        observations = session.exec(select(Observation)).all()
        assert len(observations) == 1
        assert observations[0].metrics.get("attempts") == 2

        audits = session.exec(select(AuditLog)).all()
        assert any(a.action == "scan_target_timeout" for a in audits)
        assert any(a.action == "scan_job_completed" for a in audits)
        assert session.get(ScanJob, job_id).status == "completed"


def test_real_collector_falls_back_to_simulation(monkeypatch, tmp_path):
    settings = get_settings()
    original = settings.use_simulated_plugins
    settings.use_simulated_plugins = False

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    def missing_dep_collector(*args, **kwargs):
        raise CollectorDependencyError("missing optional dep")

    with Session(engine) as session:
        job = ScanJob(
            name="real-mode", initiated_by="tester", target_range=["10.0.0.5"], plugins=["modbus"], parameters={}
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    monkeypatch.setattr(scanner, "collect_with_plugin", missing_dep_collector)
    run_scan_job(
        job_id,
        actor="tester",
        session_factory=lambda: Session(engine),
        collector_func=None,
        evidence_dir=tmp_path,
    )

    with Session(engine) as session:
        observations = session.exec(select(Observation)).all()
        audits = session.exec(select(AuditLog)).all()
        assert len(observations) == 1
        assert any(a.action == "collector_fallback" for a in audits)
        assert session.get(ScanJob, job_id).status == "completed"

    settings.use_simulated_plugins = original
