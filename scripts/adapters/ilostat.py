"""ILOSTAT output per hour, limited to calendar years before the model vintage."""
from __future__ import annotations

import csv
import gzip
import re
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from io import StringIO

from fetch_core import AdapterResult, SourceAdapter

CATALOG = "https://rplumber.ilo.org/metadata/toc/indicator"
DATA = "https://rplumber.ilo.org/data/indicator"


def csv_rows(content):
    if content.startswith(b"\x1f\x8b"):
        content = gzip.decompress(content)
    return csv.DictReader(StringIO(content.decode("utf-8-sig")))


def release_info(rows, code):
    match, = [row for row in rows if row["id"] == code]
    vintage = re.fullmatch(
        r"Output per hour worked, GDP constant 2021 international \$ at PPP -- "
        r"ILO modelled estimates, [A-Za-z.]+ (20\d{2})",
        match["indicator.label"],
    )
    if not vintage or match["freq"] != "A" or match["database"] != "ILOEST":
        raise ValueError("Unexpected ILOSTAT definition or model vintage")
    date = datetime.strptime(match["last.update"], "%d/%m/%Y %H:%M:%S").replace(tzinfo=timezone.utc)
    return date.isoformat(), int(vintage[1]), int(match["n.records"])


def productivity_records(rows, countries, code, vintage, safe_float):
    iso3 = {info["iso_a3"]: (name, info.get("iso_a2", ""))
            for name, info in countries.items() if info.get("iso_a3")}
    observations = {}
    for row in rows:
        if row["indicator"] != code.removesuffix("_A"):
            raise ValueError("Unexpected ILOSTAT indicator")
        year = int(row["time"])
        country = iso3.get(row["ref_area"])
        if country is None or year >= vintage:
            continue
        name, iso2 = country
        value = safe_float(row["obs_value"])
        if value is None:
            continue
        if value < 0 or (name, year) in observations:
            raise ValueError(f"Invalid or duplicate ILOSTAT observation for {name}, {year}")
        observations[name, year] = {"country": name, "iso2": iso2, "year": year, "value": value}
    coverage = Counter(year for _, year in observations)
    if not coverage or min(coverage) > 2005 or coverage[vintage - 1] < 150:
        raise ValueError("Incomplete ILOSTAT productivity history or coverage")
    return [observations[key] for key in sorted(observations, key=lambda key: (key[1], key[0]))]


def make_adapter(runtime, http_get):
    @lru_cache(maxsize=1)
    def release(code):
        response = http_get(CATALOG, params={"lang": "en", "format": ".csv"}, timeout=(10, 30))
        response.raise_for_status()
        return release_info(csv_rows(response.content), code)

    def source_date(meta):
        return release(meta["source_code"])[0]

    def run(request):
        code = request.meta["source_code"]
        updated, vintage, expected_count = release(code)
        response = http_get(DATA, params={"id": code, "format": ".csv.gz"}, timeout=(10, 30))
        response.raise_for_status()
        rows = list(csv_rows(response.content))
        if len(rows) != expected_count:
            raise ValueError("Incomplete ILOSTAT bulk download")
        records = productivity_records(rows, request.countries, code, vintage, runtime.safe_float)
        if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
            return AdapterResult()
        request.stats["others_success"] += 1
        request.stats["saved_records"] += len(records)
        request.stats["updated_kpis"].add(request.kpi_id)
        return AdapterResult(source_date=updated, data_year=vintage - 1, record_count=len(records))

    return SourceAdapter("ilostat", handler=run, source_date_resolver=source_date)
