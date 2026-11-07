#!/usr/bin/env python3
"""Build a reviewed PISA CSV from the OECD Annex B1.2a workbook."""

import argparse
import csv
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from adapters.runtime import normalize_country_key

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


def read_domain(sheet, codes_by_label, cycle):
    rows = iter(sheet.values)
    cycle_row, score_row = [next(rows) for _ in range(9)][-2:]
    columns = {
        index: int(match[1])
        for index, label in enumerate(cycle_row)
        if score_row[index] == "Mean score" and (match := re.fullmatch(r"PISA (20[0-9]{2})", str(label)))
    }
    if cycle not in columns.values():
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
        code = codes_by_label.get(normalize_country_key(label))
        if code is None:
            raise ValueError(f"Unreviewed PISA participant: {label}")
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
    parser.add_argument("--cycle", type=int, required=True)
    parser.add_argument("--expected-participants", type=int, required=True,
                        help="Reviewed count of eligible participants with all three domains")
    parser.add_argument("--tables", nargs=3, default=TABLES, metavar=("SCIENCE", "READING", "MATH"),
                        help="Exact reviewed worksheet names for the edition")
    args = parser.parse_args()
    if not 2025 <= args.cycle <= date.today().year or args.expected_participants < 1:
        parser.error("Invalid cycle or participant count")
    meta = ROOT / "data" / "meta"
    countries = json.loads((meta / "countries.json").read_text(encoding="utf-8"))
    aliases = json.loads((meta / "country_mappings.json").read_text(encoding="utf-8"))
    codes = {name: info["iso_a3"] for name, info in countries.items()}
    codes_by_label = {normalize_country_key(label): codes.get(target)
                      for label, target in (aliases | LABELS).items()}
    codes_by_label.update({normalize_country_key(label): code for label, code in codes.items()})
    codes_by_label.update({code.lower(): code for code in codes.values()})
    book = load_workbook(args.workbook, read_only=True, data_only=True)
    try:
        domains = [read_domain(book[table], codes_by_label, args.cycle) for table in args.tables]
    finally:
        book.close()
    common = set(domains[0]).intersection(*domains[1:])
    eligible = {key for key in common if key[1] == args.cycle}
    if len(eligible) != args.expected_participants:
        raise ValueError(f"Expected {args.expected_participants} eligible participants, got {len(eligible)}")
    with (ROOT / "scripts/source_csv/pisa_overall_score.csv").open(encoding="utf-8", newline="") as handle:
        history = list(csv.DictReader(handle))
    existing = {(row["country"], int(row["year"])) for row in history}
    if len(existing) != len(history):
        raise ValueError("Duplicate country-cycle in the published PISA baseline")
    if args.cycle < max(year for _, year in existing):
        raise ValueError("Requested cycle is older than the published PISA baseline")
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("country", "year", "value"))
        writer.writerows((row["country"], row["year"], row["value"]) for row in history)
        for code, year in sorted(eligible - existing):
            value = math.fsum(domain[code, year] for domain in domains) / len(domains)
            writer.writerow((code, year, f"{value:.2f}"))


if __name__ == "__main__":
    main()
