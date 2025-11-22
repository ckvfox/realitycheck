import json
import os

# Paths
status_path = os.path.join('data', 'fetch_status.json')
data_dir = 'data'

# Load fetch_status.json
with open(status_path, encoding='utf-8') as f:
    status = json.load(f)
status_kpis = set(status.get('kpis', {}).keys())

# List all KPI JSON files (excluding meta and special files)
all_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and not f.startswith('meta')]
# Remove known non-KPI files
specials = {'fetch_status.json', 'fetch_state.json', 'fetch_log.txt', 'country_mappings.json', 'country_mappings_pending.json', 'countries.json', 'groups.json', 'available_kpis.json', 'overall_ranking.json', 'fun_ranking.json', 'safe_haven_ranking.json', 'analysis.json', 'analysis_outliers.json', 'analysis.md'}
kpi_files = [f for f in all_files if f not in specials]
kpi_names = set(f[:-5] for f in kpi_files)  # strip .json

# Find missing
missing = kpi_names - status_kpis
extra = status_kpis - kpi_names

print(f"KPI files in data/: {len(kpi_names)}")
print(f"KPIs in fetch_status.json: {len(status_kpis)}")
print(f"Missing in fetch_status.json: {missing}")
print(f"Extra in fetch_status.json (not in data/): {extra}")

# Optionally, print info about the missing one
for m in missing:
    print(f"\nDetails for missing KPI: {m}")
    json_path = os.path.join(data_dir, m + '.json')
    if os.path.exists(json_path):
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
        print(f"  Rows: {len(data)}")
        if data:
            print(f"  First row: {data[0]}")
    else:
        print("  No data file found.")
