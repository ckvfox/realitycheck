#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – Overall Ranking Generator (Meta-Version)
-------------------------------------------------------
• Pfade angepasst auf /data/meta/
• Verzicht auf normalize_name(), stattdessen meta["filename"]
• Bewertungslogik: only higher / lower / target
• Ausschluss: relevance="none" oder world_kpi="e"
• Klarer Fortschritts- und Fehler-Output
"""

import os
import json
from datetime import datetime

# ======================================================================
# 🔧 Pfade
# ======================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR   = os.path.join(ROOT_DIR, "data")
META_DIR   = os.path.join(DATA_DIR, "meta")

AVAILABLE_FILE = os.path.join(META_DIR, "available_kpis.json")
OUTPUT_FILE    = os.path.join(DATA_DIR, "overall_ranking.json")
LOG_FILE       = os.path.join(DATA_DIR, "fetch_log.txt")

# ======================================================================
# 🧰 Hilfsfunktionen
# ======================================================================
def log(msg: str):
    """Schreibt Zeitstempel + Nachricht in Konsole & Logdatei."""
    line = f"[{datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
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
# 🚀 Main
# ======================================================================
def main():
    log("=== Overall Ranking Generation Started ===")

    if not os.path.exists(AVAILABLE_FILE):
        log(f"[ERR] Missing {AVAILABLE_FILE}")
        return

    available = load_json(AVAILABLE_FILE)
    valid_kpis = {}

    # === KPI-Auswahl (Filterung) ===
    for k in available:
        sort = k.get("sort")
        world_kpi = k.get("world_kpi")
        relevance = k.get("relevance", "normal")

        # Ausschlüsse ----------------------------------------------------
        if relevance == "none":
            continue            # 1️⃣ explizit ausgeschlossen
        if world_kpi == "e":
            continue            # 2️⃣ global-only KPI
        if sort not in ["higher", "lower", "target"]:
            continue            # 3️⃣ kein Ranking-Kriterium

        filename = k.get("filename")
        if not filename:
            continue

        valid_kpis[filename] = k

    log(f"✅ {len(valid_kpis)} KPIs considered for ranking")

    all_ranks = {}
    missing = []

    # === KPI-Durchlauf ===
    for filename, meta in valid_kpis.items():
        filepath = os.path.join(DATA_DIR, f"{filename}.json")
        if not os.path.exists(filepath):
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

    # === JSON speichern ===
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    log(f"✅ overall_ranking.json written to {OUTPUT_FILE}")

    if missing:
        log(f"⚠️ Missing {len(missing)} files: {', '.join(missing[:10])} ...")

    log("=== Overall Ranking Generation Finished ===")

# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    main()
