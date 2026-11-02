#!/usr/bin/env python3
"""Offline, read-only publication gate for the verified IBTrACS baseline.

Counts may be revised by NOAA and later seasons added. Historical keys must
survive, including the three observed South Atlantic seasons; do not invent zeros.
"""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

BASINS = {'NA', 'EP', 'WP', 'NI', 'SI', 'SP', 'SA'}
BASELINE_KEYS = {(b, y) for b in BASINS - {'SA'} for y in range(1980, 2026)}
BASELINE_KEYS |= {('SA', y) for y in (2004, 2010, 2011)}


def validate(rows, csv_rows):
    if rows != csv_rows:
        raise ValueError('IBTrACS JSON/CSV mismatch')
    keys = set()
    for row in rows:
        basin, year, value = row['region'], row['year'], row['value']
        if basin not in BASINS or type(year) is not int or not 1980 <= year < datetime.now(timezone.utc).year:
            raise ValueError('Invalid IBTrACS basin or completed season')
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0 or value != int(value):
            raise ValueError('IBTrACS count must be a finite positive integer')
        if row['scenario'] != 'historical' or row['horizon'] != '':
            raise ValueError('Invalid IBTrACS scenario/horizon')
        key = (basin, year)
        if key in keys:
            raise ValueError('Duplicate IBTrACS basin-season')
        keys.add(key)
    missing = BASELINE_KEYS - keys
    if missing:
        raise ValueError(f'IBTrACS verified historical seasons missing: {sorted(missing)}')


def verify(directory):
    stem = Path(directory) / 'tropical_cyclone_activity_basin'
    rows = json.loads(stem.with_suffix('.json').read_text(encoding='utf-8'))
    with stem.with_suffix('.csv').open(encoding='utf-8', newline='') as handle:
        csv_rows = [{**r, 'year': int(r['year']), 'value': float(r['value'])} for r in csv.DictReader(handle)]
    validate(rows, csv_rows)
    return len(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    args = parser.parse_args()
    print(f'IBTrACS validated: {verify(args.data_dir)} records; historical baseline retained')
