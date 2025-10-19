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

import os, csv, json, re, requests, unicodedata, traceback, io, zipfile
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

# ======================================================================
# 🔧 Pfade
# ======================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR   = os.path.join(ROOT_DIR, "data")
META_DIR   = os.path.join(DATA_DIR, "meta")
SOURCE_CSV_DIR = os.path.join(SCRIPT_DIR, "source_csv")
PENDING_DIR    = os.path.join(DATA_DIR, "pending")

COUNTRIES_FILE       = os.path.join(META_DIR, "countries.json")
COUNTRY_MAP_FILE     = os.path.join(META_DIR, "country_mappings.json")
COUNTRY_PENDING_FILE = os.path.join(META_DIR, "country_mappings_pending.json")
AVAILABLE_FILE       = os.path.join(META_DIR, "available_kpis.json")
LOG_FILE             = os.path.join(DATA_DIR, "fetch_log.txt")
STATUS_FILE          = os.path.join(DATA_DIR, "fetch_status.json")

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
    line = f"[{now_utc()}] {msg}"
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

def safe_filename(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(text))
    return text[:150]
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
def save_records(kpi_id: str, records: List[Dict[str, Any]]):
    ensure_dirs()
    write_json(os.path.join(DATA_DIR, f"{kpi_id}.json"), records)
    with open(os.path.join(DATA_DIR, f"{kpi_id}.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country","iso2","year","value"])
        w.writeheader()
        w.writerows(records)

def keep_or_dummy(kpi_id: str, reason: str, stats):
    json_path = os.path.join(DATA_DIR, f"{kpi_id}.json")
    csv_path  = os.path.join(DATA_DIR, f"{kpi_id}.csv")
    if os.path.exists(json_path) and os.path.exists(csv_path):
        log(f"[WARN] Keeping old data for {kpi_id} ({reason})")
        return
    write_json(json_path, [])
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=["country","iso2","year","value"]).writeheader()
    stats["dummies"] += 1
    log(f"[WARN] Dummy created for {kpi_id} ({reason})")

