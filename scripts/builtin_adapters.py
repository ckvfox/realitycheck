"""Built-in source adapters wired through explicit runtime services.

Legacy fetch implementations are injected as services during the migration
away from ``fetch_data.py``. This keeps source dispatch and normalization out
of the orchestration loop without introducing circular imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Callable

from fetch_core import AdapterMode, AdapterRegistry, AdapterRequest, AdapterResult, SourceAdapter
from source_contracts import SUPPORTED_SOURCE_TYPES


@dataclass(frozen=True)
class AdapterServices:
    log: Callable[..., None]
    get_worldbank_source_date: Callable[[str], str | None]
    get_owid_source_date: Callable[[str], str | None]
    process_worldbank: Callable[..., Any]
    process_owid: Callable[..., Any]
    process_csv: Callable[..., Any]
    process_unhcr: Callable[..., Any]
    fetch_data360: Callable[..., list[dict[str, Any]]]
    canonicalize_country: Callable[..., str | None]
    safe_float: Callable[[Any], float | None]
    resolve_iso2: Callable[..., str]
    save_records: Callable[..., None]
    keep_or_dummy: Callable[..., None]


def _worldbank_source_date(services: AdapterServices, meta: dict[str, Any]) -> str | None:
    code = meta.get("source_code") or meta.get("code")
    return services.get_worldbank_source_date(code) if code else None


def _owid_source_date(services: AdapterServices, meta: dict[str, Any]) -> str | None:
    code = meta.get("source_code") or meta.get("code")
    if not code:
        return None
    return services.get_owid_source_date(f"https://ourworldindata.org/grapher/{code}")


def _run_worldbank(services: AdapterServices, request: AdapterRequest) -> AdapterResult:
    services.process_worldbank(
        request.kpi_id,
        request.meta,
        request.countries,
        request.country_index,
        request.alias_index,
        request.pending,
        request.stats,
    )
    return AdapterResult(
        source_date=request.meta.get("_source_date"),
        data_year=request.meta.get("_latest_year"),
    )


def _run_owid(services: AdapterServices, request: AdapterRequest) -> AdapterResult:
    before = int(request.stats.get("saved_records", 0) or 0)
    services.process_owid(
        request.kpi_id,
        request.meta,
        request.countries,
        request.country_index,
        request.alias_index,
        request.pending,
        request.stats,
        output_dir=request.output_dir,
    )
    return AdapterResult(
        source_date=request.meta.get("_source_date"),
        data_year=request.meta.get("_latest_year"),
        record_count=max(0, int(request.stats.get("saved_records", 0) or 0) - before),
    )


def _run_csv(services: AdapterServices, request: AdapterRequest) -> AdapterResult:
    before = int(request.stats.get("saved_records", 0) or 0)
    latest_year = services.process_csv(
        request.kpi_id,
        request.meta,
        request.countries,
        request.country_index,
        request.alias_index,
        request.pending,
        request.stats,
        output_dir=request.output_dir,
    )
    return AdapterResult(
        source_date=request.meta.get("_source_date"),
        data_year=latest_year or request.meta.get("_latest_year"),
        record_count=max(0, int(request.stats.get("saved_records", 0) or 0) - before),
    )


def _run_unhcr(services: AdapterServices, request: AdapterRequest) -> AdapterResult:
    before = int(request.stats.get("saved_records", 0) or 0)
    services.process_unhcr(
        request.kpi_id,
        request.meta,
        request.countries,
        request.country_index,
        request.alias_index,
        request.pending,
        request.stats,
        output_dir=request.output_dir,
    )
    return AdapterResult(
        source_date=request.meta.get("_source_date"),
        data_year=request.meta.get("_latest_year"),
        record_count=max(0, int(request.stats.get("saved_records", 0) or 0) - before),
    )


def _run_data360(services: AdapterServices, request: AdapterRequest) -> AdapterResult:
    indicator_id = str(request.meta.get("source_code") or "")
    if indicator_id.lower().endswith(".csv"):
        indicator_id = indicator_id[:-4]
    if request.kpi_id != "press_freedom_index":
        services.log(f"[FETCH] Data360 fetch start for {request.kpi_id} ({indicator_id})")

    records = services.fetch_data360(indicator_id, request.meta) if indicator_id else []
    final_rows: list[dict[str, Any]] = []
    years_seen: list[int] = []
    for row in records:
        canon = services.canonicalize_country(
            row.get("REF_AREA"),
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        if not canon:
            continue
        try:
            year_int = int(float(row.get("year")))
        except Exception:
            continue
        value = services.safe_float(row.get("value"))
        if value is None:
            continue
        final_rows.append(
            {
                "country": canon,
                "iso2": services.resolve_iso2(canon, request.countries),
                "year": year_int,
                "value": float(value),
            }
        )
        years_seen.append(year_int)

    if not final_rows:
        services.keep_or_dummy(
            request.kpi_id,
            f"Data360 empty {indicator_id}",
            request.stats,
            output_dir=request.output_dir,
        )
        return AdapterResult(source_date="Unknown")

    services.save_records(request.kpi_id, final_rows, request.stats, output_dir=request.output_dir)
    request.stats["data360_success"] += 1
    request.stats["saved_records"] += len(final_rows)
    request.stats["fetched"] += len(final_rows)
    latest_year = max(years_seen) if years_seen else None
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    services.log(f"[OK] Data360 KPI saved: {request.kpi_id} ({len(final_rows)} rows)")
    return AdapterResult(source_date="Unknown", data_year=latest_year, record_count=len(final_rows))


def build_builtin_adapter_registry(services: AdapterServices) -> AdapterRegistry:
    """Build and validate the complete production adapter registry."""
    registry = AdapterRegistry()
    registry.register(
        SourceAdapter(
            "worldbank",
            handler=partial(_run_worldbank, services),
            source_date_resolver=partial(_worldbank_source_date, services),
        )
    )
    registry.register(
        SourceAdapter(
            "owid",
            handler=partial(_run_owid, services),
            source_date_resolver=partial(_owid_source_date, services),
        )
    )
    registry.register(SourceAdapter("data360", handler=partial(_run_data360, services)))
    registry.register(SourceAdapter("csv", handler=partial(_run_csv, services)))
    registry.register(SourceAdapter("unhcr", handler=partial(_run_unhcr, services)))
    registry.register(SourceAdapter("imf", mode=AdapterMode.BATCH))
    registry.register(SourceAdapter("special", mode=AdapterMode.SPECIAL))
    registry.ensure_complete(SUPPORTED_SOURCE_TYPES)
    return registry
