#!/usr/bin/env python3
"""Regenerate IBTrACS only after independent stdlib CSV reconciliation.

Download the NOAA CSV separately; this command has no network/deployment effects.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from adapters import ibtracs
from fetch_core import AdapterRequest

KPI = "tropical_cyclone_activity_basin"
FIELDS = ["region", "year", "value", "scenario", "horizon"]
BASINS = {"NA", "EP", "WP", "NI", "SI", "SP", "SA"}


def verify(source: Path, output: Path, reference: Path) -> dict:
    raw = source.read_bytes()
    cutoff = datetime.now().year
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    next(reader)  # NOAA units row
    triples = set()
    observation_count = 0
    for row in reader:
        observation_count += 1
        sid, basin, season = (row[key].strip() for key in ("SID", "BASIN", "SEASON"))
        if not sid or not basin or not season:
            continue
        # NOAA's source uses integer season strings. Unexpected nonblank values
        # fail validation instead of silently changing the reference definition.
        year = int(season)
        if year < cutoff:
            triples.add((sid, basin, year))
    independent = Counter((basin, year) for _, basin, year in triples)
    if {basin for basin, _ in independent} != BASINS:
        raise ValueError("Source does not contain exactly the seven expected basins")
    captured = []

    def save(_kpi, rows, _stats, *, output_dir):
        captured.extend(rows)
        return True

    def fail(*args, **kwargs):
        raise ValueError(f"Adapter fallback during verification: {args}")

    runtime = SimpleNamespace(log=print, save_region_records=save, keep_or_dummy=fail)
    request = AdapterRequest(KPI, {}, {}, {}, {}, {}, {"saved_records": 0}, output)
    result = ibtracs.run(request, runtime=runtime, http_get=lambda *_args, **_kwargs: SimpleNamespace(
        status_code=200, content=raw,
    ))
    actual = {(r["region"], r["year"]): r["value"] for r in captured}
    if len(actual) != len(captured) or actual != independent:
        raise ValueError("Adapter output differs from independent SID/basin/season enumeration")
    previous_rows = json.loads((reference / f"{KPI}.json").read_text())
    previous = {(r["region"], r["year"]): r["value"] for r in previous_rows}
    summary = {}
    for basin in sorted(BASINS):
        years = sorted(y for b, y in actual if b == basin)
        summary[basin] = {
            "rows": len(years), "years": years,
            "storm_basin_seasons": sum(actual[(basin, y)] for y in years),
            "added_rows": sum((basin, y) not in previous for y in years),
            "changed_existing_rows": sum((basin, y) in previous and previous[(basin, y)] != actual[(basin, y)] for y in years),
            "removed_rows": sum(b == basin and (b, y) not in actual for b, y in previous),
            "latest_count": actual[(basin, years[-1])],
        }
    report = {
        "source_url": ibtracs.DEFAULT_IBTRACS_URL,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw), "source_observations": observation_count,
        "excluded_seasons_from": cutoff, "record_count": result.record_count,
        "independent_comparison": "all basin-season counts match exactly",
        "basins": summary,
    }
    # No output is written until reconciliation succeeds. Missing seasons remain
    # absent; basin sums are deliberately not labelled unique global storms.
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / f"{KPI}.json"
    json_path.write_text(json.dumps(captured, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / f"{KPI}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(captured)
    with (output / f"{KPI}.csv").open(newline="") as handle:
        roundtrip = [{**r, "year": int(r["year"]), "value": float(r["value"])} for r in csv.DictReader(handle)]
    if roundtrip != json.loads(json_path.read_text()):
        raise ValueError("Generated JSON/CSV mismatch")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(json.dumps(verify(args.source, args.output_dir, args.reference_dir), indent=2))


if __name__ == "__main__":
    main()
