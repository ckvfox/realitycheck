"""Local maintained CSV source adapter."""
from __future__ import annotations

import hashlib
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


def run(request: AdapterRequest, *, runtime: SourceRuntime) -> AdapterResult:
    csv_name = str(request.meta.get("source_code") or request.meta.get("code") or f"{request.kpi_id}.csv")
    source_path = runtime.source_csv_dir / csv_name
    if not source_path.is_file():
        runtime.keep_or_dummy(
            request.kpi_id, f"CSV missing {csv_name}", request.stats, output_dir=request.output_dir
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
                runtime.mark_skip(request.stats, "CSV unchanged (hash & mtime)")
                runtime.log(f"[SKIP] {request.kpi_id}: local CSV unchanged")
                return AdapterResult()
        except OSError as exc:
            runtime.log(f"[WARN] CSV hash check failed for {request.kpi_id}: {exc}")

    try:
        frame = pd.read_csv(source_path)
    except Exception as exc:
        runtime.log(f"[ERROR] CSV read failed for {request.kpi_id}: {exc}")
        runtime.keep_or_dummy(
            request.kpi_id, f"CSV read error {csv_name}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()
    if len(frame.columns) == 1 and "," in str(frame.columns[0]):
        columns = [column.strip() for column in str(frame.columns[0]).split(",")]
        frame = frame[frame.columns[0]].astype(str).str.split(",", expand=True)
        frame.columns = columns
    frame.columns = [str(column).strip().lower() for column in frame.columns]

    required = {"country", "year", "value"}
    if not required.issubset(frame.columns):
        if request.kpi_id == "number_of_recorded_natural_disasters" and "entity" in frame.columns:
            if "total disasters" in frame.columns:
                frame["value"] = frame["total disasters"]
            else:
                numeric = [
                    column for column in frame.columns
                    if column not in {"entity", "code", "year"} and frame[column].dtype != "object"
                ]
                frame["value"] = frame[numeric].sum(axis=1)
            frame = frame.rename(columns={"entity": "country"})
        else:
            runtime.keep_or_dummy(
                request.kpi_id, f"Unknown CSV format {csv_name}", request.stats, output_dir=request.output_dir
            )
            return AdapterResult()

    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        canon = runtime.canonicalize_country(
            str(row.get("country") or "").strip(),
            request.country_index,
            request.alias_index,
            request.countries,
            request.pending,
            request.stats,
        )
        value = runtime.safe_float(row.get("value"))
        try:
            year = int(float(row.get("year")))
        except (TypeError, ValueError):
            continue
        if canon and value is not None:
            raw_iso2 = row.get("iso2")
            iso2 = "" if pd.isna(raw_iso2) else str(raw_iso2 or "").strip()
            records.append(
                {
                    "country": canon,
                    "iso2": iso2 or runtime.resolve_iso2(canon, request.countries),
                    "year": year,
                    "value": value,
                }
            )
    if not records:
        runtime.keep_or_dummy(
            request.kpi_id, f"CSV empty {csv_name}", request.stats, output_dir=request.output_dir
        )
        return AdapterResult()

    records = runtime.maybe_invert_records(request.kpi_id, request.meta, records)
    latest_year = max(row["year"] for row in records)
    if runtime.save_records(request.kpi_id, records, request.stats, output_dir=request.output_dir) is False:
        return AdapterResult(data_year=latest_year)
    source_date = f"{latest_year}-01-01T00:00:00Z"
    request.stats["csv_success"] += 1
    request.stats["saved_records"] += len(records)
    request.stats.setdefault("updated_kpis", set()).add(request.kpi_id)
    hash_path.write_text(source_hash, encoding="utf-8")
    runtime.log(f"[OK] CSV KPI saved: {request.kpi_id} ({len(records)} rows)")
    return AdapterResult(source_date=source_date, data_year=latest_year, record_count=len(records))
