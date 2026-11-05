import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters.public_annual import EUROSTAT_FILTERS, ember_records, eurostat_records
from fetch_data import safe_float


class PublicAnnualTests(unittest.TestCase):
    countries = {
        "Germany": {"iso_a2": "DE", "iso_a3": "DEU"},
        "Greece": {"iso_a2": "GR", "iso_a3": "GRC"},
    }

    def test_ember_uses_published_total_generation_only(self):
        text = """Area,Area type,ISO 3 code,Year,Electricity source,Emissions intensity (gCO2e/kWh)
World,Region,,2025,Total generation,460.116
Germany,Country,DEU,2025,Total generation,334.117
Germany,Country,DEU,2025,Wind,11
Greece,Country,GRC,2025,Total generation,
"""
        rows = list(ember_records(text, self.countries, safe_float))
        self.assertEqual([(row["country"], row["value"]) for row in rows],
                         [("World", 460.116), ("Germany", 334.117)])

    def test_eurostat_preserves_sparse_values_and_greek_country_code(self):
        axes = {name: {value: 0} for name, value in EUROSTAT_FILTERS.items()}
        axes = {"time": {"2024": 0, "2025": 1}, **axes,
                "geo": {"EL": 1, "DE": 0, "EU27_2020": 2}}
        payload = {
            "class": "dataset", "id": list(axes), "size": [len(index) for index in axes.values()],
            "dimension": {name: {"category": {"index": index}} for name, index in axes.items()},
            "value": {"0": 12.0, "2": 8.0, "3": 11.2, "4": 0.0, "5": 7.6},
        }
        rows = list(eurostat_records(payload, self.countries, safe_float))
        self.assertEqual([(row["iso2"], row["year"], row["value"]) for row in rows],
                         [("DE", 2024, 12.0), ("", 2024, 8.0), ("DE", 2025, 11.2), ("GR", 2025, 0.0), ("", 2025, 7.6)])
        payload["dimension"]["sex"]["category"]["index"] = {"F": 0}
        with self.assertRaisesRegex(ValueError, "population filters"):
            list(eurostat_records(payload, self.countries, safe_float))
