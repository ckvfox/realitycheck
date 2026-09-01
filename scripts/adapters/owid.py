"""Our World in Data adapter."""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult


def _variable_rows(variable_id: int, *, runtime: SourceRuntime, http_get) -> list[dict[str, Any]]:
    base = f"https://api.ourworldindata.org/v1/indicators/{variable_id}"
    try:
        metadata_response = http_get(f"{base}.metadata.json", timeout=30)
        data_response = http_get(f"{base}.data.json", timeout=30)
        if metadata_response.status_code != 200 or data_response.status_code != 200:
            return []
        metadata = metadata_response.json()
        payload = data_response.json()
        entities = {
            item.get("id"): item
            for item in (((metadata.get("dimensions") or {}).get("entities") or {}).get("values") or [])
            if isinstance(item, dict)
        }
        values = payload.get("values") or []
        years = payload.get("years") or []
        entity_ids = payload.get("entities") or []
        if not (len(values) == len(years) == len(entity_ids)):
            raise ValueError("OWID variable arrays have different lengths")
        rows = []
        for entity_id, year, value in zip(entity_ids, years, values):
            entity = entities.get(entity_id) or {}
            rows.append(
                {
                    "Entity": entity.get("name") or "",
                    "Code": entity.get("code") or "",
                    "Year": year,
                    "Value": value,
                }
            )
        runtime.log(f"[FETCH] OWID variable API {variable_id}: {len(rows)} observations")
        return rows
    except Exception as exc:
        runtime.log(f"[WARN] OWID variable API {variable_id} failed: {exc}")
        return []


def resolve_source_date(meta: dict[str, Any], *, runtime: SourceRuntime, http_get=requests.get) -> str | None:
    code = str(meta.get("source_code") or meta.get("code") or "")
    if not code:
        return None
    base_id = code.split("?")[0].removesuffix(".csv")
    url = f"https://ourworldindata.org/grapher/{base_id}.metadata.json"
    try:
        response = http_get(url, timeout=20)
        if response.status_code != 200:
            return None
        payload = response.json()
        columns = payload.get("columns") if isinstance(payload, dict) else None
        if isinstance(columns, dict):
            for column in columns.values():
                if isinstance(column, dict) and column.get("lastUpdated"):
                    return str(column["lastUpdated"])
        for key in ("lastUpdated", "last_updated", "updatedAt", "dataEditedAt", "publishedAt"):
            if isinstance(payload, dict) and payload.get(key):
                return str(payload[key])
    except Exception as exc:
        runtime.log(f"[WARN] OWID metadata failed for {base_id}: {exc}")
    return None


