"""Offline acceptance for climate KPIs in the scheduled full refresh."""
import argparse
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_data
from fetch_core import AdapterRegistry, AdapterResult, SourceAdapter
from source_contracts import select_kpis


class MonthlyClimateRefreshTests(unittest.TestCase):
    def test_all_climate_sources_are_active_in_default_production_selection(self):
        registry = json.loads((ROOT / "data/meta/available_kpis.json").read_text(encoding="utf-8"))
        selected = {k["filename"]: k for k in select_kpis(registry).selected}
        expected = {
            "tropical_cyclone_activity_basin": "ibtracs", "wildfire_burned_area": "owid",
            "flood_affected_people": "owid", "extreme_heat_days": "worldbank", "drought_spei": "worldbank",
        }
        for name, source in expected.items():
            self.assertIn(name, selected)
            self.assertEqual(selected[name]["source_type"], source)
            self.assertNotEqual(selected[name].get("publication_status"), "pending_first_fetch")
            self.assertNotEqual(selected[name].get("fetch_policy"), "provider_restricted")
        for name in ["wildfire_burned_area", "flood_affected_people"]:
            self.assertTrue(selected[name]["owid_complete_years_only"])
            self.assertTrue(selected[name]["owid_countries_only"])
        for name in ["extreme_heat_days", "drought_spei"]:
            self.assertEqual(selected[name]["worldbank_source_id"], 75)

    def test_monthly_workflow_runs_unfiltered_pipeline_before_data_upload(self):
        text = (ROOT / ".github/workflows/monthly-fetch.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "0 3 1 * *"', text)
        command = next(line.strip() for line in text.splitlines() if line.strip().startswith("python ./scripts/fetch_data.py"))
        self.assertEqual(command, "python ./scripts/fetch_data.py 2>&1 | tee data/workflow_fetch_console.log")
        self.assertLess(text.index(command), text.index("python scripts/deploy_ftps.py --scope data"))

    def test_monthly_upload_targets_verified_domain_data_directory(self):
        text = (ROOT / ".github/workflows/monthly-fetch.yml").read_text(encoding="utf-8")
        import deploy_ftps
        self.assertEqual(deploy_ftps.REMOTE_ROOT, "/realitycheck.great-site.net/htdocs")
        self.assertIn("python scripts/deploy_ftps.py --scope data", text)
        self.assertLess(text.index("python scripts/prepare_deployment.py --mode full"),
                        text.index("python scripts/deploy_ftps.py --scope data"))
        self.assertNotIn("secrets.FTP_DIR", text)

    def test_full_fetch_updates_esg_even_when_wdi_release_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as patches:
            root = Path(tmp)
            entries = [
                {"filename":"wdi", "source_type":"worldbank", "source_code":"WDI"},
                {"filename":"heat", "source_type":"worldbank", "source_code":"HEAT", "worldbank_source_id":75},
                {"filename":"drought", "source_type":"worldbank", "source_code":"SPEI", "worldbank_source_id":75},
            ]
            files = {"AVAILABLE_FILE":entries, "COUNTRIES_FILE":{"Germany":{"iso3":"DEU"}},
                     "COUNTRY_MAP_FILE":{}, "COUNTRY_PENDING_FILE":{},
                     "STATUS_FILE":{"kpis":{e["filename"]:{"source_date":"2026-10-01", "data_year":2023} for e in entries}}}
            for key, payload in files.items():
                path = root / (key + ".json")
                path.write_text(json.dumps(payload), encoding="utf-8")
                patches.enter_context(patch.object(fetch_data, key, path))
            for entry in entries:
                (root / (entry["filename"] + ".json")).write_text('[{"country":"Germany","year":2023,"value":1}]',encoding="utf-8")
                (root / (entry["filename"] + ".csv")).write_text("country,iso2,year,value\nGermany,DE,2023,1\n",encoding="utf-8")
            resolved = []
            def source_date(meta):
                source = meta.get("worldbank_source_id", 2)
                resolved.append(source)
                return "2026-10-29" if source == 75 else "2026-10-01"
            def handler(request):
                fetch_data.save_records(request.kpi_id,[{"country":"Germany","iso2":"DE","year":2024,"value":2}],request.stats,request.output_dir)
                request.stats["updated_kpis"].add(request.kpi_id)
                request.stats["saved_records"] += 1
                request.stats["wb_success"] += 1
                return AdapterResult(source_date=request.meta["_discovered_source_date"],data_year=2024,record_count=1)
            registry = AdapterRegistry()
            registry.register(SourceAdapter("worldbank",handler=handler,source_date_resolver=source_date))
            for key, value in {"DATA_DIR":root,"ACTIVE_DATA_DIR":root,"ALLOW_MAPPING_WRITES":False,"LOG_FILE":str(root/"fetch_log.txt")}.items():
                patches.enter_context(patch.object(fetch_data,key,value))
            patches.enter_context(patch.object(fetch_data,"ensure_dirs"))
            patches.enter_context(patch.object(fetch_data,"get_openai_key",Mock(return_value="offline-test")))
            patches.enter_context(patch.object(fetch_data,"log"))
            patches.enter_context(patch.object(fetch_data,"build_builtin_adapter_registry",return_value=registry))
            result = fetch_data.main(argparse.Namespace(test=False,force=False,no_analysis=True,kpi=None))
            self.assertEqual(resolved,[2,75])
            self.assertEqual(result["updated_kpis"],{"heat","drought"})
            self.assertEqual(result["errors"],0)
            for name in ["heat","drought"]:
                payload = json.loads((root/(name+".json")).read_text())
                self.assertEqual(payload[0]["year"],2024)
            status = json.loads(fetch_data.STATUS_FILE.read_text())
            self.assertEqual(status["kpis"]["heat"]["source_date"],"2026-10-29")
            self.assertEqual(status["kpis"]["wdi"]["source_date"],"2026-10-01")
