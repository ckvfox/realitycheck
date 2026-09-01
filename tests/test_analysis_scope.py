import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import analysis


class GlobalAnalysisScopeTests(unittest.TestCase):
    def test_world_series_uses_latest_global_value_and_five_year_change(self):
        entry = {"filename": "temperature", "title": "Temperature", "cluster": "Environment", "unit": "°C"}
        records = [
            {"country": "World", "year": 2019, "value": 1.0},
            {"country": "World", "year": 2024, "value": 1.5},
        ]
        line = analysis.build_kpi_snapshot(entry, records=records)
        self.assertIn("global value 1.50 in 2024", line)
        self.assertIn("+0.50 °C", line)

    def test_physical_anomalies_use_absolute_units_not_baseline_percentages(self):
        entry = {
            "filename": "sea_level", "title": "Sea level", "cluster": "Environment",
            "unit": "millimetres relative to reference",
        }
        records = [
            {"country": "World", "year": 2020, "value": 60.0},
            {"country": "World", "year": 2025, "value": 80.0},
        ]
        line = analysis.build_kpi_snapshot(entry, records=records)
        self.assertIn("+20.00 mm", line)
        self.assertNotIn("+33.3%", line)

    def test_country_series_uses_representative_year_not_thin_latest_year(self):
        entry = {"filename": "education", "title": "Education", "cluster": "Education", "unit": "%"}
        records = []
        for year, values in [(2019, range(10, 20)), (2024, range(20, 30)), (2025, [99])]:
            records.extend({"country": f"C{i}", "year": year, "value": value} for i, value in enumerate(values))
        countries = {f"C{i}" for i in range(10)}
        line = analysis.build_kpi_snapshot(entry, records=records, country_names=countries)
        self.assertIn("in 2024 across 10 countries", line)
        self.assertNotIn("in 2025", line)

    def test_country_snapshot_includes_traceable_extremes_groups_and_changes(self):
        entry = {"filename": "sample", "title": "Sample", "cluster": "Test", "unit": "index"}
        records = []
        for index, country in enumerate(["A", "B", "C", "D", "E", "F"]):
            records.extend([
                {"country": country, "year": 2019, "value": index + 1},
                {"country": country, "year": 2024, "value": (index + 1) * 2},
            ])
        line = analysis.build_kpi_snapshot(
            entry, records=records, country_names={"A", "B", "C", "D", "E", "F"},
            groups={"TestGroup": {"A", "B", "C", "D"}},
        )
        self.assertIn("Country evidence 2024", line)
        self.assertIn("Group medians: TestGroup=", line)
        self.assertIn("Largest observed changes", line)

    def test_cross_kpi_context_labels_association_as_non_causal(self):
        countries = {f"C{i}" for i in range(30)}
        meta = [
            {"filename": "one", "title": "One"},
            {"filename": "two", "title": "Two"},
        ]
        records = {
            "one": [{"country": f"C{i}", "year": 2024, "value": i} for i in range(30)],
            "two": [{"country": f"C{i}", "year": 2023, "value": 100 - i} for i in range(30)],
        }
        with patch.object(analysis, "iter_kpi_records", side_effect=lambda kpi: records[kpi]):
            result = analysis.build_cross_kpi_associations(meta, countries)
        self.assertIn("rho=-1.00", result["one"])
        self.assertIn("association is not causation", result["one"])

    def test_volatile_world_series_uses_five_year_averages(self):
        entry = {
            "filename": "disasters", "title": "Disasters", "cluster": "Environment",
            "unit": "people", "analysis_trend": "five_year_average",
        }
        records = [
            {"country": "World", "year": year, "value": value}
            for year, value in zip(range(2016, 2026), [10] * 5 + [20] * 5)
        ]
        line = analysis.build_kpi_snapshot(entry, records=records)
        self.assertIn("five-year average 20.00 for 2021–2025", line)
        self.assertIn("versus 2016–2020: +100.0%", line)

    def test_global_run_uses_complete_catalogue_even_for_incremental_update(self):
        summaries = ["one", "two", "three"]
        with (
            patch.object(analysis, "build_global_kpi_summaries", return_value=summaries),
            patch.object(analysis, "build_cross_kpi_associations", return_value={}),
            patch.object(analysis, "build_global_analysis_prompt", return_value="prompt") as prompt_builder,
            patch.object(analysis, "gpt_call", return_value="A complete analytical report."),
            patch.object(analysis, "safe_write_text"),
            patch.object(analysis, "safe_write_json") as write_json,
        ):
            analysis.run_global_analysis(["one_recent_kpi"])
        prompt_builder.assert_called_once_with(summaries)
        payload = write_json.call_args.args[1]
        self.assertEqual(payload["kpi_count"], 3)
        self.assertEqual(payload["scope"], "all_registered_kpis")

    def test_kpi_analysis_stores_an_exact_utc_generation_timestamp(self):
        meta = [{"filename": "sample", "title": "Sample", "cluster": "Test", "unit": "count"}]
        with (
            patch.object(analysis, "load_meta", return_value=meta),
            patch.object(analysis, "build_kpi_snapshot", return_value="snapshot"),
            patch.object(analysis, "gpt_call", return_value="Summary"),
            patch.object(analysis, "safe_write_json") as write_json,
            patch.object(analysis, "OUT_KPI", Path("missing-kpi-analysis.json")),
            patch.object(analysis.time, "sleep"),
        ):
            analysis.generate_kpi_analyses(Path("."), updated_only=["sample"])
        payload = write_json.call_args.args[1]["sample"]
        self.assertRegex(payload["generated_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        self.assertEqual(payload["last_update"], payload["generated_at"][:10])


if __name__ == "__main__":
    unittest.main()
