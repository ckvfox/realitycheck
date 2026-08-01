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

    def test_world_state_kpis_have_reviewed_ranking_defaults(self) -> None:
        registry = json.loads((ROOT / "data" / "meta" / "available_kpis.json").read_text(encoding="utf-8"))
        by_id = {item["filename"]: item for item in registry}
        included = {
            "basic_sanitation_access",
            "access_to_electricity",
            "lower_secondary_completion_rate",
            "prevalence_of_undernourishment",
            "real_gdp_per_capita_growth",
            "women_in_parliament",
            "terrestrial_protected_areas",
        }
        guardrails = {
            "refugees_hosted",
            "net_migration",
            "statistical_performance_indicator",
        }

        self.assertEqual(included | guardrails, set(by_id) & (included | guardrails))
        self.assertTrue(all(by_id[kpi]["relevance"] != "none" for kpi in included))
        self.assertTrue(all(by_id[kpi]["relevance"] == "none" for kpi in guardrails))
        self.assertEqual(by_id["prevalence_of_undernourishment"]["sort"], "lower")
        completion = by_id["lower_secondary_completion_rate"]
        self.assertEqual(completion["sort"], "target")
        self.assertEqual(completion["target_value"], 100)
        self.assertEqual(completion["relevance"], "low")
        self.assertIn("Values above 100%", completion["description"])

    def test_new_world_dashboard_kpis_are_explicitly_excluded_from_country_ranking(self) -> None:
        registry = json.loads((ROOT / "data" / "meta" / "available_kpis.json").read_text(encoding="utf-8"))
        by_id = {item["filename"]: item for item in registry}
        world_only = {
            "military_spending_sipri",
            "people_forcibly_displaced_worldwide",
            "climate_disaster_deaths",
            "people_affected_by_climate_disasters",
            "climate_disaster_damage_gdp",
            "global_mean_sea_level",
            "global_ocean_heat_content",
            "atmospheric_co2_concentration",
        }
        self.assertTrue(all(by_id[kpi]["world_kpi"] == "e" for kpi in world_only))

    def test_overall_defaults_prioritize_outcomes_over_ambiguous_proxies(self) -> None:
        registry = json.loads((ROOT / "data" / "meta" / "available_kpis.json").read_text(encoding="utf-8"))
        by_id = {item["filename"]: item for item in registry}
        high_outcomes = {
            "purchasing_power_parity", "life_expectancy_at_birth", "infant_mortality_rate",
            "access_to_basic_drinking_water", "air_quality_pm2_5_exposure", "democracy_index",
            "human_rights_index_vdem", "rule_of_law_index", "world_happiness_index",
            "global_peace_index", "intentional_homicides",
        }
        low_inputs = {
            "employment_to_population_ratio", "education_expenditure_of_gdp",
            "general_government_gross_debt_gdp", "human_development_index_hdi",
        }
        self.assertTrue(all(by_id[kpi]["relevance"] == "high" for kpi in high_outcomes))
        self.assertTrue(all(by_id[kpi]["relevance"] == "low" for kpi in low_inputs))
        self.assertEqual(by_id["big_mac_index"]["relevance"], "none")

    def test_household_energy_cohesion_and_mental_health_gap_kpis_are_registered(self) -> None:
        registry = json.loads((ROOT / "data" / "meta" / "available_kpis.json").read_text(encoding="utf-8"))
        by_id = {item["filename"]: item for item in registry}
        expected = {
            "median_income_or_consumption_per_day",
            "urban_inadequate_housing",
            "healthy_diet_unaffordable",
            "energy_import_dependency",
            "electricity_grid_losses",
            "interpersonal_trust",
            "trust_in_government",
            "suicide_mortality_rate",
        }
        self.assertTrue(expected.issubset(by_id))
        self.assertEqual(by_id["median_income_or_consumption_per_day"]["relevance"], "high")
        self.assertEqual(by_id["healthy_diet_unaffordable"]["relevance"], "high")
        self.assertEqual(by_id["urban_inadequate_housing"]["relevance"], "none")
        self.assertEqual(by_id["trust_in_government"]["relevance"], "none")
        self.assertTrue(all(by_id[kpi].get("analysis_guardrail") for kpi in expected))
        self.assertEqual(by_id["energy_import_dependency"]["sort"], "lower")
        self.assertEqual(by_id["suicide_mortality_rate"]["sort"], "lower")

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

    def test_invalid_publication_status_is_rejected(self) -> None:
        errors = validate_source_registry([
            {
                "filename": "candidate",
                "source_type": "worldbank",
                "source_code": "TEST",
                "publication_status": "maybe",
            }
        ])
        self.assertTrue(any("publication_status" in error for error in errors))

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
