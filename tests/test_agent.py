from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from project_x_agent import MockCodexExecutor, MockGitPublisher, ProjectXAgent


class ProjectXAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.tasks = self.root / "tasks"
        self.results = self.root / "results"
        self.tasks.mkdir()
        self.agent = ProjectXAgent(
            tasks_dir=self.tasks,
            results_dir=self.results,
            executor=MockCodexExecutor(),
            publisher=MockGitPublisher(),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_low_risk_task_completes_with_mock_artifact(self) -> None:
        self._write_task("low.json", self._task())

        summary = self.agent.scan_once()

        self.assertEqual(summary.completed, 1)
        result = self._result("test-task-001")
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["executor_is_mock"])
        self.assertTrue((self.results / "test-task-001" / "mock-output.md").is_file())
        publication = self._publication("test-task-001")
        self.assertFalse(publication["pushed"])

    def test_high_risk_task_is_blocked_without_explicit_authorization(self) -> None:
        task = self._task(risk_level="high")
        self._write_task("high.json", task)

        summary = self.agent.scan_once()

        self.assertEqual(summary.blocked, 1)
        result = self._result("test-task-001")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["policy"]["code"], "explicit_authorization_required")
        self.assertFalse((self.results / "test-task-001" / "mock-output.md").exists())

    def test_high_risk_task_reaches_only_mock_executor_when_authorized(self) -> None:
        task = self._task(risk_level="high")
        task["authorization"] = {
            "execute": True,
            "approved_by": "test-human",
            "approved_at": "2026-08-26T15:00:00+08:00",
            "reason": "Unit test approval",
        }
        self._write_task("high-approved.json", task)

        summary = self.agent.scan_once()

        self.assertEqual(summary.completed, 1)
        result = self._result("test-task-001")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["executor"], "mock-codex")
        self.assertTrue(result["executor_is_mock"])

    def test_same_task_hash_is_idempotently_skipped(self) -> None:
        self._write_task("low.json", self._task())
        first = self.agent.scan_once()
        second = self.agent.scan_once()

        self.assertEqual(first.completed, 1)
        self.assertEqual(second.skipped, 1)
        self.assertEqual(second.completed, 0)

    def test_inline_sensitive_field_is_rejected(self) -> None:
        task = self._task()
        task["metadata"] = {"api_token": "not-a-real-value"}
        self._write_task("invalid.json", task)

        summary = self.agent.scan_once()

        self.assertEqual(summary.invalid, 1)
        invalid = json.loads(
            (self.results / "_invalid" / "invalid.json").read_text(encoding="utf-8")
        )
        self.assertEqual(invalid["status"], "invalid")
        self.assertIn("inline sensitive field is forbidden", invalid["error"])

    def test_inline_sensitive_value_is_rejected(self) -> None:
        task = self._task()
        task["objective"] = "Use " + "ghp_" + "1234567890abcdefghij in a request"
        self._write_task("sensitive-value.json", task)

        summary = self.agent.scan_once()

        self.assertEqual(summary.invalid, 1)
        invalid = json.loads(
            (self.results / "_invalid" / "sensitive-value.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("inline sensitive value is forbidden", invalid["error"])

    def test_timestamp_requires_timezone(self) -> None:
        task = self._task()
        task["created_at"] = "2026-08-26T15:00:00"
        self._write_task("bad-time.json", task)

        summary = self.agent.scan_once()

        self.assertEqual(summary.invalid, 1)
        invalid = json.loads(
            (self.results / "_invalid" / "bad-time.json").read_text(encoding="utf-8")
        )
        self.assertIn("must include a timezone", invalid["error"])

    def test_non_mock_adapter_is_rejected(self) -> None:
        class UnsafeExecutor:
            name = "unsafe"
            is_mock = False

        with self.assertRaisesRegex(ValueError, "mock executor"):
            ProjectXAgent(
                tasks_dir=self.tasks,
                results_dir=self.results,
                executor=UnsafeExecutor(),
                publisher=MockGitPublisher(),
            )

        class UnsafePublisher:
            name = "unsafe-git"
            is_mock = False

        with self.assertRaisesRegex(ValueError, "mock executor and publisher"):
            ProjectXAgent(
                tasks_dir=self.tasks,
                results_dir=self.results,
                executor=MockCodexExecutor(),
                publisher=UnsafePublisher(),
            )

    def _task(self, *, risk_level: str = "low") -> dict[str, object]:
        return {
            "schema_version": 1,
            "id": "test-task-001",
            "title": "Test task",
            "objective": "Exercise the mock control loop.",
            "risk_level": risk_level,
            "created_at": "2026-08-26T15:00:00+08:00",
            "authorization": {"execute": False},
            "metadata": {},
        }

    def _write_task(self, filename: str, value: dict[str, object]) -> None:
        (self.tasks / filename).write_text(
            json.dumps(value, ensure_ascii=False), encoding="utf-8"
        )

    def _result(self, task_id: str) -> dict[str, object]:
        return json.loads(
            (self.results / task_id / "result.json").read_text(encoding="utf-8")
        )

    def _publication(self, task_id: str) -> dict[str, object]:
        return json.loads(
            (self.results / task_id / "publication.json").read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
