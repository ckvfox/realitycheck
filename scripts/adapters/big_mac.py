"""Append validated July Big Mac prices from The Economist (CC BY 4.0)."""
from __future__ import annotations

import csv
import io
import json
import math
from datetime import date

from fetch_core import AdapterResult

URL = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"

RAW_URL = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/source-data/big-mac-source-data-v2.csv"
FIRST_BACKFILL_YEAR = 2023


def supplement_euro_prices(content, editions, markets):
    reader = csv.DictReader(io.StringIO(content))
    required = {"date", "iso_a3", "currency_code", "local_price", "dollar_ex"}
    if not required.issubset(reader.fieldnames or ()):
        raise ValueError("Unexpected Economist raw CSV schema")
    seen = set()
    for row in reader:
        release = date.fromisoformat(row["date"])
        code = row["iso_a3"]
        if ((release.month, release.day) != (7, 1) or release.year not in editions
                or row["currency_code"] != "EUR" or code == "EUZ"):
            continue
        if code not in markets:
            raise ValueError(f"Unrecognized Economist raw market: {code}")
        country, iso2 = markets[code]
        key = release.year, iso2
        if key in seen:
            raise ValueError(f"Duplicate Economist raw market {code}/{release.year}")
        seen.add(key)
        if iso2 in editions[release.year] or row["local_price"] in {"", "#N/A"}:
            continue
        price, exchange = float(row["local_price"]), float(row["dollar_ex"])
        if not all(math.isfinite(value) and value > 0 for value in (price, exchange)):
            raise ValueError(f"Invalid Economist raw price or exchange rate for {code}/{release.year}")
        editions[release.year][iso2] = {
            "country": country, "iso2": iso2, "year": release.year, "value": price / exchange
        }


def append_july_editions(content, history, countries, today, raw_content=None):
    reader = csv.DictReader(io.StringIO(content))
    if not {"date", "iso_a3", "dollar_price"}.issubset(reader.fieldnames or ()):
        raise ValueError("Unexpected Economist CSV schema")

    markets = {info["iso_a3"]: (name, info["iso_a2"]) for name, info in countries.items()}
    last_year = max(row["year"] for row in history)
    baseline = {row["iso2"] for row in history if row["year"] == last_year}
    editions = {}
    seen = set()
    for row in reader:
        release = date.fromisoformat(row["date"])
        if (release.month, release.day) != (7, 1) or release.year < min(last_year, FIRST_BACKFILL_YEAR):
            continue
        if release > today:
            raise ValueError("Future Economist release")
        code = row["iso_a3"]
        key = release.year, code
        if key in seen:
            raise ValueError(f"Duplicate Economist market {code}/{release.year}")
        seen.add(key)
        if code in {"EUZ", "HKG"}:
            continue
        if code not in markets:
            raise ValueError(f"Unrecognized Economist market: {code}")
        country, iso2 = markets[code]
        price = float(row["dollar_price"])
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"Invalid USD price for {code}/{release.year}")
        edition = editions.setdefault(release.year, {})
        if iso2 in edition:
            raise ValueError(f"Duplicate normalized Economist market {iso2}/{release.year}")
        edition[iso2] = {
            "country": country, "iso2": iso2, "year": release.year, "value": price
        }

    export_keys = {(iso2, year) for year, edition in editions.items() for iso2 in edition}
    if raw_content is not None:
        supplement_euro_prices(raw_content, editions, markets)

    if not baseline or not baseline.issubset(editions.get(last_year, {})):
        raise ValueError("Economist CSV is missing markets from the published July edition")
    appended = []
    for expected_year, year in enumerate(sorted(y for y in editions if y > last_year), last_year + 1):
        edition = editions[year]
        if year != expected_year or not baseline.issubset(edition):
            raise ValueError(f"Incomplete Economist July edition {year}")
        appended.extend(sorted(edition.values(), key=lambda row: row["country"]))
        baseline = set(edition)
    existing = {(row["iso2"], row["year"]) for row in history}
    if raw_content is not None:
        # The export defines historical edition availability. Backfill only
        # absent EUR markets; existing country-years remain authoritative.
        for year in sorted(y for y in editions if FIRST_BACKFILL_YEAR <= y <= last_year):
            for iso2, row in sorted(editions[year].items()):
                if (iso2, year) not in existing and (iso2, year) not in export_keys:
                    appended.append(row)
    return history + appended


def run(request, *, runtime, http_get):
    try:
        response = http_get(URL, timeout=(10, 45))
        response.raise_for_status()
        raw_response = http_get(RAW_URL, timeout=(10, 45))
        raw_response.raise_for_status()
    except OSError as exc:
        runtime.keep_or_dummy(request.kpi_id, f"Big Mac request failed: {exc}", request.stats, output_dir=request.output_dir)
        return AdapterResult(outcome="source_unavailable")
    try:
        target = request.output_dir / f"{request.kpi_id}.json"
        baseline = target if target.exists() else runtime.data_dir / target.name
        with baseline.open(encoding="utf-8") as handle:
            history = json.load(handle)
        records = append_july_editions(
            response.content.decode("utf-8-sig"), history, request.countries, date.today(),
            raw_content=raw_response.content.decode("utf-8-sig"),
        )
    except (ValueError, KeyError, TypeError, OSError) as exc:
        runtime.keep_or_dummy(request.kpi_id, f"Big Mac refresh failed: {exc}", request.stats, output_dir=request.output_dir)
        return AdapterResult(outcome="rejected")

    if len(records) == len(history) and target.exists() and target.with_suffix(".csv").exists():
        runtime.mark_skip(request.stats, "No newer complete Economist July edition")
        return AdapterResult(outcome="unchanged")
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()

    latest = max(row["year"] for row in records)
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(source_date=f"{latest}-07-01T00:00:00Z", data_year=latest, record_count=len(records))
