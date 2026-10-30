#!/usr/bin/env python3
"""Incrementally upload the validated production package via FTPS, without deletes."""
from __future__ import annotations

import argparse
import ftplib
import hashlib
import io
import json
import os
import ssl
from contextlib import suppress
from pathlib import Path

from prepare_deployment import ROOT, TARGET_FULL, is_allowed_productive, should_exclude

REMOTE_ROOT = "/realitycheck.great-site.net/htdocs"
STATE_NAME = ".realitycheck-auto-deploy.json"
RECEIPT = ROOT / "build/deployment/auto-deploy-receipt.json"


def package_manifest(package: Path) -> dict[str, dict]:
    if package.is_symlink() or package.resolve() != TARGET_FULL.resolve():
        raise ValueError("Upload must use the canonical production package")
    files = {}
    for path in sorted(package.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks cannot be deployed")
        if not path.is_file():
            continue
        name = path.relative_to(package).as_posix()
        if should_exclude(name) or not is_allowed_productive(name):
            raise ValueError("Package contains a non-productive path")
        files[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size}
    if not files or not {"index.html", "world.html", "style.css"} <= files.keys():
        raise ValueError("Production package is incomplete")
    return files


def read_remote_state(ftp) -> dict:
    payload = bytearray()

    def collect(chunk):
        if len(payload) + len(chunk) > 2_000_000:
            raise ValueError("Remote deployment state exceeds size limit")
        payload.extend(chunk)

    try:
        ftp.retrbinary(f"RETR {STATE_NAME}", collect)
    except ftplib.error_perm as exc:
        if not str(exc).startswith("550"):
            raise
        return {}
    try:
        state = json.loads(payload)
        if state.get("version") == 1 and isinstance(state.get("files"), dict):
            return state["files"]
    except (ValueError, AttributeError):
        pass
    return {}


def ensure_remote_directory(ftp, relative: str, known: set[str]) -> None:
    parts = Path(relative).parts[:-1]
    for end in range(1, len(parts) + 1):
        directory = "/".join(parts[:end])
        if directory in known:
            continue
        absolute = f"{REMOTE_ROOT}/{directory}"
        try:
            ftp.cwd(absolute)
        except ftplib.error_perm as exc:
            if not str(exc).startswith("550"):
                raise
            ftp.mkd(absolute)
            ftp.cwd(absolute)
        known.add(directory)
    ftp.cwd(REMOTE_ROOT)


def upload_package(ftp, package: Path, files: dict, *, commit: str, force: bool = False) -> dict:
    ftp.cwd(REMOTE_ROOT)
    previous = {} if force else read_remote_state(ftp)
    uploaded = []
    known = set()
    for name, metadata in files.items():
        if previous.get(name) == metadata:
            try:
                if ftp.size(name) == metadata["size"]:
                    continue
            except ftplib.error_perm as exc:
                if not str(exc).startswith("550"):
                    raise
        ensure_remote_directory(ftp, name, known)
        with (package / name).open("rb") as handle:
            ftp.storbinary(f"STOR {name}", handle, blocksize=256 * 1024)
        if ftp.size(name) != metadata["size"]:
            raise ValueError("Uploaded size differs from production package")
        uploaded.append(name)
        print(f"Uploaded {name}", flush=True)
    # Advance the checkpoint only after every transfer and size check succeeds.
    state = json.dumps({"version": 1, "commit": commit, "files": files}, sort_keys=True).encode()
    ftp.storbinary(f"STOR {STATE_NAME}", io.BytesIO(state))
    return {"commit": commit, "destination": REMOTE_ROOT, "total_files": len(files),
            "uploaded_files": uploaded, "skipped_files": len(files) - len(uploaded), "deleted_files": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--force", action="store_true", help="Upload all allowlisted files again")
    args = parser.parse_args()
    ftp = None
    try:
        files = package_manifest(TARGET_FULL)
        # Read runtime settings only; never open local secret files or print values.
        config = {key: os.environ.get(key) for key in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD")}
        if not all(config.values()):
            raise ValueError("Required FTPS runtime settings are missing")
        ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60)
        ftp.connect(config["FTP_SERVER"], 21)
        ftp.login(config["FTP_USERNAME"], config["FTP_PASSWORD"])
        ftp.prot_p()
        report = upload_package(ftp, TARGET_FULL, files, commit=args.commit, force=args.force)
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"FTPS complete: {len(report['uploaded_files'])} uploaded, {report['skipped_files']} unchanged, 0 deleted")
        return 0
    except Exception as exc:
        # FTP replies can contain account/server details. Keep diagnostics secret-free.
        print(f"FTPS deployment failed ({type(exc).__name__}); checkpoint was not advanced.")
        return 1
    finally:
        if ftp is not None:
            with suppress(Exception):
                ftp.quit()


if __name__ == "__main__":
    raise SystemExit(main())
