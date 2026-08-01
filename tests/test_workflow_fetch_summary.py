"""Tests for the non-secret GitHub Actions fetch summary."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from write_fetch_summary import build_summary


class WorkflowFetchSummaryTests(unittest.TestCase):
    def test_summary_reports_result_and_updated_data_years(self) -> None:
        result = build_summary(
            job_status="success",
            run_url="https://github.example/run/1",
            fetch_status={
                "summary": {"lastRun": "2026-08-01T03:00:00Z", "updated": 1, "skipped": 84, "errors": 0},
                "kpis": {"access_to_electricity": {"data_year": 2024}},
            },
            fetch_state={"updated_kpis": ["access_to_electricity"]},
            manual_status={"summary": {"possible_updates": 4}},
        )

        self.assertIn("**Workflow status:** success", result)
        self.assertIn("**Fetcher errors:** 0", result)
        self.assertIn("`access_to_electricity` | 2024", result)
        self.assertIn("**Manual CSV update hints:** 4", result)

    def test_summary_remains_useful_when_fetch_files_are_missing(self) -> None:
        result = build_summary(
            job_status="failure",
            run_url="",
            fetch_status={},
            fetch_state={},
            manual_status={},
        )
        self.assertIn("**Workflow status:** failure", result)
        self.assertIn("No KPI replacement was recorded", result)


if __name__ == "__main__":
    unittest.main()
