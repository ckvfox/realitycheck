"""Typed orchestration primitives for the RealityCheck fetch pipeline.

The module is deliberately free of network and filesystem access. Concrete
source adapters are registered by ``fetch_data.py`` while orchestration and
status rules remain independently testable here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping


class AdapterMode(str, Enum):
    IMMEDIATE = "immediate"
    BATCH = "batch"
    SPECIAL = "special"


class AdapterRegistryError(RuntimeError):
    """Raised for missing, duplicate, or incorrectly used adapters."""


@dataclass
class AdapterRequest:
    kpi_id: str
    meta: MutableMapping[str, Any]
    countries: Mapping[str, Any]
    country_index: Mapping[str, str]
    alias_index: Mapping[str, str]
    pending: MutableMapping[str, Any]
    stats: MutableMapping[str, Any]
    output_dir: Path


@dataclass(frozen=True)
class AdapterResult:
    source_date: str | None = None
    data_year: int | None = None
    record_count: int = 0

    def apply_to(self, meta: MutableMapping[str, Any]) -> None:
        if self.source_date is not None:
            meta["_source_date"] = self.source_date
        if self.data_year is not None:
            meta["_latest_year"] = self.data_year


AdapterHandler = Callable[[AdapterRequest], AdapterResult]
SourceDateResolver = Callable[[Mapping[str, Any]], str | None]


def unknown_source_date(_: Mapping[str, Any]) -> str:
    return "Unknown"


@dataclass(frozen=True)
class SourceAdapter:
    source_type: str
    mode: AdapterMode = AdapterMode.IMMEDIATE
    handler: AdapterHandler | None = None
    source_date_resolver: SourceDateResolver = unknown_source_date

    def resolve_source_date(self, meta: Mapping[str, Any]) -> str | None:
        return self.source_date_resolver(meta)


class AdapterRegistry:
    """Explicit source-type registry replacing condition-heavy dispatch."""

    def __init__(self) -> None:
        self._adapters: dict[str, SourceAdapter] = {}

    @property
    def source_types(self) -> frozenset[str]:
        return frozenset(self._adapters)

    def register(self, adapter: SourceAdapter) -> None:
        source_type = adapter.source_type.strip().lower()
        if not source_type:
            raise AdapterRegistryError("Adapter source_type must not be empty")
        if source_type in self._adapters:
            raise AdapterRegistryError(f"Duplicate adapter registration: {source_type}")
        if adapter.mode is AdapterMode.IMMEDIATE and adapter.handler is None:
            raise AdapterRegistryError(f"Immediate adapter requires a handler: {source_type}")
        self._adapters[source_type] = adapter

    def get(self, source_type: str) -> SourceAdapter:
        key = source_type.strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            raise AdapterRegistryError(f"No adapter registered for source_type '{key}'") from exc

    def dispatch(self, source_type: str, request: AdapterRequest) -> AdapterResult:
        adapter = self.get(source_type)
        if adapter.mode is not AdapterMode.IMMEDIATE or adapter.handler is None:
            raise AdapterRegistryError(
                f"Adapter '{adapter.source_type}' is {adapter.mode.value} and cannot run immediately"
            )
        result = adapter.handler(request)
        if not isinstance(result, AdapterResult):
            raise AdapterRegistryError(f"Adapter '{adapter.source_type}' returned an invalid result")
        return result

    def ensure_complete(self, expected_source_types: set[str] | frozenset[str]) -> None:
        expected = {item.strip().lower() for item in expected_source_types}
        missing = expected - set(self._adapters)
        extra = set(self._adapters) - expected
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing={','.join(sorted(missing))}")
            if extra:
                details.append(f"unexpected={','.join(sorted(extra))}")
            raise AdapterRegistryError("Adapter registry mismatch: " + "; ".join(details))


@dataclass(frozen=True)
class StatusResolution:
    entry: dict[str, Any]
    source_date: str
    data_year: int | None


def build_status_entry(
    meta: Mapping[str, Any],
    *,
    discovered_source_date: str | None,
    previous: Mapping[str, Any] | None,
    fetched_at: str,
) -> StatusResolution:
    """Build a stable fetch-status entry without mutating adapter metadata."""
    previous = previous or {}
    data_year = meta.get("_latest_year") or previous.get("data_year") or None
    candidate_date = meta.get("_source_date") or discovered_source_date
    if not candidate_date or candidate_date == "Unknown":
        candidate_date = previous.get("source_date") or "Unknown"
    source_date = str(candidate_date)
    entry = {
        "source": meta.get("source") or meta.get("source_type") or "unknown",
        "url": meta.get("source_url") or meta.get("url") or "",
        "source_date": source_date,
        "data_year": data_year,
        "last_fetch": fetched_at,
    }
    return StatusResolution(entry=entry, source_date=source_date, data_year=data_year)


def force_refresh_required(force_requested: bool, fetch_status: Mapping[str, Any] | None) -> bool:
    """Force refreshes when requested or when no usable prior KPI status exists."""
    status_kpis = (fetch_status or {}).get("kpis")
    return bool(force_requested or not isinstance(status_kpis, Mapping) or not status_kpis)
