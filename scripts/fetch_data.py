#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RealityCheck fetch orchestrator.

Network access and source-specific parsing live in ``adapters/``. This module
owns selection, country mapping, persistence, status reporting and the
post-fetch safety pipeline.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import subprocess
import sys
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters import imf as imf_adapter, special as special_adapter
from adapters.runtime import SourceRuntime
from builtin_adapters import build_builtin_adapter_registry
from env_utils import get_openai_key
from fetch_core import AdapterMode, AdapterRequest, build_status_entry, force_refresh_required
from pipeline_guard import PipelineGuardError, ensure_fetch_succeeded
from source_contracts import SourceContractError, ensure_source_registry, select_kpis
from script_utils import (
    ensure_utf8_stdout,
    read_json as load_json_file,
    safe_write_json as write_json_atomic,
    setup_logger,
)

ensure_utf8_stdout()

SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
META_DIR = DATA_DIR / "meta"
SOURCE_CSV_DIR = SCRIPT_DIR / "source_csv"
SOURCE_CSV_REGIONS_DIR = SCRIPT_DIR / "source_csv_regions"
PENDING_DIR = DATA_DIR / "pending"
TEST_DATA_DIR = DATA_DIR / "test"

COUNTRIES_FILE = META_DIR / "countries.json"
COUNTRY_MAP_FILE = META_DIR / "country_mappings.json"
STATUS_FILE = DATA_DIR / "fetch_status.json"
COUNTRY_PENDING_FILE = DATA_DIR / "country_mappings_pending.json"
AVAILABLE_FILE = META_DIR / "available_kpis.json"
REGION_SETS_FILE = META_DIR / "region_sets.json"
REGION_RECORD_FIELDS = ["region", "year", "value", "scenario", "horizon"]

ACTIVE_DATA_DIR = DATA_DIR
ALLOW_MAPPING_WRITES = True
LOG_FILE = str(ACTIVE_DATA_DIR / "fetch_log.txt")


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    try:
        length = len(obj)
    except TypeError:
        length = None
    note = f"JSON written -> {os.path.relpath(path, ROOT_DIR)}"
    if length is not None:
        note += f" ({length} entries)"
    write_json_atomic(path, obj, logger=None, note=note)


def safe_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        numeric = float(str(value).replace(",", "."))
        return numeric if math.isfinite(numeric) else None
    except (TypeError, ValueError):
        return None


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str, level: str = "info") -> None:
    logger = setup_logger("fetch_log", ACTIVE_DATA_DIR / "fetch_log.txt")
    if level == "error":
        logger.error(message)
    elif level in {"warning", "warn"}:
        logger.warning(message)
    else:
        logger.info(message)


