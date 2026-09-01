"""Tests for built-in adapter registration independent of live clients."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters.runtime import SourceRuntime
from builtin_adapters import build_builtin_adapter_registry
from fetch_core import AdapterMode
from source_contracts import SUPPORTED_SOURCE_TYPES


class BuiltinAdapterTests(unittest.TestCase):
    def make_runtime(self, root: Path) -> SourceRuntime:
        return SourceRuntime(
            log=Mock(),
            canonicalize_country=Mock(return_value="Germany"),
            safe_float=lambda value: float(value),
            resolve_iso2=Mock(return_value="DE"),
            resolve_iso3=Mock(return_value="DEU"),
            maybe_invert_records=lambda _kpi, _meta, rows: rows,
            save_records=Mock(),
            save_imf_records=Mock(),
            save_region_records=Mock(),
            keep_or_dummy=Mock(),
            mark_skip=Mock(),
            write_json=Mock(),
            now_utc=Mock(return_value="2026-08-01T00:00:00Z"),
            data_dir=root,
            meta_dir=root / "meta",
            source_csv_dir=root / "source_csv",
            region_source_csv_dir=root / "region_source_csv",
            pending_dir=root / "pending",
        )

    def test_registry_covers_contract_and_declares_all_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = build_builtin_adapter_registry(self.make_runtime(Path(tmp)))
        self.assertEqual(registry.source_types, SUPPORTED_SOURCE_TYPES)
        for source_type in {"worldbank", "owid", "data360", "csv", "unhcr", "noaa"}:
            self.assertIs(registry.get(source_type).mode, AdapterMode.IMMEDIATE)
            self.assertIsNotNone(registry.get(source_type).handler)
        self.assertIs(registry.get("imf").mode, AdapterMode.BATCH)
        self.assertIs(registry.get("special").mode, AdapterMode.SPECIAL)


if __name__ == "__main__":
    unittest.main()
