"""Regression tests for deterministic manual CSV source auditing."""
from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_source_csv_updates import (
    _parse_latest_year_payload,
    extract_release_years,
    inspect_local_csv,
)


class CsvUpdateCheckTests(unittest.TestCase):
    def test_local_csv_profile_reports_latest_year_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.csv"
            path.write_text(
                "country,year,value\nGermany,2022,1\nFrance,2024,2\n",
                encoding="utf-8",
            )
            profile = inspect_local_csv(path)

        self.assertTrue(profile["valid"])
        self.assertEqual(profile["row_count"], 2)
        self.assertEqual(profile["latest_year"], 2024)
        self.assertEqual(len(profile["sha256"]), 64)

    def test_local_csv_profile_rejects_missing_contract_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.csv"
            path.write_text("country,year\nGermany,2024\n", encoding="utf-8")
            profile = inspect_local_csv(path)

        self.assertFalse(profile["valid"])
        self.assertIn("missing required columns: value", profile["issues"])

    def test_release_years_require_a_reviewed_source_pattern(self) -> None:
        html = "Archive 2022. The Environmental Performance Index EPI 2026 is available."
        years = extract_release_years(
            html,
            [r"(?:Environmental Performance Index|EPI)[^0-9]{0,30}(20\d{2})"],
            current_year=2026,
        )
        self.assertEqual(years, [2026])

    def test_unrelated_page_years_are_not_treated_as_releases(self) -> None:
        years = extract_release_years(
            "Copyright 2026. Previous dataset 2022.",
            [r"World Happiness Report[^0-9]{0,30}(20\d{2})"],
            current_year=2026,
        )
        self.assertEqual(years, [])

    def test_null_latest_year_is_a_valid_no_update_result(self) -> None:
        self.assertEqual(
            _parse_latest_year_payload('{"latest_year": null}', current_year=2026),
            (True, None),
        )

    def test_valid_year_is_returned(self) -> None:
        self.assertEqual(
            _parse_latest_year_payload('{"latest_year": "2026"}', current_year=2026),
            (True, 2026),
        )

    def test_invalid_payload_requests_a_retry(self) -> None:
        self.assertEqual(
            _parse_latest_year_payload("not json", current_year=2026),
            (False, None),
        )


if __name__ == "__main__":
    unittest.main()
