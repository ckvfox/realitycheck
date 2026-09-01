"""Tests for the productive deployment allowlist and delta detection."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_deployment


class DeploymentPackagingTests(unittest.TestCase):
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
            with patch.object(prepare_deployment, "ROOT", root):
                inventory = {path.relative_to(root).as_posix() for path in prepare_deployment.iter_productive_files()}
        self.assertEqual(inventory, {"data/analysis.md", "data/sample.json", "index.html", "scripts/core.js"})

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


if __name__ == "__main__":
    unittest.main()
