"""Minimal scan job execution stub with audit logging and rate limiting.

This is a placeholder that simulates protocol collection while honoring
timeout/limits so the platform API can exercise the full job lifecycle.
"""

from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Lock, Thread
from time import sleep
from typing import Callable, Iterable, Optional

from sqlmodel import Session

from app.db.session import engine
from app.models.core import Observation, RawEvidence, ScanJob
from app.core.config import get_settings
from app.services.audit import record_audit
from app.services.plugins import (
    PLUGIN_REGISTRY,
    simulate_plugin_collection,
    validate_operations,
)


_worker_started = False
_worker_lock = Lock()
_scan_queue: "Queue[tuple[int, str, float, Optional[Iterable[str]]]]" = Queue()
_cancellations = set()


def _default_session_factory():
    return Session(engine)


def _default_evidence_dir():
    return get_settings().evidence_dir


def run_scan_job(
    job_id: int,
    actor: str,
    rate_limit_rps: float = 1.0,
    session_factory: Callable[[], Session] = _default_session_factory,
    targets: Optional[Iterable[str]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
    evidence_dir: Optional[str] = None,
) -> None:
    sleep_interval = 1.0 / rate_limit_rps if rate_limit_rps > 0 else 0
    with session_factory() as session:
        job = session.get(ScanJob, job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        target_list = list(targets or job.target_range)

    for target in target_list:
        if cancelled and cancelled():
            with session_factory() as cancel_session:
                cancel_job = cancel_session.get(ScanJob, job_id)
                if cancel_job:
                    cancel_job.status = "cancelled"
                    cancel_job.finished_at = datetime.utcnow()
                    cancel_job.updated_at = datetime.utcnow()
                    cancel_session.add(cancel_job)
                    record_audit(
                        cancel_session,
                        actor=actor,
                        action="scan_job_cancelled",
                        resource=str(job_id),
                        detail={"target": target},
                    )
                    cancel_session.commit()
            break
        with session_factory() as inner:
            current_job = inner.get(ScanJob, job_id)
            if not current_job:
                return

            plugin_names = current_job.plugins or ["generic"]
            for plugin_name in plugin_names:
                spec = PLUGIN_REGISTRY.get(plugin_name, PLUGIN_REGISTRY["generic"])
                try:
                    allowed_ops = validate_operations(
                        spec,
                        requested_ops=current_job.parameters.get("operations"),
                        allow_side_effects=current_job.parameters.get("allow_side_effects", False),
                    )
                    params = dict(current_job.parameters)
                    params["operations"] = allowed_ops
                    observation_payload, evidence_payload = simulate_plugin_collection(
                        spec, target, params, evidence_dir=Path(evidence_dir or _default_evidence_dir())
                    )

                    observation = Observation(**observation_payload)
                    inner.add(observation)
                    inner.commit()
                    inner.refresh(observation)

                    evidence = RawEvidence(observation_id=observation.id, **evidence_payload)
                    inner.add(evidence)
                    record_audit(
                        inner,
                        actor=actor,
                        action="scan_target",
                        resource=target,
                        detail={
                            "job_id": job_id,
                            "plugin": plugin_name,
                            "protocol": spec.protocol,
                            "read_only": spec.read_only,
                            "operations": allowed_ops,
                        },
                    )
                    inner.commit()
                except PermissionError as exc:
                    record_audit(
                        inner,
                        actor=actor,
                        action="scan_target_denied",
                        resource=target,
                        status="denied",
                        detail={
                            "job_id": job_id,
                            "plugin": plugin_name,
                            "reason": str(exc),
                        },
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    record_audit(
                        inner,
                        actor=actor,
                        action="scan_target_error",
                        resource=target,
                        status="error",
                        detail={"job_id": job_id, "plugin": plugin_name, "reason": str(exc)},
                    )

        if sleep_interval:
            sleep(sleep_interval)

    with session_factory() as final:
        finished_job = final.get(ScanJob, job_id)
        if not finished_job:
            return
        if finished_job.status != "cancelled":
            finished_job.status = "completed"
            finished_job.finished_at = datetime.utcnow()
            finished_job.updated_at = datetime.utcnow()
            final.add(finished_job)
            record_audit(
                final,
                actor=actor,
                action="scan_job_completed",
                resource=str(job_id),
                detail={"target_count": len(targets or finished_job.target_range)},
            )
            final.commit()


def _scan_worker():
    while True:
        try:
            job_id, actor, rate_limit_rps, targets = _scan_queue.get(timeout=1)
        except Empty:
            continue

        run_scan_job(
            job_id,
            actor,
            rate_limit_rps=rate_limit_rps,
            targets=targets,
            cancelled=lambda: job_id in _cancellations,
        )
        _scan_queue.task_done()


def _start_worker_if_needed():
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            worker = Thread(target=_scan_worker, daemon=True)
            worker.start()
            _worker_started = True


def enqueue_scan_job(job_id: int, actor: str, rate_limit_rps: float = 1.0, targets: Optional[Iterable[str]] = None):
    _start_worker_if_needed()
    _scan_queue.put((job_id, actor, rate_limit_rps, targets))


def cancel_scan_job(job_id: int, actor: str, session_factory: Callable[[], Session] = _default_session_factory) -> bool:
    _cancellations.add(job_id)
    with session_factory() as session:
        job = session.get(ScanJob, job_id)
        if not job:
            return False
        job.status = "cancelled"
        job.finished_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        session.add(job)
        record_audit(
            session,
            actor=actor,
            action="scan_job_cancel_request",
            resource=str(job_id),
            detail={"status": "cancelled"},
        )
        session.commit()
    return True
