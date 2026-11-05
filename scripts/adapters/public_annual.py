"""Annual public series from Ember CSV and Eurostat JSON-stat."""
from __future__ import annotations

import csv
import io
import itertools
from collections import Counter
from datetime import date
from email.utils import parsedate_to_datetime

from fetch_core import AdapterResult

EMBER_URL = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"
EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_lvho07a"
EU_COUNTRIES = frozenset("AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split())
EUROSTAT_FILTERS = {"freq": "A", "unit": "PC", "rskpovth": "TOTAL", "age": "TOTAL", "sex": "T"}


def ember_records(text, countries, safe_float):
    names = {info["iso_a3"]: name for name, info in countries.items() if info.get("iso_a3")}
    reader = csv.DictReader(io.StringIO(text.removeprefix("\ufeff")))
    field = "Emissions intensity (gCO2e/kWh)"
    required = {"Area", "Area type", "ISO 3 code", "Year", "Electricity source", field}
    if not required.issubset(reader.fieldnames or ()):
        raise ValueError("Unexpected Ember CSV columns")
    for row in reader:
        if row["Electricity source"] != "Total generation":
            continue
        country = "World" if row["Area"] == "World" else names.get(row["ISO 3 code"])
        value = safe_float(row[field])
        if country and value is not None:
            if value < 0:
                raise ValueError("Negative Ember electricity emissions intensity")
            yield {"country": country, "iso2": countries.get(country, {}).get("iso_a2", ""), "year": int(row["Year"]), "value": value}


def eurostat_records(payload, countries, safe_float):
    dimensions = payload["id"]
    if payload["class"] != "dataset" or set(dimensions) != {*EUROSTAT_FILTERS, "geo", "time"}:
        raise ValueError("Unexpected Eurostat JSON-stat dimensions")
    indexes = [payload["dimension"][dimension]["category"]["index"] for dimension in dimensions]
    if any(set(indexes[dimensions.index(key)]) != {value} for key, value in EUROSTAT_FILTERS.items()):
        raise ValueError("Unexpected Eurostat population filters")
    keys = [sorted(index, key=index.get) for index in indexes]
    if [len(key) for key in keys] != payload["size"]:
        raise ValueError("Inconsistent Eurostat JSON-stat dimensions")
    values = payload["value"]
    names = {info["iso_a2"]: name for name, info in countries.items() if info.get("iso_a2")}
    names["EL"] = names.get("GR")
    names["EU27_2020"] = "European Union"
    for index, coordinates in enumerate(itertools.product(*keys)):
        geo = coordinates[dimensions.index("geo")]
        country = names.get(geo)
        if not country or geo not in EU_COUNTRIES | {"EU27_2020"}:
            continue
        raw = values.get(str(index)) if isinstance(values, dict) else values[index]
        value = safe_float(raw)
        if value is not None:
            if not 0 <= value <= 100:
                raise ValueError("Eurostat rate outside 0–100 percent")
            yield {"country": country, "iso2": "GR" if geo == "EL" else geo if geo in EU_COUNTRIES else "",
                   "year": int(coordinates[dimensions.index("time")]), "value": value}


def run(request, *, runtime, http_get, provider):
    try:
        if provider == "ember":
            response = http_get(EMBER_URL, timeout=(10, 60))
            response.raise_for_status()
            records = list(ember_records(response.content.decode("utf-8-sig"), request.countries, runtime.safe_float))
            release = response.headers.get("Last-Modified")
            source_date = parsedate_to_datetime(release).isoformat() if release else None
            anchor, minimum = "World", 150
        else:
            response = http_get(EUROSTAT_URL, params=EUROSTAT_FILTERS, timeout=(10, 45))
            response.raise_for_status()
            payload = response.json()
            records = list(eurostat_records(payload, request.countries, runtime.safe_float))
            source_date = payload.get("updated")
            anchor, minimum = "European Union", 24

        keys = {(row["country"], row["year"]) for row in records}
        latest = max((year for country, year in keys if country == anchor), default=0)
        coverage = Counter(year for country, year in keys if country != anchor)
        if (len(keys) != len(records) or latest < 2000 or max(year for _, year in keys) > date.today().year
                or max(coverage.get(year, 0) for year in range(latest - 2, latest + 1)) < minimum
                or (provider == "eurostat" and ("Germany", latest) not in keys)):
            raise ValueError("Incomplete or inconsistent source coverage")
    except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
        runtime.keep_or_dummy(request.kpi_id, f"{provider} fetch failed: {exc}", request.stats, output_dir=request.output_dir)
        return AdapterResult()

    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(source_date=source_date, data_year=max(row["year"] for row in records), record_count=len(records))
