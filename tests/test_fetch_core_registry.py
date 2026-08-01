"""Unit tests for typed fetch orchestration and adapter contracts."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_core import (
    AdapterMode,
    AdapterRegistry,
    AdapterRegistryError,
    AdapterRequest,
    AdapterResult,
    SourceAdapter,
    build_status_entry,
    force_refresh_required,
)


class FetchCoreRegistryTests(unittest.TestCase):
    def make_request(self, output_dir: Path) -> AdapterRequest:
        return AdapterRequest(
            kpi_id="population",
            meta={"filename": "population", "source_type": "worldbank"},
            countries={},
            country_index={},
            alias_index={},
            pending={},
            stats={},
            output_dir=output_dir,
        )

    def test_immediate_adapter_dispatches_and_applies_result(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            SourceAdapter(
                "worldbank",
                handler=lambda request: AdapterResult(source_date="2026-01-01", data_year=2025, record_count=3),
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            request = self.make_request(Path(tmp))
            result = registry.dispatch("worldbank", request)
            result.apply_to(request.meta)
        self.assertEqual(request.meta["_latest_year"], 2025)
        self.assertEqual(result.record_count, 3)

    def test_duplicate_missing_and_deferred_dispatch_are_blocked(self) -> None:
        registry = AdapterRegistry()
        registry.register(SourceAdapter("imf", mode=AdapterMode.BATCH))
        with self.assertRaises(AdapterRegistryError):
            registry.register(SourceAdapter("imf", mode=AdapterMode.BATCH))
        with self.assertRaises(AdapterRegistryError):
            registry.ensure_complete({"imf", "owid"})
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(AdapterRegistryError):
            registry.dispatch("imf", self.make_request(Path(tmp)))

    def test_status_resolution_keeps_last_known_metadata(self) -> None:
        resolution = build_status_entry(
            {"source_type": "owid", "url": "https://example.test"},
            discovered_source_date="Unknown",
            previous={"source_date": "2025-12-01", "data_year": 2024},
            fetched_at="2026-08-01T10:00:00Z",
        )
        self.assertEqual(resolution.source_date, "2025-12-01")
        self.assertEqual(resolution.data_year, 2024)
        self.assertEqual(resolution.entry["last_fetch"], "2026-08-01T10:00:00Z")

    def test_force_refresh_policy_honors_flag_and_missing_status(self) -> None:
        status = {"kpis": {"population": {"source_date": "2025-01-01"}}}
        self.assertFalse(force_refresh_required(False, status))
        self.assertTrue(force_refresh_required(True, status))
        self.assertTrue(force_refresh_required(False, {"kpis": {}}))


if __name__ == "__main__":
    unittest.main()
