"""Network-free contract tests for the remaining source adapters."""
from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters import csv_source, data360, imf, noaa, owid, special, unhcr
from adapters.runtime import SourceRuntime
from fetch_core import AdapterRequest


class Response:
    status_code = 200
    headers: dict[str, str] = {}
    text = ""
    content = b""

    def __init__(self, *, payload=None, text="", content=b""):
        self.payload = payload
        self.text = text
        self.content = content

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def make_stats() -> dict:
    return {
        "mapped_ok": 0, "mapped_drop": 0, "mapped_pending": 0, "new_pending": set(),
        "saved_records": 0, "csv_success": 0, "data360_success": 0, "owid_success": 0,
        "noaa_success": 0,
        "unhcr_success": 0, "imf_success": 0, "updated": 0, "fetched": 0,
        "errors": 0, "dummies": 0, "skipped": 0, "skipped_breakdown": {},
        "updated_kpis": set(),
    }


class SourceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.countries = {"Germany": {"iso2": "DE", "iso3": "DEU"}}

    def runtime(self, root: Path) -> SourceRuntime:
        return SourceRuntime(
            log=Mock(),
            canonicalize_country=lambda name, *_: "Germany" if str(name) in {"Germany", "DE", "DEU"} else None,
            safe_float=lambda value: float(value),
            resolve_iso2=lambda *_: "DE",
            resolve_iso3=lambda *_args, **_kwargs: "DEU",
            maybe_invert_records=lambda _kpi, _meta, rows: rows,
            save_records=Mock(),
            save_imf_records=Mock(),
            keep_or_dummy=Mock(),
            mark_skip=Mock(),
            write_json=Mock(),
            now_utc=Mock(return_value="2026-08-01T00:00:00Z"),
            data_dir=root / "production",
            meta_dir=root / "meta",
            source_csv_dir=root / "source_csv",
            pending_dir=root / "pending",
        )

    def request(self, root: Path, source_type: str, meta: dict) -> AdapterRequest:
        return AdapterRequest(
            kpi_id=f"{source_type}_sample",
            meta=meta,
            countries=self.countries,
            country_index={"germany": "Germany", "de": "Germany", "deu": "Germany"},
            alias_index={},
            pending={},
            stats=make_stats(),
            output_dir=root / "test-output",
        )

    def test_csv_adapter_reads_maintained_source_and_isolates_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            runtime.source_csv_dir.mkdir(parents=True)
            (runtime.source_csv_dir / "sample.csv").write_text(
                "country,year,value\nGermany,2024,12.5\n", encoding="utf-8"
            )
            request = self.request(root, "csv", {"source_code": "sample.csv"})
            result = csv_source.run(request, runtime=runtime)
            self.assertEqual(result.record_count, 1)
            runtime.save_records.assert_called_once()
            self.assertTrue((request.output_dir / "pending" / "csv_sample.md5").is_file())

    def test_data360_adapter_normalizes_api_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(
                root,
                "data360",
                {"database_id": "DB", "source_code": "IND", "unit_measure": "SCORE"},
            )
            response = Response(payload={"value": [{"REF_AREA": "DEU", "TIME_PERIOD": "2024", "OBS_VALUE": "7.5"}]})
            get = Mock(return_value=response)
            result = data360.run(request, runtime=runtime, http_get=get)
            self.assertEqual((result.data_year, result.record_count), (2024, 1))
            runtime.save_records.assert_called_once()
            self.assertEqual(get.call_args.kwargs["params"]["UNIT_MEASURE"], "SCORE")

    def test_data360_prefers_newer_maintained_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            raw_dir = runtime.source_csv_dir.parent / "source_raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "fallback.csv").write_text(
                "REF_AREA,TIME_PERIOD,OBS_VALUE\nDEU,2025,8.5\n", encoding="utf-8"
            )
            request = self.request(
                root,
                "data360",
                {"database_id": "DB", "source_code": "IND", "fallback_file": "fallback.csv"},
            )
            response = Response(
                payload={"value": [
                    {"REF_AREA": "DEU", "TIME_PERIOD": "2024", "OBS_VALUE": "7.5"},
                    {"REF_AREA": "DEU", "TIME_PERIOD": "2025", "OBS_VALUE": None},
                ]}
            )
            result = data360.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual(result.data_year, 2025)
            saved_rows = runtime.save_records.call_args.args[1]
            self.assertEqual(saved_rows[0]["value"], 8.5)

    def test_owid_world_series_does_not_require_code_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            runtime = replace(runtime, canonicalize_country=Mock(return_value=None))
            request = self.request(
                root,
                "owid",
                {"source_code": "natural-disasters.csv", "_discovered_source_date": "2024-01-01"},
            )
            request.kpi_id = "number_of_recorded_natural_disasters"
            response = Response(text="entity,year,n_events\nAll disasters,2024,17\n")
            result = owid.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual((result.data_year, result.record_count), (2024, 1))
            saved_rows = runtime.save_records.call_args.args[1]
            self.assertEqual(saved_rows[0]["iso2"], "OWID_WRL")

    def test_owid_selects_and_sums_named_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = replace(self.runtime(root), canonicalize_country=Mock(return_value=None))
            request = self.request(root, "owid", {
                "source_code": "climate-disasters.csv",
                "owid_sum_columns": ["flood", "storm"],
                "_discovered_source_date": "2026-01-01",
            })
            response = Response(text="entity,code,year,flood,earthquake,storm\nWorld,OWID_WRL,2025,4,99,6\n")
            result = owid.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual((result.data_year, result.record_count), (2025, 1))
            self.assertEqual(runtime.save_records.call_args.args[1][0]["value"], 10.0)

    def test_owid_annualizes_day_series_and_drops_incomplete_latest_year(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = replace(self.runtime(root), canonicalize_country=Mock(return_value=None))
            request = self.request(root, "owid", {
                "source_code": "monthly.csv",
                "owid_time_column": "day",
                "owid_value_column": "value",
                "owid_aggregation": "annual_mean",
                "_discovered_source_date": "2026-01-01",
            })
            response = Response(text=(
                "entity,code,day,value\n"
                "World,OWID_WRL,2024-01-15,2\nWorld,OWID_WRL,2024-02-15,4\n"
                "World,OWID_WRL,2025-01-15,8\n"
            ))
            result = owid.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual((result.data_year, result.record_count), (2024, 1))
            self.assertEqual(runtime.save_records.call_args.args[1][0]["value"], 3.0)

    def test_owid_restricted_dataset_is_a_non_blocking_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(root, "owid", {"source_code": "restricted.csv"})
            response = Response(payload={"error": "This chart contains non-redistributable data that we are not allowed to re-share."})
            response.status_code = 403
            result = owid.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual(result.record_count, 0)
            runtime.mark_skip.assert_called_once()
            runtime.keep_or_dummy.assert_not_called()

    def test_owid_source_date_uses_current_metadata_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.runtime(Path(tmp))
            response = Response(payload={"columns": {"value": {"lastUpdated": "2026-07-31"}}})
            get = Mock(return_value=response)
            source_date = owid.resolve_source_date(
                {"source_code": "sample.csv?useColumnShortNames=true"},
                runtime=runtime,
                http_get=get,
            )
            self.assertEqual(source_date, "2026-07-31")
            self.assertEqual(get.call_args.args[0], "https://ourworldindata.org/grapher/sample.metadata.json")

    def test_owid_variable_api_preserves_projection_years(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(
                root,
                "owid",
                {
                    "source_code": "mean-years-of-schooling-long-run.csv",
                    "owid_variable_id": 809139,
                    "_discovered_source_date": "2025-03-25",
                },
            )
            responses = {
                "https://api.ourworldindata.org/v1/indicators/809139.metadata.json": Response(
                    payload={"dimensions": {"entities": {"values": [{"id": 1, "name": "Germany", "code": "DEU"}]}}}
                ),
                "https://api.ourworldindata.org/v1/indicators/809139.data.json": Response(
                    payload={"values": [13.2, 13.4], "years": [2020, 2025], "entities": [1, 1]}
                ),
            }
            result = owid.run(request, runtime=runtime, http_get=lambda url, **_kwargs: responses[url])
            self.assertEqual((result.data_year, result.record_count), (2025, 2))
            saved_rows = runtime.save_records.call_args.args[1]
            self.assertEqual(saved_rows[-1], {"country": "Germany", "iso2": "DEU", "year": 2025, "value": 13.4})

    def test_unhcr_adapter_normalizes_plain_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(root, "unhcr", {"source_code": "population", "unhcr_field": "refugees"})
            response = Response(text="Country of asylum,Year,Refugees\nGermany,2024,123\n")
            result = unhcr.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual((result.data_year, result.record_count), (2024, 1))
            runtime.save_records.assert_called_once()

    def test_noaa_sea_level_averages_mission_handover_and_excludes_partial_year(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(root, "noaa", {"source_code": "https://example.test/sea.csv"})
            response = Response(text=(
                "# NOAA comment\n"
                "year,Jason-3,Sentinel-6MF\n"
                "2024.10,80,82\n2024.80,84,\n2026.01,,90\n"
            ))
            result = noaa.run(request, runtime=runtime, http_get=lambda *args, **kwargs: response)
            self.assertEqual((result.data_year, result.record_count), (2024, 1))
            self.assertEqual(runtime.save_records.call_args.args[1][0]["value"], 82.5)

    def test_unhcr_global_displacement_combines_non_overlapping_population_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            request = self.request(root, "unhcr", {
                "source_code": "population",
                "unhcr_mode": "global_forced_displacement",
                "year_from": 2025,
            })
            def get(url, **_kwargs):
                if "/population/?" in url:
                    return Response(payload={"items": [{
                        "year": 2025, "refugees": 10, "asylum_seekers": 2, "oip": 3, "idps": 999,
                    }]})
                if "/unrwa/?" in url:
                    return Response(payload={"items": [{"year": 2025, "total": 5}]})
                return Response(payload={"items": [{"year": 2025, "total": 20}]})
            result = unhcr.run(request, runtime=runtime, http_get=get)
            self.assertEqual((result.data_year, result.record_count), (2025, 1))
            self.assertEqual(runtime.save_records.call_args.args[1][0]["value"], 40.0)

    def test_imf_batch_uses_shared_runtime_and_updates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            session = Mock()
            session.get.return_value = Response(payload={"values": {"GGXWDG_NGDP": {"DEU": {"2024": 62.1}}}})
            stats = make_stats()
            status = {"kpis": {}}
            imf.fetch_batch(
                [{"filename": "debt", "source_code": "GGXWDG_NGDP"}],
                countries=self.countries,
                country_index={"deu": "Germany"},
                alias_index={},
                pending={},
                fetch_status=status,
                stats=stats,
                force_all_updates=True,
                output_dir=root / "test-output",
                runtime=runtime,
                should_fetch=Mock(return_value=True),
                session=session,
            )
            runtime.save_imf_records.assert_called_once()
            self.assertEqual(status["kpis"]["debt"]["data_year"], 2024)
            self.assertEqual(stats["imf_success"], 1)

    def test_special_gpr_adapter_writes_to_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = self.runtime(root)
            frame = pd.DataFrame({"month": ["01.01.2024", "01.02.2024"], "GPR": [100, 120]})
            with patch.object(special.pd, "read_excel", return_value=frame):
                status = special.fetch_geopolitical_risk_index(
                    output_dir=root / "test-output",
                    runtime=runtime,
                    http_get=lambda *args, **kwargs: Response(content=b"workbook"),
                )
            self.assertIsNotNone(status)
            runtime.write_json.assert_called_once()
            self.assertEqual(runtime.write_json.call_args.args[0].parent, root / "test-output")


if __name__ == "__main__":
    unittest.main()