# ======================================================================
# 🔍 Update-Check & Source-Date Extraction
# ======================================================================
def get_source_date_from_worldbank(code: str) -> Optional[str]:
    meta_url = f"https://api.worldbank.org/v2/indicator/{code}?format=json"
    try:
        r = requests.get(meta_url, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                meta = data[0]
                for key in ["lastupdated","LastUpdated","lastUpdated","lastupdate"]:
                    if key in meta and meta[key]:
                        d = meta[key]
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                            return d + "T00:00:00Z"
                        return str(d)
    except Exception as e:
        log(f"[WARN] Could not get WorldBank source_date for {code}: {e}")
    return None

def get_source_date_from_owid(url: str) -> Optional[str]:
    try:
        meta_url = url.replace("/grapher/", "/grapher/data/metadata/")
        r = requests.get(meta_url, timeout=20)
        if r.status_code == 200:
            data = r.json()
            for key in ["last_updated","updatedAt","lastUpdatedAtSource","dataEditedAt","publishedAt"]:
                if key in data and data[key]:
                    return data[key]
    except Exception as e:
        log(f"[WARN] Could not get OWID source_date: {e}")
    return None

def should_fetch(kpi_id: str, source_date: Optional[str], fetch_status: dict) -> bool:
    local_info = fetch_status.get("kpis", {}).get(kpi_id)
    if not local_info:
        return True
    local_date = local_info.get("source_date")
    if not source_date or not local_date or local_date == "Unknown":
        return True
    try:
        l = datetime.fromisoformat(local_date.replace("Z","+00:00"))
        r = datetime.fromisoformat(source_date.replace("Z","+00:00"))
        return r > l
    except Exception:
        return True

# ======================================================================
# 🌐 Datenquellen – World Bank & CSV
# ======================================================================
def fetch_worldbank_series(code: str) -> Optional[List[Dict[str, Any]]]:
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000"
    try:
        r = requests.get(url, timeout=40)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")
        data = r.json()
        if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
            raise ValueError("Unexpected World Bank format")
        return data[1]
    except Exception as e:
        log(f"[ERR] WorldBank fetch failed for {code}: {e}")
        return None

def process_worldbank(kpi_id, meta, countries, c_index, a_index, pending, stats):
    code = meta.get("source_code") or meta.get("code")
    if not code:
        keep_or_dummy(kpi_id, "missing source_code", stats)
        return
    rows = fetch_worldbank_series(code)
    if not rows:
        keep_or_dummy(kpi_id, f"WorldBank fetch failed ({code})", stats)
        return
    out = []
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
            out.append({"country": canon,"iso2":"","year":year,"value":float(val)})
        except:
            continue
    if out:
        save_records(kpi_id, out)
        stats["wb_success"] += 1
        stats["saved_records"] += len(out)
        log(f"[OK] WorldBank KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        keep_or_dummy(kpi_id, f"WorldBank empty {code}", stats)

def process_csv(kpi_id, meta, countries, c_index, a_index, pending, stats):
    csv_name = meta.get("source_code") or meta.get("code") or f"{kpi_id}.csv"
    path = os.path.join(SOURCE_CSV_DIR, csv_name)
    if not os.path.exists(path):
        keep_or_dummy(kpi_id, f"CSV missing {csv_name}", stats)
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        out = []
        for r in reader:
            cname = (r.get("country") or "").strip()
            canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
            if not canon:
                continue
            year = r.get("year")
            val = safe_float(r.get("value"))
            if not year or val is None:
                continue
            try:
                y = int(float(year))
            except:
                continue
            out.append({"country":canon,"iso2":r.get("iso2",""),"year":y,"value":val})
    if out:
        save_records(kpi_id, out)
        stats["csv_success"] += 1
        stats["saved_records"] += len(out)
        log(f"[OK] CSV KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        keep_or_dummy(kpi_id, f"CSV empty {csv_name}", stats)
        
    # ======================================================================
# 🧭 OWID Fetch
# ======================================================================
def process_owid(kpi_id, meta, countries, c_index, a_index, pending, stats):
    source_code = meta.get("source_code")
    if not source_code:
        keep_or_dummy(kpi_id, "missing source_code", stats)
        return

    url = f"https://ourworldindata.org/grapher/{source_code}"

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        text = resp.text
    except Exception as e:
        log(f"[ERR] OWID fetch failed for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"OWID fetch failed {source_code}", stats)
        filename = f"{kpi_id}_{safe_filename(source_code)}_error.txt"
        ensure_dirs()
        with open(os.path.join(PENDING_DIR, filename[:180]), "w", encoding="utf-8") as f:
            f.write(str(e))
        return

    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not {"Entity","Code","Year"}.issubset(set(cols)):
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{source_code}.csv"), "w", encoding="utf-8").write(text)
        log(f"[WARN] OWID format unknown → pending saved: {source_code}")
        keep_or_dummy(kpi_id, f"OWID format unknown {source_code}", stats)
        return

    var_cols = [c for c in cols if c not in ("Entity","Code","Year")]
    if not var_cols:
        keep_or_dummy(kpi_id, f"OWID no data column {source_code}", stats)
        return

    var = var_cols[0]
    out = []
    for row in reader:
        cname = row.get("Entity", "")
        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon:
            continue
        year = row.get("Year")
        val = safe_float(row.get(var))
        if val is None or not year:
            continue
        try:
            y = int(float(year))
        except:
            continue
        out.append({"country":canon,"iso2":row.get("Code",""),"year":y,"value":val})

    if out:
        save_records(kpi_id, out)
        stats["owid_success"] += 1
        stats["saved_records"] += len(out)
        log(f"[OK] OWID KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{source_code}_nodata.csv"), "w", encoding="utf-8").write(text)
        keep_or_dummy(kpi_id, f"OWID empty {source_code}", stats)

# ======================================================================
# 🕊️ UNHCR Fetch (ZIP/CSV, Encoding & Header-robust)
# ======================================================================
def process_unhcr(kpi_id, meta, countries, c_index, a_index, pending, stats):
    def _norm_local(s: str) -> str:
        s = "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]+", " ", s).strip()

    def _find_col(cols_list, *patterns):
        norms = {c: _norm_local(c) for c in cols_list}
        pats  = [(_norm_local(p) if isinstance(p, str) else "") for p in patterns if p]
        for c, cn in norms.items():
            for p in pats:
                if p and p in cn:
                    return c
        return None

    source_code = meta.get("source_code") or "population?download=true"
    base_url = "https://api.unhcr.org/population/v1/"
    if not source_code.startswith("population"):
        source_code = "population?download=true"
    url = f"{base_url}{source_code}"
    safe_code = re.sub(r'[^a-zA-Z0-9._-]', '_', source_code)

    # --- Download ---
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
    except Exception as e:
        log(f"[ERR] UNHCR fetch failed for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"UNHCR fetch failed {source_code}", stats)
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{safe_code}_error.txt"), "w", encoding="utf-8").write(str(e))
        return

    # --- Extract text from ZIP or response ---
    content_type = (resp.headers.get("Content-Type") or "").lower()
    text = None
    try:
        if "zip" in content_type or resp.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                name = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
                if not name:
                    raise Exception("No CSV file inside ZIP")
                raw = zf.read(name)
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = raw.decode("utf-16")
                log(f"[INFO] Extracted CSV '{name}' from UNHCR ZIP ({len(text)} bytes)")
        else:
            try:
                resp.encoding = "utf-8-sig"
                text = resp.text
                if len(text) < 10 or "PK\x03\x04" in text:
                    text = resp.content.decode("utf-16")
            except UnicodeDecodeError:
                text = resp.content.decode("utf-16")
    except Exception as e:
        log(f"[ERR] Failed to decode UNHCR response for {source_code}: {e}")
        keep_or_dummy(kpi_id, f"UNHCR decode error {source_code}", stats)
        return

    # --- Normalize newlines & detect dialect ---
    text = text.replace("\r\n","\n").replace("\r","\n")
    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=[",",";","\t"])
    except Exception:
        dialect = csv.excel

    try:
        reader = csv.DictReader(io.StringIO(text), dialect=dialect, skipinitialspace=True)
    except csv.Error as e:
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{safe_code}_raw.csv"), "w", encoding="utf-8").write(text)
        log(f"[ERR] CSV parse error for UNHCR ({safe_code}): {e}")
        keep_or_dummy(kpi_id, f"CSV parse error {safe_code}", stats)
        return

    cols = reader.fieldnames or []
    if not cols:
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{safe_code}_empty.csv"), "w", encoding="utf-8").write(text)
        log(f"[WARN] UNHCR CSV has no header → pending: {safe_code}")
        keep_or_dummy(kpi_id, f"UNHCR no header {safe_code}", stats)
        return

    # --- Column mapping ---
    country_key = (_find_col(cols, "country of asylum","territory of asylum","country / territory of asylum")
                   or _find_col(cols, "country of asylum/residence")
                   or _find_col(cols, "asylum"))
    year_key = _find_col(cols, "year")
    explicit_field = meta.get("unhcr_field")
    if explicit_field:
        value_key = _find_col(cols, explicit_field)
    else:
        value_key = (_find_col(cols, "refugees under unhcr's mandate")
                     or _find_col(cols, "refugees (incl. refugee-like situations)")
                     or _find_col(cols, "refugees"))

    if not all([country_key, year_key, value_key]):
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{safe_code}_cols.txt"), "w", encoding="utf-8").write("\n".join(cols))
        log(f"[WARN] UNHCR column mapping failed → pending: {safe_code}")
        keep_or_dummy(kpi_id, f"UNHCR unknown format {safe_code}", stats)
        return

    # --- Records ---
    out = []
    for row in reader:
        cname = (row.get(country_key) or "").strip()
        if not cname:
            continue
        canon = canonicalize_country(cname, c_index, a_index, countries, pending, stats)
        if not canon:
            continue
        y_raw = row.get(year_key)
        v_raw = row.get(value_key)
        if y_raw in (None,"") or v_raw in (None,""):
            continue
        val = safe_float(v_raw)
        if val is None:
            continue
        try:
            year = int(float(y_raw))
        except Exception:
            continue
        out.append({"country":canon,"iso2":"","year":year,"value":val})

    if out:
        log(f"[INFO] Parsed {len(out)} UNHCR records ({value_key})")
        save_records(kpi_id, out)
        stats["unhcr_success"] = stats.get("unhcr_success",0)+1
        stats["saved_records"] += len(out)
        log(f"[OK] UNHCR KPI saved: {kpi_id} ({len(out)} rows)")
    else:
        open(os.path.join(PENDING_DIR, f"{kpi_id}_{safe_code}_nodata.csv"), "w", encoding="utf-8").write(text)
        keep_or_dummy(kpi_id, f"UNHCR empty {safe_code}", stats)
        
# ======================================================================
# 🚀 Main
# ======================================================================
def main():
    ensure_dirs()
    log("=== Fetch started ===")

    # --- Bestehenden Status laden ---
    fetch_status = read_json(STATUS_FILE, {"kpis": {}})

    stats = {
        "countries_loaded": 0, "kpis_loaded": 0, "saved_records": 0, "dummies": 0,
        "mapped_ok": 0, "mapped_drop": 0, "mapped_pending": 0, "new_pending": set(),
        "wb_success": 0, "csv_success": 0, "owid_success": 0, "unhcr_success": 0,
        "errors": 0, "skipped": 0
    }

    # --- Metadaten & Mapping laden ---
    countries = read_json(COUNTRIES_FILE, {})
    mapping   = read_json(COUNTRY_MAP_FILE, {})
    pending   = read_json(COUNTRY_PENDING_FILE, {})
    c_index, a_index = build_country_indices(countries, mapping)
    stats["countries_loaded"] = len(countries)

    raw_kpis = read_json(AVAILABLE_FILE, [])
    kpi_list = [v for v in raw_kpis if isinstance(v, dict)]
    stats["kpis_loaded"] = len(kpi_list)

    # --- KPI-Schleife ---
    for meta in kpi_list:
        try:
            kpi_id = meta.get("filename") or meta.get("id") or meta.get("title") or "kpi"
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

            # Prüfen, ob Fetch nötig
            if not should_fetch(kpi_id, source_date, fetch_status):
                stats["skipped"] += 1
                log(f"[SKIP] {kpi_id} – local data up to date ({source_date})")
                continue

            # Quelle verarbeiten
            if source_type == "worldbank":
                process_worldbank(kpi_id, meta, countries, c_index, a_index, pending, stats)
            elif source_type == "csv":
                process_csv(kpi_id, meta, countries, c_index, a_index, pending, stats)
            elif source_type == "owid":
                process_owid(kpi_id, meta, countries, c_index, a_index, pending, stats)
            elif source_type == "unhcr":
                process_unhcr(kpi_id, meta, countries, c_index, a_index, pending, stats)
            else:
                keep_or_dummy(kpi_id, f"unknown source_type {source_type}", stats)

            # Status aktualisieren
            fetch_status.setdefault("kpis", {})[kpi_id] = {
                "source": meta.get("source") or meta.get("source_type") or "unknown",
                "url": meta.get("source_url") or meta.get("url") or "",
                "source_date": source_date or "Unknown",
                "last_fetch": now_utc()
            }

        except Exception as e:
            stats["errors"] += 1
            log(f"[ERR] {meta.get('title','unknown')} failed: {e}\n{traceback.format_exc()}")

    # --- Abschluss ---
    fetch_status["lastRun"] = now_utc()
    write_json(STATUS_FILE, fetch_status)
    write_json(COUNTRY_PENDING_FILE, pending)

    log(f"[INFO] fetch_status.json updated with {len(fetch_status.get('kpis',{}))} KPIs")

    summary = [
        "=== RealityCheck Fetch Report ===",
        f"Countries loaded:   {stats['countries_loaded']}",
        f"KPIs processed:    {stats['kpis_loaded']}",
        f"Saved records:     {stats['saved_records']}",
        "",
        f"WorldBank KPIs:    {stats['wb_success']}",
        f"CSV KPIs:          {stats['csv_success']}",
        f"OWID KPIs:         {stats['owid_success']}",
        f"UNHCR KPIs:        {stats['unhcr_success']}",
        "",
        f"Mapping OK:        {stats['mapped_ok']}",
        f"Mapping dropped:   {stats['mapped_drop']}",
        f"Mapping pending:   {stats['mapped_pending']}",
        "",
        f"Dummies created:   {stats['dummies']}",
        f"Skipped (up-to-date): {stats['skipped']}",
        f"Errors:            {stats['errors']}",
        "=================================",
        "✅ Fetch completed successfully\n"
    ]
    report = "\n".join(summary)
    print(report)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(report + "\n")

# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    main()
    try:
        import subprocess
        print("➡️ Starte fetch_overall_ranking.py ...")
        subprocess.run(["python", "scripts/fetch_overall_ranking.py"], check=True)
        print("✅ Overall Ranking erfolgreich erstellt.")
    except Exception as e:
        print(f"⚠️ Fehler beim Erstellen des Overall-Rankings: {e}")

    try:
        from analysis import run_global_analysis
        print("➡️ Starte globale KI-Analyse ...")
        run_global_analysis()
        print("✅ Globale Analyse abgeschlossen (data/analysis.md)")
    except Exception as e:
        print(f"⚠️ Fehler bei der Analyse: {e}") 