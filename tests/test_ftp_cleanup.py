import copy
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cleanup_ftp_reviewed as cleanup


class FakeFTP:
    def __init__(self, plan):
        self.files = {}
        self.modified = {}
        self.deleted = []
        self.retrieved = []
        for site in plan["sites"]:
            self.files[site["backup_root"] + "/.htaccess"] = cleanup.GUARD
            for name in site["preserved"]:
                self.files[site["root"] + "/" + name] = b"protected fixture"
            for row in site["candidates"]:
                path = site["root"] + "/" + row["path"]
                self.files[path] = b"x" * row["size"]
                self.modified[path] = row["modified"]

    def cwd(self, path):
        pass

    def storbinary(self, command, stream):
        self.files[command.removeprefix("STOR ")] = stream.read()

    def retrbinary(self, command, callback):
        path = command.removeprefix("RETR ")
        self.retrieved.append(path)
        callback(self.files[path])

    def delete(self, path):
        del self.files[path]
        self.deleted.append(path)

    def inventory(self, ftp, root):
        return {"root": root, "entries": [
            {"path": name[len(root)+1:], "type": "file", "size": len(data),
             "modified": self.modified.get(name, "fixture")}
            for name, data in self.files.items() if name.startswith(root + "/")
        ]}


class FTPCleanupTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(cleanup.PLAN.read_text(encoding="utf-8"))
        self.ftp = FakeFTP(self.plan)

    def test_exact_approved_plan_and_protected_paths(self):
        cleanup.validate_plan(self.plan)
        for name in ("index.html", "analysis-private/real-wages-auth.php", "../outside", ".env"):
            with self.subTest(name=name):
                plan = copy.deepcopy(self.plan)
                plan["sites"][0]["candidates"][0]["path"] = name
                with self.assertRaises(ValueError):
                    cleanup.validate_plan(plan)

    def test_both_verified_backups_precede_only_targeted_deletions(self):
        expected = {s["root"] + "/" + r["path"] for s in self.plan["sites"] for r in s["candidates"]}
        preserved = {s["root"] + "/" + name for s in self.plan["sites"] for name in s["preserved"]}
        with patch.object(cleanup, "inventory", self.ftp.inventory), redirect_stdout(io.StringIO()):
            receipts = cleanup.backup(self.ftp, self.plan)
            self.assertEqual(sum(len(r["files"]) for r in receipts), 111)
            self.assertEqual(self.ftp.deleted, [])
            report = {"deleted": []}
            cleanup.delete_reviewed(self.ftp, self.plan, report)
        self.assertEqual(set(self.ftp.deleted), expected)
        self.assertTrue(preserved <= self.ftp.files.keys())
        self.assertFalse(preserved & set(self.ftp.retrieved))

    def test_corrupt_backup_on_second_site_blocks_all_deletions(self):
        with patch.object(cleanup, "inventory", self.ftp.inventory), redirect_stdout(io.StringIO()):
            cleanup.backup(self.ftp, self.plan)
            site = self.plan["sites"][1]
            self.ftp.files[site["backup_root"] + "/" + site["candidates"][0]["path"]] = b"corrupt"
            with self.assertRaises(ValueError):
                cleanup.delete_reviewed(self.ftp, self.plan, {"deleted": []})
        self.assertEqual(self.ftp.deleted, [])

    def test_changed_original_or_missing_backup_blocks_deletion(self):
        with patch.object(cleanup, "inventory", self.ftp.inventory), redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyError):
                cleanup.delete_reviewed(self.ftp, self.plan, {"deleted": []})
            cleanup.backup(self.ftp, self.plan)
            site = self.plan["sites"][1]
            row = site["candidates"][0]
            self.ftp.files[site["root"] + "/" + row["path"]] = b"z" * row["size"]
            with self.assertRaises(ValueError):
                cleanup.delete_reviewed(self.ftp, self.plan, {"deleted": []})
        self.assertEqual(self.ftp.deleted, [])
