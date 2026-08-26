from __future__ import annotations

from dataclasses import dataclass, field
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
