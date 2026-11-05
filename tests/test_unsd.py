import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters.unsd import fetch_rows


class UnsdPaginationTests(unittest.TestCase):
    def test_reads_all_reported_pages(self):
        pages = [
            {"pageNumber": page, "totalPages": 2, "totalElements": 2, "data": [{"value": page}]}
            for page in (1, 2)
        ]
        http_get = Mock(side_effect=[Mock(json=Mock(return_value=page)) for page in pages])
        self.assertEqual(fetch_rows("EG_FEC_RNEW", http_get), [{"value": 1}, {"value": 2}])
        self.assertEqual([call.kwargs["params"]["page"] for call in http_get.call_args_list], [1, 2])

    def test_rejects_repeated_or_incomplete_pages(self):
        first = {"pageNumber": 1, "totalPages": 2, "totalElements": 3, "data": [{"value": 1}]}
        for second, error in (
            (first, "Inconsistent UNSD pagination"),
            (dict(first, pageNumber=2), "Incomplete UNSD response"),
        ):
            http_get = Mock(side_effect=[Mock(json=Mock(return_value=page)) for page in (first, second)])
            with self.assertRaisesRegex(ValueError, error):
                fetch_rows("EG_FEC_RNEW", http_get)
