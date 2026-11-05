"""Global UNSD indicator series with complete pagination and country-only output."""
from __future__ import annotations

from collections import Counter
from datetime import date

from adapters.runtime import normalize_country_key
from fetch_core import AdapterResult

SERIES_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Series/Data"


def fetch_rows(code, http_get):
    rows = []
    page, pages, total = 1, 1, None
    while page <= pages:
        response = http_get(SERIES_URL, params={"seriesCode": code, "page": page, "pageSize": 5000},
                            timeout=(10, 30))
        response.raise_for_status()
        payload = response.json()
        if page == 1:
            pages, total = payload["totalPages"], payload["totalElements"]
        batch = payload["data"]
        if (not 1 <= pages <= 100 or payload["pageNumber"] != page
                or payload["totalPages"] != pages or payload["totalElements"] != total
                or not isinstance(batch, list) or not batch):
            raise ValueError("Inconsistent UNSD pagination")
        rows.extend(batch)
        page += 1
    if len(rows) != total:
        raise ValueError("Incomplete UNSD response")
    return rows


def country_records(rows, request, safe_float):
    records, seen = [], set()
    for row in rows:
        if row["series"] != request.meta["source_code"]:
            raise ValueError("Unexpected UNSD indicator")
        if row["dimensions"]["Reporting Type"] != "G":
            continue
        key = normalize_country_key(row["geoAreaName"])
        country = request.country_index.get(key, request.alias_index.get(key))
        # UNSD uses "Micronesia" for both the region (057) and a country in our registry.
        if country == "Micronesia" and row["geoAreaCode"] != "583":
            continue
        value = safe_float(row["value"])
        if country not in request.countries or value is None:
            continue
        year = int(row["timePeriodStart"])
        if (row["attributes"]["Units"] != "PERCENT" or not 0 <= value <= 100
                or not 1990 <= year <= date.today().year or year != row["timePeriodStart"]
                or (country, year) in seen):
            raise ValueError(f"Invalid or duplicate UNSD observation for {country}, {year}")
        seen.add((country, year))
        records.append({"country": country, "iso2": request.countries[country].get("iso_a2", ""),
                        "year": year, "value": value})
    coverage = Counter(row["year"] for row in records)
    latest = max(coverage, default=0)
    if (min(coverage, default=0) != 1990 or set(coverage) != set(range(1990, latest + 1))
            or max((coverage[y] for y in range(latest - 2, latest + 1)), default=0) < 150):
        raise ValueError("Incomplete UNSD history or recent coverage")
    return records


def run(request, *, runtime, http_get):
    try:
        records = country_records(fetch_rows(request.meta["source_code"], http_get), request, runtime.safe_float)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        runtime.keep_or_dummy(request.kpi_id, f"UNSD fetch failed: {exc}", request.stats,
                              output_dir=request.output_dir)
        return AdapterResult()
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(data_year=max(row["year"] for row in records), record_count=len(records))
