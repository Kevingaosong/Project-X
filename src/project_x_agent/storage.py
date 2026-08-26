from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ResultStore:
    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir

    def task_dir(self, task_id: str) -> Path:
        return self.results_dir / task_id

    def current_result(self, task_id: str) -> dict[str, Any] | None:
        path = self.task_dir(task_id) / "result.json"
        if not path.is_file():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def is_current(self, task_id: str, content_hash: str) -> bool:
        result = self.current_result(task_id)
        return bool(
            result
            and result.get("task_hash") == content_hash
            and result.get("status") in {"blocked", "completed", "failed"}
        )

    def append_event(self, task_id: str, event: str, **fields: Any) -> None:
        directory = self.task_dir(task_id)
        directory.mkdir(parents=True, exist_ok=True)
        record = {"timestamp": utc_now(), "event": event, **fields}
        with (directory / "execution.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def write_json(self, task_id: str, filename: str, value: dict[str, Any]) -> Path:
        path = self.task_dir(task_id) / filename
        _atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return path

    def write_text(self, task_id: str, relative_path: str, content: str) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("artifact path must stay inside the task result directory")
        path = self.task_dir(task_id) / relative
        _atomic_write(path, content)
        return path

    def write_invalid(self, source_name: str, source_hash: str, error: str) -> Path:
        safe_name = Path(source_name).name.replace(".json", "")
        path = self.results_dir / "_invalid" / f"{safe_name}.json"
        if path.is_file():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                existing = None
            if (
                isinstance(existing, dict)
                and existing.get("source_hash") == source_hash
                and existing.get("error") == error
            ):
                return path
        _atomic_write(
            path,
            json.dumps(
                {
                    "status": "invalid",
                    "source": Path(source_name).name,
                    "source_hash": source_hash,
                    "error": error,
                    "recorded_at": utc_now(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
        return path


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
