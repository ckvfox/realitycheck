"""Package Destatis real-wage trends and OECD PPP wage comparisons."""

from __future__ import annotations

import csv
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_PATH = ROOT / "data" / "meta" / "country_mappings.json"
DESTATIS_SNAPSHOT_PATH = (
    ROOT / "scripts" / "source_raw" / "destatis_reallohnindex_62361-0020.csv"
)
OUTPUT_PATH = ROOT / "analysis-private" / "real-wages-data.php"
OECD_SOURCE_URL = (
    "https://sdmx.oecd.org/public/rest/v1/data/"
    "OECD.ELS.SAE,DSD_EARNINGS@AV_AN_WAGE,1.0/..USD_PPP...."
    "?startPeriod=1990&dimensionAtObservation=AllDimensions"
)
OECD_SOURCE_PAGE = (
    "https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.ELS.SAE&"
    "df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_EARNINGS%40AV_AN_WAGE&"
    "df%5Bvs%5D=1.0&dq=..USD_PPP..Q..&pd=1990%2C&to%5BTIME_PERIOD%5D=false"
)
DESTATIS_SOURCE_PAGE = (
    "https://genesis.destatis.de/datenbank/online/statistic/62361/"
    "table/62361-0020"
)
MIN_COUNTRIES = 30
MIN_PEAK_SHARE = 0.85
RECENT_WINDOW_YEARS = 10


def fetch_oecd_rows() -> list[dict[str, str]]:
    request = urllib.request.Request(
        OECD_SOURCE_URL,
        headers={"Accept": "text/csv", "User-Agent": "RealityCheck data refresh"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(body)))


def load_destatis_series() -> list[dict[str, float | int]]:
    with DESTATIS_SNAPSHOT_PATH.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    series: list[dict[str, float | int]] = []
    for row in rows:
        try:
            year = int(row["year"])
            value = float(row["reallohnindex"])
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Invalid Destatis snapshot row") from error
        if not math.isfinite(value):
            raise RuntimeError("Destatis snapshot contains a non-finite value")
        series.append({"year": year, "value": value})
    series.sort(key=lambda item: int(item["year"]))
    if [int(item["year"]) for item in series] != list(range(2007, 2026)):
        raise RuntimeError("Destatis snapshot must cover every year from 2007 to 2025")
    if not series or series[-1] != {"year": 2025, "value": 100.0}:
        raise RuntimeError("Destatis snapshot does not match the documented 2025 base")
    return series


def build_payload(rows: list[dict[str, str]]) -> dict[str, object]:
    mappings = json.loads(MAPPINGS_PATH.read_text(encoding="utf-8"))
    by_year: dict[int, dict[str, float]] = defaultdict(dict)

    for row in rows:
        country = mappings.get(row.get("REF_AREA", ""))
        if not country:
            continue
        try:
            year = int(row["TIME_PERIOD"])
            value = float(row["OBS_VALUE"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            by_year[year][country] = round(value, 3)

    all_years = sorted(by_year, reverse=True)
    recent_years = all_years[:RECENT_WINDOW_YEARS]
    peak_count = max(len(by_year[year]) for year in recent_years)
    required_count = max(MIN_COUNTRIES, math.ceil(peak_count * MIN_PEAK_SHARE))
    reference_year = next(
        (
            year
            for year in recent_years
            if "Germany" in by_year[year] and len(by_year[year]) >= required_count
        ),
        None,
    )
    if reference_year is None:
        raise RuntimeError("No recent year meets the documented coverage threshold")

    comparison = dict(sorted(by_year[reference_year].items()))
    base_periods = {
        row.get("BASE_PER", "")
        for row in rows
        if row.get("REF_AREA") == "DEU" and row.get("OBS_VALUE")
    }
    price_base = sorted(base_periods)[-1] if base_periods else "unknown"

    return {
        "meta": {
            "title": "OECD average annual wages",
            "definition": (
                "Average annual wage per full-time-equivalent dependent employee "
                "in the total economy"
            ),
            "unit": f"constant {price_base} US dollars, PPP converted",
            "priceBase": int(price_base) if price_base.isdigit() else price_base,
            "sourceName": "OECD Data Explorer – Average annual wages",
            "sourceUrl": OECD_SOURCE_PAGE,
            "dataset": "OECD.ELS.SAE:DSD_EARNINGS@AV_AN_WAGE(1.0)",
            "retrievedAt": datetime.now(timezone.utc).date().isoformat(),
            "referenceYear": reference_year,
            "countryCount": len(comparison),
            "peakCountryCount": peak_count,
            "minimumCountryCount": required_count,
            "minimumPeakShare": MIN_PEAK_SHARE,
        },
        "trendMeta": {
            "title": "Reallohnindex Deutschland",
            "definition": (
                "Quotient aus Nominallohnindex und Verbraucherpreisindex; "
                "Bruttomonatsverdienste einschließlich Sonderzahlungen"
            ),
            "unit": "Reallohnindex (2025 = 100)",
            "sourceName": "Destatis GENESIS – Tabelle 62361-0020",
            "sourceUrl": DESTATIS_SOURCE_PAGE,
            "dataset": "62361-0020",
            "sourceUpdatedAt": "2026-05-28",
            "methodBreakNote": (
                "2007–2021 Vierteljährliche Verdiensterhebung; "
                "ab 2022 Verdiensterhebung. Der Übergang 2021/2022 ist "
                "methodisch eingeschränkt vergleichbar."
            ),
        },
        "germanySeries": load_destatis_series(),
        "comparison": comparison,
    }


def write_php(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    php = (
        "<?php\n"
        "declare(strict_types=1);\n\n"
        "// Generated by scripts/fetch_real_wages_analysis.py; do not edit manually.\n"
        "if (isset($_SERVER['SCRIPT_FILENAME']) "
        "&& realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {\n"
        "    header('X-Robots-Tag: noindex, nofollow, noarchive', true);\n"
        "    http_response_code(404);\n"
        "    exit;\n"
        "}\n\n"
        "return json_decode(<<<'JSON'\n"
        f"{encoded}\n"
        "JSON\n"
        ", true, 512, JSON_THROW_ON_ERROR);\n"
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(php, encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload(fetch_oecd_rows())
    write_php(payload)
    meta = payload["meta"]
    print(
        f"Wrote {OUTPUT_PATH.relative_to(ROOT)}: "
        f"{meta['referenceYear']}, {meta['countryCount']} countries."
    )


if __name__ == "__main__":
    main()
