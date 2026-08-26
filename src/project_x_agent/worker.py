from __future__ import annotations

import fcntl
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from .agent import ProjectXAgent
from .executor import CodexCliExecutor
from .gitops import GitRepository, GitSafetyError, validate_and_copy_changes
from .models import TaskValidationError, load_task
from .publisher import QueuedGitPublisher


class ProjectXWorker:
    def __init__(self, *, repo_root: Path, codex_binary: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.codex_binary = codex_binary.resolve()
        self.repository = GitRepository(self.repo_root)
        self.work_dir = self.repo_root / "work" / "agent"

    def run_once(self) -> dict[str, object]:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.work_dir / "worker.lock"
        with lock_path.open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return {"status": "skipped", "reason": "another worker run is active"}
            return self._run_locked()

    def _run_locked(self) -> dict[str, object]:
        self.repository.ensure_ready_and_sync()
        pending = self._next_pending_task()
        if pending is None:
            return {"status": "idle", "published": False}
        source_path, task_id, write_paths = pending
        with tempfile.TemporaryDirectory(prefix="project-x-agent-") as temporary:
            worktree = Path(temporary) / "repo"
            self.repository.add_detached_worktree(worktree)
            try:
                agent = ProjectXAgent(
                    tasks_dir=worktree / "tasks",
                    results_dir=worktree / "results",
                    executor=CodexCliExecutor(
                        repo_root=worktree,
                        codex_binary=self.codex_binary,
                    ),
                    publisher=QueuedGitPublisher(),
                )
                summary = agent.scan_once(max_tasks=1)
                result_prefix = f"results/{task_id}" if task_id else "results/_invalid"
                copied = validate_and_copy_changes(
                    repository=self.repository,
                    worktree=worktree,
                    destination=self.repo_root,
                    allowed_prefixes=(result_prefix, *write_paths),
                )
            finally:
                self.repository.remove_worktree(worktree)
        commit = self.repository.publish(copied, task_ids=summary.task_ids)
        return {
            "status": "completed",
            "source": source_path.name,
            "summary": asdict(summary),
            "published": bool(commit),
            "commit": commit,
        }

    def _next_pending_task(self) -> tuple[Path, str | None, tuple[str, ...]] | None:
        results = self.repo_root / "results"
        for source in sorted((self.repo_root / "tasks").glob("*.json")):
            try:
                envelope = load_task(source)
            except TaskValidationError:
                invalid = results / "_invalid" / f"{source.stem}.json"
                if invalid.is_file():
                    try:
                        existing = json.loads(invalid.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        existing = {}
                    import hashlib

                    if existing.get("source_hash") == hashlib.sha256(source.read_bytes()).hexdigest():
                        continue
                return source, None, ()
            result = results / envelope.task.id / "result.json"
            if result.is_file():
                try:
                    current = json.loads(result.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    current = {}
                if current.get("task_hash") == envelope.content_hash and current.get("status") in {
                    "blocked", "completed", "failed"
                }:
                    continue
            return source, envelope.task.id, envelope.task.execution.write_paths
        return None


__all__ = ["GitSafetyError", "ProjectXWorker"]
