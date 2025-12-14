from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine, select

from app.models.core import AuditLog, Observation, RawEvidence, ScanJob
from app.services import scanner
from app.services.scanner import cancel_scan_job, run_scan_job


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
