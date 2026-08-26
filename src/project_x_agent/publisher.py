from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class PublicationReceipt:
    status: str
    adapter: str
    commit_message: str
    pushed: bool
    detail: str


class ResultPublisher(Protocol):
    name: str
    is_mock: bool

    def publish(
        self,
        *,
        task_id: str,
        commit_message: str,
        paths: Sequence[Path],
    ) -> PublicationReceipt: ...


class MockGitPublisher:
    """Records publish intent without running git or changing a remote repository."""

    name = "mock-git"
    is_mock = True

    def publish(
        self,
        *,
        task_id: str,
        commit_message: str,
        paths: Sequence[Path],
    ) -> PublicationReceipt:
        del task_id, paths
        return PublicationReceipt(
            status="mocked",
            adapter=self.name,
            commit_message=commit_message,
            pushed=False,
            detail="No git command was executed and no remote was changed.",
        )
