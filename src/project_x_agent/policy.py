from __future__ import annotations

from dataclasses import dataclass

from .models import RiskLevel, Task


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    code: str
    reason: str


class SafetyPolicy:
    """Fail-closed V1 policy for tasks that may carry material risk."""

    guarded_levels = frozenset({RiskLevel.HIGH, RiskLevel.CRITICAL})

    def evaluate(self, task: Task) -> PolicyDecision:
        if task.risk_level not in self.guarded_levels:
            return PolicyDecision(
                allowed=True,
                code="risk_level_allowed",
                reason=f"{task.risk_level.value} risk is allowed to reach the configured executor",
            )

        if not task.authorization.is_explicit:
            return PolicyDecision(
                allowed=False,
                code="explicit_authorization_required",
                reason=(
                    "high and critical risk tasks require authorization.execute=true "
                    "plus approved_by, approved_at, and reason"
                ),
            )

        return PolicyDecision(
            allowed=True,
            code="explicit_authorization_present",
            reason="explicit authorization marker is complete",
        )
