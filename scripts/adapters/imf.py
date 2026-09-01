"""IMF DataMapper batch adapter."""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from adapters.runtime import SourceRuntime

DATAMAPPER_URL = "https://www.imf.org/external/datamapper/api/v1/{source_code}"


def _download(source_code: str, *, session: requests.Session, runtime: SourceRuntime) -> dict[str, Any] | None:
    url = DATAMAPPER_URL.format(source_code=source_code)
    for attempt in range(1, 4):
        try:
            response = session.get(url, timeout=45)
            if response.status_code == 200:
                payload = response.json()
                return payload if isinstance(payload, dict) else None
            runtime.log(f"[WARN] IMF DataMapper HTTP {response.status_code} for {source_code} ({attempt}/3)")
            if response.status_code < 500 and response.status_code != 429:
                return None
        except Exception as exc:
            runtime.log(f"[WARN] IMF DataMapper request failed for {source_code} ({attempt}/3): {exc}")
        if attempt < 3:
            time.sleep(attempt * 2)
    return None


def fetch_batch(
    imf_kpis: list[dict[str, Any]],
    *,
    countries: dict[str, Any],
    country_index,
    alias_index,
    pending: dict[str, Any],
    fetch_status: dict[str, Any],
    stats: dict[str, Any],
    force_all_updates: bool,
    output_dir: Path,
    runtime: SourceRuntime,
    should_fetch,
    session: requests.Session | None = None,
) -> None:
    """Fetch all selected IMF KPIs through one reusable HTTP session."""
    if not imf_kpis:
        return
    client = session or requests.Session()
    runtime.log(f"[FETCH] IMF DataMapper batch start for {len(imf_kpis)} KPI(s)")

    for meta in imf_kpis:
        kpi_id = str(meta.get("filename") or meta.get("id") or "kpi")
        source_code = str(meta.get("source_code") or "").strip()
        if not source_code:
            runtime.keep_or_dummy(kpi_id, "IMF missing source_code", stats, output_dir=output_dir)
            continue
        if not force_all_updates and not should_fetch(kpi_id, "imf", None, meta, fetch_status):
            runtime.mark_skip(stats, "Remote data unchanged")
            runtime.log(f"[SKIP] {kpi_id}: IMF source unchanged")
            continue

        payload = _download(source_code, session=client, runtime=runtime)
        indicator_block = ((payload or {}).get("values") or {}).get(source_code, {})
        records: list[dict[str, Any]] = []
        latest_year: int | None = None
        current_year = datetime.now().year
        for iso3, year_values in indicator_block.items():
            if not isinstance(year_values, dict):
                continue
            canon = runtime.canonicalize_country(
                iso3, country_index, alias_index, countries, pending, stats
            )
            if not canon:
                continue
            canonical_iso3 = runtime.resolve_iso3(canon, countries, fallback=iso3)
            for year, value in year_values.items():
                try:
                    year_int = int(year)
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                if year_int > current_year:
                    continue
                latest_year = max(latest_year or year_int, year_int)
                records.append(
                    {"country": canon, "iso3": canonical_iso3, "year": year_int, "value": numeric}
                )

        if not records:
            runtime.keep_or_dummy(
                kpi_id, f"IMF DataMapper empty {source_code}", stats, output_dir=output_dir
            )
            continue

        if runtime.save_imf_records(kpi_id, records, stats, output_dir=output_dir) is False:
            continue
        stats["imf_success"] += 1
        stats["saved_records"] += len(records)
        stats["fetched"] += len(records)
        updated = stats.setdefault("updated_kpis", set())
        already_updated = kpi_id in updated
        updated.add(kpi_id)
        if not already_updated:
            stats["updated"] += 1
        source_date = str(latest_year) if latest_year else "Unknown"
        fetch_status.setdefault("kpis", {})[kpi_id] = {
            "source": "IMF DataMapper API",
            "source_type": "imf",
            "source_code": source_code,
            "source_date": source_date,
            "data_year": latest_year,
            "last_fetch": runtime.now_utc(),
        }
        runtime.log(f"[OK] IMF KPI saved: {kpi_id} ({len(records)} rows, last year {latest_year})")

    runtime.log("[INFO] IMF DataMapper batch completed")
