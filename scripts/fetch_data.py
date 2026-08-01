from pathlib import Path
# === Robust JSON Writer ===
def write_json(path: str | Path, obj):
    """
    Write JSON data to the given path using safe_write_json from script_utils.py (aliased as write_json_atomic).
    Adds a log note with relative path and entry count.
    """
    path = Path(path)
    length = None
    try:
        length = len(obj)
    except Exception:
        length = None
    rel_path = os.path.relpath(path, ROOT_DIR)
    note = f"JSON written → {rel_path}"
    if length is not None:
        note += f" ({length} entries)"
    write_json_atomic(path, obj, logger=None, note=note)
# ======================================================================
# 🔢 Utility: safe_float (robust float conversion)
# ======================================================================
def safe_float(x):
    try:
        if x in ("", None):
            return None
        return float(str(x).replace(",", "."))
    except Exception:
        return None

# ======================================================================
# 🕒 Utility: now_utc (ISO UTC timestamp)
# ======================================================================
def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# ======================================================================
# 📝 Logging Helper
# ======================================================================
def log(msg, level="info"):
    log_path = ACTIVE_DATA_DIR / "fetch_log.txt"
    logger = setup_logger("fetch_log", log_path)
    if level == "error":
        logger.error(msg)
    elif level == "warning" or level == "warn":
        logger.warning(msg)
    else:
        logger.info(msg)
# ======================================================================
# 📁 Ensure Required Directories Exist
# ======================================================================
def ensure_dirs():
    for d in [DATA_DIR, META_DIR, SOURCE_CSV_DIR, PENDING_DIR]:
        os.makedirs(d, exist_ok=True)
# ======================================================================
# 🏁 CLI Argument Parsing (parse_args)
# ======================================================================
def parse_args():
    parser = argparse.ArgumentParser(description="RealityCheck Data Fetcher")
    parser.add_argument("-k", "--kpi", dest="kpi", type=str, default=None, help="Fetch only this KPI filename")
    parser.add_argument("-f", "--force", dest="force", action="store_true", help="Force refetch of all KPIs")
    parser.add_argument("-n", "--no-analysis", dest="no_analysis", action="store_true", help="Skip AI-based analysis")
    parser.add_argument("-t", "--test", dest="test", action="store_true", help="Test mode (only KPIs with test=*)")
    return parser.parse_args()

from pathlib import Path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck Fetch Script – Oktober 2025 (Meta-Version)
-------------------------------------------------------
Produktive Version mit:
 • Logging nach /data/fetch_log.txt
 • Pfade auf /data/meta/
 • filename statt normalize_name()
 • vollständigem Mapping-, Dummy-, und Analyse-Handling
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import re
import zipfile
import unicodedata
import traceback
import subprocess
import pandas as pd
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from builtin_adapters import AdapterServices, build_builtin_adapter_registry
from env_utils import get_openai_key  # ✅ wichtig: hier fehlte der Import
from fetch_core import (
    AdapterMode,
    AdapterRequest,
    build_status_entry,
    force_refresh_required,
)
from pipeline_guard import PipelineGuardError, ensure_fetch_succeeded
from source_contracts import SourceContractError, ensure_source_registry, select_kpis
from script_utils import (
    ensure_utf8_stdout,
    read_json as load_json_file,
    safe_write_json as write_json_atomic,
    safe_write_text as write_text_atomic,
    setup_logger,
)

# ----------------------------------------------------------------------
# 🌍 World Bank API/ZIP Headers and Robust Request Helper
# ----------------------------------------------------------------------
WORLD_BANK_HEADERS = {
    "User-Agent": "RealityCheck/1.0 (contact: info@realitycheck.global)",
    "Accept": "application/json, text/plain, */*",
}
WORLD_BANK_ZIP_HEADERS = {
    "User-Agent": "RealityCheck/1.0 (contact: info@realitycheck.global)",
    "Accept": "application/zip, application/octet-stream, */*",
}

import time as _time
def worldbank_request(url, timeout=30, headers=None, label=None, attempts=3, wait_base=3):
    """
    Robust HTTP GET with retry/backoff for World Bank API/ZIP endpoints.
    Logs all attempts and errors. Returns requests.Response or None.
    """
    headers = headers or WORLD_BANK_HEADERS
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            if resp.status_code == 429:
                log(f"[RATE] {label or url}: HTTP 429 (rate limit), attempt {attempt}/{attempts}")
                if attempt < attempts:
                    _time.sleep(wait_base * attempt)
                    continue
            elif resp.status_code >= 500:
                log(f"[WARN] {label or url}: HTTP {resp.status_code}, attempt {attempt}/{attempts}")
                if attempt < attempts:
                    _time.sleep(wait_base * attempt)
                    continue
            return resp
        except Exception as e:
            log(f"[ERR] {label or url}: request failed on attempt {attempt}/{attempts}: {e}")
            if attempt < attempts:
                _time.sleep(wait_base * attempt)
    log(f"[FAIL] {label or url}: all {attempts} attempts failed")
    return None



# ✅ UTF-8-Fix
ensure_utf8_stdout()


# ======================================================================
# 🔧 Pfade (pathlib-Version – robust gegen OS-Unterschiede)
# ======================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR   = SCRIPT_DIR.parent.resolve()
DATA_DIR   = ROOT_DIR / "data"
META_DIR   = DATA_DIR / "meta"

SOURCE_CSV_DIR = SCRIPT_DIR / "source_csv"
PENDING_DIR    = DATA_DIR / "pending"

# === Test data directory for test mode output ===
TEST_DATA_DIR = DATA_DIR / "test"

# Runtime paths switch to data/test in test mode. Keeping this explicit makes
# accidental writes to the productive snapshot detectable in unit tests.
ACTIVE_DATA_DIR = DATA_DIR
ALLOW_MAPPING_WRITES = True

# === Global logfile path for summary report ===
LOG_FILE = str(ACTIVE_DATA_DIR / "fetch_log.txt")

COUNTRIES_FILE       = META_DIR / "countries.json"
COUNTRY_MAP_FILE     = META_DIR / "country_mappings.json"
STATUS_FILE = DATA_DIR / "fetch_status.json"
COUNTRY_PENDING_FILE = DATA_DIR / "country_mappings_pending.json"
AVAILABLE_FILE = META_DIR / "available_kpis.json"

# --- New IMF API fetch using sdmx1 ---
import sdmx
def fetch_imf_api(imf_kpis, countries, c_index, a_index, pending, fetch_status, stats, force_all_updates):
    if not imf_kpis:
        return
    log(f"[FETCH] IMF API import start for {len(imf_kpis)} KPIs")
    client = sdmx.Client('IMF_WEO')
    import requests
    for meta in imf_kpis:
        kpi_id = resolve_kpi_id(meta)
        source_code = (meta.get("source_code") or "").strip()
        output_dir = meta.get("output_dir", DATA_DIR)
        updated_set = stats.setdefault("updated_kpis", set())
        already_marked = kpi_id in updated_set
        # For debug: test with a single country (DEU) to isolate SDMX API issues
        iso3_list = ["DEU"]
        if not source_code:
            log(f"[WARN] IMF KPI {kpi_id} missing source_code")
            keep_or_dummy(kpi_id, "IMF missing source_code", stats, output_dir=output_dir)
            continue
        # Only fetch if needed
        if not force_all_updates and not should_fetch(
            kpi_id, "imf", None, meta, fetch_status
        ):
            mark_skip(stats, "Remote data unchanged")
            log(f"[⏸️] {kpi_id} – IMF API unchanged")
            continue
        # Build iso3_list from all country meta entries, fallback to empty string if not found
        iso3_list = [meta.get("iso3") or meta.get("iso_a3") or meta.get("alpha3") or '' for cname, meta in (countries or {}).items()]
        # Try SDMX API first
        # Debug-Ausgaben entfernt
        df = None
        try:
            # Try the original call
            data_msg = None
            try:
                data_msg = client.data(source_code, key="+".join(iso3_list), params={"startPeriod": "1990"})
            except Exception as exc1:
                # Suppress intermediate errors, only log at debug level or not at all
                # log(f"[DEBUG] IMF API fetch (key=+join) failed for {source_code}: {exc1}")
                try:
                    data_msg = client.data(source_code, key=iso3_list, params={"startPeriod": "1990"})
                except Exception as exc2:
                    # log(f"[DEBUG] IMF API fetch (key=list) failed for {source_code}: {exc2}")
                    try:
                        data_msg = client.data(source_code, key="DEU", params={"startPeriod": "1990"})
                    except Exception as exc3:
                        # Only log the final failure as error
                        log(f"[ERR] IMF API fetch failed for {source_code}: All key formats failed. Last error: {exc3}")
                        data_msg = None
            if data_msg is not None:
                try:
                    df = sdmx.to_pandas(data_msg)
                except Exception as exc_df:
                    log(f"[ERR] IMF SDMX to_pandas failed for {source_code}: {exc_df}")
                    df = None
        except Exception as exc:
            import traceback
            log(f"[ERR] IMF API fetch failed for {source_code}: {exc}\n{traceback.format_exc()}")
            df = None

        # If SDMX failed, try IMF Datamapper API as fallback
        if df is None or (hasattr(df, 'empty') and df.empty):
            log(f"[INFO] Trying IMF Datamapper API fallback for {source_code}")
            try:
                url = f"https://www.imf.org/external/datamapper/api/v1/{source_code}"
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    # Structure: {"values": {"GGXWDG_NGDP": {"SDN": {"1992": ...}, ...}}, ...}
                    values = data.get("values", {})
                    indicator_block = values.get(source_code, {})
                    records = []
                    latest_year = None
                    trimmed_years = []
                    for iso3, yearvals in indicator_block.items():
                        canon = canonicalize_country(iso3, c_index, a_index, countries, pending, stats)
                        if not canon:
                            continue
                        iso3_code = resolve_iso3(canon, countries, fallback=iso3)
                        for year, val in yearvals.items():
                            try:
                                year_int = int(year)
                                v = float(val)
                            except Exception:
                                continue
                            # Only keep years <= current year
                            from datetime import datetime
                            if year_int > datetime.now().year:
                                continue
                            trimmed_years.append(year_int)
                            latest_year = max(latest_year or year_int, year_int)
                            records.append({"country": canon, "iso3": iso3_code, "year": year_int, "value": v})
                    if records:
                        save_imf_records(kpi_id, records, stats, output_dir=output_dir)
                        stats["imf_success"] += 1
                        stats["saved_records"] += len(records)
                        stats["fetched"] += len(records)
                        meta["source"] = "IMF Datamapper API"
                        meta["_latest_year"] = max(trimmed_years) if trimmed_years else latest_year
                        meta["_source_date"] = str(meta["_latest_year"])
                        updated_set.add(kpi_id)
                        if not already_marked:
                            stats["updated"] += 1
                        log(f"[OK] IMF Datamapper API KPI saved: {kpi_id} ({len(records)} rows, last year {meta['_latest_year']})")
                    else:
                        save_imf_records(kpi_id, [], output_dir=output_dir)
                        keep_or_dummy(kpi_id, f"IMF Datamapper API empty {source_code}", stats, output_dir=output_dir)
                        meta["_source_date"] = str(latest_year) if latest_year else "Unknown"
                    used_source_date = meta.get("_source_date") or "Unknown"
                    fetch_status.setdefault("kpis", {})[kpi_id] = {
                        "source": meta.get("source") or "IMF Datamapper API",
                        "source_type": "imf",
                        "source_code": source_code,
                        "source_date": used_source_date,
                        "data_year": meta.get("_latest_year"),
                        "last_fetch": now_utc(),
                    }
                    continue
                else:
                    log(f"[ERR] IMF Datamapper API fetch failed: HTTP {resp.status_code}")
            except Exception as exc:
                log(f"[ERR] IMF Datamapper API fetch failed: {exc}")
            # If fallback fails, dummy
            keep_or_dummy(kpi_id, f"IMF Datamapper API fetch failed", stats, output_dir=output_dir)
            continue

        # If SDMX worked, process as before
        if df is not None and not getattr(df, 'empty', False):
            records = []
            latest_year = None
            for (country, year), value in df.stack().items():
                canon = canonicalize_country(country, c_index, a_index, countries, pending, stats)
                if not canon:
                    continue
                try:
                    year_int = int(year)
                    val = float(value)
                except Exception:
                    continue
                latest_year = max(latest_year or year_int, year_int)
                iso3_code = resolve_iso3(canon, countries)
                records.append({"country": canon, "iso3": iso3_code, "year": year_int, "value": val})
            if records:
                save_imf_records(kpi_id, records, stats, output_dir=output_dir)
                stats["imf_success"] += 1
                stats["saved_records"] += len(records)
                stats["fetched"] += len(records)
                meta["source"] = "IMF WEO API"
                meta["_latest_year"] = latest_year
                meta["_source_date"] = str(latest_year)
                updated_set.add(kpi_id)
                if not already_marked:
                    stats["updated"] += 1
                log(f"[OK] IMF API KPI saved: {kpi_id} ({len(records)} rows, last year {latest_year})")
            else:
                save_imf_records(kpi_id, [], output_dir=output_dir)
                keep_or_dummy(kpi_id, f"IMF API empty {source_code}", stats, output_dir=output_dir)
                meta["_source_date"] = str(latest_year) if latest_year else "Unknown"
            used_source_date = meta.get("_source_date") or "Unknown"
            fetch_status.setdefault("kpis", {})[kpi_id] = {
                "source": meta.get("source") or "IMF WEO API",
                "source_type": "imf",
                "source_code": source_code,
                "source_date": used_source_date,
                "data_year": meta.get("_latest_year"),
                "last_fetch": now_utc(),
            }
    log("[INFO] IMF API import completed")
    try:
        if x in ("", None):
            return None
        return float(str(x).replace(",", "."))
    except Exception:
        return None

