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

    def rename(self, source, destination):
        self.files[destination] = self.files.pop(source) + (b"bad" if destination == self.corrupt_on else b"")

    def close(self):
        pass


class AutoDeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = Path(self.tmp.name) / "full"
        self.package.mkdir()
        for name in ("index.html", "world.html", "style.css", "data/example.json", "scripts/core.js"):
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
        with self.assertRaises(deploy.UploadSizeMismatch):
            self.upload()
        self.assertEqual(self.ftp.files[deploy.STATE_NAME], checkpoint)
        self.ftp.corrupt_on = None
        self.assertEqual(self.upload()["uploaded_files"], ["style.css"])

    def test_deleted_remote_file_is_restored_and_force_reuploads_everything(self):
        self.upload()
        del self.ftp.files["index.html"]
        self.assertEqual(self.upload()["uploaded_files"], ["index.html"])
        self.assertEqual(len(self.upload(force=True)["uploaded_files"]), 5)

    def test_size_mismatch_reconnects_and_reuploads_unverified_file(self):
        self.ftp.corrupt_on = "style.css"
        retry = FakeFTP()
        retry.files = self.ftp.files
        with patch.dict(deploy.os.environ, {"FTP_SERVER": "offline", "FTP_USERNAME": "offline", "FTP_PASSWORD": "offline"}), \
             patch.object(deploy, "connect_ftps", side_effect=[self.ftp, retry]) as connect, \
             patch.object(deploy.time, "sleep"), redirect_stdout(io.StringIO()):
            result = deploy.publish_package(self.package, deploy.package_manifest(self.package), commit="a" * 40)
        self.assertEqual(connect.call_count, 2)
        self.assertEqual(retry.files["style.css"], (self.package / "style.css").read_bytes())
        self.assertEqual(len(result["uploaded_files"]), 5)
        self.assertEqual(self.ftp.uploads.count("style.css") + retry.uploads.count("style.css"), 2)

    def test_verified_staging_recovers_a_corrupt_direct_overwrite(self):
        original_store = self.ftp.storbinary

        def corrupt_direct_overwrite(command, handle, **kwargs):
            original_store(command, handle, **kwargs)
            if command == "STOR style.css":
                self.ftp.files["style.css"] += b"bad"

        with patch.object(self.ftp, "storbinary", side_effect=corrupt_direct_overwrite):
            result = self.upload()
        self.assertEqual(self.ftp.files["style.css"], (self.package / "style.css").read_bytes())
        self.assertEqual(len(result["uploaded_files"]), 5)
        self.assertFalse(any(name.endswith(".upload") for name in self.ftp.files))

    def test_inaccurate_size_requires_exact_downloaded_size_and_hash(self):
        files = deploy.package_manifest(self.package)
        self.upload()
        with patch.object(self.ftp, "size", return_value=1), redirect_stdout(io.StringIO()) as output:
            deploy.verify_uploaded_file(self.ftp, "style.css", files["style.css"])
        self.assertIn("SHA-256 match: true", output.getvalue())
        self.ftp.files["style.css"] = b"x" * files["style.css"]["size"]
        with patch.object(self.ftp, "size", return_value=1), redirect_stdout(io.StringIO()), \
             self.assertRaises(deploy.UploadSizeMismatch):
            deploy.verify_uploaded_file(self.ftp, "style.css", files["style.css"])

    def test_persistent_size_mismatch_exhausts_retries_without_advancing_checkpoint(self):
        self.upload()
        checkpoint = self.ftp.files[deploy.STATE_NAME]
        (self.package / "style.css").write_bytes(b"change")
        self.ftp.corrupt_on = "style.css"
        with patch.dict(deploy.os.environ, {"FTP_SERVER": "offline", "FTP_USERNAME": "offline", "FTP_PASSWORD": "offline"}), \
             patch.object(deploy, "connect_ftps", return_value=self.ftp) as connect, \
             patch.object(deploy.time, "sleep"), redirect_stdout(io.StringIO()) as output, \
             self.assertRaises(deploy.UploadSizeMismatch):
            deploy.publish_package(self.package, deploy.package_manifest(self.package), commit="b" * 40)
        self.assertEqual(connect.call_count, 4)
        self.assertEqual(self.ftp.files[deploy.STATE_NAME], checkpoint)
        self.assertIn("FTPS size mismatch for style.css: expected 6 bytes; received 9 bytes", output.getvalue())

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
