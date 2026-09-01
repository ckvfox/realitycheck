"""Offline smoke tests for local assets referenced by key public pages."""
from __future__ import annotations

import json
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
KEY_PAGES = (
    "index.html",
    "world.html",
    "overall_ranking_countries.html",
    "analysis.html",
    "data_glossary.html",
    "germany-dossier.php",
)


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"script", "img"} and values.get("src"):
            self.references.append(str(values["src"]))
        if tag == "link" and values.get("href"):
            self.references.append(str(values["href"]))


class PublicPageSmokeTests(unittest.TestCase):
    def test_key_pages_exist_and_reference_existing_local_assets(self) -> None:
        missing: list[str] = []
        for relative_page in KEY_PAGES:
            page = ROOT / relative_page
            self.assertTrue(page.is_file(), relative_page)
            parser = AssetParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for reference in parser.references:
                if reference.startswith(("http://", "https://", "//", "data:")) or "<?" in reference:
                    continue
                path = urlsplit(reference).path
                if not path:
                    continue
                target = ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
                if not target.resolve().is_file():
                    missing.append(f"{relative_page}: {reference}")
        self.assertEqual(missing, [])

    def test_frontend_performance_and_accessibility_contracts(self) -> None:
        core = (ROOT / "scripts/core.js").read_text(encoding="utf-8")
        countries = (ROOT / "scripts/script.js").read_text(encoding="utf-8")
        world = (ROOT / "scripts/script_world.js").read_text(encoding="utf-8")
        ranking = (ROOT / "scripts/script_overall_ranking_countries.js").read_text(encoding="utf-8")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        analysis_page = (ROOT / "analysis.html").read_text(encoding="utf-8")
        styles = (ROOT / "style.css").read_text(encoding="utf-8")

        self.assertIn("JSON_REQUEST_CACHE", core)
        self.assertIn("function loadKPIData", core)
        self.assertLess(
            core.index("window.loadAllKPIData = loadAllKPIData;"),
            core.index("// 🧠 KPI Smart Analysis Loader"),
        )
        self.assertIn("DecompressionStream", core)
        self.assertIn("formatKpiAnalysisTimestamp", core)
        self.assertIn('timestamp.className = "kpi-analysis-timestamp"', core)
        self.assertIn("if (!visible && document.activeElement === btn)", core)
        self.assertLess(
            core.index("if (!visible && document.activeElement === btn)"),
            core.index('btn.setAttribute("aria-hidden", visible ? "false" : "true")'),
        )
        self.assertNotIn("ALL_DATA = await loadAllKPIData()", countries)
        self.assertIn('await loadKPIData(filename)', countries)
        self.assertNotIn("ALL_DATA = await loadAllKPIData()", world)
        self.assertIn("Promise.all(worldKpis.map", world)
        self.assertIn("calculateAdditiveShare", world)
        self.assertIn("calculateMedianMetric", world)
        self.assertIn("syncWorldMapUrl", world)
        self.assertIn('params.get("group")', world)
        self.assertIn('params.get("kpi")', world)
        self.assertIn('params.get("year")', world)
        self.assertIn('params.get("compare")', world)
        self.assertIn('params.get("value")', world)
        self.assertIn('params.get("aggregate")', world)
        world_page = (ROOT / "world.html").read_text(encoding="utf-8")
        self.assertIn('id="world-group-summary"', world_page)
        self.assertIn('id="worldMapKpiSelect"', world_page)
        self.assertIn('id="worldMapYearSelect"', world_page)
        self.assertIn('id="comparisonGroupSelect"', world_page)
        self.assertIn('id="worldMapValueMode"', world_page)
        self.assertIn('id="worldMapAggregationMode"', world_page)
        self.assertIn(".world-map-section .map-controls", styles)
        self.assertIn("grid-template-columns: repeat(12, minmax(0, 1fr))", styles)
        self.assertIn(".world-group-summary--comparison .world-group-summary__cards", styles)
        self.assertIn('world-group-summary__card--${modifier}', world)
        self.assertIn(".world-group-summary--comparison .world-group-summary__card--overlap", styles)
        self.assertIn("grid-column: 1 / -1", styles)
        self.assertIn("body.world-page .world-cluster", styles)
        self.assertIn("body.world-page #world-kpis .graph-block", styles)
        self.assertIn("body.world-page #world-kpis .kpi-desc", styles)
        self.assertIn("overflow-wrap: anywhere", styles)
        self.assertNotIn("margin: -.35rem 0 .75rem", styles)
        self.assertEqual(ranking.count('getElementById("calc-btn").addEventListener'), 1)
        self.assertEqual(ranking.count("let funOn = false;"), 1)
        self.assertIn("window.loadAllKPIData()", ranking)
        self.assertIn('OVERALL_WEIGHTS_STORAGE_KEY = "overallKPIWeightsV3"', ranking)
        self.assertIn("CURRENT_OVERALL_RESULTS", ranking)
        self.assertIn("function renderModeAnalysis", ranking)
        self.assertIn('getElementById("mode-analysis")', ranking)
        self.assertIn('mode === "fun"', ranking)
        self.assertIn('mode === "safe"', ranking)
        self.assertIn('mode === "immigration"', ranking)
        self.assertIn('fetch("data/fun_ranking_bottom.json?v=20260801-ranking-2")', ranking)
        self.assertIn('fetch("data/safe_haven_ranking_bottom.json?v=20260801-ranking-2")', ranking)
        self.assertIn('fetch("data/immigration_ranking_bottom.json?v=20260801-ranking-2")', ranking)
        self.assertIn('icons = "☔"', ranking)
        self.assertIn('icons = "💥"', ranking)
        self.assertIn('icons = "🚧"', ranking)
        self.assertIn("filter(e => !FUN_SET.has", ranking)
        self.assertIn("filter(e => !SAFE_SET.has", ranking)
        self.assertIn("filter(e => !IMMIG_SET.has", ranking)
        self.assertIn("obj.sum / obj.weightSum", ranking)
        self.assertIn("countryNames.has(d.country)", ranking)
        self.assertIn("percentileByValue", ranking)
        self.assertIn('meta.sort === "target"', ranking)
        self.assertLess(
            ranking.index("let funOn = false;"),
            ranking.index("function initModeSwitch"),
        )
        self.assertIn('id="view-status" role="status" aria-live="polite"', index)
        self.assertIn('class="visually-hidden"', index)
        self.assertIn("width: min(calc(100% - 2rem), 900px)", styles)
        self.assertIn("max-width: 900px", styles)
        self.assertIn("#map .leaflet-interactive:focus", styles)
        self.assertIn("outline: none", styles)
        self.assertIn("AI-generated analyses based on public datasets", analysis_page)
        self.assertNotIn("OpenAI GPT-4", analysis_page)

    def test_manifest_icon_dimensions_match_png(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for icon in manifest["icons"]:
            image = ROOT / icon["src"]
            with image.open("rb") as handle:
                header = handle.read(24)
            self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", header[16:24])
            self.assertEqual(icon["sizes"], f"{width}x{height}")


if __name__ == "__main__":
    unittest.main()
