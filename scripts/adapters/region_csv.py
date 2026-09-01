"""Local maintained CSV source adapter for region-keyed (non-country) KPIs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest, AdapterResult


def _file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_region_codes(runtime: SourceRuntime, region_set: str) -> set[str]:
    region_sets = json.loads((runtime.meta_dir / "region_sets.json").read_text(encoding="utf-8"))
    config = region_sets.get(region_set)
    if not config:
        return set()
    geo_path = runtime.meta_dir / config["geo_file"]
    geojson = json.loads(geo_path.read_text(encoding="utf-8"))
    code_property = config.get("code_property", "Acronym")
    return {
        str(feature.get("properties", {}).get(code_property))
        for feature in geojson.get("features", [])
        if feature.get("properties", {}).get(code_property)
    }


def run(request: AdapterRequest, *, runtime: SourceRuntime) -> AdapterResult:
    csv_name = str(request.meta.get("source_code") or f"{request.kpi_id}.csv")
    source_path = runtime.region_source_csv_dir / csv_name
    region_set = str(request.meta.get("region_set") or "")
    if not source_path.is_file():
        runtime.keep_or_dummy(
            request.kpi_id, f"Region CSV missing {csv_name}", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()

    is_test = request.output_dir.resolve() != runtime.data_dir.resolve()
    hash_root = request.output_dir / "pending" if is_test else runtime.pending_dir
    hash_root.mkdir(parents=True, exist_ok=True)
    hash_path = hash_root / f"{request.kpi_id}.md5"
    output_path = request.output_dir / f"{request.kpi_id}.json"
    source_hash = _file_md5(source_path)
    if not is_test and output_path.exists() and hash_path.exists():
        try:
            if source_path.stat().st_mtime <= output_path.stat().st_mtime and hash_path.read_text().strip() == source_hash:
                runtime.mark_skip(request.stats, "Region CSV unchanged (hash & mtime)")
                runtime.log(f"[SKIP] {request.kpi_id}: local region CSV unchanged")
                return AdapterResult()
        except OSError as exc:
            runtime.log(f"[WARN] Region CSV hash check failed for {request.kpi_id}: {exc}")

    try:
        frame = pd.read_csv(source_path)
    except Exception as exc:
        runtime.log(f"[ERROR] Region CSV read failed for {request.kpi_id}: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, f"Region CSV read error {csv_name}", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()
    frame.columns = [str(column).strip().lower() for column in frame.columns]

    required = {"region", "year", "value"}
    if not required.issubset(frame.columns):
        runtime.keep_or_dummy(
            request.kpi_id, f"Unknown region CSV format {csv_name}", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()

    valid_codes = _load_region_codes(runtime, region_set)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        region = str(row.get("region") or "").strip()
        value = runtime.safe_float(row.get("value"))
        try:
            year = int(float(row.get("year")))
        except (TypeError, ValueError):
            continue
        if not region or value is None:
            continue
        if valid_codes and region not in valid_codes:
            runtime.log(f"[WARN] {request.kpi_id}: unknown region code '{region}' for region_set '{region_set}', skipping row")
            continue
        records.append(
            {
                "region": region,
                "year": year,
                "value": value,
                "scenario": str(row.get("scenario") or "").strip(),
                "horizon": str(row.get("horizon") or "").strip(),
            }
        )
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, f"Region CSV empty {csv_name}", request.stats,
            output_dir=request.output_dir, fields=["region", "year", "value", "scenario", "horizon"],
        )
        return AdapterResult()

    latest_year = max(row["year"] for row in records)
    if runtime.save_region_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(data_year=latest_year)
    source_date = f"{latest_year}-01-01T00:00:00Z"
    request.stats["csv_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    hash_path.write_text(source_hash, encoding="utf-8")
    runtime.log(f"[OK] Region CSV KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(source_date=source_date, data_year=latest_year, record_count=len(records))
