from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from project_x_agent.executor import CodexCliExecutor
from project_x_agent.models import Task


class CodexCliExecutorTests(unittest.TestCase):
    def test_analysis_mode_maps_to_read_only_cli_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "fake-codex"
            executable.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\"\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            task = Task.from_dict(
                {
                    "schema_version": 1,
                    "id": "executor-test-001",
                    "title": "Test sandbox mapping",
                    "objective": "Return the fake CLI arguments.",
                    "risk_level": "low",
                    "created_at": "2026-08-26T18:00:00+08:00",
                    "authorization": {"execute": False},
                    "execution": {"mode": "analysis", "write_paths": []},
                    "metadata": {},
                }
            )

            outcome = CodexCliExecutor(
                repo_root=root,
                codex_binary=executable,
            ).execute(task)

            self.assertEqual(outcome.status, "completed")
            final = next(item.content for item in outcome.artifacts if item.relative_path == "codex-final.md")
            self.assertIn("read-only", final)
            self.assertNotIn("\nanalysis\n", final)


if __name__ == "__main__":
    unittest.main()
