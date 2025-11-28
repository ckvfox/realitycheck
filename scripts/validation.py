import os
import json
import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / 'data'
META_DIR = DATA_DIR / 'meta'
PENDING_DIR = DATA_DIR / 'pending'
MASTER_DIR = DATA_DIR / 'master'
LOG_FILE = DATA_DIR / 'validation_log.txt'
KPI_META_FILE = META_DIR / 'available_kpis.json'

# Utility functions
def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    print(msg)

def check_file_exists_and_nonempty(path):
    if not path.exists():
        log(f"❌ MISSING: {path}")
        return False
    if path.stat().st_size == 0:
        log(f"❌ EMPTY: {path}")
        return False
    return True

def sample_compare_json(new_file, master_file, sample_size=5):
    try:
        with open(new_file, encoding='utf-8') as f:
            new_data = json.load(f)
        with open(master_file, encoding='utf-8') as f:
            master_data = json.load(f)
        # Sample comparison: check first N records
        for i in range(min(sample_size, len(master_data))):
            if master_data[i] != new_data[i]:
                log(f"⚠️ SAMPLE MISMATCH in {new_file.name} at record {i}: {master_data[i]} != {new_data[i]}")
                return False
        return True
    except Exception as e:
        log(f"❌ ERROR comparing {new_file} and {master_file}: {e}")
        return False

def sample_compare_csv(new_file, master_file, sample_size=5):
    try:
        with open(new_file, encoding='utf-8') as f:
            new_rows = list(csv.reader(f))
        with open(master_file, encoding='utf-8') as f:
            master_rows = list(csv.reader(f))
        for i in range(1, min(sample_size+1, len(master_rows))):
            if master_rows[i] != new_rows[i]:
                log(f"⚠️ SAMPLE MISMATCH in {new_file.name} at row {i}: {master_rows[i]} != {new_rows[i]}")
                return False
        return True
    except Exception as e:
        log(f"❌ ERROR comparing {new_file} and {master_file}: {e}")
        return False

def main():
    log("==== RealityCheck Data Validation Started ====")
    # 1. Inventory all expected KPI files
    with open(KPI_META_FILE, encoding='utf-8') as f:
        kpis = json.load(f)
    missing_files = []
    for kpi in kpis:
        # Skip KPIs with test = 'o'
        if str(kpi.get('test', '')).strip().lower() == 'o':
            continue
        fname = kpi['filename']
        for ext in ['json', 'csv']:
            # geopolitcal_risk_index.csv wird nicht mehr erwartet
            if fname == 'geopolitical_risk_index' and ext == 'csv':
                continue
            fpath = DATA_DIR / f"{fname}.{ext}"
            if not check_file_exists_and_nonempty(fpath):
                missing_files.append(str(fpath))
    # 2. Check meta and pending dirs
    for meta_file in META_DIR.glob('*.json'):
        check_file_exists_and_nonempty(meta_file)
    for pending_file in PENDING_DIR.glob('*.json'):
        check_file_exists_and_nonempty(pending_file)
    # 3. Master file comparison for Land Area and Human Rights Index
    for base, ext in [("area", "json"), ("area", "csv"), ("human_rights_index_vdem", "json"), ("human_rights_index_vdem", "csv")]:
        new_file = DATA_DIR / f"{base}.{ext}"
        master_file = MASTER_DIR / f"{base}.{ext}"
        if check_file_exists_and_nonempty(master_file) and check_file_exists_and_nonempty(new_file):
            if ext == 'json':
                sample_compare_json(new_file, master_file)
            else:
                sample_compare_csv(new_file, master_file)
    log("==== Validation Complete ====")
    if missing_files:
        log(f"❌ {len(missing_files)} files missing or empty. See above.")
    else:
        log("✅ All expected files present and non-empty.")
    log("Suggestions: Check for plausible value ranges, outliers, and year coverage in future.")

if __name__ == '__main__':
    main()
