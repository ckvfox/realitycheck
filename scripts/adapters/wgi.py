"""World Bank WGI estimates from the complete official release workbook."""
from __future__ import annotations

import re
from collections import Counter
from email.utils import parsedate_to_datetime
from html import unescape
from io import BytesIO
from urllib.parse import unquote
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from fetch_core import AdapterResult

CATALOG_URL = "https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators"
RELEASE_LINK = re.compile(
    r"https://datacatalogfiles\.worldbank\.org/ddh-published/0038026/DR[0-9]+/"
    r"WGI (20[0-9]{2}) Governance Estimates and Scores \(1996-(20[0-9]{2})\)\.xlsx"
)


def latest_release(html: str) -> tuple[str, int]:
    releases = list(RELEASE_LINK.finditer(unquote(unescape(html))))
    if not releases:
        raise ValueError("No official WGI release workbook listed")
    newest = max(releases, key=lambda link: (link[2], link[1]))
    return newest[0], int(newest[2])


def governance_estimates(content: bytes, countries, latest_year: int, safe_float):
    names = {country["iso_a3"]: (name, country.get("iso_a2", ""))
             for name, country in countries.items() if country.get("iso_a3")}
    book = load_workbook(BytesIO(content), read_only=True, data_only=True)
    try:
        rows = iter(book["ge"].values)
        header = next(rows, ())
        iso, year, estimate = (header.index(label) for label in (
            "Economy (code)", "Year", "Governance estimate (approx. -2.5 to +2.5)"
        ))
        records = []
        keys = set()
        for row in rows:
            country = names.get(row[iso])
            value = safe_float(row[estimate])
            if country is None or value is None:
                continue
            name, iso2 = country
            observation_year = row[year]
            key = (name, observation_year)
            if type(observation_year) is not int or key in keys:
                raise ValueError("Invalid or duplicate WGI country-year")
            keys.add(key)
            records.append({"country": name, "iso2": iso2, "year": observation_year, "value": value})
    finally:
        book.close()

    coverage = Counter(row["year"] for row in records)
    expected_years = {1996, 1998, 2000, *range(2002, latest_year + 1)}
    if set(coverage) != expected_years or min(coverage.values(), default=0) < 100 or coverage[latest_year] < 190:
        raise ValueError("Incomplete WGI history or country coverage")
    if "Taiwan" in countries and any(("Taiwan", year) not in keys for year in expected_years):
        raise ValueError("Incomplete WGI Taiwan series")
    return records


def run(request, *, runtime, http_get):
    try:
        catalog = http_get(CATALOG_URL, timeout=(10, 30))
        catalog.raise_for_status()
        url, year = latest_release(catalog.text)
        response = http_get(url, timeout=(10, 60))
        response.raise_for_status()
        records = governance_estimates(response.content, request.countries, year, runtime.safe_float)
        modified = response.headers.get("Last-Modified")
        source_date = parsedate_to_datetime(modified).isoformat() if modified else None
    except (ValueError, KeyError, IndexError, TypeError, OSError, BadZipFile, InvalidFileException) as exc:
        runtime.keep_or_dummy(request.kpi_id, f"WGI fetch failed: {exc}", request.stats, output_dir=request.output_dir)
        return AdapterResult()
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()
    request.meta["source_url"] = response.url
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(source_date=source_date, data_year=year, record_count=len(records))
