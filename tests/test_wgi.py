import io
import sys
import unittest
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters.wgi import governance_estimates, latest_release
from fetch_data import safe_float


class WgiReleaseTests(unittest.TestCase):
    def test_selects_newest_official_workbook(self):
        root = "https://datacatalogfiles.worldbank.org/ddh-published/0038026/"
        old = root + "DR1/WGI%202025%20Governance%20Estimates%20and%20Scores%20(1996-2024).xlsx"
        new = root + "DR2/WGI%202026%20Governance%20Estimates%20and%20Scores%20(1996-2025).xlsx"
        fake = new.replace("datacatalogfiles.worldbank.org", "other.example")
        self.assertEqual(latest_release(f'"{old}" "{new}"'), (new.replace("%20", " "), 2025))
        with self.assertRaises(ValueError):
            latest_release(fake)

    def test_reads_estimates_on_existing_scale_and_rejects_partial_history(self):
        countries = {f"Country {i}": {"iso_a3": f"X{i:03}"} for i in range(189)}
        countries["Taiwan"] = {"iso_a3": "TWN", "iso_a2": "TW"}
        book = Workbook(write_only=True)
        sheet = book.create_sheet("ge")
        sheet.append(["Economy (code)", "Year", "Governance score (0-100)",
                      "Governance estimate (approx. -2.5 to +2.5)"])
        for year in (1996, 1998, 2000, *range(2002, 2026)):
            for country in countries.values():
                sheet.append([country["iso_a3"], year, 40, -0.5])
        content = io.BytesIO()
        book.save(content)
        rows = governance_estimates(content.getvalue(), countries, 2025, safe_float)
        self.assertEqual(len(rows), 190 * 27)
        self.assertEqual(rows[-1], {"country": "Taiwan", "iso2": "TW", "year": 2025, "value": -0.5})
        with self.assertRaisesRegex(ValueError, "Incomplete WGI history"):
            governance_estimates(content.getvalue(), countries, 2026, safe_float)
