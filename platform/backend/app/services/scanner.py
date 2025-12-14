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
from sqlmodel import select

from app.models.core import Asset, Observation, RawEvidence, ScanJob
from app.core.config import get_settings
from app.services.audit import record_audit
from app.services.collectors import (
    CollectorDependencyError,
    CollectorExecutionError,
    collect_with_plugin,
)
from app.services.plugins import PLUGIN_REGISTRY, simulate_plugin_collection, validate_operations


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
    rate_limit_rps: Optional[float] = None,
    session_factory: Callable[[], Session] = _default_session_factory,
    targets: Optional[Iterable[str]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
    evidence_dir: Optional[str] = None,
    collector_func: Callable | None = None,
) -> None:
    settings = get_settings()
    with session_factory() as session:
        job = session.get(ScanJob, job_id)
        if not job:
            return

        job.rate_limit_rps = rate_limit_rps or job.rate_limit_rps or settings.default_rate_limit_rps
        job.connect_timeout_s = job.connect_timeout_s or settings.default_connect_timeout
        job.read_timeout_s = job.read_timeout_s or settings.default_read_timeout
        job.max_retries = job.max_retries if job.max_retries is not None else settings.max_retry_attempts
        job.retry_backoff_s = job.retry_backoff_s or settings.retry_backoff_seconds

        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        target_list = list(targets or job.target_range)

        target_hosts = [t.split(":", 1)[0] for t in target_list]
        asset_map = {
            asset.ip: asset.id
            for asset in session.exec(select(Asset).where(Asset.ip.in_(target_hosts))).all()
        }

    sleep_interval = 1.0 / job.rate_limit_rps if job.rate_limit_rps > 0 else 0
    settings = get_settings()

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

            target_host = target.split(":", 1)[0]
            asset = None
            if target_host in asset_map:
                asset = inner.get(Asset, asset_map[target_host])

            plugin_names = current_job.plugins or ["generic"]
            for plugin_name in plugin_names:
                spec = PLUGIN_REGISTRY.get(plugin_name, PLUGIN_REGISTRY["generic"])
                attempts = 0
                while attempts <= current_job.max_retries:
                    try:
                        collector = collector_func
                        if collector is None:
                            collector = (
                                simulate_plugin_collection
                                if settings.use_simulated_plugins
                                else collect_with_plugin
                            )

                        allowed_ops = validate_operations(
                            spec,
                            requested_ops=current_job.parameters.get("operations"),
                            allow_side_effects=current_job.parameters.get("allow_side_effects", False),
                        )
                        params = dict(current_job.parameters)
                        params["operations"] = allowed_ops
                        params.setdefault("timeouts", {})
                        params["timeouts"].update(
                            {
                                "connect_s": current_job.connect_timeout_s,
                                "read_s": current_job.read_timeout_s,
                            }
                        )
                        evidence_root = Path(evidence_dir or _default_evidence_dir())
                        try:
                            observation_payload, evidence_payload = collector(
                                spec,
                                target,
                                params,
                                evidence_dir=evidence_root,
                            )
                        except (CollectorDependencyError, CollectorExecutionError) as exc:
                            record_audit(
                                inner,
                                actor=actor,
                                action="collector_fallback",
                                resource=target,
                                status="fallback",  # soft warning
                                detail={"job_id": job_id, "plugin": plugin_name, "reason": str(exc)},
                            )
                            observation_payload, evidence_payload = simulate_plugin_collection(
                                spec,
                                target,
                                params,
                                evidence_dir=evidence_root,
                            )

                        observation_payload.setdefault("metrics", {})[
                            "attempts"
                        ] = attempts + 1

                        if asset:
                            observation_payload["asset_id"] = asset.id
                            updated = False
                            protocols = list(asset.protocols or [])
                            if spec.protocol not in protocols:
                                protocols.append(spec.protocol)
                                asset.protocols = protocols
                                updated = True
                            if not asset.device_type and spec.device_types:
                                asset.device_type = spec.device_types[0]
                                updated = True
                            if updated:
                                asset.updated_at = datetime.utcnow()
                                inner.add(asset)

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
                                "attempt": attempts + 1,
                            },
                        )
                        inner.commit()
                        break
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
                        break
                    except TimeoutError as exc:
                        attempts += 1
                        record_audit(
                            inner,
                            actor=actor,
                            action="scan_target_timeout",
                            resource=target,
                            status="timeout",
                            detail={
                                "job_id": job_id,
                                "plugin": plugin_name,
                                "attempt": attempts,
                                "max_retries": current_job.max_retries,
                                "reason": str(exc),
                            },
                        )
                        inner.commit()
                        if attempts > current_job.max_retries:
                            break
                        sleep(current_job.retry_backoff_s * (2 ** (attempts - 1)))
                    except Exception as exc:  # pragma: no cover - defensive
                        record_audit(
                            inner,
                            actor=actor,
                            action="scan_target_error",
                            resource=target,
                            status="error",
                            detail={"job_id": job_id, "plugin": plugin_name, "reason": str(exc)},
                        )
                        break

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
