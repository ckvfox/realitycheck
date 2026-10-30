"""Offline contracts for the automatic, non-deleting FTPS deployment."""
from __future__ import annotations

import ftplib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deploy_ftps as deploy


class FakeFTP:
    def __init__(self):
        self.files = {}
        self.directories = {deploy.REMOTE_ROOT}
        self.uploads = []
        self.fail_on = None
        self.corrupt_on = None

    def cwd(self, path):
        if path not in self.directories:
            raise ftplib.error_perm("550 Missing directory")

    def mkd(self, path):
        self.directories.add(path)

    def retrbinary(self, command, callback):
        name = command.removeprefix("RETR ")
        if name not in self.files:
            raise ftplib.error_perm("550 Missing file")
        callback(self.files[name])

    def storbinary(self, command, handle, **kwargs):
        name = command.removeprefix("STOR ")
        if name == self.fail_on:
            raise ConnectionError("Simulated transfer failure")
        self.files[name] = handle.read() + (b"bad" if name == self.corrupt_on else b"")
        self.uploads.append(name)

    def size(self, name):
        if name not in self.files:
            raise ftplib.error_perm("550 Missing file")
        return len(self.files[name])

    def delete(self, name):
        raise AssertionError("Deployment must never delete remote files")

    def close(self):
        pass


class AutoDeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = Path(self.tmp.name) / "full"
        self.package.mkdir()
        for name in ("index.html", "world.html", "style.css", "data/gdp.json", "scripts/core.js"):
            path = self.package / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
        self.target_patch = patch.object(deploy, "TARGET_FULL", self.package)
        self.target_patch.start()
        self.addCleanup(self.target_patch.stop)
        self.ftp = FakeFTP()

    def upload(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return deploy.upload_package(self.ftp, self.package, deploy.package_manifest(self.package),
                                         commit="a" * 40, **kwargs)

    def test_first_upload_then_only_changed_files_and_no_remote_deletion(self):
        self.ftp.files["tracking.json"] = b"server-owned"
        first = self.upload()
        self.assertEqual(len(first["uploaded_files"]), 5)
        self.ftp.uploads.clear()
        again = self.upload()
        self.assertEqual(again["uploaded_files"], [])
        self.assertEqual(again["skipped_files"], 5)
        (self.package / "style.css").write_bytes(b"changed")
        (self.package / "scripts/core.js").unlink()
        third = self.upload()
        self.assertEqual(third["uploaded_files"], ["style.css"])
        self.assertIn("scripts/core.js", self.ftp.files)
        self.assertEqual(self.ftp.files["tracking.json"], b"server-owned")
        self.assertEqual(third["deleted_files"], 0)

    def test_failed_or_truncated_transfer_does_not_advance_checkpoint(self):
        self.upload()
        checkpoint = self.ftp.files[deploy.STATE_NAME]
        (self.package / "style.css").write_bytes(b"change")
        self.ftp.fail_on = "style.css"
        with self.assertRaises(ConnectionError):
            self.upload()
        self.assertEqual(self.ftp.files[deploy.STATE_NAME], checkpoint)
        self.ftp.fail_on = None
        self.ftp.corrupt_on = "style.css"
        with self.assertRaises(ValueError):
            self.upload()
        self.assertEqual(self.ftp.files[deploy.STATE_NAME], checkpoint)
        self.ftp.corrupt_on = None
        self.assertEqual(self.upload()["uploaded_files"], ["style.css"])

    def test_deleted_remote_file_is_restored_and_force_reuploads_everything(self):
        self.upload()
        del self.ftp.files["index.html"]
        self.assertEqual(self.upload()["uploaded_files"], ["index.html"])
        self.assertEqual(len(self.upload(force=True)["uploaded_files"]), 5)

    def test_bad_checkpoint_falls_back_to_complete_upload(self):
        self.ftp.files[deploy.STATE_NAME] = b"not json"
        self.assertEqual(len(self.upload()["uploaded_files"]), 5)

    def test_non_productive_files_and_noncanonical_package_are_rejected(self):
        with self.assertRaises(ValueError):
            deploy.package_manifest(self.package.parent)
        (self.package / "scripts/unknown.js").write_text("unexpected")
        with self.assertRaises(ValueError):
            deploy.package_manifest(self.package)

    def test_transport_failures_do_not_print_account_or_server_replies(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["deploy_ftps.py", "--commit", "a" * 40]), \
             patch.dict(deploy.os.environ, {"FTP_SERVER":"offline", "FTP_USERNAME":"offline", "FTP_PASSWORD":"offline"}), \
             patch.object(deploy.ftplib, "FTP_TLS", side_effect=RuntimeError("private server reply")), \
             redirect_stdout(output):
            self.assertEqual(deploy.main(), 1)
        self.assertNotIn("private server reply", output.getvalue())

    def test_timeout_reconnects_and_preserves_verified_transfers_in_run(self):
        self.ftp.fail_on = "style.css"
        retry = FakeFTP()
        retry.files = self.ftp.files
        with patch.object(sys, "argv", ["deploy_ftps.py", "--commit", "a" * 40]), \
             patch.dict(deploy.os.environ, {"FTP_SERVER":"offline", "FTP_USERNAME":"offline", "FTP_PASSWORD":"offline"}), \
             patch.object(deploy, "connect_ftps", side_effect=[self.ftp, retry]) as connect, \
             patch.object(deploy.time, "sleep"), \
             patch.object(deploy, "RECEIPT", self.package.parent / "receipt.json"), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(deploy.main(), 0)
        self.assertEqual(connect.call_count, 2)
        receipt = json.loads((self.package.parent / "receipt.json").read_text())
        self.assertEqual(len(receipt["uploaded_files"]), 5)
        self.assertEqual(receipt["skipped_files"], 0)
        self.assertEqual(len(self.ftp.uploads + retry.uploads), 6)  # 5 productive files + checkpoint

    def test_shared_transport_keeps_other_site_root_and_checkpoint_separate(self):
        root = "/energyplanning.great-site.net/htdocs"
        self.ftp.directories.add(root)
        with redirect_stdout(io.StringIO()):
            result = deploy.upload_package(self.ftp, self.package, deploy.package_manifest(self.package),
                                           commit="a" * 40, remote_root=root,
                                           state_name=".energyplanning-auto-deploy.json")
        self.assertEqual(result["destination"], root)
        self.assertIn(root + "/data", self.ftp.directories)
        self.assertIn(".energyplanning-auto-deploy.json", self.ftp.files)
        self.assertNotIn(deploy.STATE_NAME, self.ftp.files)

    def test_data_and_partial_scopes_cannot_bypass_full_package_validation(self):
        files = deploy.package_manifest(self.package)
        self.assertEqual(set(deploy.select_files(files, scope="data")), {"data/gdp.json"})
        self.assertEqual(set(deploy.select_files(files, requested="style.css, index.html")), {"style.css", "index.html"})
        for requested in ("../index.html", "/index.html", "scripts/fetch_data.py", "data/meta/country_mappings_pending.json", ""):
            with self.assertRaises(ValueError):
                deploy.select_files(files, requested=requested)

    def test_workflow_has_main_guard_tests_before_upload_and_shared_lock(self):
        workflow = (ROOT / ".github/workflows/auto-deploy.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [main]", workflow)
        self.assertIn("if: github.ref == 'refs/heads/main'", workflow)
        self.assertIn("ref: main", workflow)
        self.assertLess(workflow.index("python scripts/run_tests.py"), workflow.index("python scripts/deploy_ftps.py"))
        self.assertIn("fpf_project_compliance.py . --profile apache-shared-hosting --production", workflow)
        self.assertIn("group: realitycheck-data-pipeline", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("contents: read", workflow)
        self.assertEqual(deploy.REMOTE_ROOT, "/realitycheck.great-site.net/htdocs")
        for name in ("monthly-fetch.yml", "manual-ftp-full.yml", "manual-ftp-sync.yml", "manual-partial-upload.yml"):
            text = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            self.assertIn("group: realitycheck-data-pipeline", text, name)

    def test_every_production_upload_uses_the_same_validated_allowlist(self):
        names = ("monthly-fetch.yml", "manual-fetch.yml", "manual-fetch-fast.yml",
                 "manual-fetch-force.yml", "manual-fetch-force-fast.yml", "manual-ftp-full.yml",
                 "manual-ftp-sync.yml", "manual-partial-upload.yml", "auto-deploy.yml")
        for name in names:
            text = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertNotIn("SamKirkland/ftp-deploy-action", text)
                self.assertNotIn("secrets.FTP_DIR", text)
                self.assertLess(text.index("python scripts/prepare_deployment.py --mode full"),
                                text.index("python scripts/deploy_ftps.py"))
                if "fetch" in name or name == "manual-ftp-sync.yml":
                    self.assertIn("deploy_ftps.py --scope data", text)
