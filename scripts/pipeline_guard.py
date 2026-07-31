"""Fail-closed guards for the RealityCheck data pipeline."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class PipelineGuardError(RuntimeError):
    """Raised when a pipeline result is unsafe to publish."""


def fetch_failure_reasons(stats: Mapping[str, Any]) -> list[str]:
    """Return human-readable reasons why a fetch result must not be published."""
    reasons: list[str] = []
    errors = int(stats.get("errors", 0) or 0)
    dummies = int(stats.get("dummies", 0) or 0)
    processed = int(stats.get("kpis_loaded", 0) or 0)

    if processed <= 0:
        reasons.append("no KPIs were selected or processed")
    if errors > 0:
        reasons.append(f"{errors} fetch error(s) were reported")
    if dummies > 0:
        reasons.append(f"{dummies} dummy or fallback result(s) were reported")
    return reasons


def ensure_fetch_succeeded(stats: Mapping[str, Any]) -> None:
    """Raise when the fetch result is not safe for post-processing or deployment."""
    reasons = fetch_failure_reasons(stats)
    if reasons:
        raise PipelineGuardError("; ".join(reasons))
