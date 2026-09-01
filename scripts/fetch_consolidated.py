#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 RealityCheck – Consolidated KPI Split + Gzip Writer (Pathlib-Version)
──────────────────────────────────────────────────────────────
• Bündelt alle KPI-JSONs zu mehreren komprimierten Teil-Dateien (≈ 8 MB)
• Schreibt Index-Datei all_kpis_index.json mit Übersicht
• Kompatibel mit InfinityFree-Limit (~5 MB pro Datei)
"""

import json, gzip
from datetime import datetime, timezone
from pathlib import Path

from script_utils import ensure_utf8_stdout, read_json, safe_write_json

ensure_utf8_stdout()

# ======================================================================
# 🔧 Pfade (robust gegen OS-Unterschiede)
# ======================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR   = SCRIPT_DIR.parent.resolve()
DATA_DIR   = ROOT_DIR / "data"
META_PATH  = DATA_DIR / "meta" / "available_kpis.json"
OUT_PREFIX = DATA_DIR / "all_kpis_part"

MAX_SIZE_MB = 8.0  # Zielgröße pro Teil (InfinityFree Limit ≈5 MB)

# ======================================================================
# 🧰 Hilfsfunktionen
# ======================================================================

def get_file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)

def gzip_json(data, path: Path):
    """Write compressed JSON (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

# ======================================================================
# 🚀 Main
# ======================================================================
def main():
    print("🌍 Building consolidated KPI dataset (split + gzip)…")

    meta = read_json(META_PATH, default=[])
    if not meta:
        print("❌ No meta loaded – aborting.")
        return

    # === 1️⃣ Alle KPI-Dateien laden ===
    consolidated = {}
    for entry in meta:
        if entry.get("publication_status") == "pending_first_fetch":
            continue
        fname = entry.get("filename")
        if not fname:
            continue
        path = DATA_DIR / f"{fname}.json"
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            consolidated[fname] = data
        except Exception as e:
            print(f"⚠️ Failed to read {fname}.json: {e}")

    # === 2️⃣ Split nach Zielgröße ===
    parts = []
    current = {}
    counter = 1

    for k, v in consolidated.items():
        current[k] = v
        size_estimate = len(json.dumps(current)) / (1024 * 1024)
        if size_estimate >= MAX_SIZE_MB:
            out_path = OUT_PREFIX.with_name(f"{OUT_PREFIX.name}{counter}.json.gz")
            gzip_json(current, out_path)
            parts.append(out_path.name)
            print(f"✅ Wrote {out_path} ({get_file_size_mb(out_path):.2f} MB)")
            counter += 1
            current = {}

    # letzter Teil
    if current:
        out_path = OUT_PREFIX.with_name(f"{OUT_PREFIX.name}{counter}.json.gz")
        gzip_json(current, out_path)
        parts.append(out_path.name)
        print(f"✅ Wrote {out_path} ({get_file_size_mb(out_path):.2f} MB)")

    # === 3️⃣ Index-Datei sicher schreiben ===
    index_path = DATA_DIR / "all_kpis_index.json"
    index_data = {
        "parts": parts,
        "created": datetime.now(timezone.utc).isoformat(),
        "count": len(parts)
    }

    safe_write_json(index_path, index_data)
    print(f"📄 Index written → {index_path}")
    print(f"✅ Done ({len(parts)} parts total).")


# ======================================================================
# ▶ Start
# ======================================================================
if __name__ == "__main__":
    main()
