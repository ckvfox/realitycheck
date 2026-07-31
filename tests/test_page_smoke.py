"""Offline smoke tests for local assets referenced by key public pages."""
from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
