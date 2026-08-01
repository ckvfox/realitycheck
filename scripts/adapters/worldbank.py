"""World Bank indicator adapter with JSON and ZIP fallback."""
from __future__ import annotations

import csv
import io
import time
import zipfile
from datetime import datetime
from typing import Any

import requests

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult

HEADERS = {
    "User-Agent": "RealityCheck/1.0 (contact: info@realitycheck.global)",
    "Accept": "application/json, text/plain, */*",
}
ZIP_HEADERS = {**HEADERS, "Accept": "application/zip, application/octet-stream, */*"}


def _indicator_code(meta: dict[str, Any]) -> str:
    """Return the indicator id without legacy URL query fragments."""
    return str(meta.get("source_code") or meta.get("code") or "").split("?", 1)[0].strip()


def _get(url: str, *, runtime: SourceRuntime, http_get=requests.get, timeout: int = 60, attempts: int = 4, headers=None):
    for attempt in range(1, attempts + 1):
        try:
            response = http_get(url, timeout=timeout, headers=headers or HEADERS)
            if response.status_code != 429 and response.status_code < 500:
                return response
            runtime.log(f"[WARN] World Bank HTTP {response.status_code} ({attempt}/{attempts})")
        except Exception as exc:
            runtime.log(f"[WARN] World Bank request failed ({attempt}/{attempts}): {exc}")
        if attempt < attempts:
            time.sleep(attempt * 2)
    return None


def resolve_source_date(meta: dict[str, Any], *, runtime: SourceRuntime, http_get=requests.get) -> str | None:
    code = _indicator_code(meta)
    if not code:
        return None
    url = f"https://api.worldbank.org/v2/sources/2?format=json"
    response = _get(url, runtime=runtime, http_get=http_get, timeout=30, attempts=2)
    try:
        if response is not None and response.status_code == 200:
            payload = response.json()
            sources = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            if sources and sources[0].get("lastupdated"):
                return f"{sources[0]['lastupdated']}T00:00:00Z"
    except Exception as exc:
        runtime.log(f"[WARN] World Bank source date parsing failed for {code}: {exc}")
    return None


def _zip_series(code: str, *, runtime: SourceRuntime, http_get=requests.get) -> tuple[list[dict[str, Any]], str | None]:
    url = f"https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"
    response = _get(url, runtime=runtime, http_get=http_get, headers=ZIP_HEADERS, attempts=3)
    if response is None or response.status_code != 200 or response.content[:2] != b"PK":
        return [], None
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = [
                name for name in archive.namelist()
                if name.lower().endswith(".csv") and "metadata" not in name.lower()
            ]
            if not names:
                return [], None
            info = archive.getinfo(names[0])
            source_date = datetime(*info.date_time).strftime("%Y-%m-%dT00:00:00Z")
            text = archive.read(names[0]).decode("utf-8-sig", errors="ignore")
    except Exception as exc:
        runtime.log(f"[ERROR] World Bank ZIP parsing failed for {code}: {exc}")
        return [], None

    rows = list(csv.reader(io.StringIO(text)))
    header_index = next((index for index, row in enumerate(rows[:10]) if "Country Name" in row), None)
    if header_index is None:
        return [], source_date
    header = rows[header_index]
    years = [(index, value) for index, value in enumerate(header) if value.isdigit() and len(value) == 4]
    records: list[dict[str, Any]] = []
    for row in rows[header_index + 1:]:
        if len(row) < 2 or not row[0].strip():
            continue
        for index, year in years:
            if index >= len(row):
                continue
            value = runtime.safe_float(row[index])
            if value is not None:
                records.append(
                    {
                        "country": {"value": row[0].strip()},
                        "countryiso3code": row[1].strip(),
                        "date": year,
                        "value": value,
                    }
                )
    return records, source_date


def _series(code: str, *, runtime: SourceRuntime, http_get=requests.get) -> tuple[list[dict[str, Any]], str | None]:
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000"
    response = _get(url, runtime=runtime, http_get=http_get, attempts=5)
    try:
        if response is not None and response.status_code == 200:
            payload = response.json()
            if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
                return payload[1], None
    except Exception as exc:
        runtime.log(f"[WARN] World Bank JSON parsing failed for {code}: {exc}")
    runtime.log(f"[FALLBACK] World Bank {code}: trying ZIP download")
    return _zip_series(code, runtime=runtime, http_get=http_get)


def run(request: AdapterRequest, *, runtime: SourceRuntime, http_get=requests.get) -> AdapterResult:
    code = _indicator_code(request.meta)
    if not code:
        runtime.keep_or_dummy(request.kpi_id, "missing source_code", request.stats, output_dir=request.output_dir)
        return AdapterResult()
    source_date = request.meta.get("_discovered_source_date")
    rows, fallback_date = _series(code, runtime=runtime, http_get=http_get)
    records: list[dict[str, Any]] = []
    for row in rows:
        value = runtime.safe_float(row.get("value"))
        country = row.get("country") or {}
        name = country.get("value") if isinstance(country, dict) else country
        name = name or row.get("countryiso3code") or ""
        canon = runtime.canonicalize_country(
            name,
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        try:
            year = int(row.get("date"))
        except (TypeError, ValueError):
            continue
        if canon and value is not None:
            records.append({"country": canon, "iso2": "", "year": year, "value": value})
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, f"WorldBank fetch failed ({code})", request.stats, output_dir=request.output_dir
        )
        return AdapterResult(source_date=source_date or fallback_date)
    records = runtime.maybe_invert_records(request.kpi_id, request.meta, records)
    latest_year = max(row["year"] for row in records)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(source_date=str(source_date or fallback_date or "Unknown"))
    source_date = source_date or fallback_date or f"{latest_year}-01-01T00:00:00Z"
    request.stats["wb_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    runtime.log(f"[OK] World Bank KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(source_date=str(source_date), data_year=latest_year, record_count=len(records))
