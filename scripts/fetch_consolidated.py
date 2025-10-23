# ============================================================
# 🌍 RealityCheck – Consolidated KPI Split + Gzip Writer
# ============================================================

import os, json, gzip
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
META_PATH = os.path.join(DATA_DIR, "meta", "available_kpis.json")
OUT_PREFIX = os.path.join(DATA_DIR, "all_kpis_part")

MAX_SIZE_MB = 8.0  # Zielgröße pro Teil (InfinityFree Limit ~5 MB)

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {path}: {e}")
        return {}

def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def gzip_json(data, path):
    """Write compressed JSON with UTF-8"""
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

def main():
    print("🌍 Building consolidated KPI dataset (split + gzip)...")

    meta = load_json(META_PATH)
    if not meta:
        print("❌ No meta loaded – aborting.")
        return

    consolidated = {}
    for entry in meta:
        fname = entry.get("filename")
        if not fname:
            continue
        path = os.path.join(DATA_DIR, f"{fname}.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            consolidated[fname] = data
        except Exception as e:
            print(f"⚠️ Failed to read {fname}.json: {e}")

    # 🧩 Split nach Größe
    parts = []
    current = {}
    counter = 1
    size_estimate = 0

    for k, v in consolidated.items():
        current[k] = v
        size_estimate = len(json.dumps(current)) / (1024 * 1024)
        if size_estimate >= MAX_SIZE_MB:
            out_path = f"{OUT_PREFIX}{counter}.json.gz"
            gzip_json(current, out_path)
            parts.append(os.path.basename(out_path))
            print(f"✅ Wrote {out_path} ({get_file_size_mb(out_path):.2f} MB)")
            counter += 1
            current = {}
            size_estimate = 0

    # letzter Teil
    if current:
        out_path = f"{OUT_PREFIX}{counter}.json.gz"
        gzip_json(current, out_path)
        parts.append(os.path.basename(out_path))
        print(f"✅ Wrote {out_path} ({get_file_size_mb(out_path):.2f} MB)")

    # Index-Datei schreiben
    index_path = os.path.join(DATA_DIR, "all_kpis_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({
            "parts": parts,
            "created": datetime.now(timezone.utc).isoformat(),
            "count": len(parts)
        }, f, indent=2)
    print(f"📄 Index written → {index_path}")
    print(f"✅ Done ({len(parts)} parts total).")


if __name__ == "__main__":
    main()
