"""Regression tests for fail-closed fetch and validation gates."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline_guard import PipelineGuardError, ensure_fetch_succeeded, fetch_failure_reasons
from validation import validate_datasets


class PipelineGuardTests(unittest.TestCase):
    def test_clean_fetch_is_publishable(self) -> None:
        ensure_fetch_succeeded({"kpis_loaded": 2, "errors": 0, "dummies": 0})

    def test_errors_and_dummies_block_publication(self) -> None:
        stats = {"kpis_loaded": 2, "errors": 1, "dummies": 1}
        self.assertEqual(len(fetch_failure_reasons(stats)), 2)
        with self.assertRaises(PipelineGuardError):
            ensure_fetch_succeeded(stats)

    def test_empty_selection_blocks_publication(self) -> None:
        with self.assertRaises(PipelineGuardError):
            ensure_fetch_succeeded({"kpis_loaded": 0, "errors": 0, "dummies": 0})


class DatasetValidationTests(unittest.TestCase):
    def write_registry(self, root: Path, entries: list[dict]) -> Path:
        path = root / "available_kpis.json"
        path.write_text(json.dumps(entries), encoding="utf-8")
        return path

    def test_regular_source_requires_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self.write_registry(
                root,
                [{"filename": "population", "source_type": "worldbank", "source_code": "SP.POP.TOTL"}],
            )
            (root / "population.json").write_text('[{"country":"Germany","year":2024,"value":1}]', encoding="utf-8")
            errors = validate_datasets(root, registry)
            self.assertTrue(any("population.csv" in error for error in errors))

    def test_special_source_intentionally_requires_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self.write_registry(
                root,
                [{"filename": "geopolitical_risk_index", "source_type": "special", "source_code": "gpr.xls"}],
            )
            (root / "geopolitical_risk_index.json").write_text(
                '[{"country":"World","year":2024,"value":1}]', encoding="utf-8"
            )
            self.assertEqual(validate_datasets(root, registry), [])

    def test_test_mode_selects_only_starred_kpis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self.write_registry(
                root,
                [
                    {"filename": "test_kpi", "source_type": "worldbank", "source_code": "TEST", "test": "*"},
                    {
                        "filename": "production_only",
                        "source_type": "worldbank",
                        "source_code": "PROD",
                        "test": "",
                    },
                ],
            )
            (root / "test_kpi.json").write_text('[{"country":"Germany","year":2024,"value":1}]', encoding="utf-8")
            (root / "test_kpi.csv").write_text("country,year,value\nGermany,2024,1\n", encoding="utf-8")
            self.assertEqual(validate_datasets(root, registry, test_kpis_only=True), [])


if __name__ == "__main__":
    unittest.main()
