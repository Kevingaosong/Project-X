from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


TASK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
MAX_TASK_BYTES = 64 * 1024
FORBIDDEN_KEY_PARTS = (
    "api_key",
    "apikey",
    "cookie",
    "credential",
    "oauth_secret",
    "password",
    "private_key",
    "secret",
    "token",
)
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:ghp|github_pat|sk)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE),
)


class TaskValidationError(ValueError):
    """Raised when a task file violates the V1 task contract."""


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Authorization:
    execute: bool = False
    approved_by: str | None = None
    approved_at: str | None = None
    reason: str | None = None

    @property
    def is_explicit(self) -> bool:
        return bool(self.execute and self.approved_by and self.approved_at and self.reason)


@dataclass(frozen=True)
class Task:
    schema_version: int
    id: str
    title: str
    objective: str
    risk_level: RiskLevel
    created_at: str
    authorization: Authorization = field(default_factory=Authorization)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Task":
        _reject_sensitive_keys(payload)

        if payload.get("schema_version") != 1:
            raise TaskValidationError("schema_version must be 1")

        task_id = _required_string(payload, "id")
        if not TASK_ID_PATTERN.fullmatch(task_id):
            raise TaskValidationError(
                "id must be 3-64 lowercase letters, numbers, dots, dashes, or underscores"
            )

        title = _required_string(payload, "title")
        objective = _required_string(payload, "objective")
        created_at = _required_timestamp(payload, "created_at")

        try:
            risk_level = RiskLevel(payload.get("risk_level"))
        except ValueError as exc:
            raise TaskValidationError(
                "risk_level must be low, medium, high, or critical"
            ) from exc

        raw_authorization = payload.get("authorization", {})
        if not isinstance(raw_authorization, dict):
            raise TaskValidationError("authorization must be an object")

        authorization = Authorization(
            execute=raw_authorization.get("execute") is True,
            approved_by=_optional_string(raw_authorization, "approved_by"),
            approved_at=_optional_timestamp(raw_authorization, "approved_at"),
            reason=_optional_string(raw_authorization, "reason"),
        )

        raw_metadata = payload.get("metadata", {})
        if not isinstance(raw_metadata, dict):
            raise TaskValidationError("metadata must be an object")

        return cls(
            schema_version=1,
            id=task_id,
            title=title,
            objective=objective,
            risk_level=risk_level,
            created_at=created_at,
            authorization=authorization,
            metadata=raw_metadata,
        )


@dataclass(frozen=True)
class TaskEnvelope:
    task: Task
    source_path: Path
    content_hash: str


def load_task(path: Path) -> TaskEnvelope:
    size = path.stat().st_size
    if size > MAX_TASK_BYTES:
        raise TaskValidationError(f"task file exceeds {MAX_TASK_BYTES} bytes")

    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TaskValidationError(f"task file is not valid UTF-8 JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise TaskValidationError("task document must be a JSON object")

    return TaskEnvelope(
        task=Task.from_dict(payload),
        source_path=path,
        content_hash=hashlib.sha256(raw).hexdigest(),
    )


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TaskValidationError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise TaskValidationError(f"authorization.{key} must be a non-empty string")
    return value.strip()


def _required_timestamp(payload: dict[str, Any], key: str) -> str:
    value = _required_string(payload, key)
    _validate_timestamp(value, key)
    return value


def _optional_timestamp(payload: dict[str, Any], key: str) -> str | None:
    value = _optional_string(payload, key)
    if value is not None:
        _validate_timestamp(value, f"authorization.{key}")
    return value


def _validate_timestamp(value: str, key: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TaskValidationError(f"{key} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise TaskValidationError(f"{key} must include a timezone")


def _reject_sensitive_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                location = ".".join((*path, str(key)))
                raise TaskValidationError(
                    f"inline sensitive field is forbidden: {location}; use a future secret reference adapter"
                )
            _reject_sensitive_keys(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, (*path, str(index)))
    elif isinstance(value, str):
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                location = ".".join(path) or "document"
                raise TaskValidationError(
                    f"inline sensitive value is forbidden at {location}; use a future secret reference adapter"
                )
