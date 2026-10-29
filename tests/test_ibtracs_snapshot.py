"""Publication gate for historical IBTrACS basin coverage and format parity."""
import csv
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IBTrACSSnapshotTests(unittest.TestCase):
    def test_historical_coverage_and_csv_json_parity(self):
        stem = ROOT / "data" / "tropical_cyclone_activity_basin"
        rows = json.loads(stem.with_suffix(".json").read_text())
        with stem.with_suffix(".csv").open(newline="") as handle:
            csv_rows = [{**r, "year": int(r["year"]), "value": float(r["value"])} for r in csv.DictReader(handle)]
        self.assertEqual(rows, csv_rows)
        keys = {(r["region"], r["year"]) for r in rows}
        self.assertEqual(len(keys), len(rows))
        self.assertEqual({r["region"] for r in rows}, {"NA", "EP", "WP", "NI", "SI", "SP", "SA"})
        # Verified satellite-era baseline. Later releases may add seasons; sparse
        # SA seasons must not be invented as zeros to make the matrix rectangular.
        for basin in ("NA", "EP", "WP", "NI", "SI", "SP"):
            self.assertTrue({(basin, y) for y in range(1980, 2026)} <= keys, basin)
        for row in rows:
            self.assertTrue(math.isfinite(row["value"]) and row["value"] > 0)
            self.assertEqual(row["value"], int(row["value"]))
            self.assertEqual(row["scenario"], "historical")
            self.assertEqual(row["horizon"], "")


if __name__ == "__main__":
    unittest.main()
