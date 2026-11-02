"""Tests for built-in adapter registration independent of live clients."""
from __future__ import annotations

import sys
import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters import ibtracs
from adapters.runtime import SourceRuntime
from builtin_adapters import build_builtin_adapter_registry
from fetch_core import AdapterMode, AdapterRequest
from source_contracts import SUPPORTED_SOURCE_TYPES


class BuiltinAdapterTests(unittest.TestCase):
    def run_ibtracs(self, rows):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerows([["SID", "SEASON", "BASIN"], [" ", "Year", " "]])
        writer.writerows(rows)
        runtime = self.make_runtime(Path("unused"))
        request = AdapterRequest(
            "tropical_cyclone_activity_basin", {}, {}, {}, {}, {},
            {"saved_records": 0}, Path("isolated-output"),
        )
        result = ibtracs.run(request, runtime=runtime, http_get=Mock(return_value=Mock(
            status_code=200, content=buffer.getvalue().encode("utf-8"),
        )))
        return runtime, request, result

    def test_ibtracs_preserves_north_atlantic_and_deduplicates_fixes(self):
        runtime, request, result = self.run_ibtracs([
            ["storm-a", 2020, " NA "], ["storm-a", 2020, "NA"],
            [" storm-a ", 2020, "NA"], ["storm-b", 2020, "NA"],
            ["storm-a", 2020, "EP"], ["storm-a", 2021, "NA"],
            *[[f"storm-{basin}", 2020, basin] for basin in ["WP", "NI", "SI", "SP", "SA"]],
        ])
        args, kwargs = runtime.save_region_records.call_args
        actual = {(row["region"], row["year"]): row["value"] for row in args[1]}
        self.assertEqual(actual, {
            ("NA", 2020): 2.0, ("NA", 2021): 1.0,
            **{(basin, 2020): 1.0 for basin in ["EP", "WP", "NI", "SI", "SP", "SA"]},
        })
        self.assertEqual(kwargs["output_dir"], request.output_dir)
        self.assertEqual(result.record_count, 8)
        self.assertEqual(result.data_year, 2021)
        self.assertEqual(request.stats["saved_records"], 8)
        runtime.keep_or_dummy.assert_not_called()

    def test_ibtracs_excludes_missing_keys_and_invalid_seasons(self):
        runtime, _, result = self.run_ibtracs([
            ["valid", 2020, "NA"],
            ["", 2020, "NA"], ["  ", 2020, "NA"],
            ["blank-basin", 2020, ""], ["space-basin", 2020, "  "],
            ["blank-season", "", "NA"], ["space-season", "  ", "NA"],
            ["invalid-season", "unknown", "NA"],
            ["current", ibtracs.datetime.now().year, "NA"],
            ["future", ibtracs.datetime.now().year + 1, "NA"],
        ])
        runtime.save_region_records.assert_called_once()
        self.assertEqual(runtime.save_region_records.call_args.args[1], [
            {"region": "NA", "year": 2020, "value": 1.0, "scenario": "historical", "horizon": ""},
        ])
        self.assertEqual(result.record_count, 1)

    def test_ibtracs_empty_input_preserves_previous_data(self):
        runtime, _, result = self.run_ibtracs([["", "", ""], [" ", " ", " "]])
        runtime.save_region_records.assert_not_called()
        runtime.keep_or_dummy.assert_called_once()
        self.assertEqual(result.record_count, 0)

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
