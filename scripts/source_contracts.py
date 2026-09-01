"""Pure validation and selection rules for RealityCheck KPI sources.

This module intentionally performs no file, network, or environment access so
new source definitions can be checked in unit tests before a fetch is started.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


SUPPORTED_SOURCE_TYPES = frozenset(
    {"csv", "data360", "imf", "noaa", "owid", "special", "unhcr", "worldbank"}
)
_FILENAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


class SourceContractError(ValueError):
    """Raised when KPI metadata cannot be handled safely by the fetcher."""


@dataclass(frozen=True)
class KpiSelection:
    """Selected KPI metadata plus entries explicitly disabled with ``test=o``."""

    selected: tuple[dict[str, Any], ...]
    ignored: tuple[str, ...]


def validate_source_registry(entries: Iterable[Any]) -> list[str]:
    """Return deterministic contract violations for a KPI registry."""
    errors: list[str] = []
    seen: set[str] = set()
    items = list(entries)
    if not items:
        return ["registry must contain at least one entry"]

    for index, item in enumerate(items):
        label = f"entry {index + 1}"
        if not isinstance(item, Mapping):
            errors.append(f"{label}: must be an object")
            continue

        filename = str(item.get("filename", "")).strip()
        if not filename:
            errors.append(f"{label}: filename is required")
        elif not _FILENAME_PATTERN.fullmatch(filename):
            errors.append(f"{label}: invalid filename '{filename}'")
        elif filename in seen:
            errors.append(f"{label}: duplicate filename '{filename}'")
        else:
            seen.add(filename)

        source_type = str(item.get("source_type") or item.get("type") or "").strip().lower()
        if source_type not in SUPPORTED_SOURCE_TYPES:
            errors.append(f"{filename or label}: unsupported source_type '{source_type or '<missing>'}'")

        source_code = str(item.get("source_code") or item.get("code") or "").strip()
        if source_type in SUPPORTED_SOURCE_TYPES and not source_code:
            errors.append(f"{filename or label}: source_code is required for {source_type}")

        test_flag = str(item.get("test", "")).strip()
        if test_flag not in {"", "*", "o"}:
            errors.append(f"{filename or label}: test must be empty, '*' or 'o'")

        fetch_policy = str(item.get("fetch_policy", "")).strip()
        if fetch_policy not in {"", "provider_restricted"}:
            errors.append(
                f"{filename or label}: fetch_policy must be empty or 'provider_restricted'"
            )

        refresh_hours = item.get("refresh_hours")
        if refresh_hours is not None:
            try:
                if float(refresh_hours) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{filename or label}: refresh_hours must be a positive number")

        publication_status = str(item.get("publication_status", "")).strip()
        if publication_status not in {"", "pending_first_fetch"}:
            errors.append(
                f"{filename or label}: publication_status must be empty or 'pending_first_fetch'"
            )

    return errors


def ensure_source_registry(entries: Iterable[Any]) -> None:
    """Raise a single blocking error when source metadata violates contracts."""
    errors = validate_source_registry(entries)
    if errors:
        raise SourceContractError("; ".join(errors))


def select_kpis(
    entries: Iterable[Mapping[str, Any]],
    *,
    kpi: str | None = None,
    test_mode: bool = False,
) -> KpiSelection:
    """Select enabled KPI definitions without mutating the registry entries."""
    selected: list[dict[str, Any]] = []
    ignored: list[str] = []

    for raw in entries:
        item = dict(raw)
        filename = str(item.get("filename", "")).strip()
        if kpi and filename != kpi:
            continue

        test_flag = str(item.get("test", "")).strip()
        if test_flag == "o":
            ignored.append(filename or str(item.get("title") or "?"))
            continue
        if test_mode and test_flag != "*":
            continue
        selected.append(item)

    return KpiSelection(tuple(selected), tuple(ignored))
