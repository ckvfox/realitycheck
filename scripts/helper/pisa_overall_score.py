#!/usr/bin/env python3
"""Build a reviewed PISA CSV from the OECD Annex B1.2a workbook."""

import argparse
import csv
import json
import math
import re
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
TABLES = ("Table I.B1.2a.36", "Table I.B1.2a.37", "Table I.B1.2a.38")
LABELS = {
    "Korea": "South Korea",
    "Palestinian Authority": "Palestine",
    "Türkiye": "Turkey",
}
EXCLUDED = {
    "B-S-J-Z (China)", "Dushanbe (Tajikistan)", "Hong Kong (China)",
    "Kurdistan Region (Iraq)", "Macao (China)", "Ukrainian regions (17 of 27)",
}


def read_domain(sheet, countries, aliases):
    rows = iter(sheet.values)
    cycle_row, score_row = [next(rows) for _ in range(9)][-2:]
    columns = {
        index: int(match[1])
        for index, label in enumerate(cycle_row)
        if score_row[index] == "Mean score" and (match := re.fullmatch(r"PISA (20[0-9]{2})", str(label)))
    }
    if not columns or max(columns.values()) < 2025:
        raise ValueError(f"Unexpected cycle headers in {sheet.title}")
    means = {}
    for row in rows:
        label = str(row[0] or "").strip().rstrip("*").strip()
        if label.startswith("OECD average") or label in EXCLUDED:
            continue
        observations = [(year, row[index]) for index, year in columns.items()
                        if type(row[index]) in (int, float) and math.isfinite(row[index])]
        if not observations:
            continue
        country = LABELS.get(label, aliases.get(label, label))
        if country not in countries:
            raise ValueError(f"Unreviewed PISA participant: {label}")
        code = countries[country]["iso_a3"]
        for year, value in observations:
            key = (code, year)
            if key in means:
                raise ValueError(f"Duplicate PISA mean in {sheet.title}: {key}")
            means[key] = value
    return means


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Reviewed OECD Annex B1.2a XLSX")
    parser.add_argument("output", type=Path, help="CSV output path for review")
    args = parser.parse_args()
    meta = ROOT / "data" / "meta"
    countries = json.loads((meta / "countries.json").read_text(encoding="utf-8"))
    aliases = json.loads((meta / "country_mappings.json").read_text(encoding="utf-8"))
    book = load_workbook(args.workbook, read_only=True, data_only=True)
    try:
        domains = [read_domain(book[table], countries, aliases) for table in TABLES]
    finally:
        book.close()
    common = set(domains[0]).intersection(*domains[1:])
    if not common:
        raise ValueError("No country-cycle has all three PISA domains")
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("country", "year", "value"))
        for code, year in sorted(common):
            value = math.fsum(domain[code, year] for domain in domains) / len(domains)
            writer.writerow((code, year, f"{value:.2f}"))


if __name__ == "__main__":
    main()