def ensure_dirs() -> None:
    for directory in (DATA_DIR, META_DIR, SOURCE_CSV_DIR, SOURCE_CSV_REGIONS_DIR, PENDING_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RealityCheck Data Fetcher")
    parser.add_argument("-k", "--kpi", default=None, help="Fetch only this KPI filename")
    parser.add_argument("-f", "--force", action="store_true", help="Force refetch of selected KPIs")
    parser.add_argument("-n", "--no-analysis", action="store_true", help="Skip AI-based analysis")
    parser.add_argument("-t", "--test", action="store_true", help="Fetch only KPIs marked test=*")
    return parser.parse_args()


def mark_skip(stats: dict[str, Any], reason: str) -> None:
    stats["skipped"] += 1
    breakdown = stats.setdefault("skipped_breakdown", {})
    breakdown[reason] = breakdown.get(reason, 0) + 1


def resolve_kpi_id(meta: dict[str, Any] | None) -> str:
    if not isinstance(meta, dict):
        return "kpi"
    for key in ("filename", "id", "slug", "name", "title"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "kpi"


def _norm(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFKD", str(value).lower())
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def build_country_indices(countries: dict[str, Any], mapping: dict[str, str]):
    country_index: dict[str, str] = {}
    for country, meta in (countries or {}).items():
        country_index[_norm(country)] = country
        if isinstance(meta, dict):
            for key in ("iso_a2", "iso2", "alpha2", "iso_a3", "iso3", "alpha3"):
                if meta.get(key):
                    country_index[_norm(meta[key])] = country

    alias_index: dict[str, str | None] = {}
    for alias, target in (mapping or {}).items():
        alias_index[_norm(alias)] = "" if not str(target or "").strip() else country_index.get(_norm(target))
    return country_index, alias_index


def resolve_iso2(country: str, countries: dict[str, Any]) -> str:
    meta = countries.get(country, {}) or {}
    return next((str(meta[key]) for key in ("iso2", "iso_a2", "alpha2") if meta.get(key)), "")


def resolve_iso3(country: str, countries: dict[str, Any], fallback: str = "") -> str:
    meta = countries.get(country, {}) or {}
    return next((str(meta[key]) for key in ("iso3", "iso_a3", "alpha3") if meta.get(key)), fallback)


def canonicalize_country(name, country_index, alias_index, countries, pending, stats):
    if not name:
        return None
    normalized = _norm(name)
    if name in countries:
        stats["mapped_ok"] += 1
        return name
    if normalized in country_index:
        stats["mapped_ok"] += 1
        return country_index[normalized]
    if normalized in alias_index:
        target = alias_index[normalized]
        if target == "":
            stats["mapped_drop"] += 1
            return None
        if not target:
            pending[name] = "Mapping target missing or invalid"
            if name not in stats["new_pending"]:
                stats["mapped_pending"] += 1
                stats["new_pending"].add(name)
            return None
        stats["mapped_ok"] += 1
        return target

    group_terms = ("region", "group", "union", "area", "income", "world", "europe", "asia", "africa", "america", "oceania")
    if any(term in normalized for term in group_terms):
        if ALLOW_MAPPING_WRITES:
            mapping = load_json_file(COUNTRY_MAP_FILE, {})
            if mapping.get(name) != "":
                mapping[name] = ""
                write_json(COUNTRY_MAP_FILE, mapping)
                log(f"[AUTO-MAP] Persisted group/region '{name}' -> ''")
        alias_index[normalized] = ""
        stats["mapped_drop"] += 1
        return None

    if name not in pending:
        pending[name] = "Unknown alias; please map in country_mappings.json"
        stats["mapped_pending"] += 1
        stats["new_pending"].add(name)
    return None


def maybe_invert_records(kpi_id: str, meta: dict[str, Any] | None, records: list[dict[str, Any]]):
    if not isinstance(meta, dict) or str(meta.get("invert", "")).strip() != "*":
        return records
    inverted = []
    for row in records:
        updated = dict(row)
        value = safe_float(updated.get("value"))
        if value is not None:
            updated["value"] = round((1 - value) if 0 <= value <= 1 else (100 - value), 6)
        inverted.append(updated)
    log(f"[TRANSFORM] {kpi_id}: applied invert='*' to {len(records)} rows")
    return inverted


def _trim_records(kpi_id: str, records: list[dict[str, Any]], stats: dict[str, Any] | None, label: str):
    current_year = datetime.now().year
    trimmed = []
    removed_pre1900 = 0
    removed_future = 0
    for row in records:
        try:
            year = int(float(row.get("year")))
        except (TypeError, ValueError):
            continue
        if year < 1900:
            removed_pre1900 += 1
        elif year > current_year:
            removed_future += 1
        else:
            trimmed.append(row)
    log(f"[TRIM] {kpi_id}: removed {removed_pre1900} {label}records before 1900")
    log(f"[TRIM] {kpi_id}: removed {removed_future} {label}records after {current_year}")
    if stats is not None:
        stats["trimmed_records"] = stats.get("trimmed_records", 0) + removed_pre1900 + removed_future
        stats.setdefault("trimmed_kpis", set()).add(kpi_id)
        stats["trimmed_pre1900"] = stats.get("trimmed_pre1900", 0) + removed_pre1900
        stats["trimmed_future"] = stats.get("trimmed_future", 0) + removed_future
    return trimmed


def _save_rows(kpi_id, records, fields, stats=None, output_dir=None, label="") -> bool:
    target = Path(output_dir or DATA_DIR)
    target.mkdir(parents=True, exist_ok=True)
    trimmed = _trim_records(kpi_id, records, stats, label)
    json_path = target / f"{kpi_id}.json"
    if json_path.exists() and trimmed:
        previous = load_json_file(json_path, [])
        previous_years = [row.get("year") for row in previous if isinstance(row, dict)] if isinstance(previous, list) else []
        try:
            previous_latest = max(int(float(year)) for year in previous_years if year is not None)
            incoming_latest = max(int(float(row["year"])) for row in trimmed)
        except (TypeError, ValueError):
            previous_latest = incoming_latest = None
        if previous_latest is not None and incoming_latest is not None and incoming_latest < previous_latest:
            log(
                f"[STALE] {kpi_id}: incoming latest year {incoming_latest} is older than "
                f"the stored year {previous_latest}; preserving existing files"
            )
            if stats is not None:
                mark_skip(stats, "Incoming data older than stored snapshot")
            return False
    write_json(json_path, trimmed)
    with (target / f"{kpi_id}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trimmed)
    return True


def save_records(kpi_id, records, stats=None, output_dir=None) -> bool:
    return _save_rows(kpi_id, records, ["country", "iso2", "year", "value"], stats, output_dir)


def save_imf_records(kpi_id, records, stats=None, output_dir=None) -> bool:
    return _save_rows(kpi_id, records, ["country", "iso3", "year", "value"], stats, output_dir, "IMF ")


def save_region_records(kpi_id, records, stats=None, output_dir=None) -> bool:
    """Persist region-keyed KPI rows (region/year/value[/scenario/horizon]), not country rows."""
    return _save_rows(kpi_id, records, REGION_RECORD_FIELDS, stats, output_dir, "region ")


def keep_or_dummy(kpi_id: str, reason: str, stats: dict[str, Any], output_dir=None, fields=None) -> None:
    target = Path(output_dir or DATA_DIR)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / f"{kpi_id}.json"
    csv_path = target / f"{kpi_id}.csv"
    is_error = any(term in reason.lower() for term in ("failed", "error", "empty"))
    if json_path.exists() and csv_path.exists():
        log(f"[WARN] Keeping old data for {kpi_id} ({reason})")
    else:
        write_json(json_path, [])
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=fields or ["country", "iso2", "year", "value"]).writeheader()
        log(f"[WARN] Dummy created for {kpi_id} ({reason})")
    if is_error:
        stats["errors"] = stats.get("errors", 0) + 1
    stats["dummies"] = stats.get("dummies", 0) + 1


def should_fetch(kpi_id: str, source_type: str, source_date: str | None, meta, fetch_status) -> bool:
    json_exists = (DATA_DIR / f"{kpi_id}.json").exists()
    csv_exists = (DATA_DIR / f"{kpi_id}.csv").exists()
    if not json_exists or (source_type != "special" and not csv_exists):
        return True
    previous = fetch_status.get("kpis", {}).get(kpi_id)
    if not previous:
        return True
    local_date = previous.get("source_date")
    if not source_date or source_date == "Unknown" or not local_date or local_date == "Unknown":
        try:
            refresh_hours = float(meta.get("refresh_hours") or 0)
            last_fetch = datetime.fromisoformat(str(previous.get("last_fetch") or "").replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - last_fetch).total_seconds() / 3600
            if refresh_hours > 0 and age_hours < refresh_hours:
                log(
                    f"[CHECK] {kpi_id}: refresh interval not elapsed "
                    f"({age_hours:.1f}h < {refresh_hours:g}h)"
                )
                return False
        except (TypeError, ValueError):
            pass
        return True
    try:
        local = datetime.fromisoformat(str(local_date).replace("Z", "+00:00"))
        remote = datetime.fromisoformat(str(source_date).replace("Z", "+00:00"))
        return remote > local
    except (TypeError, ValueError):
        return str(source_date) != str(local_date)


def merge_fetch_state(updated_kpis: set[str]) -> None:
    state_path = DATA_DIR / "fetch_state.json"
    old_state = load_json_file(state_path, {}) if state_path.exists() else {}
    merged = sorted(set(old_state.get("updated_kpis", [])) | updated_kpis)
    write_json(state_path, {"last_run": now_utc(), "updated_kpis": merged})
    log(f"[STATE] Merged {len(updated_kpis)} updated KPIs -> total {len(merged)} entries")


def build_source_runtime() -> SourceRuntime:
    return SourceRuntime(
        log=log,
        canonicalize_country=canonicalize_country,
        safe_float=safe_float,
        resolve_iso2=resolve_iso2,
        resolve_iso3=resolve_iso3,
        maybe_invert_records=maybe_invert_records,
        save_records=save_records,
        save_imf_records=save_imf_records,
        save_region_records=save_region_records,
        keep_or_dummy=keep_or_dummy,
        mark_skip=mark_skip,
        write_json=write_json,
        now_utc=now_utc,
        data_dir=DATA_DIR,
        meta_dir=META_DIR,
        source_csv_dir=SOURCE_CSV_DIR,
        region_source_csv_dir=SOURCE_CSV_REGIONS_DIR,
        pending_dir=PENDING_DIR,
    )


def build_adapter_registry():
    return build_builtin_adapter_registry(build_source_runtime())


def _initial_stats() -> dict[str, Any]:
    return {
        "countries_loaded": 0, "kpis_loaded": 0, "saved_records": 0, "dummies": 0,
        "mapped_ok": 0, "mapped_drop": 0, "mapped_pending": 0, "new_pending": set(),
        "wb_success": 0, "csv_success": 0, "owid_success": 0, "noaa_success": 0,
        "unhcr_success": 0,
        "imf_success": 0, "data360_success": 0, "others_success": 0,
        "errors": 0, "skipped": 0, "skipped_breakdown": {}, "updated": 0,
        "updated_kpis": set(), "trimmed_records": 0, "trimmed_kpis": set(), "fetched": 0,
    }


def main(args: argparse.Namespace) -> dict[str, Any]:
    global ACTIVE_DATA_DIR, ALLOW_MAPPING_WRITES, LOG_FILE
    ACTIVE_DATA_DIR = TEST_DATA_DIR if args.test else DATA_DIR
    ALLOW_MAPPING_WRITES = not args.test
    LOG_FILE = str(ACTIVE_DATA_DIR / "fetch_log.txt")
    ensure_dirs()
    ACTIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        get_openai_key()
        key_status = "found"
    except ValueError as exc:
        key_status = "missing"
        log(f"[WARN] {exc}")
    log(f"[INFO] Using OPENAI_API_KEY: {key_status}")
    log("=== Fetch started ===")

    fetch_status = load_json_file(STATUS_FILE, {"kpis": {}})
    if not STATUS_FILE.exists() or not fetch_status.get("kpis"):
        fetch_status = {"kpis": {}}
    force_all_updates = force_refresh_required(args.force, fetch_status)
    stats = _initial_stats()

    countries = load_json_file(COUNTRIES_FILE, {})
    mapping = load_json_file(COUNTRY_MAP_FILE, {})
    pending = load_json_file(COUNTRY_PENDING_FILE, {})
    country_index, alias_index = build_country_indices(countries, mapping)
    stats["countries_loaded"] = len(countries)

    raw_kpis = load_json_file(AVAILABLE_FILE, [])
    if not isinstance(raw_kpis, list):
        raise SourceContractError("KPI registry must contain an array")
    ensure_source_registry(raw_kpis)
    selection = select_kpis([item for item in raw_kpis if isinstance(item, dict)], kpi=args.kpi, test_mode=args.test)
    kpi_list = list(selection.selected)
    ignored_kpis = list(selection.ignored)
    if not kpi_list:
        raise SourceContractError("No enabled KPIs matched the requested selection")
    if args.test:
        args.no_analysis = True
    stats["kpis_loaded"] = len(kpi_list)

    output_dir = TEST_DATA_DIR if args.test else DATA_DIR
    runtime = build_source_runtime()
    registry = build_builtin_adapter_registry(runtime)
    imf_queue: list[dict[str, Any]] = []
    special_queue: list[dict[str, Any]] = []
    source_date_cache: dict[str, str] = {}

    for source_meta in kpi_list:
        meta = dict(source_meta)
        meta["output_dir"] = output_dir
        kpi_id = resolve_kpi_id(meta)
        try:
            source_type = str(meta.get("source_type") or meta.get("type") or "").lower().strip()
            adapter = registry.get(source_type)
            if adapter.mode is AdapterMode.BATCH:
                imf_queue.append(meta)
                continue
            if adapter.mode is AdapterMode.SPECIAL:
                special_queue.append(meta)
                continue
            if meta.get("fetch_policy") == "provider_restricted":
                mark_skip(stats, "Provider redistribution restricted")
                log(
                    f"[SKIP] {kpi_id}: provider redistribution restriction is recorded in KPI metadata; "
                    "preserving the last known-good dataset"
                )
                continue

            cache_key = "worldbank-database" if source_type == "worldbank" else ""
            if cache_key and cache_key in source_date_cache:
                source_date = source_date_cache[cache_key]
            else:
                source_date = adapter.resolve_source_date(meta) or "Unknown"
                if cache_key:
                    source_date_cache[cache_key] = source_date
            meta["_discovered_source_date"] = source_date
            if not args.test and not force_all_updates and not should_fetch(kpi_id, source_type, source_date, meta, fetch_status):
                mark_skip(stats, "Remote data unchanged")
                log(f"[SKIP] {kpi_id}: source unchanged ({source_date})")
                continue

            updated = stats.setdefault("updated_kpis", set())
            was_updated = kpi_id in updated
            request = AdapterRequest(
                kpi_id=kpi_id,
                meta=meta,
                countries=countries,
                country_index=country_index,
                alias_index=alias_index,
                pending=pending,
                stats=stats,
                output_dir=output_dir,
            )
            result = registry.dispatch(source_type, request)
            result.apply_to(meta)
            if kpi_id not in updated:
                log(f"[STATUS] {kpi_id}: no successful replacement; preserving previous status")
                continue
            if not was_updated:
                stats["updated"] += 1
            status = build_status_entry(
                meta,
                discovered_source_date=source_date,
                previous=fetch_status.get("kpis", {}).get(kpi_id, {}),
                fetched_at=now_utc(),
            )
            fetch_status.setdefault("kpis", {})[kpi_id] = status.entry
        except Exception as exc:
            keep_or_dummy(kpi_id, f"Exception: {exc}", stats, output_dir=output_dir)
            log(f"[ERROR] {kpi_id} failed: {exc}\n{traceback.format_exc()}")

    if imf_queue:
        try:
            imf_adapter.fetch_batch(
                imf_queue,
                countries=countries,
                country_index=country_index,
                alias_index=alias_index,
                pending=pending,
                fetch_status=fetch_status,
                stats=stats,
                force_all_updates=force_all_updates,
                output_dir=output_dir,
                runtime=runtime,
                should_fetch=should_fetch,
            )
        except Exception as exc:
            stats["errors"] += 1
            log(f"[ERROR] IMF batch failed: {exc}\n{traceback.format_exc()}")

    if special_queue and not args.test:
        special_meta = special_queue[0]
        special_id = resolve_kpi_id(special_meta)
        special_due = force_all_updates or should_fetch(
            special_id, "special", None, special_meta, fetch_status
        )
        if special_due:
            status = special_adapter.fetch_geopolitical_risk_index(output_dir=output_dir, runtime=runtime)
        else:
            mark_skip(stats, "Refresh interval not elapsed")
            log(f"[SKIP] {special_id}: configured refresh interval not elapsed")
            status = None
        if status:
            fetch_status.setdefault("kpis", {})["geopolitical_risk_index"] = status
            stats["others_success"] += 1
            if "geopolitical_risk_index" not in stats["updated_kpis"]:
                stats["updated"] += 1
            stats["updated_kpis"].add("geopolitical_risk_index")
        elif special_due:
            stats["errors"] += 1

    fetch_status["summary"] = {
        "lastRun": now_utc(),
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "errors": stats["errors"],
    }
    mapping_filter = load_json_file(COUNTRY_MAP_FILE, {})
    filtered_pending = {key: value for key, value in pending.items() if mapping_filter.get(key) != ""}
    if args.test:
        write_json(TEST_DATA_DIR / "fetch_status.json", fetch_status)
        write_json(TEST_DATA_DIR / "country_mappings_pending.json", filtered_pending)
    else:
        write_json(STATUS_FILE, fetch_status)
        write_json(COUNTRY_PENDING_FILE, filtered_pending)
        if stats.get("mapped_pending") or stats.get("new_pending"):
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "auto_resolve_pending_mappings.py")],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                log(f"[WARN] Auto mapping failed: {result.stderr}")

    fetch_state = {
        "last_run": now_utc(),
        "updated_kpis": sorted(stats["updated_kpis"]),
        "summary": {key: stats[key] for key in ("updated", "skipped", "errors")},
    }
    write_json(output_dir / "fetch_state.json", fetch_state)

    summary = [
        "=== RealityCheck Fetch Report ===",
        f"Countries loaded:   {stats['countries_loaded']}",
        f"KPIs processed:     {stats['kpis_loaded']}",
        f"Saved records:      {stats['saved_records']}",
        f"WorldBank KPIs:     {stats['wb_success']}",
        f"CSV KPIs:           {stats['csv_success']}",
        f"OWID KPIs:          {stats['owid_success']}",
        f"NOAA KPIs:          {stats['noaa_success']}",
        f"IMF KPIs:           {stats['imf_success']}",
        f"Data360 KPIs:       {stats['data360_success']}",
        f"UNHCR KPIs:         {stats['unhcr_success']}",
        f"Others KPIs:        {stats['others_success']}",
        f"Mapping pending:    {stats['mapped_pending']}",
        f"Dummies:            {stats['dummies']}",
        f"Skipped:            {stats['skipped']}",
        f"Errors:             {stats['errors']}",
        f"Updated KPIs:       {stats['updated']}",
        f"Ignored test=o:     {len(ignored_kpis)}",
    ]
    if stats["updated_kpis"]:
        summary.extend(["", "Updated KPI files:", *[f"  - {name}" for name in sorted(stats["updated_kpis"])]] )
    safe_result = stats["errors"] == 0 and stats["dummies"] == 0
    summary.extend(["=================================", "Fetch completed successfully" if safe_result else "Fetch completed with blocking safety errors"])
    report = "\n".join(summary) + "\n"
    print(report)
    with Path(LOG_FILE).open("a", encoding="utf-8") as handle:
        handle.write(report)
    return stats


def _run_post_fetch(args: argparse.Namespace, stats: dict[str, Any]) -> None:
    ensure_fetch_succeeded(stats)
    if args.test:
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validation.py"), "--data-dir", str(TEST_DATA_DIR), "--test-kpis-only"],
            check=True,
        )
        return

    subprocess.run([sys.executable, str(SCRIPT_DIR / "promote_ready_kpis.py")], check=True)

    if not args.no_analysis:
        for script in ("fetch_overall_ranking.py", "fetch_consolidated.py"):
            subprocess.run([sys.executable, str(SCRIPT_DIR / script)], check=True)

    state = load_json_file(DATA_DIR / "fetch_state.json", {})
    updated_kpis = set(state.get("updated_kpis", []))
    merge_fetch_state(updated_kpis)

    if not args.no_analysis:
        if args.force or updated_kpis:
            subprocess.run([sys.executable, str(SCRIPT_DIR / "analysis.py")], check=True)
        fun_path = DATA_DIR / "fun_ranking.json"
        safe_path = DATA_DIR / "safe_haven_ranking.json"

        def file_age_days(path: Path) -> int:
            return 999 if not path.exists() else (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days

        if file_age_days(fun_path) > 30 or file_age_days(safe_path) > 30:
            subprocess.run([sys.executable, str(SCRIPT_DIR / "generate_fun_safe_rankings.py")], check=True)
        subprocess.run([sys.executable, str(SCRIPT_DIR / "check_source_csv_updates.py")], check=True)

    subprocess.run([sys.executable, str(SCRIPT_DIR / "validation.py")], check=True)


if __name__ == "__main__":
    cli_args = parse_args()
    if cli_args.test:
        cli_args.no_analysis = True
    run_stats = main(cli_args)
    try:
        _run_post_fetch(cli_args, run_stats)
    except PipelineGuardError as exc:
        print(f"ERROR: Pipeline safety gate blocked post-processing and deployment: {exc}")
        raise SystemExit(2) from exc
