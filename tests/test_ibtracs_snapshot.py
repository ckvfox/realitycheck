"""Offline publication gate and negative regressions for IBTrACS."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_ibtracs import validate, verify


class IBTrACSSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / "data/tropical_cyclone_activity_basin.json").read_text())

    def test_committed_historical_coverage_and_csv_json_parity(self):
        self.assertGreaterEqual(verify(ROOT / "data"), 279)

    def test_rejects_missing_atlantic_even_when_csv_agrees(self):
        rows = [r for r in self.rows if r["region"] != "NA"]
        with self.assertRaisesRegex(ValueError, "historical seasons missing"):
            validate(rows, rows)

    def test_rejects_missing_sparse_south_atlantic_season(self):
        rows = [r for r in self.rows if (r["region"], r["year"]) != ("SA", 2011)]
        with self.assertRaisesRegex(ValueError, "historical seasons missing"):
            validate(rows, rows)

    def test_rejects_invalid_values_duplicates_and_format_mismatch(self):
        for value in (0, -1, 1.5, float("inf"), True):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[0]["value"] = value
                with self.assertRaises(ValueError):
                    validate(rows, rows)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate(self.rows + self.rows[:1], self.rows + self.rows[:1])
        with self.assertRaisesRegex(ValueError, "mismatch"):
            validate(self.rows, self.rows[:-1])

    def test_allows_noaa_count_revisions_and_additional_observed_keys(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["value"] += 1
        rows.append({"region": "SA", "year": 2012, "value": 1.0, "scenario": "historical", "horizon": ""})
        validate(rows, rows)

    def test_fetch_workflows_gate_before_packaging_upload_and_commit(self):
        for name in ("monthly-fetch", "manual-fetch", "manual-fetch-force", "manual-fetch-fast", "manual-fetch-force-fast"):
            text = (ROOT / f".github/workflows/{name}.yml").read_text()
            gate = text.index("-p test_ibtracs_snapshot.py")
            for command in ("python scripts/prepare_deployment.py", "python scripts/deploy_ftps.py", "git add data/"):
                self.assertLess(gate, text.index(command), name)
        text = (ROOT / ".github/workflows/monthly-fetch.yml").read_text()
        self.assertLess(text.index("-p test_builtin_adapters.py"), text.index("python ./scripts/fetch_data.py"))


if __name__ == "__main__":
    unittest.main()
