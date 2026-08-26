from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitSafetyError(RuntimeError):
    pass


SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(rb"\b(?:ghp|github_pat|sk)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/=-]{16,}"),
)


@dataclass(frozen=True)
class GitChange:
    status: str
    path: str


class GitRepository:
    def __init__(self, root: Path, *, branch: str = "main") -> None:
        self.root = root.resolve()
        self.branch = branch

    def ensure_ready_and_sync(self) -> None:
        if self._output("status", "--porcelain=v1", "--untracked-files=all"):
            raise GitSafetyError("main worktree is dirty; automatic sync stopped")
        if self._output("branch", "--show-current") != self.branch:
            raise GitSafetyError(f"expected branch {self.branch}")
        self._run("fetch", "origin", self.branch)
        local = self._output("rev-parse", "HEAD")
        remote = self._output("rev-parse", f"origin/{self.branch}")
        if local == remote:
            return
        if self._is_ancestor(local, remote):
            self._run("merge", "--ff-only", f"origin/{self.branch}")
            return
        if self._is_ancestor(remote, local):
            self._run("push", "origin", f"HEAD:{self.branch}")
            return
        raise GitSafetyError("local and remote branches diverged; manual review required")

    def changes(self, *, cwd: Path | None = None) -> tuple[GitChange, ...]:
        output = self._bytes(
            "status", "--porcelain=v1", "-z", "--untracked-files=all", cwd=cwd
        )
        records = output.split(b"\0")
        changes: list[GitChange] = []
        index = 0
        while index < len(records) and records[index]:
            record = records[index]
            status = record[:2].decode("ascii", "replace")
            path = record[3:].decode("utf-8", "surrogateescape")
            if "R" in status or "C" in status:
                index += 1
                if index >= len(records) or not records[index]:
                    raise GitSafetyError("malformed git rename record")
                path = records[index].decode("utf-8", "surrogateescape")
            changes.append(GitChange(status=status, path=path))
            index += 1
        return tuple(changes)

    def publish(self, paths: tuple[str, ...], *, task_ids: tuple[str, ...]) -> str | None:
        if not paths:
            return None
        for relative in paths:
            path = self.root / relative
            if not path.is_file():
                raise GitSafetyError(f"publication path is not a regular file: {relative}")
            _scan_file(path)
        self._run("diff", "--check")
        self._run("add", "--", *paths)
        staged = self._output("diff", "--cached", "--name-only")
        staged_paths = tuple(line for line in staged.splitlines() if line)
        if set(staged_paths) != set(paths):
            raise GitSafetyError("staged paths differ from the validated publication set")
        task_label = ", ".join(task_ids) if task_ids else "invalid task record"
        self._run("commit", "-m", f"Complete Project X task {task_label}")
        self._run("fetch", "origin", self.branch)
        remote = self._output("rev-parse", f"origin/{self.branch}")
        local = self._output("rev-parse", "HEAD")
        if not self._is_ancestor(remote, local):
            self._run("rebase", f"origin/{self.branch}")
        self._run("push", "origin", f"HEAD:{self.branch}")
        self._run("fetch", "origin", self.branch)
        local = self._output("rev-parse", "HEAD")
        remote = self._output("rev-parse", f"origin/{self.branch}")
        if local != remote:
            raise GitSafetyError("remote verification failed after push")
        return local

    def add_detached_worktree(self, path: Path) -> None:
        self._run("worktree", "add", "--detach", str(path), "HEAD")

    def remove_worktree(self, path: Path) -> None:
        self._run("worktree", "remove", "--force", str(path))
        self._run("worktree", "prune")

    def _is_ancestor(self, older: str, newer: str) -> bool:
        result = self._run("merge-base", "--is-ancestor", older, newer, check=False)
        return result.returncode == 0

    def _output(self, *args: str, cwd: Path | None = None) -> str:
        return self._run(*args, cwd=cwd).stdout.strip()

    def _bytes(self, *args: str, cwd: Path | None = None) -> bytes:
        command = ["git", "-C", str((cwd or self.root).resolve()), *args]
        completed = subprocess.run(command, capture_output=True, timeout=120, check=False)
        if completed.returncode != 0:
            raise GitSafetyError(f"git {args[0]} failed with status {completed.returncode}")
        return completed.stdout

    def _run(
        self,
        *args: str,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        command = ["git", "-C", str((cwd or self.root).resolve()), *args]
        completed = subprocess.run(
            command, text=True, capture_output=True, timeout=120, check=False
        )
        if check and completed.returncode != 0:
            raise GitSafetyError(f"git {args[0]} failed with status {completed.returncode}")
        return completed


def validate_and_copy_changes(
    *,
    repository: GitRepository,
    worktree: Path,
    destination: Path,
    allowed_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    copied: list[str] = []
    for change in repository.changes(cwd=worktree):
        if "D" in change.status or "R" in change.status or "C" in change.status:
            raise GitSafetyError(f"deletions, renames, and copies are not automatic: {change.path}")
        if not _is_allowed(change.path, allowed_prefixes):
            raise GitSafetyError(f"Codex changed a path outside the task scope: {change.path}")
        source = worktree / change.path
        if not source.is_file() or source.is_symlink():
            raise GitSafetyError(f"only regular files may be published: {change.path}")
        _scan_file(source)
        target = destination / change.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(change.path)
    return tuple(sorted(set(copied)))


def _is_allowed(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _scan_file(path: Path) -> None:
    size = path.stat().st_size
    if size > 1_000_000:
        raise GitSafetyError(f"file exceeds the 1 MB publication limit: {path.name}")
    content = path.read_bytes()
    if b"\0" in content:
        raise GitSafetyError(f"binary files are not automatically published: {path.name}")
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        digest = hashlib.sha256(content).hexdigest()[:12]
        raise GitSafetyError(f"possible secret detected; publication blocked ({digest})")
