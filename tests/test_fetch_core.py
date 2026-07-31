"""Network-free regression tests for core fetch transformations and output isolation."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_data


def make_stats() -> dict:
    return {
        "mapped_ok": 0,
        "mapped_drop": 0,
        "mapped_pending": 0,
        "new_pending": set(),
        "saved_records": 0,
        "wb_success": 0,
        "owid_success": 0,
        "errors": 0,
        "dummies": 0,
        "trimmed_records": 0,
        "trimmed_kpis": set(),
        "updated_kpis": set(),
    }


class FakeResponse:
    status_code = 200
    text = "Entity,Code,Year,Value\nGermany,DEU,2024,81.2\n"


class FetchCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.countries = {"Germany": {"iso2": "DE", "iso3": "DEU"}}
        self.c_index, self.a_index = fetch_data.build_country_indices(
            self.countries, {"Deutschland": "Germany", "Aggregate": ""}
        )

    def test_numeric_and_country_normalization(self) -> None:
        self.assertEqual(fetch_data.safe_float("1,25"), 1.25)
        self.assertIsNone(fetch_data.safe_float("n/a"))
        stats = make_stats()
        pending: dict[str, str] = {}
        self.assertEqual(
            fetch_data.canonicalize_country(
                "Deutschland", self.c_index, self.a_index, self.countries, pending, stats
            ),
            "Germany",
        )
        self.assertIsNone(
            fetch_data.canonicalize_country("Aggregate", self.c_index, self.a_index, self.countries, pending, stats)
        )
        self.assertEqual((stats["mapped_ok"], stats["mapped_drop"]), (1, 1))

    def test_inversion_does_not_mutate_input(self) -> None:
        rows = [{"country": "Germany", "year": 2024, "value": 0.2}]
        with patch.object(fetch_data, "log"):
            result = fetch_data.maybe_invert_records("index", {"invert": "*"}, rows)
        self.assertEqual(result[0]["value"], 0.8)
        self.assertEqual(rows[0]["value"], 0.2)

    def test_save_records_trims_unsafe_years_and_writes_both_formats(self) -> None:
        current_year = datetime.now().year
        records = [
            {"country": "Germany", "iso2": "DE", "year": 1899, "value": 1},
            {"country": "Germany", "iso2": "DE", "year": current_year, "value": 2},
            {"country": "Germany", "iso2": "DE", "year": current_year + 1, "value": 3},
        ]
        stats = make_stats()
        with tempfile.TemporaryDirectory() as tmp, patch.object(fetch_data, "log"):
            output = Path(tmp)
            fetch_data.save_records("sample", records, stats, output_dir=output)
            payload = json.loads((output / "sample.json").read_text(encoding="utf-8"))
            with (output / "sample.csv").open(encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
        self.assertEqual(len(payload), 1)
        self.assertEqual(len(csv_rows), 1)
        self.assertEqual(stats["trimmed_pre1900"], 1)
        self.assertEqual(stats["trimmed_future"], 1)

    def test_failed_fetch_preserves_last_known_good_files(self) -> None:
        stats = make_stats()
        with tempfile.TemporaryDirectory() as tmp, patch.object(fetch_data, "log"):
            output = Path(tmp)
            (output / "sample.json").write_text('[{"value": 7}]', encoding="utf-8")
            (output / "sample.csv").write_text("country,year,value\nGermany,2024,7\n", encoding="utf-8")
            fetch_data.keep_or_dummy("sample", "fetch failed", stats, output_dir=output)
            self.assertEqual(json.loads((output / "sample.json").read_text(encoding="utf-8"))[0]["value"], 7)
        self.assertEqual((stats["errors"], stats["dummies"]), (1, 1))

    def test_owid_adapter_writes_only_to_requested_test_directory(self) -> None:
        stats = make_stats()
        pending: dict[str, str] = {}
        with tempfile.TemporaryDirectory() as tmp, patch.object(fetch_data.requests, "get", return_value=FakeResponse()), patch.object(
            fetch_data, "get_source_date_from_owid", return_value="2024-01-01"
        ), patch.object(fetch_data, "log"):
            output = Path(tmp)
            fetch_data.process_owid(
                "life_expectancy",
                {"source_code": "life.csv"},
                self.countries,
                self.c_index,
                self.a_index,
                pending,
                stats,
                output_dir=output,
            )
            self.assertTrue((output / "life_expectancy.json").is_file())
            self.assertTrue((output / "life_expectancy.csv").is_file())

    def test_worldbank_adapter_honors_metadata_output_directory(self) -> None:
        stats = make_stats()
        pending: dict[str, str] = {}
        rows = [{"country": {"value": "Germany"}, "countryiso3code": "DEU", "date": "2024", "value": 5}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            fetch_data, "get_source_date_from_worldbank", return_value="2024-01-01"
        ), patch.object(fetch_data, "fetch_worldbank_series", return_value=(rows, None)), patch.object(fetch_data, "log"):
            output = Path(tmp)
            fetch_data.process_worldbank(
                "population",
                {"source_code": "SP.POP.TOTL", "output_dir": output},
                self.countries,
                self.c_index,
                self.a_index,
                pending,
                stats,
            )
            self.assertTrue((output / "population.json").is_file())
            self.assertTrue((output / "population.csv").is_file())


if __name__ == "__main__":
    unittest.main()
