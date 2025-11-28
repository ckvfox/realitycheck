import zipfile
import csv
import io
from pathlib import Path
from typing import List, Dict, Optional

def fetch_worldbank_zipfile_local(zip_path: str) -> List[Dict[str, any]]:
    """
    Extracts and parses a World Bank indicator ZIP file (local), returning a list of records in the standard format.
    """
    records = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        data_csv = next(
            (name for name in zf.namelist() if name.lower().endswith('.csv') and 'metadata' not in name.lower()),
            None
        )
        if not data_csv:
            raise ValueError('No data CSV found in ZIP')
        raw_csv = zf.read(data_csv).decode('utf-8-sig', errors='replace')
    stream = io.StringIO(raw_csv)
    reader = csv.reader(stream)
    header = None
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) >= 4 and row[0].strip() == 'Country Name' and row[1].strip() == 'Country Code':
            header = row
            break
    if header is None:
        raise ValueError('Header row not found in CSV')
    data_rows = list(reader)
    year_columns = [
        (idx, col.strip())
        for idx, col in enumerate(header)
        if idx >= 4 and col and col.strip().isdigit()
    ]
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
            try:
                value = float(row[idx])
            except Exception:
                continue
            records.append({
                'country': country_name,
                'iso3': iso3,
                'year': int(year),
                'value': value
            })
    return records
