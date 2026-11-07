import csv
import gzip
import json
import math
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters.big_mac import append_july_editions


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_csv(path, fields):
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fields:
            raise ValueError(f"Unexpected CSV schema: {reader.fieldnames}")
        return [
            {**row, "year": int(row["year"]), "value": float(row["value"])}
            for row in reader
        ]


class BigMacIndexTests(unittest.TestCase):
    def test_july_snapshot_matches_country_registry_and_published_formats(self):
        source = read_csv("scripts/source_csv/big_mac_index.csv", ["country", "year", "value"])
        published_csv = read_csv("data/big_mac_index.csv", ["country", "iso2", "year", "value"])
        published_json = read_json("data/big_mac_index.json")
        self.assertEqual(published_csv, published_json)

        current = [row for row in published_json if row["year"] == 2026]
        countries = read_json("data/meta/countries.json")
        prices = {row["country"]: row["value"] for row in current}
        self.assertEqual(len(current), len(prices))
        self.assertEqual(len(prices), 70)
        self.assertEqual(
            [{k: v for k, v in row.items() if k != "iso2"} for row in current if row["country"] in {r["country"] for r in source if r["year"] == 2026}],
            [row for row in source if row["year"] == 2026],
        )
        for row in current:
            self.assertEqual(row["iso2"], countries[row["country"]]["iso_a2"])
            self.assertTrue(math.isfinite(row["value"]) and row["value"] > 0)

        self.assertEqual(prices["United States"], 6.22)
        self.assertAlmostEqual(prices["Switzerland"], 9.0419272929956)
        self.assertAlmostEqual(prices["China"], 3.91386542210669)
        self.assertAlmostEqual(prices["Germany"], 6.99 / 0.87439)
        for excluded in ("Euro area", "Hong Kong"):
            self.assertNotIn(excluded, prices)

    def test_consolidated_snapshot_matches_country_view(self):
        parts = read_json("data/all_kpis_index.json")["parts"]
        for part in parts:
            with gzip.open(ROOT / "data" / part, "rt", encoding="utf-8") as handle:
                rows = json.load(handle).get("big_mac_index")
            if rows is not None:
                self.assertEqual(rows, read_json("data/big_mac_index.json"))
                return
        self.fail("Big Mac Index is missing from the consolidated dataset")

    def test_release_date_and_annual_coverage(self):
        rows = read_json("data/big_mac_index.json")
        meta = next(e for e in read_json("data/meta/available_kpis.json") if e["filename"] == "big_mac_index")
        status = read_json("data/fetch_status.json")["kpis"]["big_mac_index"]
        self.assertEqual(meta["unit"], "USD")
        self.assertEqual(meta["source_type"], "big_mac")
        self.assertEqual(status["source_date"], f'{status["data_year"]}-07-01T00:00:00Z')
        self.assertEqual(status["data_year"], max(row["year"] for row in rows))
        self.assertEqual({row["year"] for row in rows}, set(range(2000, status["data_year"] + 1)))
        self.assertEqual({row["year"] for row in rows if row["iso2"] == "DE" and 2022 <= row["year"] <= 2026}, set(range(2022, 2027)))


    def test_automatic_import_appends_only_complete_july_editions(self):
        countries = read_json("data/meta/countries.json")
        history = [{"country": "United States", "iso2": "US", "year": 2026, "value": 6.22}]
        baseline = "date,iso_a3,dollar_price,USD_raw\n2026-07-01,USA,99,0\n"
        january = "2027-01-01,USA,7.99,0\n"
        july = "2027-07-01,USA,6.50,0\n"
        excluded = "2027-07-01,EUZ,7.50,0.15\n2027-07-01,HKG,3.50,-0.46\n"
        today = date(2027, 11, 7)
        self.assertEqual(append_july_editions(baseline + january, history, countries, today), history)
        self.assertEqual(
            append_july_editions(baseline + january + july + excluded, history, countries, today),
            history + [{"country": "United States", "iso2": "US", "year": 2027, "value": 6.50}],
        )
        for invalid in (july + july, july.replace("6.50", "NaN"), july.replace("USA", "CHE")):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                append_july_editions(baseline + invalid, history, countries, today)


    def test_raw_prices_fill_missing_country_years_without_replacing_history(self):
        countries = read_json("data/meta/countries.json")
        existing = [{"country": "United States", "iso2": "US", "year": 2026, "value": 6.22}]
        export = "date,iso_a3,dollar_price\n2026-07-01,USA,6.22\n"
        raw = ("date,iso_a3,currency_code,local_price,dollar_ex\n"
               "2026-07-01,DEU,EUR,6.99,0.87439\n"
               "2026-07-01,EUZ,EUR,6.19,0.87439\n")
        result = append_july_editions(export, existing, countries, date(2026, 11, 7), raw)
        self.assertEqual(result[:1], existing)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["iso2"], "DE")
        self.assertAlmostEqual(result[1]["value"], 6.99 / 0.87439)
        self.assertEqual(append_july_editions(export, result, countries, date(2026, 11, 7), raw), result)
