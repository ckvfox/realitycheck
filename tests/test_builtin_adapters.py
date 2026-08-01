"""Tests for built-in adapter wiring independent of live source clients."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from builtin_adapters import AdapterServices, build_builtin_adapter_registry
from fetch_core import AdapterMode, AdapterRequest
from source_contracts import SUPPORTED_SOURCE_TYPES


class BuiltinAdapterTests(unittest.TestCase):
    def make_services(self) -> AdapterServices:
        return AdapterServices(
            log=Mock(),
            get_worldbank_source_date=Mock(return_value="2026-01-01"),
            get_owid_source_date=Mock(return_value="2026-02-01"),
            process_worldbank=Mock(),
            process_owid=Mock(),
            process_csv=Mock(return_value=2025),
            process_unhcr=Mock(),
            fetch_data360=Mock(
                return_value=[{"REF_AREA": "DEU", "year": "2025", "value": "73.5"}]
            ),
            canonicalize_country=Mock(return_value="Germany"),
            safe_float=lambda value: float(value),
            resolve_iso2=Mock(return_value="DE"),
            save_records=Mock(),
            keep_or_dummy=Mock(),
        )

    def test_registry_covers_contract_and_declares_deferred_modes(self) -> None:
        registry = build_builtin_adapter_registry(self.make_services())
        self.assertEqual(registry.source_types, SUPPORTED_SOURCE_TYPES)
        self.assertIs(registry.get("imf").mode, AdapterMode.BATCH)
        self.assertIs(registry.get("special").mode, AdapterMode.SPECIAL)

    def test_data360_adapter_normalizes_and_returns_standard_result(self) -> None:
        services = self.make_services()
        registry = build_builtin_adapter_registry(services)
        stats = {"data360_success": 0, "saved_records": 0, "fetched": 0, "updated_kpis": set()}
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            request = AdapterRequest(
                kpi_id="press_freedom_index",
                meta={"source_type": "data360", "source_code": "RWB_SCORE"},
                countries={"Germany": {"iso2": "DE"}},
                country_index={},
                alias_index={},
                pending={},
                stats=stats,
                output_dir=output_dir,
            )
            result = registry.dispatch("data360", request)

        self.assertEqual((result.data_year, result.record_count), (2025, 1))
        self.assertEqual(stats["updated_kpis"], {"press_freedom_index"})
        saved_rows = services.save_records.call_args.args[1]
        self.assertEqual(saved_rows[0], {"country": "Germany", "iso2": "DE", "year": 2025, "value": 73.5})


if __name__ == "__main__":
    unittest.main()
