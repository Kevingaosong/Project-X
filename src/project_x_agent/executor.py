from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import subprocess
from typing import Protocol

from .models import Task


@dataclass(frozen=True)
class GeneratedArtifact:
    relative_path: str
    content: str


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    summary: str
    artifacts: tuple[GeneratedArtifact, ...] = field(default_factory=tuple)


class TaskExecutor(Protocol):
    name: str
    is_mock: bool

    def execute(self, task: Task) -> ExecutionOutcome: ...


class MockCodexExecutor:
    """Deterministic executor that never invokes Codex, a shell, or a network API."""

    name = "mock-codex"
    is_mock = True

    def execute(self, task: Task) -> ExecutionOutcome:
        artifact = GeneratedArtifact(
            relative_path="mock-output.md",
            content=(
                f"# Mock result: {task.title}\n\n"
                "No command, Codex session, external API, or business adapter was invoked.\n\n"
                f"Task ID: `{task.id}`  \n"
                f"Risk level: `{task.risk_level.value}`\n"
            ),
        )
        return ExecutionOutcome(
            status="completed",
            summary="Mock execution completed without invoking any real capability.",
            artifacts=(artifact,),
        )


class CodexCliExecutor:
    """Run one task through the authenticated local Codex CLI with a fixed sandbox."""

    name = "codex-cli"
    is_mock = False

    def __init__(
        self,
        *,
        repo_root: Path,
        codex_binary: Path,
        timeout_seconds: int = 900,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.codex_binary = codex_binary.resolve()
        self.timeout_seconds = timeout_seconds

    def execute(self, task: Task) -> ExecutionOutcome:
        sandbox = task.execution.mode.value
        allowed = ", ".join(task.execution.write_paths) or "none (read-only analysis)"
        prompt = (
            "You are a constrained Project X worker. Complete only the task below.\n"
            "Safety boundary:\n"
            "- Work only inside the current Git worktree.\n"
            "- Do not access files outside it, secrets, credentials, tokens, cookies, or private keys.\n"
            "- Do not use network services, production APIs, messaging, trading, brokerage, or payments.\n"
            "- Do not run git commit, git push, launchctl, cron, or persistent processes.\n"
            "- Do not modify tasks/, results/, the Project X control plane, or any path not explicitly allowed.\n"
            f"Allowed write paths: {allowed}\n"
            "If the request conflicts with these boundaries, explain the block without taking the action.\n\n"
            f"Task title: {task.title}\n"
            f"Task objective: {task.objective}\n"
        )
        command = [
            str(self.codex_binary),
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            sandbox,
            "--cd",
            str(self.repo_root),
            "--color",
            "never",
            "-",
        ]
        environment = os.environ.copy()
        for name in tuple(environment):
            lowered = name.lower()
            if any(part in lowered for part in ("token", "secret", "password", "api_key", "cookie")):
                environment.pop(name, None)
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                cwd=self.repo_root,
                env=environment,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Codex execution timed out after {self.timeout_seconds}s") from exc

        stdout = _safe_output(completed.stdout)
        stderr = _safe_output(completed.stderr)
        artifacts = (
            GeneratedArtifact("codex-final.md", stdout or "Codex returned no final message.\n"),
            GeneratedArtifact("codex-events.log", stderr),
        )
        if completed.returncode != 0:
            return ExecutionOutcome(
                status="failed",
                summary=f"Codex CLI exited with status {completed.returncode}.",
                artifacts=artifacts,
            )
        return ExecutionOutcome(
            status="completed",
            summary="Codex CLI completed inside the task worktree sandbox.",
            artifacts=artifacts,
        )


def _safe_output(value: str, limit: int = 1_000_000) -> str:
    text = value[:limit]
    for pattern in (
        r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}",
        r"\b(?:ghp|github_pat|sk)_[A-Za-z0-9_-]{12,}\b",
        r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----",
    ):
        import re

        text = re.sub(pattern, "[REDACTED]", text)
    if len(value) > limit:
        text += "\n[output truncated]\n"
    return text
