import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters.inform import extend_history
from adapters.olympic_medals import NON_MEMBERS, records


class InformTests(unittest.TestCase):
    def score(self, code, year, score, indicator="INFORM Risk Index"):
        return dict(Iso3=code, GNAYear=year, IndicatorScore=score, FullName=indicator)

    def test_preserves_existing_scores_and_ignores_other_indicators(self):
        baseline = {("DEU", 2025): 2.6}
        payload = [
            self.score("DEU", 2025, 2.5),
            self.score("DEU", 2026, 2.4),
            self.score("DEU", 2026, 1.2, "Lack of Coping Capacity"),
        ]
        self.assertEqual(extend_history(payload, baseline, 2026), baseline | {("DEU", 2026): 2.4})

    def test_rejects_incomplete_or_duplicate_editions(self):
        baseline = {("DEU", 2025): 2.6, ("FRA", 2025): 2.8}
        payload = [self.score("DEU", 2025, 2.6), self.score("FRA", 2025, 2.8)]
        for invalid in (
            [self.score("DEU", 2026, 2.4)],
            [self.score("DEU", 2025, 2.4)],
            [self.score("DEU", 2027, 2.4), self.score("FRA", 2027, 2.6)],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                extend_history(payload + invalid, baseline, 2027)


class OlympicTests(unittest.TestCase):
    def test_olympic_codes_and_defunct_delegations(self):
        countries = {
            name: {"iso_a2": code}
            for name, code in (("Germany", "DE"), ("Slovenia", "SI"), ("Taiwan", "TW"))
        }
        source = [
            dict(country=label, year=year, value=total)
            for label, year, total in (
                ("West Germany", 1988, 8), ("GDR", 1988, 25), ("United Team of Germany (EUA)", 1964, 9),
                ("ROC", 2022, 32), ("Chinese Taipei", 2020, 12), ("URS", 1988, 29),
                ("SLO", 2018, 2), ("Slovenia", 2018, 2),
            )
        ]
        parsed = records(source, countries, lambda name: "Taiwan" if name == "ROC" else name)
        self.assertEqual(
            [(r["country"], r["year"], r["value"]) for r in parsed],
            [("Germany", 1988, 8), ("Germany", 1964, 9), ("Slovenia", 2018, 2)],
        )
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            records(source + [dict(country="SLO", year=2018, value=3)], countries, lambda name: name)

    def test_published_country_and_edition_coverage(self):
        for season in ("summer", "winter"):
            path = ROOT / "data" / f"olympic_medals_{season}"
            rows = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
            with path.with_suffix(".csv").open(encoding="utf-8", newline="") as handle:
                csv_rows = [{**r, "year": int(r["year"]), "value": float(r["value"])} for r in csv.DictReader(handle)]
            self.assertEqual(rows, csv_rows)
            self.assertTrue(NON_MEMBERS.isdisjoint(row["iso2"] for row in rows))
            keys = Counter((row["iso2"], row["year"]) for row in rows)
            self.assertEqual(max(keys.values()), 1)
        winter = [row for row in rows if row["year"] == 2026]
        self.assertEqual((len(winter), sum(row["value"] for row in winter)), (29, 348))
        self.assertEqual(next(row["value"] for row in winter if row["iso2"] == "DE"), 26)
