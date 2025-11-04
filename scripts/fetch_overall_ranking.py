#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Overall Ranking Generator (Meta-Version)
─────────────────────────────────────────────
• Pfade angepasst auf /data/meta/
• Bewertungslogik: only higher / lower / target
• Ausschluss: relevance="none" oder world_kpi="e"
• Fortschritts- und Fehler-Output
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ======================================================================
# 🔧 Pfade (pathlib-Version – robust gegen OS-Unterschiede)
# ======================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR   = SCRIPT_DIR.parent.resolve()
DATA_DIR   = ROOT_DIR / "data"
META_DIR   = DATA_DIR / "meta"

COUNTRIES_FILE       = META_DIR / "countries.json"
AVAILABLE_FILE       = META_DIR / "available_kpis.json"
LOG_FILE             = DATA_DIR / "fetch_log.txt"
OUTPUT_FILE          = DATA_DIR / "overall_ranking.json"  # ✅ hinzugefügt

# ======================================================================
# 🧰 Hilfsfunktionen
# ======================================================================
def log(msg: str):
    """Schreibt Zeitstempel + Nachricht in Konsole & Logdatei (UTC)."""
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')} UTC] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def get_latest_values(entries):
    """Findet den neuesten Wert pro Land."""
    latest = {}
    for e in entries:
        country = e.get("country")
        year = e.get("year")
        value = e.get("value")
        if not country or value is None:
            continue
        if country not in latest or year > latest[country]["year"]:
            latest[country] = {"year": year, "value": value}
    return latest
# ======================================================================
# 💾 Safe Write Helper
# ======================================================================
def safe_write_json(path: Path, data):
    """Garantiert sicheres Schreiben einer JSON-Datei mit UTF-8 und Verzeichnis-Erstellung."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"💾 JSON saved successfully → {path.relative_to(ROOT_DIR)} ({len(data)} records)")
    except Exception as e:
        log(f"❌ Failed to write JSON file {path}: {e}")

# ======================================================================
# 🚀 Main
# ======================================================================
def main():
    log("=== Overall Ranking Generation Started ===")

    if not AVAILABLE_FILE.exists():
        log(f"[ERR] Missing {AVAILABLE_FILE}")
        return

    available = load_json(AVAILABLE_FILE)
    valid_kpis = {}

    # === KPI-Auswahl (Filterung) ===
    for k in available:
        sort = k.get("sort")
        world_kpi = k.get("world_kpi")
        relevance = k.get("relevance", "normal")

        if relevance == "none":
            continue
        if world_kpi == "e":
            continue
        if sort not in ["higher", "lower", "target"]:
            continue

        filename = k.get("filename")
        if not filename:
            continue

        valid_kpis[filename] = k

    log(f"✅ {len(valid_kpis)} KPIs considered for ranking")

    all_ranks = {}
    missing = []

    # === KPI-Durchlauf ===
    for filename, meta in valid_kpis.items():
        filepath = DATA_DIR / f"{filename}.json"
        if not filepath.exists():
            missing.append(filename)
            log(f"⚠️ Missing file: {filename}.json")
            continue

        try:
            data = load_json(filepath)
        except Exception as e:
            log(f"⚠️ Could not read {filename}: {e}")
            continue

        latest = get_latest_values(data)
        sort_type = meta.get("sort")
        target_val = float(meta.get("target_value", 0))
        values = [v["value"] for v in latest.values() if isinstance(v.get("value"), (int, float))]

        if not values:
            log(f"⚠️ No numeric values for {filename}")
            continue

        # === Sortierung nach KPI-Typ ===
        if sort_type == "higher":
            sorted_countries = sorted(latest.items(), key=lambda x: x[1]["value"], reverse=True)
        elif sort_type == "lower":
            sorted_countries = sorted(latest.items(), key=lambda x: x[1]["value"])
        elif sort_type == "target":
            sorted_countries = sorted(latest.items(), key=lambda x: abs(x[1]["value"] - target_val))
        else:
            continue

        # === Rangvergabe ===
        for rank, (country, _) in enumerate(sorted_countries, start=1):
            if country not in all_ranks:
                all_ranks[country] = {"ranks": {}, "kpi_count": 0}
            all_ranks[country]["ranks"][filename] = rank
            all_ranks[country]["kpi_count"] += 1

    # === Zusammenfassung ===
    result = [
        {"country": country, "ranks": info["ranks"], "kpi_count": info["kpi_count"]}
        for country, info in all_ranks.items()
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    safe_write_json(OUTPUT_FILE, result)


    log(f"✅ overall_ranking.json written to {OUTPUT_FILE}")

    if missing:
        log(f"⚠️ Missing {len(missing)} files: {', '.join(missing[:10])} ...")

    # ============================================================
    # 🧠 Trigger Fun & Safe Haven AI Rankings (safe subprocess)
    # ============================================================
    try:
        log("➡️ Starting fun/safe haven ranking generation ...")
        subprocess.run(["python", str(SCRIPT_DIR / "generate_fun_safe_rankings.py")], check=True)
        log("✅ Fun & Safe Haven rankings successfully generated.")
    except Exception as e:
        log(f"⚠️ Fun/Safe Haven ranking generation failed: {e}")

# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    main()
