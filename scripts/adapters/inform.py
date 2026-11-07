"""Append comparable global INFORM Risk Index editions from the JRC API."""
from __future__ import annotations

import csv
import json
from datetime import date

from fetch_core import AdapterResult

URL = "https://drmkc.jrc.ec.europa.eu/inform-index/api/informapi/countries/trends"


def extend_history(payload, history, current_year):
    if not isinstance(payload, list):
        raise ValueError("Expected an INFORM trend array")
    years = {year for _, year in history}
    last_year = max(years)
    baseline = {code for code, year in history if year == last_year}
    editions = {}
    for row in payload:
        if row["IndicatorName"] != "INFORM Risk Index":
            continue
        code = row["Iso3"]
        raw_year = float(row["GNAYear"])
        if not raw_year.is_integer():
            raise ValueError(f"Invalid INFORM release year for {code}")
        year = int(raw_year)
        score = float(row["IndicatorScore"])
        if not 0 <= score <= 10 or not 2016 <= year <= current_year:
            raise ValueError(f"Invalid INFORM score for {code}/{year}")
        scores = editions.setdefault(year, {})
        if code in scores:
            raise ValueError(f"Duplicate INFORM country/year: {code}/{year}")
        scores[code] = score
    if not editions or not baseline.issubset(editions.get(last_year, {})):
        raise ValueError("INFORM API does not cover the baseline edition")
    for year in sorted(y for y in editions if y > last_year):
        if year != max(years) + 1 or not baseline.issubset(editions[year]):
            raise ValueError(f"Missing INFORM year or countries in edition {year}")
        years.add(year)
    return history | {
        (code, year): value
        for year in years if year > last_year
        for code, value in editions[year].items()
    }


def run(request, *, runtime, http_get):
    try:
        names = {item["iso_a3"]: (country, item["iso_a2"]) for country, item in request.countries.items()}
        with (runtime.source_csv_dir / "inform_resilience_index.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            history = {(row["country"], int(row["year"])): float(row["value"]) for row in csv.DictReader(handle)}
        # Preserve already published editions if the provider later recalculates a trend.
        target = request.output_dir / f"{request.kpi_id}.json"
        baseline_year = max(year for _, year in history)
        if target.exists():
            codes = {name: code for code, (name, _) in names.items()}
            with target.open(encoding="utf-8") as handle:
                previous = json.load(handle)
            for row in previous:
                code = codes.get(row["country"])
                if code and row["year"] > baseline_year:
                    history[(code, row["year"])] = row["value"]
        response = http_get(URL, params={"workflowid": 0}, timeout=(10, 45))
        response.raise_for_status()
        combined = extend_history(response.json(), history, date.today().year)
        baseline_codes = {code for code, _ in history}
        if {code for code, _ in combined} - baseline_codes - names.keys():
            raise ValueError("INFORM introduced an unknown country code")
        records = [
            {"country": names[code][0], "iso2": names[code][1], "year": year, "value": value}
            for (code, year), value in sorted(combined.items()) if code in names
        ]
        latest = max(row["year"] for row in records)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        runtime.keep_or_dummy(request.kpi_id, f"INFORM refresh failed: {exc}", request.stats, output_dir=request.output_dir)
        return AdapterResult()

    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(data_year=latest, record_count=len(records))
