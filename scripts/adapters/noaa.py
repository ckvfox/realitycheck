"""NOAA Laboratory for Satellite Altimetry CSV adapter."""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime
from statistics import mean

import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult


def run(
    request: AdapterRequest,
    *,
    runtime: SourceRuntime,
    http_get=requests.get,
) -> AdapterResult:
    """Fetch and annualize NOAA's multi-mission global sea-level series."""
    source_code = str(request.meta.get("source_code") or "").strip()
    try:
        response = http_get(source_code, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
    except Exception as exc:
        runtime.log(f"[ERROR] NOAA fetch failed for {source_code}: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, f"NOAA fetch failed {source_code}", request.stats,
            output_dir=request.output_dir,
        )
        return AdapterResult()

    text = "\n".join(line for line in response.text.splitlines() if not line.startswith("#"))
    reader = csv.DictReader(io.StringIO(text))
    annual: dict[int, list[float]] = defaultdict(list)
    for row in reader:
        try:
            year = int(float(str(row.get("year") or "")))
        except (TypeError, ValueError):
            continue
        # Mission columns overlap during handovers. Average all available values
        # for an observation date, then annualize those observation means.
        values = [
            runtime.safe_float(value) for key, value in row.items()
            if key != "year" and str(value or "").strip()
        ]
        usable = [value for value in values if value is not None]
        if usable:
            annual[year].append(mean(usable))

    current_year = datetime.now().year
    records = [
        {"country": "World", "iso2": "OWID_WRL", "year": year, "value": mean(values)}
        for year, values in sorted(annual.items())
        if values and year < current_year
    ]
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, "NOAA global sea-level series empty", request.stats,
            output_dir=request.output_dir,
        )
        return AdapterResult()
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()

    latest_year = records[-1]["year"]
    request.stats["noaa_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    runtime.log(f"[OK] NOAA KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(
        source_date=f"{latest_year}-12-31", data_year=latest_year, record_count=len(records)
    )
