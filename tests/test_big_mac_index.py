import csv
import gzip
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        self.assertEqual(len(prices), 52)
        self.assertEqual(
            [{k: v for k, v in row.items() if k != "iso2"} for row in current],
            [row for row in source if row["year"] == 2026],
        )
        for row in current:
            self.assertEqual(row["iso2"], countries[row["country"]]["iso_a2"])
            self.assertTrue(math.isfinite(row["value"]) and row["value"] > 0)

        self.assertEqual(prices["United States"], 6.22)
        self.assertAlmostEqual(prices["Switzerland"], 9.0419272929956)
        self.assertAlmostEqual(prices["China"], 3.91386542210669)
        for excluded in ("Germany", "Euro area", "Hong Kong"):
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
        self.assertEqual(meta["source_release_date"], "2026-07-01")
        self.assertEqual(status["source_date"], meta["source_release_date"] + "T00:00:00Z")
        self.assertEqual(status["data_year"], max(row["year"] for row in rows))
        self.assertEqual({row["year"] for row in rows}, set(range(2000, 2027)))
        self.assertEqual(max(row["year"] for row in rows if row["iso2"] == "DE"), 2022)
