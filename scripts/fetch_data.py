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
import shutil
import logging
import argparse
import requests
import re
import zipfile
import unicodedata
import traceback
import subprocess
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime, timezone
from env_utils import get_openai_key  # ✅ wichtig: hier fehlte der Import



# ✅ UTF-8-Fix
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


# ======================================================================
# 🔧 Pfade (pathlib-Version – robust gegen OS-Unterschiede)
# ======================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR   = SCRIPT_DIR.parent.resolve()
DATA_DIR   = ROOT_DIR / "data"
META_DIR   = DATA_DIR / "meta"
SOURCE_CSV_DIR = SCRIPT_DIR / "source_csv"
PENDING_DIR    = DATA_DIR / "pending"

COUNTRIES_FILE       = META_DIR / "countries.json"
COUNTRY_MAP_FILE     = META_DIR / "country_mappings.json"
COUNTRY_PENDING_FILE = META_DIR / "country_mappings_pending.json"
AVAILABLE_FILE       = META_DIR / "available_kpis.json"
LOG_FILE             = DATA_DIR / "fetch_log.txt"
STATUS_FILE          = DATA_DIR / "fetch_status.json"



# === Argumente ===
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RealityCheck Fetcher")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force full refetch (clear /data except /meta)",
    )
    parser.add_argument(
        "-n",
        "--no-analysis",
        action="store_true",
        help="Skip AI-based analysis and ranking follow-up tasks",
    )
    parser.add_argument(
        "-k",
        "--kpi",
        dest="kpi_filters",
        action="append",
        default=[],
        metavar="ID",
        help="Fetch only the given KPI identifier (repeatable)",
    )
    return parser


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)

    extra_filters: List[str] = []
    for token in unknown:
        if token.startswith("-") and len(token) > 1:
            extra_filters.append(token.lstrip("-"))
        else:
            parser.error(f"Unrecognized argument: {token}")

    if extra_filters:
        args.kpi_filters.extend(extra_filters)

    # Normalisiere IDs (leerzeichen entfernen)
    args.kpi_filters = [k.strip() for k in args.kpi_filters if k and k.strip()]

    return args


def handle_force_cleanup() -> None:
    print("[INFO] Force mode enabled – clearing data except /meta …")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for item in DATA_DIR.iterdir():
        if item.name == "meta":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)

    if (SCRIPT_DIR / "__pycache__").exists():
        shutil.rmtree(SCRIPT_DIR / "__pycache__", ignore_errors=True)

    for f in SCRIPT_DIR.glob("*.md5"):
        f.unlink(missing_ok=True)

    if PENDING_DIR.exists():
        shutil.rmtree(PENDING_DIR, ignore_errors=True)

    print("[OK] Data folders cleared for full refetch.")

# ======================================================================
# 🧰 Hilfsfunktionen
# ======================================================================
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PENDING_DIR, exist_ok=True)

def log(msg: str):
    ensure_dirs()
    line = f"[{now_utc()} UTC] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path: str, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_float(x) -> Optional[float]:
    try:
        if x in ("", None):
            return None
        return float(str(x).replace(",", "."))
    except Exception:
        return None

import hashlib

def safe_filename(text: str) -> str:
    """Sanitize and shorten filenames safely (handles long URLs and special chars)."""
    text = str(text)
    # Grundbereinigung
    text = re.sub(r'[^a-zA-Z0-9_.-]', '_', text)
    # Wenn zu lang, hinten Hash ergänzen
    if len(text) > 100:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        text = text[:90] + "_" + digest
    return text


def safe_pending_filename(text: str) -> str:
    """Erzeugt einen sicheren, kurzen Dateinamen für Pending-Files (z. B. bei OWID-404s)."""
    text = str(text)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', text)
    if len(clean) > 100:
        digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
        clean = clean[:90] + "_" + digest
    return clean


