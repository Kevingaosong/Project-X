from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from project_x_agent.gitops import GitRepository, GitSafetyError, validate_and_copy_changes


class GitOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.main = self.root / "main"
        self.worktree = self.root / "worktree"
        self.main.mkdir()
        self._git(self.main, "init", "-b", "main")
        self._git(self.main, "config", "user.name", "Project X Test")
        self._git(self.main, "config", "user.email", "project-x-test@example.invalid")
        (self.main / "README.md").write_text("baseline\n", encoding="utf-8")
        self._git(self.main, "add", "README.md")
        self._git(self.main, "commit", "-m", "baseline")
        self.repository = GitRepository(self.main)
        self.repository.add_detached_worktree(self.worktree)

    def tearDown(self) -> None:
        if self.worktree.exists():
            self.repository.remove_worktree(self.worktree)
        self.temporary_directory.cleanup()

    def test_only_allowed_regular_file_is_copied(self) -> None:
        generated = self.worktree / "outputs" / "demo.txt"
        generated.parent.mkdir()
        generated.write_text("safe output\n", encoding="utf-8")

        copied = validate_and_copy_changes(
            repository=self.repository,
            worktree=self.worktree,
            destination=self.main,
            allowed_prefixes=("outputs",),
        )

        self.assertEqual(copied, ("outputs/demo.txt",))
        self.assertEqual((self.main / "outputs" / "demo.txt").read_text(), "safe output\n")

    def test_out_of_scope_change_is_blocked(self) -> None:
        (self.worktree / "README.md").write_text("unauthorized\n", encoding="utf-8")

        with self.assertRaisesRegex(GitSafetyError, "outside the task scope"):
            validate_and_copy_changes(
                repository=self.repository,
                worktree=self.worktree,
                destination=self.main,
                allowed_prefixes=("outputs",),
            )

    def test_possible_secret_is_blocked_without_echoing_value(self) -> None:
        generated = self.worktree / "outputs" / "unsafe.txt"
        generated.parent.mkdir()
        generated.write_text(
            "github_" + "pat_1234567890abcdefghij\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(GitSafetyError, "possible secret detected") as raised:
            validate_and_copy_changes(
                repository=self.repository,
                worktree=self.worktree,
                destination=self.main,
                allowed_prefixes=("outputs",),
            )
        self.assertNotIn("github_pat", str(raised.exception))

    @staticmethod
    def _git(directory: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(directory), *args],
            capture_output=True,
            text=True,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
