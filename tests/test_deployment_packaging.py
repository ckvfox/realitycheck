"""Tests for the productive deployment allowlist and delta detection."""
from __future__ import annotations

import sys
import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_deployment


class DeploymentPackagingTests(unittest.TestCase):
    def fixture_registries(self, root):
        payloads = {
            "data/meta/available_kpis.json": [{"filename": "sample"}],
            "data/all_kpis_index.json": {"parts": ["all_kpis_part1.json.gz"]},
            "data/meta/countries.json": {"Germany": {"iso_a2": "DE", "flag": "images/flag/de.svg"}},
            "data/meta/region_sets.json": {},
        }
        for name, payload in payloads.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")
        (root / "data/all_kpis_part1.json.gz").write_bytes(b"fixture")
        return set(payloads) | {"data/all_kpis_part1.json.gz"}

    def test_secret_bearing_names_are_excluded_before_packaging(self):
        for name in ("credentials.json", "data/credentials-backup.json", "auth.json", "data/auth.json",
                     ".env", "nested/private.key", "nested/id_ed25519", "known_hosts", ".npmrc"):
            self.assertTrue(prepare_deployment.should_exclude(name), name)

    def test_explicit_baseline_is_used_and_invalid_baselines_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "baseline.json"
            with self.assertRaises(FileNotFoundError):
                prepare_deployment.load_previous_manifest(baseline)
            baseline.write_text(json.dumps({"manifest":{"world.html":"old"}}),encoding="utf-8")
            self.assertEqual(prepare_deployment.load_previous_manifest(baseline), {"world.html":"old"})
            baseline.write_text('{}',encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_deployment.load_previous_manifest(baseline)

    def test_framework_build_tree_is_the_only_handover_target(self) -> None:
        self.assertEqual(
            prepare_deployment.TARGET_FULL,
            prepare_deployment.ROOT / "build" / "deployment" / "full",
        )
        self.assertEqual(
            prepare_deployment.TARGET_DELTA,
            prepare_deployment.ROOT / "build" / "deployment" / "delta",
        )
        self.assertFalse(hasattr(prepare_deployment, "LEGACY_FULL"))
        self.assertFalse(hasattr(prepare_deployment, "LEGACY_DELTA"))

    def test_allowlist_accepts_productive_assets_only(self) -> None:
        self.assertTrue(prepare_deployment.is_allowed_productive("index.html"))
        self.assertTrue(prepare_deployment.is_allowed_productive("data/all_kpis_part1.json.gz"))
        self.assertTrue(prepare_deployment.is_allowed_productive("scripts/core.js"))
        self.assertTrue(prepare_deployment.is_allowed_productive("data/analysis.md"))
        self.assertFalse(prepare_deployment.should_exclude("data/analysis.md"))
        self.assertFalse(prepare_deployment.is_allowed_productive("scripts/fetch_data.py"))
        self.assertFalse(prepare_deployment.is_allowed_productive("scripts/unknown.js"))
        self.assertFalse(prepare_deployment.is_allowed_productive("data/test/fetch_status.json"))
        self.assertTrue(prepare_deployment.should_exclude("data/fetch_state.json"))
        self.assertTrue(prepare_deployment.should_exclude("data/manual_source_status.json"))
        self.assertTrue(prepare_deployment.should_exclude("data/meta/manual_csv_sources.json"))
        self.assertTrue(prepare_deployment.should_exclude("docs/runbook.md"))
        self.assertTrue(prepare_deployment.should_exclude("data/test/sample.json"))
        self.assertTrue(prepare_deployment.should_exclude("tracking.json"))
        self.assertTrue(prepare_deployment.should_exclude(".env"))

    def test_inventory_excludes_repository_and_backend_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "index.html": "ok",
                "data/sample.json": "[]",
                "data/analysis.md": "# Productive report",
                "data/test/sample.json": "[]",
                "data/manual_source_status.json": "{}",
                "data/meta/manual_csv_sources.json": "{}",
                "scripts/core.js": "const ok = true;",
                "scripts/fetch_data.py": "pass",
                "docs/notes.html": "private",
                "tracking.json": '{"total": 42}',
                ".env": "restricted",
            }
            for relative, content in paths.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            registries = self.fixture_registries(root)
            with patch.object(prepare_deployment, "ROOT", root):
                inventory = {path.relative_to(root).as_posix() for path in prepare_deployment.iter_productive_files()}
        self.assertEqual(inventory, {"data/analysis.md", "data/sample.json", "index.html", "scripts/core.js"} | registries)

    def test_unregistered_assets_and_backend_json_are_not_productive(self):
        for name in ("images/logo_bak.png", "images/logo_alt2.png", "images/original_translate.png",
                     "images/logo4.png", "images/Logo.PNG", "images/flag/ai.svg", "src/example.json",
                     "data/analysis.json", "data/overall_ranking.json", "data/master/area.json",
                     "data/meta/country_analysis_context.json", "data/meta/country_mappings_pending.json",
                     "data/country_mappings_pending.json", "new-page.html", "setup.php"):
            self.assertFalse(prepare_deployment.is_allowed_productive(name), name)

    def test_unsafe_registry_paths_and_missing_parts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(prepare_deployment, "ROOT", Path(tmp)):
            root = Path(tmp)
            self.fixture_registries(root)
            (root / "data/meta/available_kpis.json").write_text('[{"filename":"../outside"}]')
            with self.assertRaises(ValueError):
                prepare_deployment.iter_productive_files()
            self.fixture_registries(root)
            (root / "data/all_kpis_index.json").write_text('{"parts":["../../outside.json.gz"]}')
            with self.assertRaises(ValueError):
                prepare_deployment.iter_productive_files()
            self.fixture_registries(root)
            (root / "data/all_kpis_part1.json.gz").unlink()
            with self.assertRaises(ValueError):
                prepare_deployment.iter_productive_files()

    def test_delta_contains_only_new_or_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unchanged = root / "index.html"
            changed = root / "style.css"
            unchanged.write_text("same", encoding="utf-8")
            changed.write_text("new", encoding="utf-8")
            previous = {
                "index.html": prepare_deployment.sha256_of(unchanged),
                "style.css": "old-digest",
            }
            with patch.object(prepare_deployment, "ROOT", root):
                delta = prepare_deployment.detect_delta([unchanged, changed], previous)
        self.assertEqual(delta, [changed])

    def test_registry_updates_automatically_include_new_productive_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(prepare_deployment, "ROOT", Path(tmp)):
            root = Path(tmp)
            self.fixture_registries(root)
            prepare_deployment.iter_productive_files()  # Populate cache before a new release.
            updates = {
                "data/meta/available_kpis.json": [{"filename": "new_climate_kpi"}],
                "data/all_kpis_index.json": {"parts": ["all_kpis_part1.json.gz", "all_kpis_part7.json.gz"]},
                "data/meta/countries.json": {"New country": {"iso_a2": "FR", "flag": "images/flag/fr.svg"}},
                "data/meta/region_sets.json": {"new": {"geo_file": "regions_new_geo.json"}},
            }
            for name, payload in updates.items():
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            expected = {"data/new_climate_kpi.json", "data/all_kpis_part7.json.gz",
                        "images/flag/fr.svg", "data/meta/regions_new_geo.json"}
            for name in expected:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            paths = {p.relative_to(root).as_posix() for p in prepare_deployment.iter_productive_files()}
            self.assertTrue(expected <= paths)
            self.assertFalse(prepare_deployment.is_allowed_productive("data/not_registered.json"))

    def test_productive_symlink_is_rejected_before_reading_its_target(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(prepare_deployment, "ROOT", Path(tmp)):
            root = Path(tmp)
            self.fixture_registries(root)
            target = root / "unrelated.txt"
            target.write_text("fixture", encoding="utf-8")
            try:
                (root / "index.html").symlink_to(target)
            except OSError:
                self.skipTest("Symlink creation unavailable on this Windows account")
            with self.assertRaises(ValueError):
                prepare_deployment.iter_productive_files()


if __name__ == "__main__":
    unittest.main()
