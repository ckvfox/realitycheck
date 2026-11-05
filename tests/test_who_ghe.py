import io
import sys
import unittest
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters.who_ghe import REQUIRED_YEARS, latest_download, parse_rates
from fetch_data import safe_float


class WhoGheTests(unittest.TestCase):
    def test_selects_crude_country_file_from_who(self):
        root = "https://cdn.who.int/media/docs/default-source/gho-documents/global-health-estimates/"
        old = root + "crude-death-rates-2000-2023_bycountry_2026-10-01.xlsx"
        new = root + "crude-death-rates-2000-2024_bycountry_2027-10-01.xlsx?sfvrsn=1"
        self.assertEqual(latest_download(f'<a href="{old}">old</a><a href="{new}">new</a>'),
                         (new, 2024, "2027-10-01"))
        with self.assertRaises(ValueError):
            latest_download(old.replace("cdn.who.int", "example.org"))

    def test_uses_all_person_crude_rates_and_keeps_only_reported_years(self):
        countries = {f"Country {i}": {"iso_a3": f"X{i:03}"} for i in range(180)}
        book = Workbook(write_only=True)
        for year in sorted(REQUIRED_YEARS):
            sheet = book.create_sheet(f"CDR {year}")
            for _ in range(4):
                sheet.append([None])
            sheet.append([None, None, None, "Crude death rate per 100 000 population"])
            sheet.append([None])
            sheet.append(["Sex", "GHE code"])
            sheet.append([None] * 6 + ["ISO-3 Code"] + [entry["iso_a3"] for entry in countries.values()])
            sheet.append(["Males", 1530, None, None, None, "Road injury", None] + [999] * 180)
            sheet.append(["Persons", 1530, None, None, None, "Road injury", None] + [3.5] * 180)
            sheet.append(["Persons", 1610, None, None, None, "Self-harm", None] + [0] * 180)
        stream = io.BytesIO()
        book.save(stream)
        rates = parse_rates(stream.getvalue(), countries, 2023, safe_float)
        self.assertEqual({row["year"] for row in rates["1530"]}, REQUIRED_YEARS)
        self.assertEqual({row["value"] for row in rates["1530"]}, {3.5})
        self.assertEqual({row["value"] for row in rates["1610"]}, {0})
        with self.assertRaisesRegex(ValueError, "Incomplete WHO release years"):
            parse_rates(stream.getvalue(), countries, 2024, safe_float)
