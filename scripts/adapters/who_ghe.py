"""WHO Global Health Estimates country workbook, crude all-person rates."""
from __future__ import annotations

import re
from datetime import date
from functools import lru_cache, partial
from html import unescape
from io import BytesIO

from openpyxl import load_workbook

from fetch_core import AdapterResult

SOURCE = "https://www.who.int/data/gho/data/themes/mortality-and-global-health-estimates/ghe-leading-causes-of-death"
DOWNLOAD = re.compile(
    r"https://cdn\.who\.int/media/docs/default-source/gho-documents/global-health-estimates/"
    r"crude-death-rates-2000-(20\d{2})_bycountry_(20\d{2}-\d{2}-\d{2})\.xlsx(?:\?[^\s\"'<>]+)?",
    re.IGNORECASE,
)
CAUSES = {"1530": "Road injury", "1610": "Self-harm"}
REQUIRED_YEARS = {2000, 2010, 2015, 2019, 2020, 2021, 2022, 2023}


def latest_download(html):
    links = list(DOWNLOAD.finditer(unescape(html)))
    if not links:
        raise ValueError("Official WHO crude-rate workbook link missing")
    link = max(links, key=lambda match: (match[1], match[2]))
    return link[0], int(link[1]), date.fromisoformat(link[2]).isoformat()


def parse_rates(content, countries, latest_year, safe_float):
    by_iso3 = {info["iso_a3"]: (name, info.get("iso_a2", ""))
               for name, info in countries.items() if info.get("iso_a3")}
    result = {code: [] for code in CAUSES}
    book = load_workbook(BytesIO(content), read_only=True, data_only=True)
    try:
        sheets = {int(name[4:]): name for name in book.sheetnames if re.fullmatch(r"CDR \d{4}", name)}
        if not REQUIRED_YEARS <= sheets.keys() or max(sheets) != latest_year:
            raise ValueError("Incomplete WHO release years")
        for year, name in sorted(sheets.items()):
            rows = iter(book[name].values)
            heading = [next(rows) for _ in range(8)]
            if (heading[6][:2] != ("Sex", "GHE code") or heading[7][6] != "ISO-3 Code"
                    or "Crude death rate per 100 000 population" not in str(heading[4][3])):
                raise ValueError(f"Unexpected WHO table structure for {year}")
            columns = {index: by_iso3[code] for index, code in enumerate(heading[7]) if code in by_iso3}
            if len(columns) != len(set(columns.values())) or len(columns) < 180:
                raise ValueError(f"Incomplete or duplicate WHO country codes for {year}")
            seen = set()
            for row in rows:
                code = str(row[1])
                if row[0] != "Persons" or code not in CAUSES:
                    continue
                if row[5] != CAUSES[code] or code in seen:
                    raise ValueError(f"Unexpected WHO cause row {code} in {year}")
                seen.add(code)
                rates = []
                for index, (country, iso2) in columns.items():
                    value = safe_float(row[index])
                    if value is None:
                        continue
                    if value < 0:
                        raise ValueError(f"Negative WHO rate for {country}, {year}")
                    rates.append({"country": country, "iso2": iso2, "year": year, "value": value})
                if len(rates) < 180:
                    raise ValueError(f"Incomplete WHO rates for cause {code} in {year}")
                result[code].extend(rates)
                if seen == CAUSES.keys():
                    break
            if seen != CAUSES.keys():
                raise ValueError(f"WHO cause row missing in {year}")
    finally:
        book.close()
    return result


def make_handler(runtime, http_get):
    @lru_cache(maxsize=1)
    def get_release():
        page = http_get(SOURCE, timeout=(10, 30))
        page.raise_for_status()
        url, year, source_date = latest_download(page.text)
        response = http_get(url, timeout=(10, 60))
        response.raise_for_status()
        return url, year, source_date, response.content

    return partial(run, runtime=runtime, get_release=get_release)


def run(request, *, runtime, get_release):
    url, year, source_date, content = get_release()
    records = parse_rates(content, request.countries, year, runtime.safe_float)[request.meta["source_code"]]
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult()
    request.meta["source_url"] = url
    request.stats["others_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats["updated_kpis"].add(request.kpi_id)
    return AdapterResult(source_date=source_date, data_year=year, record_count=len(records))
