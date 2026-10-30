import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_ftp_inventory import WEBROOTS, inventory


class MetadataOnlyFTP:
    def __init__(self):
        self.visited = []

    def mlsd(self, path):
        self.visited.append(path)
        if path == WEBROOTS[0]:
            return [("..", {"type": "pdir"}), ("assets", {"type": "dir"}),
                    ("index.html", {"type": "file", "size": "12"}),
                    ("outside", {"type": "OS.unix=slink"})]
        return [("image.png", {"type": "file", "size": "42"})]


class FTPInventoryTests(unittest.TestCase):
    def test_only_metadata_is_listed_and_symlinks_are_not_followed(self):
        ftp = MetadataOnlyFTP()  # No download, upload or deletion methods exist.
        result = inventory(ftp, WEBROOTS[0])
        self.assertEqual(ftp.visited, [WEBROOTS[0], WEBROOTS[0] + "/assets"])
        self.assertEqual({r["path"] for r in result["entries"]},
                         {"assets", "assets/image.png", "index.html", "outside"})

    def test_unapproved_root_and_unsafe_remote_entry_are_rejected(self):
        with self.assertRaises(ValueError):
            inventory(MetadataOnlyFTP(), "/other-site/htdocs")
        class UnsafeFTP:
            def mlsd(self, path):
                return [("../outside", {"type": "dir"})]
        with self.assertRaises(ValueError):
            inventory(UnsafeFTP(), WEBROOTS[0])
