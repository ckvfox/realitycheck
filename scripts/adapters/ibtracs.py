"""NOAA IBTrACS global tropical cyclone best-track adapter, aggregated per ocean basin."""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult

# Public domain NOAA archive, no login required. "since1980" balances completeness
# (satellite-era, most reliable basin-wide records) against download size.
DEFAULT_IBTRACS_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.since1980.list.v04r01.csv"
)


def run(request: AdapterRequest, *, runtime: SourceRuntime, http_get=requests.get) -> AdapterResult:
    source_code = str(request.meta.get("source_code") or DEFAULT_IBTRACS_URL).strip()
    try:
        # (connect_timeout, read_timeout): fail fast if the host is unreachable
        # instead of hanging on a silently-dropped connection.
        response = http_get(source_code, timeout=(15, 90))
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
        raw = response.content
    except Exception as exc:
        runtime.log(f"[ERROR] IBTrACS fetch failed for {source_code}: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, f"IBTrACS fetch failed {source_code}", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()

    try:
        # Row 0 = column names, row 1 = units; data starts at row 2.
        frame = pd.read_csv(
            io.BytesIO(raw), header=0, skiprows=[1],
            usecols=["SID", "SEASON", "BASIN"], dtype=str, low_memory=False,
        )
    except Exception as exc:
        runtime.log(f"[ERROR] IBTrACS parse failed: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, "IBTrACS parse error", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()

    frame["BASIN"] = frame["BASIN"].str.strip()
    frame["SEASON"] = pd.to_numeric(frame["SEASON"], errors="coerce")
    frame = frame.dropna(subset=["SID", "BASIN", "SEASON"])
    frame = frame[frame["BASIN"] != ""]
    frame["SEASON"] = frame["SEASON"].astype(int)

    # One row per storm-basin-season combination avoids double counting the many
    # best-track fixes recorded for each storm.
    storm_seasons = frame.drop_duplicates(subset=["SID", "BASIN", "SEASON"])
    counts = storm_seasons.groupby(["BASIN", "SEASON"]).size()

    current_year = datetime.now().year
    records = [
        {"region": basin, "year": int(season), "value": float(count), "scenario": "historical", "horizon": ""}
        for (basin, season), count in counts.items()
        if season < current_year
    ]
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, "IBTrACS series empty", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()
    if runtime.save_region_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()

    latest_year = max(row["year"] for row in records)
    request.stats["others_success"] = request.stats.get("others_success", 0) + 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    runtime.log(f"[OK] IBTrACS KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(
        source_date=f"{latest_year}-12-31", data_year=latest_year, record_count=len(records)
    )
