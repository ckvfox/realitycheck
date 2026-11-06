import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters.ilostat import productivity_records, release_info
from fetch_data import safe_float


class IloStatTests(unittest.TestCase):
    code = "GDP_2HRW_NOC_NB_A"

    def test_model_vintage_is_distinct_from_catalog_update_date(self):
        row = {
            "id": self.code,
            "indicator.label": "Output per hour worked, GDP constant 2021 international $ at PPP -- ILO modelled estimates, Nov. 2025",
            "freq": "A", "database": "ILOEST", "last.update": "02/01/2026 13:06:11", "n.records": "6324",
        }
        self.assertEqual(release_info([row], self.code), ("2026-01-02T13:06:11+00:00", 2025, 6324))
        with self.assertRaisesRegex(ValueError, "definition or model vintage"):
            release_info([dict(row, **{"indicator.label": row["indicator.label"].replace("hour", "worker")})], self.code)

    def test_excludes_vintage_year_forecasts_and_aggregates(self):
        countries = {f"Country {i}": {"iso_a3": str(i)} for i in range(150)}
        rows = [
            {"indicator": self.code.removesuffix("_A"), "time": str(year), "ref_area": code, "obs_value": "10"}
            for year in (2005, 2024, 2025, 2026)
            for code in ("WORLD", *(str(i) for i in range(150)))
        ]
        result = productivity_records(rows, countries, self.code, 2025, safe_float)
        self.assertEqual(len(result), 300)
        self.assertEqual({r["year"] for r in result}, {2005, 2024})