def run(
    request: AdapterRequest,
    *,
    runtime: SourceRuntime,
    http_get=requests.get,
) -> AdapterResult:
    source_code = str(request.meta.get("source_code") or "")
    if not source_code:
        runtime.keep_or_dummy(request.kpi_id, "missing source_code", request.stats, output_dir=request.output_dir)
        return AdapterResult()
    url = f"https://ourworldindata.org/grapher/{source_code}"
    source_date = request.meta.get("_discovered_source_date")
    variable_id = request.meta.get("owid_variable_id")
    variable_rows = _variable_rows(int(variable_id), runtime=runtime, http_get=http_get) if variable_id else []
    if variable_rows:
        columns = ["Entity", "Code", "Year", "Value"]
        rows = variable_rows
    else:
        rows = None
    response = None
    if rows is None:
        try:
            response = http_get(url, timeout=30)
            if response.status_code == 403:
                try:
                    restriction = str((response.json() or {}).get("error") or "")
                except Exception:
                    restriction = ""
                if "non-redistributable" in restriction.lower() or "not allowed to re-share" in restriction.lower():
                    runtime.mark_skip(request.stats, "OWID redistribution restricted")
                    runtime.log(
                        f"[SKIP] {request.kpi_id}: OWID no longer permits CSV redistribution; "
                        "preserving the last known-good dataset"
                    )
                    return AdapterResult(source_date=source_date)
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")
        except Exception as exc:
            runtime.log(f"[ERROR] OWID fetch failed for {source_code}: {exc}")
            runtime.keep_or_dummy(
                request.kpi_id, f"OWID fetch failed {source_code}", request.stats, output_dir=request.output_dir
            )
            return AdapterResult(source_date=source_date)

    if rows is None:
        assert response is not None
        reader = csv.DictReader(io.StringIO(response.text))
        columns = reader.fieldnames or []
        rows = list(reader)
    column_lookup = {column.strip().lstrip("\ufeff").lower(): column for column in columns}
    configured_time = str(request.meta.get("owid_time_column") or "year").strip().lower()
    if "entity" not in column_lookup or configured_time not in column_lookup:
        runtime.keep_or_dummy(
            request.kpi_id, f"OWID format unknown {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date=source_date)
    entity_column = column_lookup["entity"]
    code_column = column_lookup.get("code")
    time_column = column_lookup[configured_time]
    identity_columns = {entity_column, time_column}
    if code_column:
        identity_columns.add(code_column)
    value_columns = [column for column in columns if column not in identity_columns]
    if not value_columns:
        runtime.keep_or_dummy(
            request.kpi_id, f"OWID no data column {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date=source_date)

    configured_value = str(request.meta.get("owid_value_column") or "").strip().lower()
    configured_sum = [str(value).strip().lower() for value in request.meta.get("owid_sum_columns", [])]
    if configured_value:
        value_column = column_lookup.get(configured_value)
        if not value_column:
            runtime.keep_or_dummy(
                request.kpi_id, f"OWID value column missing: {configured_value}", request.stats,
                output_dir=request.output_dir,
            )
            return AdapterResult(source_date=source_date)
    else:
        value_column = value_columns[0]
    sum_columns = [column_lookup.get(name) for name in configured_sum]
    if configured_sum and any(column is None for column in sum_columns):
        runtime.keep_or_dummy(
            request.kpi_id, "OWID configured sum column missing", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date=source_date)
    records: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get(entity_column) or "").strip()
        if request.kpi_id == "number_of_recorded_natural_disasters" and name.lower() in {
            "all disasters", "all disasters (total)", "total disasters"
        }:
            name = "World"
        canon = runtime.canonicalize_country(
            name,
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        if not canon and name.lower() == "world":
            canon = "World"
        if sum_columns:
            parts = [runtime.safe_float(row.get(column)) for column in sum_columns]
            usable = [value for value in parts if value is not None]
            value = sum(usable) if usable else None
        else:
            value = runtime.safe_float(row.get(value_column))
        try:
            raw_time = str(row.get(time_column) or "").strip()
            year = int(raw_time[:4]) if configured_time == "day" else int(float(raw_time))
        except (TypeError, ValueError):
            continue
        if canon and value is not None:
            records.append(
                {
                    "country": canon,
                    "iso2": "OWID_WRL" if canon == "World" else str(row.get(code_column) or "") if code_column else "",
                    "year": year,
                    "value": value,
                }
            )

    if request.meta.get("owid_aggregation") == "annual_mean":
        grouped: dict[tuple[str, str, int], list[float]] = defaultdict(list)
        for record in records:
            grouped[(record["country"], record["iso2"], record["year"])].append(record["value"])
        if grouped:
            latest_year = max(year for _, _, year in grouped)
            recent_previous_counts = [
                len(values) for (_, _, year), values in grouped.items()
                if latest_year - 5 <= year < latest_year
            ]
            expected_count = max(recent_previous_counts, default=0)
            if expected_count:
                grouped = {
                    key: values for key, values in grouped.items()
                    if key[2] != latest_year or len(values) >= expected_count
                }
        records = [
            {"country": country, "iso2": iso2, "year": year, "value": mean(values)}
            for (country, iso2, year), values in sorted(grouped.items())
        ]

    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, f"OWID empty {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date=source_date)
    records = runtime.maybe_invert_records(request.kpi_id, request.meta, records)
    latest_year = max(row["year"] for row in records)
    latest_year = min(latest_year, datetime.now().year)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(source_date=str(source_date or "Unknown"))
    if not source_date or source_date == "Unknown":
        source_date = f"{latest_year}-01-01"
    request.stats["owid_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    runtime.log(f"[OK] OWID KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(source_date=str(source_date), data_year=latest_year, record_count=len(records))
