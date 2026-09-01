"""UNHCR population CSV/ZIP adapter."""
from __future__ import annotations

import csv
import io
import unicodedata
import zipfile
from typing import Any

import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult


def _fetch_json_items(url: str, http_get) -> list[dict[str, Any]]:
    response = http_get(url, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    payload = response.json()
    return payload.get("items", []) if isinstance(payload, dict) else []


def _run_global_forced_displacement(request: AdapterRequest, *, runtime: SourceRuntime, http_get) -> AdapterResult:
    year_from = int(request.meta.get("year_from") or 1951)
    year_to = int(request.meta.get("year_to") or 2100)
    query = f"?limit=200&yearFrom={year_from}&yearTo={year_to}"
    try:
        population = _fetch_json_items(f"https://api.unhcr.org/population/v1/population/{query}", http_get)
        unrwa = _fetch_json_items(f"https://api.unhcr.org/population/v1/unrwa/{query}", http_get)
        idmc = _fetch_json_items(f"https://api.unhcr.org/population/v1/idmc/{query}", http_get)
    except Exception as exc:
        runtime.log(f"[ERROR] UNHCR global displacement fetch failed: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, "UNHCR global displacement fetch failed", request.stats,
            output_dir=request.output_dir,
        )
        return AdapterResult()

    values: dict[int, float] = {}
    for row in population:
        try:
            year = int(row.get("year"))
        except (TypeError, ValueError):
            continue
        fields = ("refugees", "asylum_seekers", "oip")
        values[year] = sum(runtime.safe_float(row.get(field)) or 0 for field in fields)
    for rows in (unrwa, idmc):
        for row in rows:
            try:
                year = int(row.get("year"))
            except (TypeError, ValueError):
                continue
            values[year] = values.get(year, 0) + (runtime.safe_float(row.get("total")) or 0)

    records = [
        {"country": "World", "iso2": "OWID_WRL", "year": year, "value": value}
        for year, value in sorted(values.items()) if value > 0
    ]
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, "UNHCR global displacement empty", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()
    latest_year = max(row["year"] for row in records)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(data_year=latest_year)
    request.stats["unhcr_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    return AdapterResult(data_year=latest_year, record_count=len(records))


def _normalized(value: Any) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", str(value).lower())
        if not unicodedata.combining(char)
    )


def _find_column(columns: list[str], *patterns: str) -> str | None:
    for column in columns:
        normalized = _normalized(column)
        if any(_normalized(pattern) in normalized for pattern in patterns):
            return column
    return None


def run(request: AdapterRequest, *, runtime: SourceRuntime, http_get=requests.get) -> AdapterResult:
    if request.meta.get("unhcr_mode") == "global_forced_displacement":
        return _run_global_forced_displacement(request, runtime=runtime, http_get=http_get)
    source_code = str(request.meta.get("source_code") or "population?download=true")
    url = f"https://api.unhcr.org/population/v1/{source_code}"
    try:
        response = http_get(url, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
        if "zip" in response.headers.get("Content-Type", "").lower() or response.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                name = next(item for item in archive.namelist() if item.lower().endswith(".csv"))
                text = archive.read(name).decode("utf-8-sig", errors="ignore")
        else:
            text = response.text
    except Exception as exc:
        runtime.log(f"[ERROR] UNHCR fetch failed for {source_code}: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, f"UNHCR fetch failed {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()

    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    country_column = _find_column(columns, "country of asylum", "territory of asylum", "asylum")
    year_column = _find_column(columns, "year")
    value_column = _find_column(columns, str(request.meta.get("unhcr_field") or "refugees"))
    if not all((country_column, year_column, value_column)):
        runtime.keep_or_dummy(
            request.kpi_id, f"UNHCR unknown format {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()

    records: list[dict[str, Any]] = []
    for row in reader:
        canon = runtime.canonicalize_country(
            str(row.get(country_column) or "").strip(),
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        value = runtime.safe_float(row.get(value_column))
        try:
            year = int(float(str(row.get(year_column) or "")))
        except ValueError:
            continue
        if canon and value is not None:
            records.append({"country": canon, "iso2": "", "year": year, "value": value})

    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, f"UNHCR empty {source_code}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()
    records = runtime.maybe_invert_records(request.kpi_id, request.meta, records)
    latest_year = max(row["year"] for row in records)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(data_year=latest_year)
    request.stats["unhcr_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    return AdapterResult(data_year=latest_year, record_count=len(records))
