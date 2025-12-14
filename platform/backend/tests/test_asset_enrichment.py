from sqlmodel import SQLModel, Session, create_engine, select

from app.models.core import Asset, Observation, RawEvidence, ScanJob
from app.services.scanner import run_scan_job
from app.services.plugins import simulate_plugin_collection


def _snmp_collector(spec, target, params, evidence_dir):
    observation, evidence = simulate_plugin_collection(spec, target, params, evidence_dir)
    observation["parsed_data"].update(
        {
            "oids": {
                "1.3.6.1.2.1.1.1.0": "Siemens Simatic S7-300 CPU",
                "1.3.6.1.2.1.1.5.0": "plant-gateway",
            },
            "softwareVersion": "3.2.1",
            "device_type": "gateway",
        }
    )
    return observation, evidence


def test_scan_job_discovers_and_enriches_asset_metadata():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        job = ScanJob(
            name="discover",
            initiated_by="tester",
            target_range=["192.0.2.5"],
            plugins=["snmp"],
            parameters={},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    run_scan_job(
        job_id,
        actor="tester",
        rate_limit_rps=0,
        session_factory=lambda: Session(engine),
        collector_func=_snmp_collector,
    )

    with Session(engine) as session:
        asset = session.exec(select(Asset)).one()
        assert asset.ip == "192.0.2.5"
        assert asset.vendor == "Siemens"
        assert asset.model == "S7-300"
        assert asset.firmware == "3.2.1"
        assert "snmp" in asset.protocols
        assert asset.device_type == "gateway"

        observations = session.exec(select(Observation)).all()
        assert observations and observations[0].asset_id == asset.id

        evidence = session.exec(select(RawEvidence)).all()
        assert evidence
