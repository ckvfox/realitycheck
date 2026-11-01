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
import time
from contextlib import suppress
from pathlib import Path

from prepare_deployment import ROOT, TARGET_FULL, is_allowed_productive, should_exclude

REMOTE_ROOT = "/realitycheck.great-site.net/htdocs"
STATE_NAME = ".realitycheck-auto-deploy.json"
RECEIPT = ROOT / "build/deployment/auto-deploy-receipt.json"


class UploadSizeMismatch(ftplib.error_temp):
    """Retry an unverified upload without advancing the deployment checkpoint."""


def verify_uploaded_file(ftp, name: str, metadata: dict) -> None:
    actual_size = ftp.size(name)
    if actual_size == metadata["size"]:
        return
    # Some hosts report stale SIZE metadata. Only exact downloaded bytes can
    # establish success in that case; never accept a mismatch on size alone.
    print(f"FTPS size mismatch for {name}: expected {metadata['size']} bytes; received {actual_size} bytes", flush=True)
    digest = hashlib.sha256()
    received = 0

    def collect(chunk):
        nonlocal received
        received += len(chunk)
        if received > metadata["size"]:
            raise UploadSizeMismatch("Downloaded size differs from production package")
        digest.update(chunk)

    ftp.retrbinary(f"RETR {name}", collect)
    if received != metadata["size"] or digest.hexdigest() != metadata["sha256"]:
        print(f"FTPS readback mismatch for {name}: downloaded {received} bytes; SHA-256 match: false", flush=True)
        raise UploadSizeMismatch("Downloaded bytes differ from production package")
    print(f"Verified {name} by FTPS readback: {received} bytes; SHA-256 match: true", flush=True)


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


def read_remote_state(ftp, state_name: str = STATE_NAME) -> dict:
    payload = bytearray()

    def collect(chunk):
        if len(payload) + len(chunk) > 2_000_000:
            raise ValueError("Remote deployment state exceeds size limit")
        payload.extend(chunk)

    try:
        ftp.retrbinary(f"RETR {state_name}", collect)
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


def ensure_remote_directory(ftp, relative: str, known: set[str], remote_root: str = REMOTE_ROOT) -> None:
    parts = Path(relative).parts[:-1]
    for end in range(1, len(parts) + 1):
        directory = "/".join(parts[:end])
        if directory in known:
            continue
        absolute = f"{remote_root}/{directory}"
        try:
            ftp.cwd(absolute)
        except ftplib.error_perm as exc:
            if not str(exc).startswith("550"):
                raise
            ftp.mkd(absolute)
            ftp.cwd(absolute)
        known.add(directory)
    ftp.cwd(remote_root)


def upload_package(ftp, package: Path, files: dict, *, commit: str, force: bool = False,
                   completed: dict | None = None, remote_root: str = REMOTE_ROOT,
                   state_name: str = STATE_NAME) -> dict:
    ftp.cwd(remote_root)
    previous = {} if force else read_remote_state(ftp, state_name)
    completed = completed if completed is not None else {}
    previous.update(completed)
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
        ensure_remote_directory(ftp, name, known, remote_root)
        with (package / name).open("rb") as handle:
            ftp.storbinary(f"STOR {name}", handle, blocksize=256 * 1024)
        try:
            verify_uploaded_file(ftp, name, metadata)
        except UploadSizeMismatch:
            # Stage with a hidden, non-image suffix before replacing the final
            # path. Some hosts transform direct overwrites of image filenames.
            path = Path(name)
            staged = (path.parent / f".{path.name}.{metadata['sha256'][:12]}.upload").as_posix()
            print(f"Retrying {name} through verified staging", flush=True)
            with (package / name).open("rb") as handle:
                ftp.storbinary(f"STOR {staged}", handle, blocksize=256 * 1024)
            verify_uploaded_file(ftp, staged, metadata)
            ftp.rename(staged, name)
            verify_uploaded_file(ftp, name, metadata)
        uploaded.append(name)
        completed[name] = metadata
        print(f"Uploaded {name}", flush=True)
    # Advance the checkpoint only after every transfer and size check succeeds.
    state = json.dumps({"version": 1, "commit": commit, "files": files}, sort_keys=True).encode()
    ftp.storbinary(f"STOR {state_name}", io.BytesIO(state))
    return {"commit": commit, "destination": remote_root, "total_files": len(files),
            "uploaded_files": uploaded, "skipped_files": len(files) - len(uploaded), "deleted_files": 0}


def connect_ftps(config):
    ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60)
    try:
        ftp.connect(config["FTP_SERVER"], 21)
        ftp.login(config["FTP_USERNAME"], config["FTP_PASSWORD"])
        ftp.prot_p()
        return ftp
    except Exception:
        ftp.close()
        raise


def publish_package(package: Path, files: dict, *, commit: str, remote_root: str = REMOTE_ROOT,
                    state_name: str = STATE_NAME, force: bool = False) -> dict:
    """Shared transport API; the caller validates its project-specific package allowlist."""
    if not remote_root.startswith("/") or ".." in remote_root.split("/") or any(c in remote_root for c in "\r\n"):
        raise ValueError("Unsafe remote root")
    if Path(state_name).name != state_name or any(c in state_name for c in "\r\n\\/"):
        raise ValueError("Unsafe checkpoint name")
    config = {key: os.environ.get(key) for key in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD")}
    if not all(config.values()):
        raise ValueError("Required FTPS runtime settings are missing")
    completed = {}
    for attempt in range(4):
        ftp = None
        try:
            ftp = connect_ftps(config)
            report = upload_package(ftp, package, files, commit=commit, force=force,
                                    completed=completed, remote_root=remote_root, state_name=state_name)
            break
        except (OSError, EOFError, ftplib.error_temp, ftplib.error_proto, ftplib.error_reply) as exc:
            if attempt == 3:
                raise
            print(f"FTPS connection interrupted ({type(exc).__name__}); reconnecting ({attempt + 1}/3)", flush=True)
            time.sleep(2 ** attempt)
        finally:
            if ftp is not None:
                with suppress(Exception):
                    ftp.close()
    report["uploaded_files"] = sorted(completed)
    report["skipped_files"] = len(files) - len(completed)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--force", action="store_true", help="Upload all allowlisted files again")
    args = parser.parse_args()
    try:
        files = package_manifest(TARGET_FULL)
        report = publish_package(TARGET_FULL, files, commit=args.commit, force=args.force)
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"FTPS complete: {len(report['uploaded_files'])} uploaded, {report['skipped_files']} unchanged, 0 deleted")
        return 0
    except Exception as exc:
        # FTP replies can contain account/server details. Keep diagnostics secret-free.
        print(f"FTPS deployment failed ({type(exc).__name__}); checkpoint was not advanced.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