import hashlib


def _sanitize_filename(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(text))
    if len(cleaned) > 100:
        digest = hashlib.md5(cleaned.encode("utf-8")).hexdigest()[:8]
        cleaned = cleaned[:90] + "_" + digest
    return cleaned


def safe_filename(text: str) -> str:
    """Sanitize and shorten filenames safely (handles long URLs and special chars)."""
    return _sanitize_filename(text)


def safe_pending_filename(text: str) -> str:
    """Erzeugt einen sicheren, kurzen Dateinamen für Pending-Files (z. B. bei OWID-404s)."""
    return _sanitize_filename(text)


def mark_skip(stats: Dict[str, Any], reason: str) -> None:
    """Increment skipped counters and keep a human-readable breakdown."""
    stats["skipped"] += 1
    breakdown = stats.setdefault("skipped_breakdown", {})
    breakdown[reason] = breakdown.get(reason, 0) + 1


def resolve_kpi_id(meta: Dict[str, Any] | None) -> str:
    """Return a stable KPI identifier from assorted metadata fields.

    Older versions of the fetcher called this helper directly, so it doubles
    as a backwards-compatibility shim for environments that still expect the
    function to exist.
    """

    if not isinstance(meta, dict):
        return "kpi"

    for key in ("filename", "id", "slug", "name", "title"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return "kpi"

# ======================================================================
# 💾 Safe Write Helpers (robuste Datei-Speicherung)
# ======================================================================
# ======================================================================
# 🌍 Country Mapping
# ======================================================================
def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s)

def build_country_indices(countries: Dict[str, Any], mapping: Dict[str, str]):
    """Create lookup tables for canonical names and aliases.

    Besides normalized country names we now also index ISO2/ISO3 codes so that
    CSV sources which only provide codes (e.g. "AFG" or "DE") are resolved
    without requiring manual aliases.
    """

    c_index = {}
    for cname, meta in (countries or {}).items():
        c_index[_norm(cname)] = cname

        if isinstance(meta, dict):
            for key in ("iso_a2", "iso2", "alpha2", "iso_a3", "iso3", "alpha3"):
                code = meta.get(key)
                if code:
                    c_index[_norm(code)] = cname

    a_index = {}
    for alias, target in (mapping or {}).items():
        if not target or str(target).strip() == "":
            a_index[_norm(alias)] = ""
        else:
            t_norm = _norm(target)
            a_index[_norm(alias)] = c_index.get(t_norm)
    return c_index, a_index


def resolve_iso2(canon: str, countries: Dict[str, Any]) -> str:
    meta = countries.get(canon, {}) or {}
    for key in ("iso2", "iso_a2", "alpha2"):
        val = meta.get(key)
        if val:
            return val
    return ""


def resolve_iso3(canon: str, countries: Dict[str, Any], fallback: str = "") -> str:
    meta = countries.get(canon, {}) or {}
    for key in ("iso3", "iso_a3", "alpha3"):
        val = meta.get(key)
        if val:
            return val
    return fallback

def canonicalize_country(name: str, c_index, a_index, countries, pending, stats):
    if not name:
        return None
    n = _norm(name)
    # 1. Always prefer canonical entry in countries.json
    if name in countries:
        stats["mapped_ok"] += 1
        return name
    if n in c_index:
        stats["mapped_ok"] += 1
        return c_index[n]
    # 2. Check mapping in a_index (country_mappings.json)
    if n in a_index:
        target = a_index[n]
        # If the mapping is empty, double-check if the name is a canonical country (should not exclude real countries)
        if target == "":
            if name in countries or c_index.get(n) in countries:
                stats["mapped_ok"] += 1
                return name if name in countries else c_index.get(n)
            stats["mapped_drop"] += 1
            return None
        if not target:
            pending[name] = "Mapping target missing or invalid"
            stats["mapped_pending"] += 1
            return None
        stats["mapped_ok"] += 1
        return target
    # 3. Detect group/region (only if not a canonical country)
    GROUP_REGION_KEYWORDS = ["region", "group", "union", "area", "income", "world", "europe", "asia", "africa", "america", "oceania"]
    if any(kw in n for kw in GROUP_REGION_KEYWORDS):
        # Production runs persist known aggregate labels. Isolated tests must
        # never mutate the productive country mapping registry.
        if ALLOW_MAPPING_WRITES:
            import json, os
            mapping_path = os.path.join(META_DIR, "country_mappings.json")
            try:
                with open(mapping_path, encoding="utf-8") as f:
                    mapping = json.load(f)
            except Exception:
                mapping = {}
            if name not in mapping or mapping[name] != "":
                mapping[name] = ""
                with open(mapping_path, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=2)
                log(f"[AUTO-MAP] Persisted group/region '{name}' → '' in country_mappings.json")
        a_index[n] = ""
        stats["mapped_drop"] += 1
        log(f"EXCLUDED (Gruppe/Region): '{name}' (auto-mapped to '')")
        return None
    # 4. Not found: add to pending
    pending[name] = "Unknown alias; please map in country_mappings.json"
    stats["mapped_pending"] += 1
    stats["new_pending"].add(name)
    return None

# ======================================================================
# 💾 Speicherung / Dummy
# ======================================================================
def maybe_invert_records(kpi_id: str, meta: Dict[str, Any] | None, records: List[Dict[str, Any]]):
    """Apply post-fetch inversions for KPIs flagged with invert="*"."""
    if not isinstance(meta, dict):
        return records

    invert_flag = str(meta.get("invert", "")).strip()
    if invert_flag != "*":
        return records

    inverted: List[Dict[str, Any]] = []
    for row in records:
        new_row = dict(row)
        value = safe_float(new_row.get("value"))
        if value is None:
            inverted.append(new_row)
            continue

        if 0 <= value <= 1:
            new_value = 1 - value
        else:
            new_value = 100 - value

        new_row["value"] = round(new_value, 6)
        inverted.append(new_row)

    log(f"[TRANSFORM] {kpi_id}: applied invert='*' to {len(records)} rows")
    return inverted


def save_records(kpi_id: str, records: List[Dict[str, Any]], stats=None, output_dir=None):
    """
    Speichert Daten im Standardformat, entfernt automatisch alle Jahre < 1900
    und protokolliert die Kürzungen im Fetch-Report.
    """
    if output_dir is None:
        output_dir = DATA_DIR
    os.makedirs(output_dir, exist_ok=True)
    before = len(records)

    # 🕐 Trim extreme years (remove pre-1900 and future projections)
    from datetime import datetime
    current_year = datetime.now().year

    trimmed = []
    removed_pre1900 = 0
    removed_future = 0
    for r in records:
        y = r.get("year")
        try:
            y = int(float(y))
        except Exception:
            continue
        if y < 1900:
            removed_pre1900 += 1
            continue
        if y > current_year:
            removed_future += 1
            continue
        trimmed.append(r)

    after = len(trimmed)
    removed = before - after
    # Always log pre-1900 and post-current-year cuts, even if 0
    log(f"[TRIM] {kpi_id}: removed {removed_pre1900} records before 1900")
    log(f"[TRIM] {kpi_id}: removed {removed_future} records after {current_year}")
    if stats is not None:
        stats.setdefault("trimmed_records", 0)
        stats["trimmed_records"] += removed
        stats.setdefault("trimmed_kpis", set())
        stats["trimmed_kpis"].add(kpi_id)
        # Track pre-1900 and post-current-year cuts separately
        stats.setdefault("trimmed_pre1900", 0)
        stats.setdefault("trimmed_future", 0)
        stats["trimmed_pre1900"] += removed_pre1900
        stats["trimmed_future"] += removed_future

    # --- Normal speichern ---
    write_json(os.path.join(output_dir, f"{kpi_id}.json"), trimmed)
    with open(os.path.join(output_dir, f"{kpi_id}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country", "iso2", "year", "value"])
        w.writeheader()
        w.writerows(trimmed)


def keep_or_dummy(kpi_id: str, reason: str, stats, output_dir=None):
    if output_dir is None:
        output_dir = DATA_DIR
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{kpi_id}.json")
    csv_path  = os.path.join(output_dir, f"{kpi_id}.csv")
    is_error = "failed" in reason.lower() or "error" in reason.lower() or "empty" in reason.lower()
    if os.path.exists(json_path) and os.path.exists(csv_path):
        log(f"[WARN] Keeping old data for {kpi_id} ({reason})")
        if is_error:
            stats["errors"] = stats.get("errors", 0) + 1
            stats["dummies"] = stats.get("dummies", 0) + 1
            log(f"[WARN] Dummy (virtual) counted for {kpi_id} ({reason})")
        return
    write_json(json_path, [])
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=["country", "iso2", "year", "value"]).writeheader()
    stats["dummies"] = stats.get("dummies", 0) + 1
    log(f"[WARN] Dummy created for {kpi_id} ({reason})")
    if is_error:
        stats["errors"] = stats.get("errors", 0) + 1


def save_imf_records(kpi_id: str, records: List[Dict[str, Any]], stats=None, output_dir=None):
    """Save IMF records that use iso3 codes while keeping trimming logic."""

    if output_dir is None:
        output_dir = DATA_DIR
    os.makedirs(output_dir, exist_ok=True)
    before = len(records)
    from datetime import datetime

    current_year = datetime.now().year
    trimmed = []
    removed_pre1900 = 0
    removed_future = 0
    for r in records:
        y = r.get("year")
        try:
            y = int(float(y))
        except Exception:
            continue
        if y < 1900:
            removed_pre1900 += 1
            continue
        if y > current_year:
            removed_future += 1
            continue
        trimmed.append(r)

    after = len(trimmed)
    removed = before - after
    # Always log pre-1900 and post-current-year cuts, even if 0
    log(f"[TRIM] {kpi_id}: removed {removed_pre1900} IMF records before 1900")
    log(f"[TRIM] {kpi_id}: removed {removed_future} IMF records after {current_year}")
    if stats is not None:
        stats.setdefault("trimmed_records", 0)
        stats["trimmed_records"] += removed
        stats.setdefault("trimmed_kpis", set())
        stats["trimmed_kpis"].add(kpi_id)
        # Track pre-1900 and post-current-year cuts separately
        stats.setdefault("trimmed_pre1900", 0)
        stats.setdefault("trimmed_future", 0)
        stats["trimmed_pre1900"] += removed_pre1900
        stats["trimmed_future"] += removed_future

    write_json(os.path.join(output_dir, f"{kpi_id}.json"), trimmed)
    with open(os.path.join(output_dir, f"{kpi_id}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country", "iso3", "year", "value"])
        w.writeheader()
        w.writerows(trimmed)

