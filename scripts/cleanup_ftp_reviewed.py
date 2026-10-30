"""One-off, explicitly approved cleanup. Backup outside htdocs before deleting exact paths."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath

from audit_ftp_inventory import WEBROOTS, inventory
from deploy_ftps import connect_ftps
from prepare_deployment import productive_paths

PLAN = Path(__file__).with_name("ftp_cleanup_plan_2026_10_30.json")
RECEIPT = Path("build/source-review/ftp-cleanup-receipt.json")


def validate_plan(plan):
    if plan.get("id") != "2026-10-30-reviewed-cleanup" or len(plan["sites"]) != 2:
        raise ValueError("Unapproved cleanup plan")
    if [site["root"] for site in plan["sites"]] != list(WEBROOTS):
        raise ValueError("Unapproved webroots")
    for site, count in zip(plan["sites"], (109, 2)):
        root = site["root"]
        expected_backup = root.removesuffix("/htdocs") + "/ftp-backups/" + plan["id"]
        if site["backup_root"] != expected_backup:
            raise ValueError("Backup must be outside htdocs")
        names = [row["path"] for row in site["candidates"]]
        if len(names) != count or len(set(names)) != count or set(names) & set(site["preserved"]):
            raise ValueError("Invalid candidate set")
        if root == WEBROOTS[0] and set(names) & productive_paths():
            raise ValueError("Candidate became productive; audit again")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or any(c in name for c in "\\\r\n"):
                raise ValueError("Unsafe path")
            base = path.name.lower()
            if base in {"auth.json", "real-wages-auth.php", "tracking.json", "id_rsa", "id_ed25519", "known_hosts", ".npmrc", ".pypirc", ".secrets"} or any(
                fnmatch.fnmatch(base, pattern) for pattern in (".env*", "credentials*", "*.pem", "*.key", "*.pfx", "*.p12", ".*-auto-deploy.json")
            ):
                raise ValueError("Protected server file")


def retrieve(ftp, path):
    data = io.BytesIO()
    ftp.retrbinary("RETR " + path, data.write)
    return data.getvalue()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def mkdirs(ftp, absolute, known):
    path = ""
    for part in PurePosixPath(absolute).parts[1:]:
        path += "/" + part
        if path in known:
            continue
        try:
            ftp.cwd(path)
        except Exception:
            ftp.mkd(path)
            ftp.cwd(path)
        known.add(path)


def snapshot(ftp, site):
    rows = {r["path"]: r for r in inventory(ftp, site["root"])["entries"] if r["type"] == "file"}
    if not set(site["preserved"]) <= rows.keys():
        raise ValueError("Preserved file is missing")
    return rows


def verify_original(row, current):
    if current is None or any(current.get(key) != row.get(key) for key in ("size", "modified")):
        raise ValueError("Candidate changed since reviewed audit")


def backup(ftp, plan):
    known = set()
    receipts = []
    # Finish and verify both sites before a later, separate delete invocation.
    for site in plan["sites"]:
        current = snapshot(ftp, site)
        records = []
        for row in site["candidates"]:
            verify_original(row, current.get(row["path"]))
            data = retrieve(ftp, site["root"] + "/" + row["path"])
            if len(data) != row["size"]:
                raise ValueError("Original size changed")
            target = site["backup_root"] + "/" + row["path"]
            mkdirs(ftp, str(PurePosixPath(target).parent), known)
            ftp.storbinary("STOR " + target, io.BytesIO(data))
            if digest(retrieve(ftp, target)) != digest(data):
                raise ValueError("Backup integrity mismatch")
            records.append({"path": row["path"], "size": len(data), "sha256": digest(data)})
            print("Verified backup: " + site["root"] + "/" + row["path"], flush=True)
        receipt = {"root": site["root"], "backup_root": site["backup_root"], "files": records}
        ftp.storbinary("STOR " + site["backup_root"] + "/snapshot.json", io.BytesIO(json.dumps(receipt).encode()))
        if json.loads(retrieve(ftp, site["backup_root"] + "/snapshot.json")) != receipt:
            raise ValueError("Backup receipt mismatch")
        receipts.append(receipt)
    return receipts


def delete_reviewed(ftp, plan, report):
    # Preflight every backup and remaining original, across both sites, before any DELE.
    ready = []
    for site in plan["sites"]:
        current = snapshot(ftp, site)
        saved = json.loads(retrieve(ftp, site["backup_root"] + "/snapshot.json"))
        records = {r["path"]: r for r in saved["files"]}
        if saved["root"] != site["root"] or saved["backup_root"] != site["backup_root"] or set(records) != {r["path"] for r in site["candidates"]}:
            raise ValueError("Backup does not match approved plan")
        for row in site["candidates"]:
            name = row["path"]
            record = records[name]
            data = retrieve(ftp, site["backup_root"] + "/" + name)
            if len(data) != row["size"] or record["size"] != row["size"] or digest(data) != record["sha256"]:
                raise ValueError("Backup verification failed")
            if name in current:
                verify_original(row, current[name])
                if digest(retrieve(ftp, site["root"] + "/" + name)) != record["sha256"]:
                    raise ValueError("Original differs from backup")
                ready.append((site, name))
    for site, name in ready:
        ftp.delete(site["root"] + "/" + name)
        report["deleted"].append({"root": site["root"], "path": name})
        print("Deleted backed-up candidate: " + site["root"] + "/" + name, flush=True)
    report["post_inventory"] = []
    for site in plan["sites"]:
        rows = snapshot(ftp, site)
        if {r["path"] for r in site["candidates"]} & rows.keys():
            raise ValueError("A candidate remains")
        report["post_inventory"].append(inventory(ftp, site["root"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("backup", "delete"))
    args = parser.parse_args()
    ftp = None
    report = {"stage": args.stage, "complete": False, "deleted": []}
    try:
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        validate_plan(plan)
        ftp = connect_ftps({k: os.environ.get(k) for k in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD")})
        if args.stage == "backup":
            report["backups"] = backup(ftp, plan)
        else:
            delete_reviewed(ftp, plan, report)
        report["complete"] = True
        return 0
    except Exception as exc:
        print(f"Cleanup stopped ({type(exc).__name__}); inspect metadata receipt, no server replies exposed")
        return 1
    finally:
        if ftp is not None:
            ftp.close()
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
