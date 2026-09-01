"""World Bank Data360 adapter."""
from __future__ import annotations

import math
from typing import Any

import pandas as pd
import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult

API_URL = "https://data360api.worldbank.org/data360/data"


def _latest_raw_year(records: list[dict[str, Any]]) -> int | None:
    years: list[int] = []
    for row in records:
        try:
            value = float(row.get("OBS_VALUE", row.get("value")))
            if not math.isfinite(value):
                continue
            years.append(int(float(row.get("TIME_PERIOD", row.get("year")))))
        except (TypeError, ValueError):
            continue
    return max(years) if years else None


def _read_csv_records(source, *, runtime: SourceRuntime) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        frame = pd.read_csv(source)
    except Exception as exc:
        runtime.log(f"[WARN] Data360 CSV failed for {source}: {exc}")
        return records
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    columns = list(frame.columns)
    iso_column = next((column for column in columns if column in {"ref_area", "refarea"}), None)
    time_column = next((column for column in columns if column in {"time_period", "timeperiod", "year"}), None)
    value_column = next(
        (column for column in columns if column in {"obs_value", "obsvalue", "value", "score"}), None
    )
    label_column = next(
        (column for column in columns if column in {"ref_area_label", "country", "entity"}), None
    )
    if time_column and value_column and (iso_column or label_column):
        for _, row in frame.iterrows():
            records.append(
                {
                    "REF_AREA": str(row.get(iso_column) or "") if iso_column else "",
                    "REF_AREA_LABEL": str(row.get(label_column) or "") if label_column else "",
                    "TIME_PERIOD": row.get(time_column),
                    "OBS_VALUE": row.get(value_column),
                }
            )
        return records
    country_column = next(
        (column for column in columns if column in {"country", "ref_area_label", "ref_area", "entity"}), None
    )
    year_columns = [column for column in columns if column.isdigit() and len(column) == 4]
    if country_column and year_columns:
        for _, row in frame.iterrows():
            for year in year_columns:
                records.append(
                    {
                        "REF_AREA": str(row.get(country_column) or ""),
                        "TIME_PERIOD": year,
                        "OBS_VALUE": row.get(year),
                    }
                )
    return records


def _fetch_raw(request: AdapterRequest, *, runtime: SourceRuntime, http_get=requests.get) -> list[dict[str, Any]]:
    meta = request.meta
    api_records: list[dict[str, Any]] = []
    if meta.get("database_id") and meta.get("source_code"):
        skip = 0
        while True:
            try:
                params = {
                    "DATABASE_ID": meta["database_id"],
                    "INDICATOR": meta["source_code"],
                    "skip": skip,
                }
                if meta.get("unit_measure"):
                    params["UNIT_MEASURE"] = meta["unit_measure"]
                response = http_get(
                    API_URL,
                    params=params,
                    timeout=30,
                )
                if response.status_code != 200:
                    runtime.log(
                        f"[WARN] Data360 API HTTP {response.status_code} for "
                        f"{meta['database_id']}/{meta['source_code']}"
                    )
                    break
                values = response.json().get("value", [])
            except Exception as exc:
                runtime.log(f"[WARN] Data360 API failed: {exc}")
                break
            if not values:
                break
            api_records.extend(values)
            if len(values) < 1000:
                break
            skip += 1000

    source_code = str(meta.get("source_code") or "")
    fallback_name = str(meta.get("fallback_file") or f"{source_code}.csv")
    local_path = runtime.source_csv_dir.parent / "source_raw" / fallback_name
    source = local_path if local_path.is_file() else None
    if source is None and not api_records and meta.get("source"):
        source = f"{str(meta['source']).rstrip('/')}/{source_code}.csv"
    if source is None:
        return api_records
    csv_records = _read_csv_records(source, runtime=runtime)
    if not api_records:
        return csv_records
    api_year = _latest_raw_year(api_records)
    csv_year = _latest_raw_year(csv_records)
    if csv_year is not None and (api_year is None or csv_year > api_year):
        runtime.log(
            f"[FALLBACK] Data360 maintained CSV is newer than API ({csv_year} > {api_year}); "
            f"using {fallback_name}"
        )
        return csv_records
    return api_records


def run(request: AdapterRequest, *, runtime: SourceRuntime, http_get=requests.get) -> AdapterResult:
    raw_records = _fetch_raw(request, runtime=runtime, http_get=http_get)
    records: list[dict[str, Any]] = []
    for row in raw_records:
        iso = row.get("REF_AREA")
        name = iso or row.get("REF_AREA_LABEL") or row.get("country")
        canon = runtime.canonicalize_country(
            name,
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        value = runtime.safe_float(row.get("OBS_VALUE", row.get("value")))
        year_value = row.get("TIME_PERIOD", row.get("year"))
        try:
            year = int(float(year_value))
        except (TypeError, ValueError):
            continue
        if canon and value is not None:
            records.append(
                {
                    "country": canon,
                    "iso2": runtime.resolve_iso2(canon, request.countries),
                    "year": year,
                    "value": value,
                }
            )
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, "Data360 empty", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date="Unknown")
    latest_year = max(row["year"] for row in records)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(source_date="Unknown", data_year=latest_year)
    request.stats["data360_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["fetched"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    runtime.log(f"[OK] Data360 KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(source_date="Unknown", data_year=latest_year, record_count=len(records))