# ======================================================================
# 🔍 Source-Date Extraction & Update Logic – finale Version Okt 2025
# ======================================================================

import csv, io

def get_source_date_from_worldbank(code: str) -> Optional[str]:
    """
    Liefert das Aktualisierungsdatum eines WB-Indikators.
    Reihenfolge:
      1) API JSON (falls vorhanden)
      2) CSV-Header in der Daten-CSV (Zeile 'Last Updated Date,"YYYY-MM-DD"')
      3) ZIP-Metadatum (Fallback)
    """
    try:
        # --- 1) JSON ---
        url_json = f"https://api.worldbank.org/v2/indicator/{code}?format=json"
        rj = worldbank_request(
            url_json,
            timeout=20,
            headers=WORLD_BANK_HEADERS,
            label=f"WorldBank meta {code}",
            attempts=3,
            wait_base=3,
        )
        if rj and rj.status_code == 200:
            data = rj.json()
            if isinstance(data, list) and data:
                meta = data[0]
                for key in ["Last Updated Date","lastupdated","LastUpdated","metadata_updated","date","Date"]:
                    if key in meta and meta[key]:
                        d = str(meta[key]).strip()
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                            d += "T00:00:00Z"
                        log(f"[META] WorldBank {code} → JSON Last Updated {d}")
                        return d

        # --- 2) CSV-Header (A3-Zeile) ---
        url_zip = f"https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"
        rz = worldbank_request(
            url_zip,
            timeout=30,
            headers=WORLD_BANK_ZIP_HEADERS,
            label=f"WorldBank meta ZIP {code}",
            attempts=3,
            wait_base=3,
        )

        if rz and rz.status_code == 200 and rz.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(rz.content)) as zf:
                data_csv = next((n for n in zf.namelist() if n.lower().endswith(".csv") and "metadata" not in n.lower()), None)
                if data_csv:
                    head = zf.read(data_csv).decode("utf-8-sig", errors="ignore")
                    first_lines = "\n".join(head.splitlines()[:10])
                    m = re.search(r'Last\s*Updated\s*Date["\s,]+(?:"|)?(\d{4}-\d{2}-\d{2})', first_lines)
                    if m:
                        d = m.group(1) + "T00:00:00Z"
                        log(f"[META] WorldBank {code} → CSV Header Last Updated Date {d}")
                        return d
                # --- 3) ZIP-Fallback ---
                info = next(iter(zf.infolist()), None)
                if info:
                    dt = datetime(*info.date_time).strftime("%Y-%m-%dT00:00:00Z")
                    log(f"[META] WorldBank {code} → ZIP fallback date {dt}")
                    return dt

        log(f"[META] WorldBank {code}: no valid date found (JSON/CSV/ZIP)")
        return None
    except Exception as e:
        log(f"[WARN] get_source_date_from_worldbank({code}) failed: {e}")
        return None

