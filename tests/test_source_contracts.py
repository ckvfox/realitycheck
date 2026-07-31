"""Contract tests for adding and selecting KPI data sources."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from source_contracts import ensure_source_registry, select_kpis, validate_source_registry


class SourceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "kpi_registry.json"
        self.entries = json.loads(fixture.read_text(encoding="utf-8"))

    def test_representative_registry_satisfies_contract(self) -> None:
        ensure_source_registry(self.entries)

    def test_empty_registry_is_rejected(self) -> None:
        self.assertIn("at least one entry", validate_source_registry([])[0])

    def test_committed_registry_satisfies_contract(self) -> None:
        registry = json.loads((ROOT / "data" / "meta" / "available_kpis.json").read_text(encoding="utf-8"))
        ensure_source_registry(registry)

    def test_invalid_source_metadata_reports_all_relevant_errors(self) -> None:
        errors = validate_source_registry(
            [
                {"filename": "Bad Name", "source_type": "unknown", "test": "yes"},
                {"filename": "duplicate", "source_type": "csv", "source_code": "a.csv"},
                {"filename": "duplicate", "source_type": "csv", "source_code": "b.csv"},
            ]
        )
        message = "\n".join(errors)
        self.assertIn("invalid filename", message)
        self.assertIn("unsupported source_type", message)
        self.assertIn("test must be", message)
        self.assertIn("duplicate filename", message)

    def test_production_selection_excludes_disabled_entries(self) -> None:
        result = select_kpis(self.entries)
        self.assertEqual([item["filename"] for item in result.selected], ["population", "life_expectancy"])
        self.assertEqual(result.ignored, ("manual_index",))

    def test_test_selection_is_explicit_and_can_be_filtered_by_name(self) -> None:
        result = select_kpis(self.entries, test_mode=True, kpi="population")
        self.assertEqual([item["filename"] for item in result.selected], ["population"])
        self.assertEqual(result.ignored, ())


if __name__ == "__main__":
    unittest.main()
