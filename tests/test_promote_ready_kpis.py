import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from promote_ready_kpis import promote_ready


class PromoteReadyKpisTests(unittest.TestCase):
    def test_only_complete_pending_kpi_is_promoted(self):
        entries = [
            {"filename": "ready", "publication_status": "pending_first_fetch"},
            {"filename": "partial", "publication_status": "pending_first_fetch"},
            {"filename": "active"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "ready.json").write_text(json.dumps([{"value": 1}]), encoding="utf-8")
            (data_dir / "ready.csv").write_text("country,year,value\nA,2024,1\n", encoding="utf-8")
            (data_dir / "partial.json").write_text(json.dumps([{"value": 1}]), encoding="utf-8")
            promoted = promote_ready(entries, data_dir)

        self.assertEqual(promoted, ["ready"])
        self.assertNotIn("publication_status", entries[0])
        self.assertEqual(entries[1]["publication_status"], "pending_first_fetch")


if __name__ == "__main__":
    unittest.main()