def should_fetch_owid(kpi_id: str, meta: dict, fetch_status: dict) -> bool:
    """
    Smarte OWID-Heuristik:
    - Wenn die CSV nur Jahre < aktuelles Jahr enthält und bereits dieses Jahr ein Fetch stattfand → skip
    - Sonst → fetch
    """
    prev = fetch_status.get("kpis", {}).get(kpi_id)
    if not prev:
        log(f"[CHECK] {kpi_id}: no previous record → fetch now")
        return True

    last_fetch_str = prev.get("last_fetch", "2000-01-01T00:00:00Z").replace("Z", "+00:00")
    try:
        last_fetch = datetime.fromisoformat(last_fetch_str)
    except Exception:
        last_fetch = datetime(2000, 1, 1, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    csv_url = f"https://ourworldindata.org/grapher/{meta.get('source_code')}.csv"
    try:
        r = requests.get(csv_url, timeout=15)
        if r.status_code != 200:
            log(f"[CHECK] {kpi_id}: CSV unavailable → fetch")
            return True
        reader = csv.DictReader(io.StringIO(r.text))
        years = []
        for row in reader:
            y = row.get("Year")
            if y and re.match(r"^\d{4}$", y):
                years.append(int(y))
        if not years:
            log(f"[CHECK] {kpi_id}: no year data → fetch")
            return True
        max_year = max(years)
        current_year = now.year
        if max_year < current_year and last_fetch.year == current_year:
            log(f"[CHECK] {kpi_id}: max_year={max_year} < {current_year}, fetched this year → skip")
            return False
        log(f"[CHECK] {kpi_id}: max_year={max_year} → fetch (possible update)")
    except Exception as e:
        log(f"[CHECK] {kpi_id}: error in year check: {e} → fetch")
        return True


def should_fetch(kpi_id: str, source_type: str, source_date: Optional[str], meta: dict, fetch_status: dict) -> bool:
    """
    Allgemeine Steuerung:
    - Für WorldBank: echtes Änderungsdatum vergleichen
    - Für OWID: Heuristik (siehe oben)
    - Für CSV/UNHCR: immer neu laden (keine API-Daten)
    """
    # 🔁 Sicherheitsnetz: Falls lokale Dateien fehlen, immer neu laden
    json_path = DATA_DIR / f"{kpi_id}.json"
    csv_path = DATA_DIR / f"{kpi_id}.csv"
    if not json_path.exists() or not csv_path.exists():
        log(f"[CHECK] {kpi_id}: local files missing → fetch now")
        return True

    if source_type == "owid":
        return should_fetch_owid(kpi_id, meta, fetch_status)

    local_info = fetch_status.get("kpis", {}).get(kpi_id)
    if not local_info:
        log(f"[CHECK] {kpi_id}: no previous data → fetch now")
        return True

    local_date = local_info.get("source_date")
    if not source_date or not local_date or local_date == "Unknown":
        log(f"[CHECK] {kpi_id}: missing or unknown date → fetch now")
        return True

    try:
        l = datetime.fromisoformat(local_date.replace("Z", "+00:00"))
        r = datetime.fromisoformat(source_date.replace("Z", "+00:00"))
        newer = r > l
        log(f"[CHECK] {kpi_id}: remote={r.date()} local={l.date()} → {'fetch' if newer else 'skip'}")
        return newer
    except Exception as e:
        log(f"[WARN] {kpi_id}: date comparison failed ({e}) → fetch")
        return True

# ----------------------------------------------------------------------
# 🧩 Hilfsfunktionen für World Bank Download
# ----------------------------------------------------------------------
def download_worldbank_zip(indicator_code: str, purpose: str) -> Optional[bytes]:
    """Download the ZIP package for a World Bank indicator with retries."""

    url = f"https://api.worldbank.org/v2/en/indicator/{indicator_code}?downloadformat=csv"
    response = worldbank_request(
        url,
        timeout=60,
        headers=WORLD_BANK_ZIP_HEADERS,
        label=purpose,
        attempts=4,
        wait_base=4,
    )

    if response and response.status_code == 200 and response.content[:2] == b"PK":
        return response.content

    if response is None:
        log(f"[ERR] {purpose}: request failed (no response)")
    else:
        log(f"[ERR] {purpose}: HTTP {response.status_code}")
    return None


def fetch_worldbank_series_via_zip(indicator_code: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Fallback: parse the World Bank CSV ZIP to reconstruct the series."""

    zip_bytes = download_worldbank_zip(indicator_code, f"WorldBank ZIP {indicator_code}")
    if not zip_bytes:
        return [], None

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            data_csv = next(
                (
                    name
                    for name in zf.namelist()
                    if name.lower().endswith(".csv")
                    and "metadata" not in name.lower()
                    and "api" in name.lower()
                ),
                None,
            )

            if not data_csv:
                data_csv = next(
                    (
                        name
                        for name in zf.namelist()
                        if name.lower().endswith(".csv") and "metadata" not in name.lower()
                    ),
                    None,
                )

            if not data_csv:
                log(f"[WARN] WorldBank {indicator_code}: ZIP fallback missing data CSV")
                return [], None

            raw_csv = zf.read(data_csv).decode("utf-8-sig", errors="replace")
    except Exception as exc:
        log(f"[WARN] WorldBank {indicator_code}: could not parse ZIP fallback ({exc})")
        return [], None

    stream = io.StringIO(raw_csv)
    reader = csv.reader(stream)
    header: Optional[List[str]] = None
    fallback_date: Optional[str] = None

    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue

        if len(row) >= 2 and "last updated date" in row[0].lower():
            candidate = row[1].strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", candidate):
                fallback_date = candidate + "T00:00:00Z"

        if len(row) >= 4 and row[0].strip() == "Country Name" and row[1].strip() == "Country Code":
            header = row
            break

    if header is None:
        log(f"[WARN] WorldBank {indicator_code}: ZIP fallback missing header row")
        return [], fallback_date

    data_rows = list(reader)

    year_columns = [
        (idx, col.strip())
        for idx, col in enumerate(header)
        if idx >= 4 and re.match(r"^\d{4}$", col or "")
    ]

    series: List[Dict[str, Any]] = []
    for row in data_rows:
        if not row or len(row) < 4:
            continue

        country_name = row[0].strip()
        iso3 = row[1].strip()
        if not country_name:
            continue

        for idx, year in year_columns:
            if idx >= len(row):
                continue
            value = safe_float(row[idx])
            if value is None:
                continue

            series.append(
                {
                    "country": {"value": country_name},
                    "countryiso3code": iso3,
                    "date": year,
                    "value": value,
                }
            )

    return series, fallback_date


def fetch_worldbank_series(indicator_code: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Ruft einen vollständigen Zeitverlauf eines World Bank-Indikators ab.
    Gibt eine Liste aus dicts zurück, jeweils mit 'country', 'date', 'value'.
    Liefert zusätzlich ein mögliches Änderungsdatum aus ZIP-Fallbacks.
    Integriert automatischen Retry mit Backoff bei HTTP 429 (Rate Limit).
    """
    base_url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=20000"

    json_response = worldbank_request(
        base_url,
        timeout=60,
        headers=WORLD_BANK_HEADERS,
        label=f"WorldBank {indicator_code}",
        attempts=5,
        wait_base=5,
    )

    if json_response and json_response.status_code == 200:
        data = json_response.json()
        if not isinstance(data, list) or len(data) < 2:
            log(f"[WARN] WorldBank {indicator_code}: unexpected JSON format")
        else:
            series = data[1]
            if isinstance(series, list):
                return series, None
            log(f"[WARN] WorldBank {indicator_code}: series not list")

    else:
        if json_response is None:
            log(f"[WARN] WorldBank {indicator_code}: JSON endpoint unreachable after retries")
        else:
            log(f"[WARN] WorldBank {indicator_code}: JSON endpoint returned HTTP {json_response.status_code}")

    # --- ZIP-Fallback ---
    fallback_rows, fallback_date = fetch_worldbank_series_via_zip(indicator_code)
    if fallback_rows:
        log(
            f"[FALLBACK] WorldBank {indicator_code}: using ZIP data ({len(fallback_rows)} rows)"
        )
        return fallback_rows, fallback_date

    log(f"[FAIL] WorldBank {indicator_code}: all fetch attempts failed")
    return [], None


def extract_worldbank_date(zip_bytes: bytes) -> Optional[str]:
    """
    Extrahiert das Änderungsdatum aus der ZIP-Datei der World Bank (falls vorhanden).
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            info = next(iter(zf.infolist()), None)
            if info:
                dt = datetime(*info.date_time)
                return dt.strftime("%Y-%m-%dT00:00:00Z")
    except Exception as e:
        log(f"[WARN] extract_worldbank_date failed: {e}")
    return None


# ----------------------------------------------------------------------
# 🌐 World Bank Data360 Fetcher
# ----------------------------------------------------------------------
def fetch_data360_indicator(indicator_id: str, meta: dict = None) -> List[Dict[str, Any]]:
    """Fetch an indicator from the World Bank Data360 API with pagination. meta (KPI-Metadaten) wird für Fallback-URL benötigt."""

    import pandas as pd, os, requests
    # Debug-Ausgabe entfernt
    records: List[Dict[str, Any]] = []
    # --- 1. Try Data360 API fetch with pagination ---
    if meta and meta.get("database_id") and meta.get("source_code"):
        api_url = "https://data360api.worldbank.org/data360/data"
        params = {
            "DATABASE_ID": meta["database_id"],
            "INDICATOR": meta["source_code"]
        }
        skip = 0
        page_size = 1000
        total_fetched = 0
        try:
            # Load country mappings for ISO code resolution
            try:
                with open(os.path.join(META_DIR, "country_mappings.json"), encoding="utf-8") as f:
                    country_mappings = json.load(f)
            except Exception as e:
                log(f"[ERR] Could not load country_mappings.json: {e}")
                country_mappings = {}

            while True:
                paged_params = params.copy()
                paged_params["skip"] = skip
                r = requests.get(api_url, params=paged_params, timeout=30)
                # Debug-Ausgabe entfernt
                if r.status_code != 200:
                    log(f"[ERR] Data360 API fetch failed: {r.status_code} {r.text}")
                    break
                data = r.json()
                api_values = data.get("value", [])
                # Debug-Ausgabe entfernt
                if not api_values:
                    break
                for i, row in enumerate(api_values):
                    iso_code = row.get("REF_AREA")
                    cname = None
                    if iso_code:
                        cname = country_mappings.get(iso_code, None)
                        # Debug-Ausgabe entfernt
                    if not cname:
                        cname = row.get("REF_AREA_LABEL") or row.get("country")
                        # Debug-Ausgabe entfernt
                    year = row.get("TIME_PERIOD")
                    val = row.get("OBS_VALUE")
                    if not cname or not year or val is None:
                        continue
                    try:
                        y = int(year)
                        v = float(val)
                        records.append({"country": cname, "year": y, "value": v, "REF_AREA": iso_code})
                    except Exception:
                        continue
                total_fetched += len(api_values)
                if len(api_values) < page_size:
                    break
                skip += page_size
            if records:
                return records
            else:
                pass
        except Exception as e:
            log(f"[ERR] Data360 API request failed: {e}")
    # --- 2. Fallback to CSV (local or remote) ---
    if meta and meta.get("source_code"):
        local_path = os.path.join(os.path.dirname(__file__), "source_raw", f"{meta['source_code']}.csv")
        if os.path.exists(local_path):
            url = local_path
            log(f"[Data360] using local test file {url}")
        elif meta.get("source"):
            url = f"{meta['source'].rstrip('/')}/{meta['source_code']}.csv"
            log(f"[Data360] trying remote CSV {url}")
        else:
            log(f"[ERR] Data360: missing meta/source for {indicator_id}")
            return records
        try:
            df = pd.read_csv(url)
            # Debug-Ausgabe entfernt
        except Exception as e:
            log(f"[ERR] Data360 CSV failed to load {url}: {e}")
            return records
        # Normalize columns
        df.columns = [c.strip().lower() for c in df.columns]
        cols = df.columns.tolist()
        # Data360 narrow layout (REF_AREA, TIME_PERIOD, OBS_VALUE, REF_AREA_LABEL)
        iso_col = next((c for c in cols if c in ("ref_area", "refarea")), None)
        time_col = next((c for c in cols if c in ("time_period", "timeperiod")), None)
        obs_col = next((c for c in cols if c in ("obs_value", "obsvalue", "value", "score")), None)
        label_col = next((c for c in cols if c in ("ref_area_label", "country", "entity")), None)
        if iso_col and time_col and obs_col:
            for _, row in df.iterrows():
                iso = str(row.get(iso_col) or "").strip()
                cname = str(row.get(label_col) or iso or "").strip()
                year = row.get(time_col)
                val = row.get(obs_col)
                if not cname or year in (None, "") or val in (None, ""):
                    continue
                try:
                    y = int(float(year))
                    v = float(val)
                    records.append({"country": cname, "year": y, "value": v, "REF_AREA": iso})
                except Exception:
                    continue
            if records:
                return records
        # Wide-to-long transformation: years as columns
        # Heuristic: find country column, then all year columns
        country_col = next((c for c in cols if c in ("country", "ref_area_label", "ref_area", "entity")), None)
        year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
        if country_col and year_cols:
            for _, row in df.iterrows():
                cname = str(row.get(country_col) or "").strip()
                if not cname:
                    continue
                for ycol in year_cols:
                    v = row.get(ycol)
                    if v is None or v == "":
                        continue
                    try:
                        y = int(ycol)
                        v = float(v)
                        records.append({"country": cname, "year": y, "value": v})
                    except Exception:
                        continue
            return records
        # Fallback: try to find country/year/value columns heuristically
        year_col = next((c for c in cols if "year" in c), None)
        value_col = next((c for c in cols if "score" in c or "value" in c), None)
        if country_col and year_col and value_col:
            for _, r in df.iterrows():
                cname = str(r.get(country_col) or "").strip()
                y = r.get(year_col)
                v = r.get(value_col)
                if not cname or y is None or v is None:
                    continue
                try:
                    y = int(float(y))
                    v = float(v)
                    records.append({"country": cname, "year": y, "value": v})
                except Exception:
                    continue
            return records
        else:
            log(f"[ERR] Data360 CSV: columns not found in {url}")
    else:
        log(f"[ERR] Data360: missing meta/source_code for {indicator_id}")
    return records


# ----------------------------------------------------------------------
# 🌍 World Bank Fetch (inkl. Heuristik & Meta-Sync)
# ----------------------------------------------------------------------
def process_worldbank(kpi_id, meta, countries, c_index, a_index, pending, stats):
    """Verarbeitet einen einzelnen WorldBank-Indikator (inkl. Heuristik für source_date & data_year)."""
    code = meta.get("source_code") or meta.get("code")
    if not code:
        keep_or_dummy(kpi_id, "missing source_code", stats, output_dir=meta.get('output_dir', DATA_DIR))
        return

    # === 1️⃣ Quelle abfragen ===
    source_date = meta.get("_discovered_source_date") or get_source_date_from_worldbank(code)
    
    # === 🧩 Erweiterung: Falls kein valides Datum aus API → ZIP prüfen ===
    if not source_date or source_date in ("Unknown", ""):
        try:
            zip_url = f"https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"
            r_zip = requests.get(zip_url, timeout=30, headers=WORLD_BANK_ZIP_HEADERS)
            if r_zip.status_code == 200:
                zip_date = extract_worldbank_date(r_zip.content)
                if zip_date:
                    source_date = zip_date
                    log(f"[META] WorldBank {code} → date accessed {zip_date} (from ZIP metadata)")
        except Exception as e:
            log(f"[WARN] WorldBank ZIP date extract failed for {code}: {e}")
     

    rows, fallback_source_date = fetch_worldbank_series(code)
    # Debug: Anzahl und Beispiel der rohen Daten
    log(f"[DEBUG] WorldBank {kpi_id}: fetched {len(rows)} raw rows", level="info")
    if rows:
        log(f"[DEBUG] WorldBank {kpi_id}: first raw row: {json.dumps(rows[0], ensure_ascii=False)[:500]}", level="info")
        if len(rows) > 1:
            log(f"[DEBUG] WorldBank {kpi_id}: second raw row: {json.dumps(rows[1], ensure_ascii=False)[:500]}", level="info")
    if not rows:
        keep_or_dummy(kpi_id, f"WorldBank fetch failed ({code})", stats, output_dir=meta.get('output_dir', DATA_DIR))
        return

    out = []
    all_years = []

    # === 2️⃣ Daten normalisieren ===
    for row in rows:
        val = row.get("value")
        if val is None:
            continue
        cname = (row.get("country") or {}).get("value") or row.get("countryiso3code") or ""
        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon:
            continue
        try:
            year = int(row.get("date"))
            all_years.append(year)
            out.append({
                "country": canon,
                "iso2": "",
                "year": year,
                "value": float(val)
            })
        except Exception:
            continue

    # Debug: Anzahl und Beispiel der gefilterten Daten
    log(f"[DEBUG] WorldBank {kpi_id}: {len(out)} rows after mapping/filtering", level="info")
    if out:
        log(f"[DEBUG] WorldBank {kpi_id}: first mapped row: {json.dumps(out[0], ensure_ascii=False)[:500]}", level="info")
        if len(out) > 1:
            log(f"[DEBUG] WorldBank {kpi_id}: second mapped row: {json.dumps(out[1], ensure_ascii=False)[:500]}", level="info")

    # === 3️⃣ Heuristik: falls source_date generisch oder unbekannt, ersetze durch jüngstes Jahr ===
    latest_year = max(all_years) if all_years else None
    if (not source_date or source_date == "Unknown") and fallback_source_date:
        source_date = fallback_source_date
        log(f"[META] WorldBank {code} → date inferred from ZIP data {source_date}")

    # ✅ Nur heuristisch, wenn wirklich KEIN Datum gefunden wurde
    if (not source_date or source_date == "Unknown") and latest_year:
        source_date = f"{latest_year}-01-01T00:00:00Z"
        log(f"[HEUR] WorldBank {kpi_id} → inferred source_date {source_date}")

    # === 4️⃣ Speichern ===
    if out:
        out = maybe_invert_records(kpi_id, meta, out)
        save_records(kpi_id, out, stats, output_dir=meta.get('output_dir', DATA_DIR))
        stats["wb_success"] += 1
        stats["saved_records"] += len(out)
        log(f"[OK] WorldBank KPI saved: {kpi_id} ({len(out)} rows, last updated {source_date})")

        # 🔹 Meta-Felder nur intern für fetch_status.json
        meta["_latest_year"] = latest_year
        meta["_source_date"] = source_date

        # 🔹 Statt _updated_now → zentrale Laufzeit-Sammelliste
        stats.setdefault("updated_kpis", set()).add(kpi_id)

    else:
        keep_or_dummy(kpi_id, f"WorldBank empty {code}", stats, output_dir=meta.get('output_dir', DATA_DIR))
# ----------------------------------------------------------------------
# 📊 CSV Fetch (smart) – inkl. Änderungsprüfung & Natural Disasters Sonderfall
# ----------------------------------------------------------------------
def process_csv(kpi_id, meta, countries, c_index, a_index, pending, stats, output_dir=None):
    import hashlib, pandas as pd, re

    csv_name = meta.get("source_code") or meta.get("code") or f"{kpi_id}.csv"
    path = os.path.join(SOURCE_CSV_DIR, csv_name)
    if not os.path.exists(path):
        keep_or_dummy(kpi_id, f"CSV missing {csv_name}", stats, output_dir=output_dir)
        return


    if output_dir is None:
        output_dir = DATA_DIR
    json_path = os.path.join(output_dir, f"{kpi_id}.json")
    hash_root = PENDING_DIR if Path(output_dir).resolve() == DATA_DIR.resolve() else Path(output_dir) / "pending"
    hash_root.mkdir(parents=True, exist_ok=True)
    hash_path = os.path.join(hash_root, f"{kpi_id}.md5")

    # In test mode, always overwrite (skip version/hash check)
    is_test_mode = (str(output_dir).endswith(os.sep + "test") or str(output_dir).endswith("/test") or str(output_dir).endswith("\\test"))

    def file_md5(p):
        h = hashlib.md5()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    csv_mtime, csv_hash = os.path.getmtime(path), file_md5(path)

    # 🔹 Änderungsprüfung (skip in test mode)
    if not is_test_mode:
        if os.path.exists(json_path) and os.path.exists(hash_path):
            try:
                old_hash = open(hash_path).read().strip()
                json_mtime = os.path.getmtime(json_path)
                if csv_mtime <= json_mtime and csv_hash == old_hash:
                    log(f"[⏸️] {kpi_id} – CSV unchanged (hash & mtime match)")
                    mark_skip(stats, "CSV unchanged (hash & mtime)")
                    return
            except Exception as e:
                log(f"[WARN] Hash check failed for {kpi_id}: {e}")

    # 🔹 CSV laden und normalisieren
    try:
        df = pd.read_csv(path)
    except Exception as e:
        log(f"[ERR] Failed to read CSV for {kpi_id}: {e}")
        keep_or_dummy(kpi_id, f"CSV read error {csv_name}", stats, output_dir=output_dir)
        return

    if len(df.columns) == 1 and "," in df.columns[0]:
        new_cols = [c.strip() for c in df.columns[0].split(",")]
        df = df[df.columns[0]].astype(str).str.split(",", expand=True)
        df.columns = new_cols
        log(f"[FIX] {kpi_id}: single-column CSV auto-split into {len(new_cols)} columns")

    df.columns = [c.strip().lower() for c in df.columns]
    cols = df.columns.tolist()

    # Sonderfall Natural Disasters
    if not {"country", "year", "value"}.issubset(set(cols)):
        if kpi_id == "number_of_recorded_natural_disasters":
            try:
                if "total disasters" in cols:
                    df["value"] = df["total disasters"]
                else:
                    numeric_cols = [
                        c for c in df.columns
                        if c not in ("entity", "code", "year") and df[c].dtype != "object"
                    ]
                    df["value"] = df[numeric_cols].sum(axis=1)
                df = df.rename(columns={"entity": "country"})[["country", "year", "value"]]
                log(f"🔄 Auto-normalized Natural Disasters CSV ({len(df)} rows)")
            except Exception as e:
                log(f"[WARN] Natural Disasters CSV normalization failed: {e}")
                keep_or_dummy(kpi_id, "Natural Disasters normalization failed", stats, output_dir=output_dir)
                return
        else:
            log(f"[WARN] CSV format unknown for {kpi_id} → {csv_name}")
            keep_or_dummy(kpi_id, f"Unknown CSV format {csv_name}", stats, output_dir=output_dir)
            return

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    out, latest_year = [], None
    for _, r in df.iterrows():
        cname = str(r.get("country") or "").strip()
        if not cname:
            continue
        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon:
            continue
        y, v = r.get("year"), safe_float(r.get("value"))
        if not y or v is None:
            continue
        try:
            y = int(float(y))
            latest_year = max(latest_year or y, y)
            out.append({"country": canon, "iso2": r.get("iso2", ""), "year": y, "value": v})
        except Exception:
            continue

    # 🧠 Falls kein Jahr in der CSV-Spalte erkannt wurde, im Text suchen
    if not latest_year:
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            found = re.findall(r"20\d{2}", txt)
            if found:
                valid_years = [int(y) for y in found if 2000 <= int(y) <= datetime.now().year]
                if valid_years:
                    latest_year = max(valid_years)
                    log(f"[TXT] {kpi_id}: detected latest_year={latest_year} from CSV text")
        except Exception as e:
            log(f"[WARN] Could not detect year from CSV text for {kpi_id}: {e}")

    # Fallback: heuristisch aus year-Spalte
    if not latest_year:
        try:
            latest_year = int(float(df["year"].dropna().max()))
            log(f"[HEUR] {kpi_id}: inferred latest_year = {latest_year}")
        except Exception:
            latest_year = None

    # 🔹 Source-Date setzen
    source_date = f"{latest_year}-01-01T00:00:00Z" if latest_year else "Unknown"

    if out:
        out = maybe_invert_records(kpi_id, meta, out)
        save_records(kpi_id, out, stats, output_dir=output_dir)
        stats["csv_success"] += 1
        stats["saved_records"] += len(out)
        meta["_source_date"], meta["_latest_year"] = source_date, latest_year
        stats.setdefault("updated_kpis", set()).add(kpi_id)
        log(f"[OK] CSV KPI saved: {kpi_id} ({len(out)} rows, last updated {source_date})")

        try:
            open(hash_path, "w").write(csv_hash)
        except Exception as e:
            log(f"[WARN] Could not write hash for {kpi_id}: {e}")
    else:
        keep_or_dummy(kpi_id, f"CSV empty {csv_name}", stats, output_dir=output_dir)

    return latest_year

# ----------------------------------------------------------------------
# 🧭 OWID Fetch (inkl. Source-Date Detection & Natural Disaster World-Fix)
# ----------------------------------------------------------------------
def get_source_date_from_owid(url: str) -> Optional[str]:
    """Liest das Aktualisierungsdatum aus der OWID-Metadatei (mehrere mögliche Formate)."""
    try:
        base_id = url.split("/grapher/")[-1].split("?")[0]
        meta_url = f"https://ourworldindata.org/grapher/data/metadata/{base_id}.json"
        r = requests.get(meta_url, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        
        # ✅ NEU: Suche direkt nach "columns.<KPI>.lastUpdated"
        try:
            if "columns" in data and isinstance(data["columns"], dict):
                first_key = next(iter(data["columns"].keys()), None)
                if first_key and "lastUpdated" in data["columns"][first_key]:
                    d = data["columns"][first_key]["lastUpdated"]
                    log(f"[META] OWID {base_id} → columns.lastUpdated {d}")
                    return d
        except Exception as e:
            log(f"[WARN] OWID columns.lastUpdated parse failed for {base_id}: {e}")

        # Alternative Keys prüfen
        for key in ["lastUpdated", "last_updated", "updatedAt", "lastUpdatedAtSource", "dataEditedAt", "publishedAt"]:
            if key in data and data[key]:
                d = str(data[key]).strip()
                log(f"[META] OWID {base_id} last updated: {d}")
                return d

        # Fallback – neue Struktur (variables → dict)
        if "data" in data and "variables" in data["data"]:
            var_data = list(data["data"]["variables"].values())[0]
            for key in ["lastUpdated", "updatedAt", "dataEditedAt"]:
                if key in var_data and var_data[key]:
                    d = str(var_data[key]).strip()
                    log(f"[META] OWID {base_id} variable updated: {d}")
                    return d
    except Exception as e:
        log(f"[WARN] Could not get OWID source_date: {e}")
    return None


def process_owid(kpi_id, meta, countries, c_index, a_index, pending, stats, output_dir=None):
    """Verarbeitet OWID-CSV-ähnliche Daten und speichert sie lokal."""
    output_dir = output_dir or DATA_DIR
    source_code = meta.get("source_code")
    if not source_code:
        keep_or_dummy(kpi_id, "missing source_code", stats, output_dir=output_dir)
        return

    url = f"https://ourworldindata.org/grapher/{source_code}"
    source_date = meta.get("_discovered_source_date") or get_source_date_from_owid(url)

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        text = resp.text
    except Exception as e:
        log(f"[ERR] OWID fetch failed for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"OWID fetch failed {source_code}", stats, output_dir=output_dir)
        return

    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not {"Entity", "Code", "Year"}.issubset(set(cols)):
        log(f"[WARN] OWID format unknown → {source_code}")
        keep_or_dummy(kpi_id, f"OWID format unknown {source_code}", stats, output_dir=output_dir)
        return

    var_cols = [c for c in cols if c not in ("Entity", "Code", "Year")]
    if not var_cols:
        keep_or_dummy(kpi_id, f"OWID no data column {source_code}", stats, output_dir=output_dir)
        return

    var = var_cols[0]
    out = []

    for row in reader:
        cname = (row.get("Entity") or "").strip()
        if kpi_id == "number_of_recorded_natural_disasters" and cname.lower() in {
            "all disasters", "all disasters (total)", "total disasters"
        }:
            cname = "World"

        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon and cname.lower() == "world":
            canon = "World"

        if not canon:
            continue

        year = row.get("Year")
        val = safe_float(row.get(var))
        if val is None or not year:
            continue
        try:
            y = int(float(year))
        except Exception:
            continue

        out.append({
            "country": canon,
            "iso2": "OWID_WRL" if canon == "World" else row.get("Code", ""),
            "year": y,
            "value": val
        })

    # --- Heuristik: OWID Datum aus Daten ableiten, falls unbekannt ---
    latest_year = None
    if not source_date or source_date == "Unknown":
        try:
            years = [int(r["year"]) for r in out if "year" in r and str(r["year"]).isdigit()]
            if years:
                latest_year = max(years)
                source_date = f"{latest_year}-01-01"
                log(f"[HEUR] OWID {kpi_id} → inferred source_date {source_date}")
            else:
                log(f"[HEUR] OWID {kpi_id} → no valid years found")
                source_date = "Unknown"
        except Exception as e:
            log(f"[HEUR] OWID {kpi_id} → failed to infer year: {e}")
            source_date = "Unknown"

    # --- Speichern ---
    if out:
        out = maybe_invert_records(kpi_id, meta, out)
        save_records(kpi_id, out, stats, output_dir=output_dir)
        stats["owid_success"] += 1
        stats["saved_records"] += len(out)

        # 🔹 Meta-Felder für fetch_status.json
        meta["_source_date"] = source_date
        if not latest_year:
            latest_year = max([r["year"] for r in out if "year" in r], default=None)
        meta["_latest_year"] = latest_year

        # ✅ Korrektur, falls Prognosejahr > aktuelles Jahr
        from datetime import datetime
        current_year = datetime.now().year
        if latest_year and latest_year > current_year:
            log(f"[FIX] {kpi_id}: future year {latest_year} detected → correcting to {current_year}")
            latest_year = current_year
            meta["_latest_year"] = current_year
            meta["_source_date"] = f"{current_year}-01-01"

        # ✅ NEU: keine Manipulation von available_kpis.json mehr
        stats.setdefault("updated_kpis", set()).add(kpi_id)
        log(f"[OK] OWID KPI saved: {kpi_id} ({len(out)} rows, last updated {meta['_source_date']})")

    else:
        keep_or_dummy(kpi_id, f"OWID empty {source_code}", stats, output_dir=output_dir)


# ----------------------------------------------------------------------
# 💰 IMF WEO Fetch
# ----------------------------------------------------------------------
def _extract_imf_source_date(compact: Dict[str, Any], series: Dict[str, Any]) -> Optional[str]:
    for container in (series, compact):
        if isinstance(container, dict):
            candidate = container.get("@TIME_FORMAT") or container.get("TIME_FORMAT")
            if candidate:
                return str(candidate)

    header = (compact or {}).get("Header") or {}
    if isinstance(header, dict):
        for key in ("ID", "PrepareDate", "Prepared", "EXTRACTED", "EXR_DATE"):
            candidate = header.get(key) or header.get(key.lower()) if hasattr(header, "get") else None
            if candidate:
                m = re.search(r"(19|20)\d{2}", str(candidate))
                if m:
                    return f"{m.group(0)}-01-01"

    return None


def fetch_imf_gross_debt(countries, c_index, a_index, pending, stats):
    """Fetch General Government Gross Debt (% of GDP) from IMF WEO."""

    base_url = "https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/WEO/{indicator}.{iso3}"
    records: List[Dict[str, Any]] = []
    latest_year: Optional[int] = None
    detected_source_date: Optional[str] = None

    total = 0
    success = 0

    session = requests.Session()

    for cname, meta in (countries or {}).items():
        iso3 = meta.get("iso3") or meta.get("iso_a3") or meta.get("alpha3")
        if not iso3:
            continue

        total += 1
        url = base_url.format(indicator="GGXWDG_NGDP", iso3=iso3)

        response = None
        for attempt in range(1, 4):
            try:
                response = session.get(url, params={"startPeriod": "1990"}, timeout=45)
            except Exception as exc:  # pragma: no cover - network/runtime safeguard
                if attempt == 3:
                    log(f"[ERR] IMF request failed for {iso3} after retries: {exc}", "error")
                    response = None
                else:
                    wait = 3 * attempt
                    log(f"[WARN] IMF request error for {iso3}: {exc} → retry in {wait}s ({attempt}/3)")
                    time.sleep(wait)
                continue

            if response.status_code == 200:
                break

            retryable = response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500
            if not retryable or attempt == 3:
                snippet = (response.text or "")[:160] if response is not None else ""
                log(
                    f"[WARN] IMF HTTP {response.status_code} for {iso3} (attempt {attempt})"
                    + (f" – body: {snippet}" if snippet else "")
                )
                break

            wait = 3 * attempt
            log(f"[WARN] IMF HTTP {response.status_code} for {iso3} → retry in {wait}s ({attempt}/3)")
            time.sleep(wait)

        if not response or response.status_code != 200:
            continue

        try:
            payload = response.json()
        except Exception as exc:
            log(f"[WARN] IMF JSON decode failed for {iso3}: {exc}")
            continue

        compact = payload.get("CompactData") or payload.get("compactdata") or {}
        dataset = compact.get("DataSet") or compact.get("dataset") or {}
        series_block = dataset.get("Series") or dataset.get("series")
        if not series_block:
            log(f"[WARN] IMF data missing series for {iso3}")
            continue

        series_list = series_block if isinstance(series_block, list) else [series_block]
        for series in series_list:
            if not isinstance(series, dict):
                continue

            obs_list = series.get("Obs") or series.get("obs") or []
            if isinstance(obs_list, dict):
                obs_list = [obs_list]

            if not obs_list:
                log(f"[WARN] IMF no observations for {iso3}")
                continue

            if not detected_source_date:
                detected_source_date = _extract_imf_source_date(compact, series)

            ref_name = (
                series.get("@REF_AREA_LABEL")
                or series.get("@REF_AREA_LB")
                or series.get("@REF_AREA")
                or iso3
            )
            canon = canonicalize_country(ref_name, c_index, a_index, countries, pending, stats)
            if not canon:
                continue

            iso3_code = series.get("@REF_AREA") or iso3
            for obs in obs_list:
                value = safe_float(obs.get("@OBS_VALUE") or obs.get("OBS_VALUE"))
                if value is None:
                    continue

                year = obs.get("@TIME_PERIOD") or obs.get("TIME_PERIOD")
                if not year:
                    continue
                try:
                    year_int = int(float(year))
                except Exception:
                    continue

                latest_year = max(latest_year or year_int, year_int)
                records.append(
                    {"country": canon, "iso3": iso3_code, "year": year_int, "value": float(value)}
                )

            success += 1

    log(
        f"[INFO] IMF gross debt fetched for {success}/{total} countries → {len(records)} records"
    )

    return records, latest_year, detected_source_date


def _find_column(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    for col in df.columns:
        norm = re.sub(r"\s+", "_", str(col).strip().lower())
        for pat in patterns:
            if pat in norm:
                return col
    return None


def _clean_imf_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"n/a", "na", "-", "--", "...", ""}:
        return None
    return safe_float(text)


def fetch_imf_bulk(
    imf_kpis: List[Dict[str, Any]],
    countries: Dict[str, Any],
    c_index,
    a_index,
    pending,
    fetch_status: Dict[str, Any],
    stats: Dict[str, Any],
    force_all_updates: bool,
):
    if not imf_kpis:
        return

    log(f"[FETCH] IMF bulk import start for {len(imf_kpis)} KPIs")

    csv_path = SCRIPT_DIR / "source_raw/IMF_Dataset.csv"
    legacy_csv_path = SCRIPT_DIR / "source_csv/IMF_Dataset.csv"
    legacy_excel_path = SCRIPT_DIR / "source_csv/imf/WEO_latest.xlsx"

    if csv_path.exists():
        load_path = csv_path
    elif legacy_csv_path.exists():
        load_path = legacy_csv_path
    elif legacy_excel_path.exists():
        load_path = legacy_excel_path
    else:
        log(
            "[ERR] IMF bulk file missing: "
            f"{csv_path} (legacy: {legacy_csv_path} / {legacy_excel_path})"
        )
        for meta in imf_kpis:
            kpi_id = resolve_kpi_id(meta)
            keep_or_dummy(kpi_id, "IMF bulk file missing", stats, output_dir=meta.get("output_dir", DATA_DIR))
        return

    try:
        if load_path.suffix.lower() in {".xls", ".xlsx"}:
            df = pd.read_excel(load_path, sheet_name=0)
        else:
            df = pd.read_csv(load_path, low_memory=False)
    except Exception as exc:
        log(f"[ERR] IMF bulk file load failed: {exc}")
        for meta in imf_kpis:
            kpi_id = resolve_kpi_id(meta)
            keep_or_dummy(kpi_id, "IMF bulk load failed", stats, output_dir=meta.get("output_dir", DATA_DIR))
        return

    subject_col = _find_column(df, ["weo_subject_code", "subject_code", "indicator", "INDICATOR"])
    country_col = _find_column(df, ["country", "weo_country", "country_name", "COUNTRY"])
    iso_col = _find_column(df, ["iso", "iso_code", "iso3"])

    if not subject_col or not country_col:
        header_row_idx = None
        header_candidates = {"weo subject code", "weo_subject_code", "subject code", "subject_code", "indicator", "INDICATOR"}
        for idx in range(min(len(df), 15)):
            row = df.iloc[idx]
            joined = " ".join(str(v) for v in row.values if pd.notna(v)).lower()
            if any(h in joined for h in header_candidates):
                header_row_idx = idx
                break

        if header_row_idx is not None:
            try:
                df.columns = [str(c).strip() for c in df.iloc[header_row_idx].values]
                df = df.drop(index=list(range(header_row_idx + 1)))
                df = df.reset_index(drop=True)
                subject_col = _find_column(df, ["weo_subject_code", "subject_code", "indicator", "INDICATOR"])
                country_col = _find_column(df, ["country", "weo_country", "country_name", "COUNTRY"])
                iso_col = _find_column(df, ["iso", "iso_code", "iso3"])
                log(f"[INFO] IMF bulk header realigned using row {header_row_idx}")
            except Exception as exc:
                log(f"[WARN] IMF bulk header realign failed: {exc}")

        if not subject_col or not country_col:
            log("[ERR] IMF bulk Excel missing required columns (subject or country)")
            for meta in imf_kpis:
                kpi_id = resolve_kpi_id(meta)
                keep_or_dummy(kpi_id, "IMF bulk columns missing", stats, output_dir=meta.get("output_dir", DATA_DIR))
            return

    year_cols = [col for col in df.columns if re.fullmatch(r"\d{4}", str(col).strip())]
    if not year_cols:
        log("[WARN] IMF bulk Excel contains no year columns")

    filename_str = load_path.name
    m = re.search(r"(20\d{2})", filename_str)
    detected_source_date = m.group(1) if m else str(datetime.now().year)

    for meta in imf_kpis:
        kpi_id = resolve_kpi_id(meta)
        source_code = (meta.get("source_code") or "").strip()
        output_dir = meta.get("output_dir", DATA_DIR)
        updated_set = stats.setdefault("updated_kpis", set())
        already_marked = kpi_id in updated_set

        if not source_code:
            log(f"[WARN] IMF KPI {kpi_id} missing source_code")
            keep_or_dummy(kpi_id, "IMF missing source_code", stats, output_dir=output_dir)
            continue

        if not force_all_updates and not should_fetch(
            kpi_id, "imf", detected_source_date, meta, fetch_status
        ):
            mark_skip(stats, "Remote data unchanged")
            log(f"[⏸️] {kpi_id} – IMF bulk unchanged ({detected_source_date})")
            continue

        subset = df[df[subject_col] == source_code]
        records: List[Dict[str, Any]] = []
        latest_year = None

        if subset.empty:
            log(f"[WARN] IMF bulk: no rows for {source_code} ({kpi_id})")
        else:
            for _, row in subset.iterrows():
                cname = str(row.get(country_col) or "").strip()
                if not cname:
                    continue

                canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
                if not canon:
                    log(f"[WARN] IMF country unmapped: {cname}")
                    continue

                iso3_raw = str(row.get(iso_col) or "").strip() if iso_col else ""
                iso3_code = resolve_iso3(canon, countries, fallback=iso3_raw)

                for col in year_cols:
                    value = _clean_imf_value(row.get(col))
                    if value is None:
                        continue

                    try:
                        year_int = int(str(col))
                    except Exception:
                        continue

                    latest_year = max(latest_year or year_int, year_int)
                    records.append(
                        {
                            "country": canon,
                            "iso3": iso3_code,
                            "year": year_int,
                            "value": float(value),
                        }
                    )

        if records:
            save_imf_records(kpi_id, records, stats, output_dir=output_dir)
            stats["imf_success"] += 1
            stats["saved_records"] += len(records)
            stats["fetched"] += len(records)
            meta["source"] = "IMF WEO"
            meta["_latest_year"] = latest_year
            meta["_source_date"] = detected_source_date
            updated_set.add(kpi_id)
            if not already_marked:
                stats["updated"] += 1
            log(
                f"[OK] IMF bulk KPI saved: {kpi_id} ({len(records)} rows, last year {latest_year})"
            )
        else:
            save_imf_records(kpi_id, [], output_dir=output_dir)
            keep_or_dummy(kpi_id, f"IMF bulk empty {source_code}", stats, output_dir=output_dir)
            meta["_source_date"] = detected_source_date

        used_source_date = meta.get("_source_date") or detected_source_date or "Unknown"
        fetch_status.setdefault("kpis", {})[kpi_id] = {
            "source": meta.get("source") or "IMF WEO",
            "source_type": "imf",
            "source_code": source_code,
            "source_date": used_source_date,
            "data_year": meta.get("_latest_year"),
            "last_fetch": now_utc(),
        }

    log("[INFO] IMF bulk import completed")


# ----------------------------------------------------------------------
# 🕊️ UNHCR Fetch (ZIP/CSV, Encoding & Header-robust)
# ----------------------------------------------------------------------
def process_unhcr(kpi_id, meta, countries, c_index, a_index, pending, stats, output_dir=None):
    output_dir = output_dir or DATA_DIR
    def _norm_local(s): return "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))
    def _find_col(cols, *pats):
        norms = {c:_norm_local(c) for c in cols}
        for c, cn in norms.items():
            for p in pats:
                if _norm_local(p) in cn:
                    return c
        return None

    source_code = meta.get("source_code") or "population?download=true"
    url = f"https://api.unhcr.org/population/v1/{source_code}"
    safe_code = re.sub(r'[^a-zA-Z0-9._-]', '_', source_code)

    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
    except Exception as e:
        log(f"[ERR] UNHCR fetch failed for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"UNHCR fetch failed {source_code}", stats, output_dir=output_dir)
        return

    text = None
    try:
        if "zip" in (resp.headers.get("Content-Type","").lower()) or resp.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                name = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
                raw = zf.read(name)
                text = raw.decode("utf-8-sig", errors="ignore")
        else:
            text = resp.text
    except Exception as e:
        log(f"[ERR] UNHCR decode failed {source_code}: {e}")
        keep_or_dummy(kpi_id, f"UNHCR decode error {source_code}", stats, output_dir=output_dir)
        return

    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not cols:
        keep_or_dummy(kpi_id, f"UNHCR no header {source_code}", stats, output_dir=output_dir)
        return

    country_key = _find_col(cols, "country of asylum","territory of asylum","asylum")
    year_key = _find_col(cols, "year")
    value_key = _find_col(cols, meta.get("unhcr_field","refugees"))
    if not all([country_key, year_key, value_key]):
        keep_or_dummy(kpi_id, f"UNHCR unknown format {source_code}", stats, output_dir=output_dir)
        return

    out = []
    for row in reader:
        cname = (row.get(country_key) or "").strip()
        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon: continue
        y, v = row.get(year_key), safe_float(row.get(value_key))
        if not y or v is None: continue
        try:
            out.append({"country": canon, "iso2": "", "year": int(float(y)), "value": v})
        except Exception:
            continue

    if out:
        out = maybe_invert_records(kpi_id, meta, out)
        save_records(kpi_id, out, stats, output_dir=output_dir)
        stats["unhcr_success"] = stats.get("unhcr_success", 0) + 1
        stats["saved_records"] += len(out)
        stats.setdefault("updated_kpis", set()).add(kpi_id)
        log(f"[OK] UNHCR KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        keep_or_dummy(kpi_id, f"UNHCR empty {source_code}", stats, output_dir=output_dir)
# ----------------------------------------------------------------------
# 🌍 Special Fetch: Geopolitical Risk Index (Matteo Iacoviello)
# ----------------------------------------------------------------------
def fetch_geopolitical_risk_index():
    """
    Fetches the monthly Geopolitical Risk Index (GPR) from Matteo Iacoviello.
    The Excel file contains one sheet (Sheet1) with columns 'Month' (TT.MM.YYYY)
    and 'GPR'. Early rows with missing GPR values are skipped.
    Complete past years are averaged, the current year uses the latest available month.
    """
    import pandas as pd, io, requests, numpy as np
    from datetime import datetime, UTC

    url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
    kpi_name = "geopolitical_risk_index"
    file_path = os.path.join(DATA_DIR, f"{kpi_name}.json")

    log(f"[FETCH] Geopolitical Risk Index → {url}")
    try:
        # === Download Excel ===
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        # === Einlesen ===
        df = pd.read_excel(io.BytesIO(resp.content), sheet_name="Sheet1")
        df.columns = [c.strip().lower() for c in df.columns]

        if not {"month", "gpr"}.issubset(set(df.columns)):
            raise Exception(f"Unexpected columns in GPR Excel: {df.columns.tolist()}")

        # === Datum parsen (TT.MM.JJJJ) ===
        df["month"] = pd.to_datetime(df["month"], format="%d.%m.%Y", errors="coerce")
        df = df.dropna(subset=["month", "gpr"])

        # === Jahr extrahieren & numerische Werte ===
        df["year"] = df["month"].dt.year
        df["value"] = pd.to_numeric(df["gpr"], errors="coerce")
        df = df.dropna(subset=["value"])

        # === Jahresweise Aggregation ===
        current_year = datetime.now(UTC).year

        # 1️⃣ Durchschnitt für abgeschlossene Jahre
        df_past = (
            df[df["year"] < current_year]
            .groupby("year", as_index=False)["value"]
            .mean()
        )

        # 2️⃣ Für das laufende Jahr nur den letzten Monatswert
        df_current = (
            df[df["year"] == current_year]
            .sort_values("month")
            .tail(1)[["year", "value"]]
        )

        # 3️⃣ Zusammenführen
        df_annual = pd.concat([df_past, df_current], ignore_index=True)
        df_annual["value"] = df_annual["value"].round(2)
        df_annual["country"] = "World"

        # === Speichern ===
        out = df_annual[["country", "year", "value"]].to_dict(orient="records")
        write_json(file_path, out)
        log(f"✅ Saved {len(out)} GPR entries → {file_path}")

        # === fetch_status entry (return instead of writing file) ===
        status_entry = {
            "source": "https://www.matteoiacoviello.com/gpr.htm",
            "url": url,
            "source_date": datetime.now(UTC).strftime("%Y-%m-%dT00:00:00Z"),
            "data_year": int(df_annual["year"].max()),
            "last_fetch": now_utc(),
        }
        log("[OK] Special world KPI status prepared: geopolitical_risk_index (Matteo Iacoviello)")
        return status_entry
    except Exception as e:
        log(f"❌ GPR fetch failed: {e}")
        return None

# ======================================================================
# 🧩 Fetch-State Merge Utility (ergänzend zur Statuslogik)
# ======================================================================
def merge_fetch_state(updated_kpis: set):
    """
    Aktualisiert /data/fetch_state.json:
    - fügt neue oder geänderte KPIs hinzu
    - behält alte Einträge bei
    - kein Duplikat
    """
    state_path = os.path.join(DATA_DIR, "fetch_state.json")
    try:
        if os.path.exists(state_path):
            with open(state_path, "r", encoding="utf-8") as f:
                old_state = json.load(f)
        else:
            old_state = {}

        old_list = set(old_state.get("updated_kpis", []))
        merged = sorted(list(old_list.union(updated_kpis)))

        merged_state = {
            "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_kpis": merged
        }

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(merged_state, f, ensure_ascii=False, indent=2)

        log(f"[STATE] Merged {len(updated_kpis)} updated KPIs → total {len(merged)} entries.")
    except Exception as e:
        log(f"[WARN] Could not update fetch_state.json: {e}")


# ======================================================================
# 🔌 Source adapter registry
# ======================================================================
def build_adapter_registry():
    """Return the complete source registry used by the production dispatcher."""
    services = AdapterServices(
        log=log,
        get_worldbank_source_date=get_source_date_from_worldbank,
        get_owid_source_date=get_source_date_from_owid,
        process_worldbank=process_worldbank,
        process_owid=process_owid,
        process_csv=process_csv,
        process_unhcr=process_unhcr,
        fetch_data360=fetch_data360_indicator,
        canonicalize_country=canonicalize_country,
        safe_float=safe_float,
        resolve_iso2=resolve_iso2,
        save_records=save_records,
        keep_or_dummy=keep_or_dummy,
    )
    return build_builtin_adapter_registry(services)

# ======================================================================
# 🚀 Main
# ======================================================================
def main(args: argparse.Namespace) -> Dict[str, Any]:
    global ACTIVE_DATA_DIR, ALLOW_MAPPING_WRITES, LOG_FILE
    ACTIVE_DATA_DIR = TEST_DATA_DIR if args.test else DATA_DIR
    ALLOW_MAPPING_WRITES = not args.test
    LOG_FILE = str(ACTIVE_DATA_DIR / "fetch_log.txt")

    if args.force:
        # Force means "refetch regardless of freshness". It must never delete
        # the last known-good production snapshot before replacements pass.
        log("[SAFE] Force mode preserves existing data until each replacement is written successfully.")

    ensure_dirs()

    try:
        get_openai_key()
        key_status = "found"
    except ValueError as exc:
        key_status = "missing"
        log(f"[WARN] {exc}")

    log(f"[INFO] Using OPENAI_API_KEY: {key_status}")
    log("=== Fetch started ===")

    # --- Bestehenden Status laden ---
    fetch_status = load_json_file(STATUS_FILE, {"kpis": {}})

    # 🆕 Force-All-Modus: Wenn kein fetch_status.json existiert oder leer ist
    if not os.path.exists(STATUS_FILE) or not fetch_status.get("kpis"):
        log("⚠️ Kein fetch_status.json vorhanden oder leer – setze ALLE KPIs auf 'neu'.")
        fetch_status = {"kpis": {}}
    force_all_updates = force_refresh_required(args.force, fetch_status)


    stats = {
        "countries_loaded": 0, "kpis_loaded": 0, "saved_records": 0, "dummies": 0,
        "mapped_ok": 0, "mapped_drop": 0, "mapped_pending": 0, "new_pending": set(),
        "wb_success": 0, "csv_success": 0, "owid_success": 0, "unhcr_success": 0,
        "imf_success": 0, "data360_success": 0, "others_success": 0,
        "errors": 0, "skipped": 0, "skipped_breakdown": {},
        "updated": 0,                     # 🔹 NEU: zählt erfolgreiche Updates
        "updated_kpis": set(),
        "trimmed_records": 0,
        "trimmed_kpis": set(),
        "fetched": 0,
    }


    # --- Metadaten & Mapping laden ---
    countries = load_json_file(COUNTRIES_FILE, {})
    mapping   = load_json_file(COUNTRY_MAP_FILE, {})
    pending   = load_json_file(COUNTRY_PENDING_FILE, {})
    c_index, a_index = build_country_indices(countries, mapping)
    stats["countries_loaded"] = len(countries)



    raw_kpis = load_json_file(AVAILABLE_FILE, [])
    if not isinstance(raw_kpis, list):
        raise SourceContractError("KPI registry must contain an array")
    ensure_source_registry(raw_kpis)
    kpi_list = [v for v in raw_kpis if isinstance(v, dict)]
    selection = select_kpis(kpi_list, kpi=args.kpi, test_mode=args.test)
    kpi_list = list(selection.selected)
    ignored_kpis = list(selection.ignored)
    if not kpi_list:
        mode = "test mode" if args.test else "the requested selection"
        raise SourceContractError(f"No enabled KPIs matched {mode}")
    if args.kpi:
        log(f"[INFO] Single KPI mode (-k): selected {len(kpi_list)} KPI for filename='{args.kpi}'")
    if args.test:
        log(f"[INFO] Test mode enabled (-t): selected {len(kpi_list)} KPI(s) with test='*', ignored {len(ignored_kpis)} with test='o', skipping all analysis.")
        args.no_analysis = True
    stats["kpis_loaded"] = len(kpi_list)

    imf_queue: List[Dict[str, Any]] = []
    special_queue: List[Dict[str, Any]] = []
    adapter_registry = build_adapter_registry()

    # --- KPI loop: resolve plan, dispatch through the explicit registry ---
    output_dir = TEST_DATA_DIR if args.test else DATA_DIR
    for meta in kpi_list:
        meta = dict(meta)  # copy to avoid mutating global
        meta["output_dir"] = output_dir
        try:
            kpi_id = resolve_kpi_id(meta)
            source_type = (meta.get("source_type") or meta.get("type") or "").lower().strip()
            adapter = adapter_registry.get(source_type)

            if adapter.mode is AdapterMode.BATCH:
                imf_queue.append(meta)
                log(f"[DEFER] {kpi_id}: queued for {source_type} batch import")
                continue
            if adapter.mode is AdapterMode.SPECIAL:
                special_queue.append(meta)
                log(f"[DEFER] {kpi_id}: handled by the special-source stage")
                continue

            source_date = adapter.resolve_source_date(meta) or "Unknown"
            meta["_discovered_source_date"] = source_date

            # In test mode, always fetch (skip version check)
            if not args.test and not force_all_updates and not should_fetch(
                kpi_id, source_type, source_date, meta, fetch_status
            ):
                log(f"[⏸️] {kpi_id} – unchanged ({source_date})")
                mark_skip(stats, "Remote data unchanged")
                continue

            updated_set = stats.setdefault("updated_kpis", set())
            already_marked = kpi_id in updated_set
            try:
                request = AdapterRequest(
                    kpi_id=kpi_id,
                    meta=meta,
                    countries=countries,
                    country_index=c_index,
                    alias_index=a_index,
                    pending=pending,
                    stats=stats,
                    output_dir=output_dir,
                )
                result = adapter_registry.dispatch(source_type, request)
                result.apply_to(meta)

                if kpi_id in updated_set and not already_marked:
                    stats["updated"] += 1

                old_meta = fetch_status.get("kpis", {}).get(kpi_id, {})
                status = build_status_entry(
                    meta,
                    discovered_source_date=source_date,
                    previous=old_meta,
                    fetched_at=now_utc(),
                )
                fetch_status.setdefault("kpis", {})[kpi_id] = status.entry
                log(
                    f"[STATUS] {kpi_id}: stored source_date={status.source_date}, "
                    f"data_year={status.data_year}"
                )

            except Exception as e:
                stats["errors"] += 1
                keep_or_dummy(kpi_id, f"Exception: {e}", stats, output_dir=output_dir)
                log(f"[❌] {kpi_id} failed: {e}\n{traceback.format_exc()}")

        except Exception as e:
            stats["errors"] += 1
            log(f"[ERR] {meta.get('title','unknown')} failed: {e}\n{traceback.format_exc()}")

    # ---------------------------------------------------------------
    # 📊 IMF WEO Bulk Import (after OWID/WB/Data360 loops)
    # ---------------------------------------------------------------

    if imf_queue:
        try:
            fetch_imf_api(
                imf_queue,
                countries,
                c_index,
                a_index,
                pending,
                fetch_status,
                stats,
                force_all_updates,
            )
        except Exception as e:
            stats["errors"] += 1
            log(f"[ERR] IMF bulk import failed: {e}\n{traceback.format_exc()}")

    # ---------------------------------------------------------------
    # 🌍 Spezial-Quelle: Geopolitical Risk Index (Matteo Iacoviello)
    # ---------------------------------------------------------------
    if special_queue and not args.test:
        try:
            updated_set = stats.setdefault("updated_kpis", set())
            already_marked = "geopolitical_risk_index" in updated_set

            gpr_status = fetch_geopolitical_risk_index()
            if gpr_status:
                fetch_status.setdefault("kpis", {})["geopolitical_risk_index"] = gpr_status
                stats["others_success"] += 1
                updated_set.add("geopolitical_risk_index")
                if not already_marked:
                    stats["updated"] += 1
                log("[OK] Special world KPI saved: geopolitical_risk_index (Matteo Iacoviello)")
            else:
                stats["errors"] += 1
                log(f"[❌] Special fetch geopolitical_risk_index failed: No status entry returned.")
        except Exception as e:
            stats["errors"] += 1
            log(f"[❌] Special fetch geopolitical_risk_index failed: {e}")
    elif args.test:
        log("[SKIP] Test mode active: skipping special geopolitical_risk_index fetch")
    else:
        log("[SKIP] No special source selected for this fetch run")



    # --- Abschluss ---
    # === Summary-Block für fetch_status.json ===
    fetch_status["summary"] = {
        "lastRun": now_utc(),
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "errors": stats["errors"]
    }
    # Patch: before writing pending, filter out aliases mapped to "" in country_mappings.json
    mapping_for_filter = load_json_file(COUNTRY_MAP_FILE, {})
    filtered_pending = {k: v for k, v in pending.items() if not (k in mapping_for_filter and mapping_for_filter[k] == "")}
    # Patch: in test mode, write status and filtered_pending to /data/test
    if args.test:
        write_json(TEST_DATA_DIR / "fetch_status.json", fetch_status)
        write_json(TEST_DATA_DIR / "country_mappings_pending.json", filtered_pending)
    else:
        write_json(STATUS_FILE, fetch_status)
        write_json(COUNTRY_PENDING_FILE, filtered_pending)

    # 🤖 Automatische Verarbeitung von pending country mappings
    agent_summary_lines = []
    try:
        if args.test:
            log("[SKIP] Test mode active: automatic production mapping updates are disabled")
        elif stats.get("mapped_pending", 0) > 0 or stats.get("new_pending"):
            log("🤖 Running auto country mapping resolution...")
            import subprocess
            result = subprocess.run(
                ["python", os.path.join(SCRIPT_DIR, "auto_resolve_pending_mappings.py")], 
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                log("✅ Auto mapping agent completed successfully")
                if result.stdout:
                    # Only keep lines that are successful mappings or summary, not pending/unresolved
                    summary_seen = False
                    for line in result.stdout.split('\n'):
                        if line.strip().startswith("ZUSAMMENFASSUNG"):
                            if not summary_seen:
                                agent_summary_lines.append(line.replace("ZUSAMMENFASSUNG", "ZUSAMMENFASSUNG AUTO MAPPING:"))
                                summary_seen = True
                        elif "AUTO-RESOLVED" in line or "Automatisch resolved" in line:
                            agent_summary_lines.append(line)
                    # Remove duplicates
                    agent_summary_lines = list(dict.fromkeys(agent_summary_lines))
            else:
                log(f"⚠️ Auto mapping agent failed: {result.stderr}")
    except Exception as e:
        log(f"⚠️ Auto mapping agent error: {e}")

    log(f"[INFO] fetch_status.json updated with {len(fetch_status.get('kpis',{}))} KPIs")

    # ======================================================================
    # 🧩 Persistenz: neue fetch_state.json (ersetzt _updated_now-Logik)
    # ======================================================================
    try:
        fetch_state = {
            "last_run": now_utc(),
            "updated_kpis": sorted(list(stats.get("updated_kpis", set()))),
            "summary": {
                "updated": stats.get("updated", 0),
                "skipped": stats.get("skipped", 0),
                "errors": stats.get("errors", 0)
            }
        }

        state_path = os.path.join(output_dir, "fetch_state.json")
        write_json(state_path, fetch_state)

        log(f"[STATE] Updated KPI info written to {state_path} "
            f"({len(fetch_state['updated_kpis'])} entries)")
    except Exception as e:
        log(f"[WARN] Failed to write fetch_state.json: {e}")
        


    # --- Zusammenfassung ---
    summary = [
        "=== RealityCheck Fetch Report ===",
        f"Countries loaded:   {stats['countries_loaded']}",
        f"KPIs processed:    {stats['kpis_loaded']}",
        f"Saved records:     {stats['saved_records']}",
        "",
        f"WorldBank KPIs:    {stats['wb_success']}",
        f"CSV KPIs:          {stats['csv_success']}",
        f"OWID KPIs:         {stats['owid_success']}",
        f"IMF KPIs:          {stats['imf_success']}",
        f"Data360 KPIs:      {stats['data360_success']}",
        f"UNHCR KPIs:        {stats['unhcr_success']}",
        f"Others KPIs:       {stats['others_success']}",
        "",
        f"Mapping OK:        {stats['mapped_ok']}",
        f"Mapping dropped:   {stats['mapped_drop']}",
        f"Mapping pending:   {stats['mapped_pending']}",
        "",
        f"Dummies created:   {stats['dummies']}",
        f"Skipped (up-to-date): {stats['skipped']}",
        f"Errors:            {stats['errors']}",
        f"Updated KPIs:      {stats['updated']}",
    ]
    summary.append("")
    summary.append(f"Ignored KPIs with test='o': {len(ignored_kpis)}")
    if ignored_kpis:
        summary.append(f"IDs: {', '.join(ignored_kpis)}")

    # Insert auto-mapping summary (in English) at the top of mapping stats
    mapping_stats = []
    mapping_stats.append("")
    mapping_stats.append("AUTO MAPPING SUMMARY:")
    if agent_summary_lines:
        for line in agent_summary_lines:
            mapping_stats.append(line.replace("ZUSAMMENFASSUNG AUTO MAPPING::", "").replace("Automatisch resolved:", "Automatically resolved:").strip())
    else:
        mapping_stats.append("Automatically resolved: 0")
    mapping_stats.append("")
    mapping_stats.append(f"Mapping OK:        {stats['mapped_ok']}")
    mapping_stats.append(f"Mapping dropped:   {stats['mapped_drop']}")
    mapping_stats.append(f"Mapping pending:   {stats['mapped_pending']}")
    summary.extend(mapping_stats)

    # ✂️ Pre-1900 and future cuts summary
    if stats.get("trimmed_pre1900", 0) > 0:
        summary.append("")
        summary.append(
            f"Pre-1900 cuts:    {stats['trimmed_pre1900']} rows in {len(stats.get('trimmed_kpis', []))} KPIs"
        )
    if stats.get("trimmed_future", 0) > 0:
        summary.append(
            f"Post-{datetime.now().year} cuts: {stats['trimmed_future']} rows in {len(stats.get('trimmed_kpis', []))} KPIs"
        )

    updated_names = sorted(stats.get("updated_kpis", set()))
    if updated_names:
        summary.append("")
        summary.append("Updated KPI files:")
        summary.extend([f"  - {name}" for name in updated_names])

    skipped_breakdown = stats.get("skipped_breakdown", {})
    if skipped_breakdown:
        summary.append("")
        summary.append("Skipped breakdown:")
        for reason, count in sorted(skipped_breakdown.items()):
            summary.append(f"  - {reason}: {count}")

    safe_result = stats.get("errors", 0) == 0 and stats.get("dummies", 0) == 0
    summary.extend([
        "=================================",
        ("Fetch completed successfully" if safe_result else "Fetch completed with blocking safety errors") + "\n"
    ])
    # Note: If 'KPIs processed' > 'fetch_status.json updated', the difference is usually due to dummies, errors, or skipped KPIs that do not result in a status update.

    report = "\n".join(summary)
    print(report)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"🪵 Logfile saved → {LOG_FILE}")
    log(f"[INFO] Full fetch report written to {LOG_FILE}")
    return stats


# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    cli_args = parse_args()

    if cli_args.test and not cli_args.no_analysis:
        cli_args.no_analysis = True
        print("⏸️ Test mode (-t): analyses and GPT-based tasks are skipped.")
    elif cli_args.no_analysis:
        print("⏸️ Smart analyses and GPT-based tasks are disabled (local test mode).")

    run_stats = main(cli_args)

    try:
        ensure_fetch_succeeded(run_stats)
    except PipelineGuardError as exc:
        print(f"ERROR: Pipeline safety gate blocked post-processing and deployment: {exc}")
        raise SystemExit(2) from exc

    # In test mode, never run analysis, consolidation, or post-fetch scripts
    if cli_args.test:
        print("➡️ Validating isolated test output …")
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validation.py"), "--data-dir", str(TEST_DATA_DIR), "--test-kpis-only"],
            check=True,
        )
        print("✅ Test-mode fetch and validation completed without touching production data.")
        raise SystemExit(0)

    if cli_args.no_analysis:
        print("⏭️ Analysis and consolidation scripts skipped (--no-analysis or test mode).")

    else:
        try:
            print("➡️ Running fetch_overall_ranking.py …")
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "fetch_overall_ranking.py")], check=True)
            print("✅ Overall Ranking successfully updated.")
        except Exception as e:
            raise RuntimeError(f"Overall ranking failed: {e}") from e

        try:
            print("➡️ Running fetch_consolidated.py …")
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "fetch_consolidated.py")], check=True)
            print("✅ Consolidated data successfully created.")
        except Exception as e:
            raise RuntimeError(f"Consolidation failed: {e}") from e

    # === Fetch-State zusammenführen ===
    try:
        state_path = Path(DATA_DIR) / "fetch_state.json"
        updated_kpis = set()
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                updated_kpis = set(state_data.get("updated_kpis", []))
        merge_fetch_state(updated_kpis)
    except Exception as e:
        raise RuntimeError(f"State merge failed: {e}") from e

    # === Nur Analysen ausführen, wenn neue Daten da sind ===
    if not cli_args.no_analysis:
        try:
            if cli_args.force or len(updated_kpis) > 0:
                print(f"➡️ Starting global KPI analysis ({len(updated_kpis)} updates or forced run) …")
                subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "analysis.py")], check=True)
            else:
                print("⏸️ No updated KPIs — skipping AI analysis.")
        except Exception as e:
            raise RuntimeError(f"Global analysis failed: {e}") from e

        # === Fun/Safe Rankings ===
        try:
            fun_path = Path(DATA_DIR) / "fun_ranking.json"
            safe_path = Path(DATA_DIR) / "safe_haven_ranking.json"

            def file_age_days(p: Path) -> int:
                if not p.exists():
                    return 999
                return (datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)).days

            if file_age_days(fun_path) > 30 or file_age_days(safe_path) > 30:
                print("➡️ Generating Fun/Safe rankings …")
                subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "generate_fun_safe_rankings.py")], check=True)
                print("✅ Fun/Safe rankings generated.")
            else:
                print("⏸️ Fun/Safe rankings are current — no update needed.")
        except Exception as e:
            raise RuntimeError(f"Fun/Safe ranking generation failed: {e}") from e

        # === CSV Update Check (läuft immer) ===
        try:
            print("➡️ Running check_source_csv_updates.py …")
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "check_source_csv_updates.py")], check=True)
            print("✅ CSV source check completed.")
        except Exception as e:
            raise RuntimeError(f"CSV source check failed: {e}") from e
    else:
        print("⏭️ AI-based analyses skipped (--no-analysis enabled).")

    # === Run validation as last step ===
    try:
        print("➡️ Running validation.py as final step …")
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "validation.py")], check=True)
        print("✅ Data validation completed.")
    except Exception as e:
        raise RuntimeError(f"Data validation failed: {e}") from e

