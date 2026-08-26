from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Event

from .executor import TaskExecutor
from .models import TaskEnvelope, TaskValidationError, load_task
from .policy import SafetyPolicy
from .publisher import ResultPublisher
from .storage import ResultStore, utc_now


@dataclass(frozen=True)
class RunSummary:
    discovered: int = 0
    completed: int = 0
    failed: int = 0
    blocked: int = 0
    invalid: int = 0
    skipped: int = 0
    task_ids: tuple[str, ...] = ()


class ProjectXAgent:
    def __init__(
        self,
        *,
        tasks_dir: Path,
        results_dir: Path,
        executor: TaskExecutor,
        publisher: ResultPublisher,
        policy: SafetyPolicy | None = None,
    ) -> None:
        self.tasks_dir = tasks_dir
        self.results_dir = results_dir
        self.executor = executor
        self.publisher = publisher
        self.policy = policy or SafetyPolicy()
        self.store = ResultStore(results_dir)

    def scan_once(self, *, max_tasks: int | None = None) -> RunSummary:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        counters = {
            "discovered": 0,
            "completed": 0,
            "failed": 0,
            "blocked": 0,
            "invalid": 0,
            "skipped": 0,
        }
        task_ids: list[str] = []
        processed = 0

        for source_path in sorted(self.tasks_dir.glob("*.json")):
            counters["discovered"] += 1
            try:
                envelope = load_task(source_path)
            except TaskValidationError as exc:
                try:
                    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                except OSError:
                    source_hash = "unavailable"
                self.store.write_invalid(source_path.name, source_hash, str(exc))
                counters["invalid"] += 1
                processed += 1
                if max_tasks is not None and processed >= max_tasks:
                    break
                continue

            if self.store.is_current(envelope.task.id, envelope.content_hash):
                counters["skipped"] += 1
                continue

            status = self._process(envelope)
            counters[status] += 1
            task_ids.append(envelope.task.id)
            processed += 1
            if max_tasks is not None and processed >= max_tasks:
                break

        return RunSummary(**counters, task_ids=tuple(task_ids))

    def watch(self, *, interval_seconds: float, stop_event: Event | None = None) -> None:
        if interval_seconds < 5:
            raise ValueError("watch interval must be at least 5 seconds")
        stopper = stop_event or Event()
        while not stopper.is_set():
            self.scan_once()
            stopper.wait(interval_seconds)

    def _process(self, envelope: TaskEnvelope) -> str:
        task = envelope.task
        started_at = utc_now()
        self.store.append_event(
            task.id,
            "task.discovered",
            task_hash=envelope.content_hash,
            risk_level=task.risk_level.value,
        )

        decision = self.policy.evaluate(task)
        self.store.append_event(
            task.id,
            "policy.evaluated",
            allowed=decision.allowed,
            code=decision.code,
        )

        if not decision.allowed:
            self.store.write_json(
                task.id,
                "result.json",
                {
                    "schema_version": 1,
                    "task_id": task.id,
                    "task_hash": envelope.content_hash,
                    "status": "blocked",
                    "risk_level": task.risk_level.value,
                    "execution_mode": task.execution.mode.value,
                    "write_paths": list(task.execution.write_paths),
                    "policy": asdict(decision),
                    "executor": self.executor.name,
                    "publisher": self.publisher.name,
                    "started_at": started_at,
                    "finished_at": utc_now(),
                },
            )
            self.store.append_event(task.id, "task.blocked", code=decision.code)
            self._publish(envelope, task.id)
            return "blocked"

        self.store.append_event(task.id, "executor.started", adapter=self.executor.name)
        try:
            outcome = self.executor.execute(task)
            artifact_paths = [
                self.store.write_text(task.id, artifact.relative_path, artifact.content)
                for artifact in outcome.artifacts
            ]
            self.store.write_json(
                task.id,
                "result.json",
                {
                    "schema_version": 1,
                    "task_id": task.id,
                    "task_hash": envelope.content_hash,
                    "status": outcome.status,
                    "risk_level": task.risk_level.value,
                    "execution_mode": task.execution.mode.value,
                    "write_paths": list(task.execution.write_paths),
                    "policy": asdict(decision),
                    "executor": self.executor.name,
                    "executor_is_mock": self.executor.is_mock,
                    "summary": outcome.summary,
                    "artifacts": [str(path.relative_to(self.results_dir)) for path in artifact_paths],
                    "publisher": self.publisher.name,
                    "publisher_is_mock": self.publisher.is_mock,
                    "started_at": started_at,
                    "finished_at": utc_now(),
                },
            )
            event = "executor.completed" if outcome.status == "completed" else "executor.failed"
            self.store.append_event(task.id, event, status=outcome.status)
        except Exception as exc:  # Fail closed and record the adapter error.
            self.store.write_json(
                task.id,
                "result.json",
                {
                    "schema_version": 1,
                    "task_id": task.id,
                    "task_hash": envelope.content_hash,
                    "status": "failed",
                    "risk_level": task.risk_level.value,
                    "execution_mode": task.execution.mode.value,
                    "write_paths": list(task.execution.write_paths),
                    "executor": self.executor.name,
                    "error_type": type(exc).__name__,
                    "started_at": started_at,
                    "finished_at": utc_now(),
                },
            )
            self.store.append_event(task.id, "executor.failed", error_type=type(exc).__name__)
            self._publish(envelope, task.id)
            return "failed"

        self._publish(envelope, task.id)
        return "completed" if outcome.status == "completed" else "failed"

    def _publish(self, envelope: TaskEnvelope, task_id: str) -> None:
        commit_message = f"Record Project X task {task_id}"
        receipt = self.publisher.publish(
            task_id=task_id,
            commit_message=commit_message,
            paths=(envelope.source_path, self.store.task_dir(task_id)),
        )
        self.store.append_event(
            task_id,
            "publisher.completed",
            adapter=receipt.adapter,
            status=receipt.status,
            pushed=receipt.pushed,
        )
        self.store.write_json(task_id, "publication.json", asdict(receipt))