def mark_skip(stats: Dict[str, Any], reason: str) -> None:
    """Increment skipped counters and keep a human-readable breakdown."""
    stats["skipped"] += 1
    breakdown = stats.setdefault("skipped_breakdown", {})
    breakdown[reason] = breakdown.get(reason, 0) + 1


def resolve_kpi_id(meta: Dict[str, Any]) -> str:
    """Bestmögliche ID eines KPI-Metadatensatzes (Dateiname bevorzugt)."""
    if not isinstance(meta, dict):
        return "kpi"

    return (
        str(meta.get("filename") or "").strip()
        or str(meta.get("id") or "").strip()
        or str(meta.get("title") or "").strip()
        or "kpi"
    )


def derive_kpi_id(meta: Dict[str, Any]) -> str:
    """Alias, damit alle Aufrufer dieselbe robuste ID-Auflösung verwenden."""
    try:
        return resolve_kpi_id(meta)
    except Exception:
        if not isinstance(meta, dict):
            return "kpi"
        filename = str(meta.get("filename") or "").strip()
        if filename:
            return filename
        legacy_id = str(meta.get("id") or "").strip()
        if legacy_id:
            return legacy_id
        title = str(meta.get("title") or "").strip()
        if title:
            return title
        return "kpi"
    
# ======================================================================
# 💾 Safe Write Helpers (robuste Datei-Speicherung)
# ======================================================================
def safe_write_json(path: str | Path, data):
    """Garantiert sicheres Schreiben von JSON mit UTF-8 und Verzeichnis-Erstellung."""
    try:
        os.makedirs(os.path.dirname(str(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"[SAFE] JSON written → {os.path.relpath(path, ROOT_DIR)} ({len(data)} keys)")
    except Exception as e:
        log(f"[❌] Failed to write {path}: {e}")

def safe_write_text(path: str | Path, text: str):
    """Sicheres Schreiben von Textdateien (z. B. Logs, Reports)."""
    try:
        os.makedirs(os.path.dirname(str(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text or "")
        log(f"[SAFE] Text written → {os.path.relpath(path, ROOT_DIR)}")
    except Exception as e:
        log(f"[❌] Failed to write text {path}: {e}")


# ======================================================================
# 🌍 Country Mapping
# ======================================================================
def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s)

def build_country_indices(countries: Dict[str, Any], mapping: Dict[str, str]):
    c_index = { _norm(k): k for k in countries.keys() }
    a_index = {}
    for alias, target in (mapping or {}).items():
        if not target or str(target).strip() == "":
            a_index[_norm(alias)] = ""
        else:
            t_norm = _norm(target)
            a_index[_norm(alias)] = c_index.get(t_norm)
    return c_index, a_index

def canonicalize_country(name: str, c_index, a_index, countries, pending, stats):
    if not name:
        return None
    if name in countries:
        stats["mapped_ok"] += 1
        return name
    n = _norm(name)
    if n in a_index:
        target = a_index[n]
        if target == "":
            stats["mapped_drop"] += 1
            return None
        if not target:
            pending[name] = "Mapping target missing or invalid"
            stats["mapped_pending"] += 1
            return None
        stats["mapped_ok"] += 1
        return target
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


def save_records(kpi_id: str, records: List[Dict[str, Any]], stats=None):
    """
    Speichert Daten im Standardformat, entfernt automatisch alle Jahre < 1900
    und protokolliert die Kürzungen im Fetch-Report.
    """
    ensure_dirs()
    before = len(records)

    # 🕐 Trim extreme years (remove pre-1900 and future projections)
    from datetime import datetime
    current_year = datetime.now().year

    trimmed = [
        r for r in records
        if isinstance(r.get("year"), (int, float, str))
        and str(r.get("year")).strip() != ""
        and 1900 <= int(float(r["year"])) <= current_year
    ]

    after = len(trimmed)
    if before != after:
        removed = before - after
        log(f"[TRIM] {kpi_id}: removed {removed} out-of-range records (before 1900 or >{current_year})")

        if stats is not None:
            stats.setdefault("trimmed_records", 0)
            stats["trimmed_records"] += removed
            stats.setdefault("trimmed_kpis", set())
            stats["trimmed_kpis"].add(kpi_id)

    # --- Normal speichern ---
    write_json(os.path.join(DATA_DIR, f"{kpi_id}.json"), trimmed)
    with open(os.path.join(DATA_DIR, f"{kpi_id}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country", "iso2", "year", "value"])
        w.writeheader()
        w.writerows(trimmed)


def keep_or_dummy(kpi_id: str, reason: str, stats):
    json_path = os.path.join(DATA_DIR, f"{kpi_id}.json")
    csv_path  = os.path.join(DATA_DIR, f"{kpi_id}.csv")
    if os.path.exists(json_path) and os.path.exists(csv_path):
        log(f"[WARN] Keeping old data for {kpi_id} ({reason})")
        return
    write_json(json_path, [])
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=["country", "iso2", "year", "value"]).writeheader()
    stats["dummies"] += 1
    log(f"[WARN] Dummy created for {kpi_id} ({reason})")

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
        rj = requests.get(url_json, timeout=20)
        if rj.status_code == 200:
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
        rz = requests.get(url_zip, timeout=30)
        if rz.status_code == 200 and rz.content[:2] == b"PK":
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

def get_source_date_from_owid(source_code: str) -> Optional[str]:
    """Liest das Aktualisierungsdatum aus der OWID-Metadatei (.metadata.json)"""
    try:
        meta_url = f"https://ourworldindata.org/grapher/{source_code}.metadata.json"
        r = requests.get(meta_url, timeout=20)
        if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""):
            data = r.json()
            if "dateDownloaded" in data:
                d = str(data["dateDownloaded"]).strip()
                log(f"[META] OWID {source_code} → dateDownloaded {d}")
                return d
            if "chart" in data and "citation" in data["chart"]:
                citation = str(data["chart"]["citation"])
                year_match = re.search(r"\b(19|20)\d{2}\b", citation)
                if year_match:
                    d = f"{year_match.group(0)}-12-31T00:00:00Z"
                    log(f"[META] OWID {source_code} → citation year {d}")
                    return d
        elif "Last-Modified" in r.headers:
            d = r.headers["Last-Modified"]
            log(f"[META] OWID {source_code} → header Last-Modified {d}")
            return d
        log(f"[META] OWID {source_code}: no date info found")
    except Exception as e:
        log(f"[WARN] OWID meta fetch failed for {source_code}: {e}")
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
        return True
    except Exception as e:
        log(f"[WARN] {kpi_id}: OWID year-check failed ({e}) → fetch")
        return True


def should_fetch(kpi_id: str, source_type: str, source_date: Optional[str], meta: dict, fetch_status: dict) -> bool:
    """
    Allgemeine Steuerung:
    - Für WorldBank: echtes Änderungsdatum vergleichen
    - Für OWID: Heuristik (siehe oben)
    - Für CSV/UNHCR: immer neu laden (keine API-Daten)
    """
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
def fetch_worldbank_series(indicator_code: str):
    """
    Ruft einen vollständigen Zeitverlauf eines World Bank-Indikators ab.
    Gibt eine Liste aus dicts zurück, jeweils mit 'country', 'date', 'value'.
    Integriert automatischen Retry mit Backoff bei HTTP 429 (Rate Limit).
    """
    base_url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=20000"

    max_retries = 5
    backoff = 5  # Sekunden

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(base_url, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if not isinstance(data, list) or len(data) < 2:
                    log(f"[WARN] WorldBank {indicator_code}: unexpected JSON format")
                    return []
                series = data[1]
                if not isinstance(series, list):
                    log(f"[WARN] WorldBank {indicator_code}: series not list")
                    return []
                return series

            elif r.status_code == 429:
                # === 🕐 Rate Limit Handling ===
                wait_time = backoff * attempt
                log(f"[RATE] WorldBank {indicator_code}: HTTP 429 → waiting {wait_time}s before retry ({attempt}/{max_retries})")
                time.sleep(wait_time)
                continue  # erneuter Versuch

            else:
                log(f"[ERR] WorldBank {indicator_code}: HTTP {r.status_code}")
                return []

        except Exception as e:
            log(f"[ERR] WorldBank fetch failed for {indicator_code} (try {attempt}/{max_retries}): {e}")
            time.sleep(2 * attempt)

    log(f"[FAIL] WorldBank {indicator_code}: all {max_retries} attempts failed")
    return []


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
# 🌍 World Bank Fetch (inkl. Heuristik & Meta-Sync)
# ----------------------------------------------------------------------
def process_worldbank(kpi_id, meta, countries, c_index, a_index, pending, stats):
    """Verarbeitet einen einzelnen WorldBank-Indikator (inkl. Heuristik für source_date & data_year)."""
    code = meta.get("source_code") or meta.get("code")
    if not code:
        keep_or_dummy(kpi_id, "missing source_code", stats)
        return

    # === 1️⃣ Quelle abfragen ===
    source_date = get_source_date_from_worldbank(code)
    
    # === 🧩 Erweiterung: Falls kein valides Datum aus API → ZIP prüfen ===
    if not source_date or source_date in ("Unknown", ""):
        try:
            zip_url = f"https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"
            r_zip = requests.get(zip_url, timeout=30)
            if r_zip.status_code == 200:
                zip_date = extract_worldbank_date(r_zip.content)
                if zip_date:
                    source_date = zip_date
                    log(f"[META] WorldBank {code} → date accessed {zip_date} (from ZIP metadata)")
        except Exception as e:
            log(f"[WARN] WorldBank ZIP date extract failed for {code}: {e}")
     
    rows = fetch_worldbank_series(code)
    if not rows:
        keep_or_dummy(kpi_id, f"WorldBank fetch failed ({code})", stats)
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

    # === 3️⃣ Heuristik: falls source_date generisch oder unbekannt, ersetze durch jüngstes Jahr ===
    latest_year = max(all_years) if all_years else None
    # ✅ Nur heuristisch, wenn wirklich KEIN Datum gefunden wurde
    if (not source_date or source_date == "Unknown") and latest_year:
        source_date = f"{latest_year}-01-01T00:00:00Z"
        log(f"[HEUR] WorldBank {kpi_id} → inferred source_date {source_date}")

    # === 4️⃣ Speichern ===
    if out:
        out = maybe_invert_records(kpi_id, meta, out)
        save_records(kpi_id, out)
        stats["wb_success"] += 1
        stats["saved_records"] += len(out)
        log(f"[OK] WorldBank KPI saved: {kpi_id} ({len(out)} rows, last updated {source_date})")

        # 🔹 Meta-Felder nur intern für fetch_status.json
        meta["_latest_year"] = latest_year
        meta["_source_date"] = source_date

        # 🔹 Statt _updated_now → zentrale Laufzeit-Sammelliste
        stats.setdefault("updated_kpis", set()).add(kpi_id)

    else:
        keep_or_dummy(kpi_id, f"WorldBank empty {code}", stats)
# ----------------------------------------------------------------------
# 📊 CSV Fetch (smart) – inkl. Änderungsprüfung & Natural Disasters Sonderfall
# ----------------------------------------------------------------------
def process_csv(kpi_id, meta, countries, c_index, a_index, pending, stats):
    import hashlib, pandas as pd, re

    csv_name = meta.get("source_code") or meta.get("code") or f"{kpi_id}.csv"
    path = os.path.join(SOURCE_CSV_DIR, csv_name)
    if not os.path.exists(path):
        keep_or_dummy(kpi_id, f"CSV missing {csv_name}", stats)
        return

    json_path = os.path.join(DATA_DIR, f"{kpi_id}.json")
    hash_path = os.path.join(PENDING_DIR, f"{kpi_id}.md5")

    def file_md5(p):
        h = hashlib.md5()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    csv_mtime, csv_hash = os.path.getmtime(path), file_md5(path)

    # 🔹 Änderungsprüfung
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
        keep_or_dummy(kpi_id, f"CSV read error {csv_name}", stats)
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
                keep_or_dummy(kpi_id, "Natural Disasters normalization failed", stats)
                return
        else:
            log(f"[WARN] CSV format unknown for {kpi_id} → {csv_name}")
            keep_or_dummy(kpi_id, f"Unknown CSV format {csv_name}", stats)
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
        save_records(kpi_id, out)
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
        keep_or_dummy(kpi_id, f"CSV empty {csv_name}", stats)

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


def process_owid(kpi_id, meta, countries, c_index, a_index, pending, stats):
    """Verarbeitet OWID-CSV-ähnliche Daten und speichert sie lokal."""
    source_code = meta.get("source_code")
    if not source_code:
        keep_or_dummy(kpi_id, "missing source_code", stats)
        return

    url = f"https://ourworldindata.org/grapher/{source_code}"
    source_date = get_source_date_from_owid(url)

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        text = resp.text
    except Exception as e:
        log(f"[ERR] OWID fetch failed for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"OWID fetch failed {source_code}", stats)
        return

    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not {"Entity", "Code", "Year"}.issubset(set(cols)):
        log(f"[WARN] OWID format unknown → {source_code}")
        keep_or_dummy(kpi_id, f"OWID format unknown {source_code}", stats)
        return

    var_cols = [c for c in cols if c not in ("Entity", "Code", "Year")]
    if not var_cols:
        keep_or_dummy(kpi_id, f"OWID no data column {source_code}", stats)
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
        save_records(kpi_id, out)
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
        keep_or_dummy(kpi_id, f"OWID empty {source_code}", stats)


# ----------------------------------------------------------------------
# 🕊️ UNHCR Fetch (ZIP/CSV, Encoding & Header-robust)
# ----------------------------------------------------------------------
def process_unhcr(kpi_id, meta, countries, c_index, a_index, pending, stats):
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
        keep_or_dummy(kpi_id, f"UNHCR fetch failed {source_code}", stats)
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
        keep_or_dummy(kpi_id, f"UNHCR decode error {source_code}", stats)
        return

    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not cols:
        keep_or_dummy(kpi_id, f"UNHCR no header {source_code}", stats)
        return

    country_key = _find_col(cols, "country of asylum","territory of asylum","asylum")
    year_key = _find_col(cols, "year")
    value_key = _find_col(cols, meta.get("unhcr_field","refugees"))
    if not all([country_key, year_key, value_key]):
        keep_or_dummy(kpi_id, f"UNHCR unknown format {source_code}", stats)
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
        save_records(kpi_id, out)
        stats["unhcr_success"] = stats.get("unhcr_success", 0) + 1
        stats["saved_records"] += len(out)
        stats.setdefault("updated_kpis", set()).add(kpi_id)
        log(f"[OK] UNHCR KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        keep_or_dummy(kpi_id, f"UNHCR empty {source_code}", stats)
# ----------------------------------------------------------------------
# 🌍 Special Fetch: Geopolitical Risk Index (Matteo Iacoviello)
# ----------------------------------------------------------------------
def fetch_geopolitical_risk_index(stats: Optional[Dict[str, Any]] = None) -> bool:
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
        safe_write_json(file_path, out)
        log(f"✅ Saved {len(out)} GPR entries → {file_path}")

        if stats is not None:
            stats.setdefault("saved_records", 0)
            stats["saved_records"] += len(out)
            updated_set = stats.setdefault("updated_kpis", set())
            was_new = kpi_name not in updated_set
            updated_set.add(kpi_name)
            if was_new:
                stats["updated"] += 1
            stats["other_success"] = stats.get("other_success", 0) + 1

        # === fetch_status aktualisieren ===
        fetch_status = read_json(STATUS_FILE, {"kpis": {}})
        fetch_status.setdefault("kpis", {})[kpi_name] = {
            "source": "https://www.matteoiacoviello.com/gpr.htm",
            "url": url,
            "source_date": datetime.now(UTC).strftime("%Y-%m-%dT00:00:00Z"),
            "data_year": int(df_annual["year"].max()),
            "last_fetch": now_utc(),
        }
        safe_write_json(STATUS_FILE, fetch_status)
        log("[OK] Special world KPI saved: geopolitical_risk_index (Matteo Iacoviello)")

        return True

    except Exception as e:
        log(f"❌ GPR fetch failed: {e}")
        if stats is not None:
            stats["errors"] += 1
        return False

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
# 🚀 Main
# ======================================================================
def main(args: argparse.Namespace) -> None:
    if args.force:
        handle_force_cleanup()

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
    fetch_status = read_json(STATUS_FILE, {"kpis": {}})

    # 🆕 Force-All-Modus: Wenn kein fetch_status.json existiert oder leer ist
    if not os.path.exists(STATUS_FILE) or not fetch_status.get("kpis"):
        log("⚠️ Kein fetch_status.json vorhanden oder leer – setze ALLE KPIs auf 'neu'.")
        fetch_status = {"kpis": {}}
        force_all_updates = True
    else:
        force_all_updates = False


    stats = {
        "countries_loaded": 0, "kpis_loaded": 0, "saved_records": 0, "dummies": 0,
        "mapped_ok": 0, "mapped_drop": 0, "mapped_pending": 0, "new_pending": set(),
        "wb_success": 0, "csv_success": 0, "owid_success": 0, "unhcr_success": 0, "other_success": 0,
        "errors": 0, "skipped": 0, "skipped_breakdown": {},
        "updated": 0,                     # 🔹 NEU: zählt erfolgreiche Updates
        "updated_kpis": set(),
        "trimmed_records": 0,
        "trimmed_kpis": set(),
    }


    # --- Metadaten & Mapping laden ---
    countries = read_json(COUNTRIES_FILE, {})
    mapping   = read_json(COUNTRY_MAP_FILE, {})
    pending   = read_json(COUNTRY_PENDING_FILE, {})
    c_index, a_index = build_country_indices(countries, mapping)
    stats["countries_loaded"] = len(countries)

    raw_kpis = read_json(AVAILABLE_FILE, [])
    kpi_list = [v for v in raw_kpis if isinstance(v, dict)]

    filter_set: Set[str] = set(args.kpi_filters or [])
    if filter_set:
        filtered: List[Dict[str, Any]] = []
        missing = set(filter_set)
        for meta in kpi_list:
            kpi_id = derive_kpi_id(meta)
            if kpi_id in filter_set:
                filtered.append(meta)
                missing.discard(kpi_id)
        matched_ids = sorted(derive_kpi_id(meta) for meta in filtered)
        if matched_ids:
            log(f"[INFO] KPI filter active → {', '.join(matched_ids)}")
        if missing:
            log(f"[WARN] Unknown KPI filter(s): {', '.join(sorted(missing))}")
        kpi_list = filtered

    stats["kpis_loaded"] = len(kpi_list)

    # --- KPI-Schleife ---
    for meta in kpi_list:
        try:
            kpi_id = derive_kpi_id(meta)
            source_type = (meta.get("source_type") or meta.get("type") or "").lower().strip()
            source_code = meta.get("source_code") or meta.get("code") or ""
            source_date = None

            # Quelle-spezifisches Datum
            if source_type == "worldbank" and source_code:
                source_date = get_source_date_from_worldbank(source_code)
            elif source_type == "owid" and source_code:
                source_date = get_source_date_from_owid(f"https://ourworldindata.org/grapher/{source_code}")
            else:
                source_date = "Unknown"

            # Prüfen, ob Fetch nötig (außer im Force-All-Modus)
            if not force_all_updates and not should_fetch(kpi_id, source_type, source_date, meta, fetch_status):
                log(f"[⏸️] {kpi_id} – unchanged ({source_date})")
                mark_skip(stats, "Remote data unchanged")
                continue
                
            # Sonderfall: Geopolitical Risk Index wird separat behandelt
            if kpi_id == "geopolitical_risk_index":
                log(f"[SKIP] {kpi_id}: handled by special fetcher later")
                continue

            # === Quelle verarbeiten ===
            updated_set = stats.setdefault("updated_kpis", set())
            already_marked = kpi_id in updated_set

            try:
                if source_type == "worldbank":
                    process_worldbank(kpi_id, meta, countries, c_index, a_index, pending, stats)
                elif source_type == "csv":
                    latest_year = process_csv(kpi_id, meta, countries, c_index, a_index, pending, stats)
                    if latest_year:
                        meta["_latest_year"] = latest_year
                elif source_type == "owid":
                    process_owid(kpi_id, meta, countries, c_index, a_index, pending, stats)
                elif source_type == "unhcr":
                    process_unhcr(kpi_id, meta, countries, c_index, a_index, pending, stats)
                else:
                    keep_or_dummy(kpi_id, f"unknown source_type {source_type}", stats)

                # Erfolgreiches Update protokollieren
                if kpi_id in updated_set and not already_marked:
                    stats["updated"] += 1

                # ✅ Preserve old data_year and source_date if not newly detected
                old_meta = fetch_status.get("kpis", {}).get(kpi_id, {})
                if not meta.get("_latest_year") and old_meta.get("data_year"):
                    meta["_latest_year"] = old_meta["data_year"]
                if (not meta.get("_source_date") or meta.get("_source_date") in ("Unknown", None)) and old_meta.get("source_date"):
                    meta["_source_date"] = old_meta["source_date"]

                # ✅ Verwende ggf. angepasste Werte aus meta
                used_source_date = meta.get("_source_date") or source_date or "Unknown"
                used_data_year   = meta.get("_latest_year") or None

                fetch_status.setdefault("kpis", {})[kpi_id] = {
                    "source": meta.get("source") or meta.get("source_type") or "unknown",
                    "url": meta.get("source_url") or meta.get("url") or "",
                    "source_date": used_source_date,
                    "data_year": used_data_year,
                    "last_fetch": now_utc()
                }

                log(f"[STATUS] {kpi_id}: stored source_date={used_source_date}, data_year={used_data_year}")

            except Exception as e:  # 👈 muss in dieser Einrückungsebene stehen
                stats["errors"] += 1
                log(f"[❌] {kpi_id} failed: {e}\n{traceback.format_exc()}")

        except Exception as e:
            stats["errors"] += 1
            log(f"[ERR] {meta.get('title','unknown')} failed: {e}\n{traceback.format_exc()}")

    # ---------------------------------------------------------------
    # 🌍 Spezial-Quelle: Geopolitical Risk Index (Matteo Iacoviello)
    # ---------------------------------------------------------------
    should_fetch_special = (not filter_set) or ("geopolitical_risk_index" in filter_set)
    if should_fetch_special:
        success = fetch_geopolitical_risk_index(stats)
        if not success:
            log("[❌] Special fetch geopolitical_risk_index failed – see details above")



    # --- Abschluss ---
    # === Summary-Block für fetch_status.json ===
    fetch_status["summary"] = {
        "lastRun": now_utc(),
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "errors": stats["errors"]
    }
    write_json(STATUS_FILE, fetch_status)
    write_json(COUNTRY_PENDING_FILE, pending)


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

        state_path = os.path.join(DATA_DIR, "fetch_state.json")
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
        f"WorldBank KPIs:    {stats.get('wb_success', 0)}",
        f"CSV KPIs:          {stats.get('csv_success', 0)}",
        f"OWID KPIs:         {stats.get('owid_success', 0)}",
        f"UNHCR KPIs:        {stats.get('unhcr_success', 0)}",
        f"Other KPIs:        {stats.get('other_success', 0)}",
        "",
        f"Mapping OK:        {stats['mapped_ok']}",
        f"Mapping dropped:   {stats['mapped_drop']}",
        f"Mapping pending:   {stats['mapped_pending']}",
        "",
        f"Dummies created:   {stats['dummies']}",
        f"Skipped (up-to-date): {stats['skipped']}",
        f"Errors:            {stats['errors']}",
        f"Updated KPIs:      {stats['updated']}",  # ✅ hier normaler Listeneintrag
        
    ]

    # ✂️ Neue Auswertung der Pre-1900-Kürzungen
    if stats.get("trimmed_records", 0) > 0:
        summary.append("")
        summary.append(
            f"Pre-1900 cuts:    {stats['trimmed_records']} rows in {len(stats.get('trimmed_kpis', []))} KPIs"
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

    summary.extend([
        "=================================",
        "✅ Fetch completed successfully\n"
    ])

    report = "\n".join(summary)
    print(report)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"🪵 Logfile saved → {LOG_FILE}")
    log(f"[INFO] Full fetch report written to {LOG_FILE}")


# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    cli_args = parse_args()

    if cli_args.no_analysis:
        print("⏸️ Smart analyses and GPT-based tasks are disabled (local test mode).")

    main(cli_args)

    try:
        print("➡️ Running fetch_overall_ranking.py …")
        subprocess.run(["python", os.path.join(SCRIPT_DIR, "fetch_overall_ranking.py")], check=True)
        print("✅ Overall Ranking successfully updated.")
    except Exception as e:
        print(f"⚠️ Error in overall ranking: {e}")

    try:
        print("➡️ Running fetch_consolidated.py …")
        subprocess.run(["python", os.path.join(SCRIPT_DIR, "fetch_consolidated.py")], check=True)
        print("✅ Consolidated data successfully created.")
    except Exception as e:
        print(f"⚠️ Error in consolidation: {e}")

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
        print(f"⚠️ State merge failed: {e}")

    # === Nur Analysen ausführen, wenn neue Daten da sind ===
    if not cli_args.no_analysis:
        try:
            if cli_args.force or len(updated_kpis) > 0:
                print(f"➡️ Starting global KPI analysis ({len(updated_kpis)} updates or forced run) …")
                subprocess.run(["python", os.path.join(SCRIPT_DIR, "analysis.py")], check=True)
            else:
                print("⏸️ No updated KPIs — skipping AI analysis.")
        except Exception as e:
            print(f"⚠️ Global analysis failed: {e}")

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
                subprocess.run(["python", os.path.join(SCRIPT_DIR, "generate_fun_safe_rankings.py")], check=True)
                print("✅ Fun/Safe rankings generated.")
            else:
                print("⏸️ Fun/Safe rankings are current — no update needed.")
        except Exception as e:
            print(f"⚠️ Fun/Safe ranking generation failed: {e}")

        # === CSV Update Check (läuft immer) ===
        try:
            print("➡️ Running check_source_csv_updates.py …")
            subprocess.run(["python", os.path.join(SCRIPT_DIR, "check_source_csv_updates.py")], check=True)
            print("✅ CSV source check completed.")
        except Exception as e:
            print(f"⚠️ CSV source check failed: {e}")
    else:
        print("⏭️ AI-based analyses skipped (--no-analysis enabled).")

