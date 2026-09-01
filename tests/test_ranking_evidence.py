import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_fun_safe_rankings as rankings
from prompt_templates import build_fun_ranking_prompt, build_immigration_prompt, build_safe_haven_prompt


class RankingEvidenceTests(unittest.TestCase):
    def test_evidence_uses_latest_country_values_and_excludes_world(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "meta").mkdir()
            (data_dir / "meta" / "countries.json").write_text(
                json.dumps({"A": {}, "B": {}}), encoding="utf-8"
            )
            (data_dir / "meta" / "country_analysis_context.json").write_text(
                json.dumps({
                    "fields": {"context_metric": {"modes": ["test"], "unit": "class"}},
                    "countries": {
                        "A": {"context_metric": {"value": "low", "source": "Reviewed source", "as_of": "2026", "confidence": "medium"}},
                        "B": {"context_metric": {"value": "high", "as_of": "2026"}},
                    },
                }),
                encoding="utf-8",
            )
            criteria = {"metric_one": "higher", "metric_two": "lower", "metric_three": "higher"}
            for kpi in criteria:
                (data_dir / f"{kpi}.json").write_text(json.dumps([
                    {"country": "A", "year": 2023, "value": 1},
                    {"country": "A", "year": 2024, "value": 2},
                    {"country": "B", "year": 2024, "value": 3},
                    {"country": "World", "year": 2024, "value": 99},
                ]), encoding="utf-8")
            with (
                patch.object(rankings, "DATA_DIR", data_dir),
                patch.dict(rankings.RANKING_KPIS, {"test": criteria}),
            ):
                evidence = rankings.build_ranking_evidence("test")
        self.assertIn("metric_one=2", evidence)
        self.assertIn("metric_one=3", evidence)
        self.assertIn("context_metric=low class", evidence)
        self.assertNotIn("context_metric=high", evidence)
        self.assertNotIn("World", evidence)

    def test_evidence_can_exclude_top_list_countries_from_bottom_shortlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "meta").mkdir()
            (data_dir / "meta" / "countries.json").write_text(
                json.dumps({"Top": {}, "Bottom": {}}), encoding="utf-8"
            )
            criteria = {"one": "higher", "two": "higher", "three": "higher"}
            for kpi in criteria:
                (data_dir / f"{kpi}.json").write_text(json.dumps([
                    {"country": "Top", "year": 2024, "value": 2},
                    {"country": "Bottom", "year": 2024, "value": 1},
                ]), encoding="utf-8")
            with (
                patch.object(rankings, "DATA_DIR", data_dir),
                patch.dict(rankings.RANKING_KPIS, {"test": criteria}),
            ):
                evidence = rankings.build_ranking_evidence(
                    "test", direction="bottom", excluded_countries={"Top"}
                )
        self.assertIn("- Bottom", evidence)
        self.assertNotIn("- Top", evidence)

    def test_editorial_prompts_restore_intended_qualitative_dimensions_with_guardrails(self):
        fun = build_fun_ranking_prompt("- Example: world_happiness_index=7")
        safe = build_safe_haven_prompt("- Example: global_peace_index=1")
        prompt = build_immigration_prompt(2026, "- Example: metric=1")
        self.assertIn("beer", fun)
        self.assertIn("Lonely Planet", fun)
        self.assertIn("gently humorous", fun)
        self.assertIn("proximity to active conflict areas", safe)
        self.assertIn("alliances", safe)
        self.assertIn("visa and work-permit barriers", prompt)
        self.assertIn("not legal advice", prompt)
        self.assertIn("must come from the evidence", prompt)
        self.assertIn("Access: ... visa/work/residence ...; Destination: ...", prompt)
        self.assertIn("Top 20", fun)
        self.assertIn("Top 20", safe)
        self.assertIn("Top 20", prompt)
        self.assertIn("Bottom 20", build_fun_ranking_prompt(direction="bottom"))

    def test_semantic_validation_rejects_missing_mode_dimensions(self):
        base = [
            {"rank": rank, "country": f"Country {rank}", "reason": "Good quality of life."}
            for rank in range(1, 11)
        ]
        valid, reason = rankings._validate_ranking_payload(base, "Immigration Mode")
        self.assertFalse(valid)
        self.assertIn("accessibility", reason)

        for entry in base:
            entry["reason"] = "Strong domestic safety and climate resilience, with remote geography reducing conflict exposure."
        valid, reason = rankings._validate_ranking_payload(base, "Safe Haven Mode")
        self.assertTrue(valid, reason)

    def test_fun_validation_rejects_unsupported_quantified_weather(self):
        entries = [
            {"rank": rank, "country": f"Country {rank}", "reason": "Cheerful life with 2,000 sunshine hours."}
            for rank in range(1, 11)
        ]
        valid, reason = rankings._validate_ranking_payload(entries, "Fun Mode")
        self.assertFalse(valid)
        self.assertIn("weather", reason)

    def test_validation_supports_twenty_ranked_entries(self):
        entries = [
            {"rank": rank, "country": f"Country {rank}", "reason": "Qualitative, evidence-bound reason."}
            for rank in range(1, 21)
        ]
        valid, reason = rankings._validate_ranking_payload(entries, expected_count=20)
        self.assertTrue(valid, reason)

    def test_percentile_fit_treats_ties_equally(self):
        scores = rankings._percentile_fit({"A": 0, "B": 0, "C": 2}, "higher")
        self.assertEqual(scores["A"], scores["B"])
        self.assertGreater(scores["C"], scores["A"])

    def test_volatile_climate_damage_uses_five_year_average(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "climate_disaster_damage_gdp.json").write_text(json.dumps([
                {"country": "A", "year": 2020, "value": 1},
                {"country": "A", "year": 2021, "value": 2},
                {"country": "A", "year": 2022, "value": 3},
                {"country": "A", "year": 2023, "value": 4},
                {"country": "A", "year": 2024, "value": 10},
                {"country": "A", "year": 2019, "value": 100},
            ]), encoding="utf-8")
            with patch.object(rankings, "DATA_DIR", data_dir):
                values = rankings._latest_country_values("climate_disaster_damage_gdp", {"A"})
        self.assertEqual(values["A"], 4)

    def test_editorial_lenses_include_new_living_condition_evidence(self):
        self.assertIn("median_income_or_consumption_per_day", rankings.RANKING_KPIS["fun"])
        self.assertIn("healthy_diet_unaffordable", rankings.RANKING_KPIS["immigration"])
        self.assertIn("climate_disaster_damage_gdp", rankings.RANKING_KPIS["safe"])
        self.assertIn("energy_import_dependency", rankings.RANKING_KPIS["safe"])
        self.assertAlmostEqual(sum(rankings.BOTTOM_WEIGHTS["fun"].values()), 1.0)
        self.assertAlmostEqual(sum(rankings.BOTTOM_WEIGHTS["safe"].values()), 1.0)

    def test_committed_bottom_lists_match_deterministic_source_bound_method(self):
        for mode, filename in (
            ("fun", "fun_ranking_bottom.json"),
            ("safe", "safe_haven_ranking_bottom.json"),
        ):
            committed = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
            top_filename = "fun_ranking.json" if mode == "fun" else "safe_haven_ranking.json"
            top_countries = {
                entry["country"]
                for entry in json.loads((ROOT / "data" / top_filename).read_text(encoding="utf-8"))
            }
            expected = rankings.build_deterministic_bottom_ranking(
                mode, excluded_countries=top_countries
            )
            self.assertEqual(committed, expected)
            self.assertEqual(len({entry["country"] for entry in committed}), 20)

        safe_countries = {
            entry["country"]
            for entry in json.loads((ROOT / "data" / "safe_haven_ranking_bottom.json").read_text(encoding="utf-8"))
        }
        self.assertTrue({"Malaysia", "Malta", "Costa Rica"}.isdisjoint(safe_countries))
        self.assertGreaterEqual(
            len(safe_countries & {"Yemen", "Sudan", "Afghanistan", "Syria", "South Sudan", "Russia", "Somalia", "Ukraine"}),
            7,
        )

    def test_validation_rejects_duplicate_countries(self):
        entries = [
            {"rank": rank, "country": "Same", "reason": "Evidence-bound reason."}
            for rank in range(1, 11)
        ]
        valid, reason = rankings._validate_ranking_payload(entries)
        self.assertFalse(valid)
        self.assertIn("Duplicate country", reason)


if __name__ == "__main__":
    unittest.main()
