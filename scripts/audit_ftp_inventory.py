"""Read directory metadata for the two authorized FTP webroots; never retrieve files."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from deploy_ftps import connect_ftps

WEBROOTS = ("/realitycheck.great-site.net/htdocs", "/energyplanning.great-site.net/htdocs")


def inventory(ftp, root: str) -> dict:
    if root not in WEBROOTS:
        raise ValueError("Webroot is outside the authorized audit scope")
    rows = []
    pending = [""]
    while pending:
        relative = pending.pop()
        for name, facts in ftp.mlsd(root + ("/" + relative if relative else "")):
            kind = facts.get("type", "").lower()
            if kind in {"cdir", "pdir"}:
                continue
            if not name or name in {".", ".."} or any(c in name for c in "/\\\r\n"):
                raise ValueError("Unsafe directory entry")
            path = relative + "/" + name if relative else name
            rows.append({"path": path, "type": kind, "size": int(facts.get("size", 0)),
                         "modified": facts.get("modify", "")})
            if kind == "dir":
                pending.append(path)
    return {"root": root, "captured_at": datetime.now(timezone.utc).isoformat(),
            "entries": sorted(rows, key=lambda row: row["path"])}


def main() -> int:
    ftp = None
    try:
        config = {key: os.environ.get(key) for key in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD")}
        if not all(config.values()):
            raise ValueError("Required runtime settings are missing")
        ftp = connect_ftps(config)
        result = {"sites": [inventory(ftp, root) for root in WEBROOTS]}
        output = Path("build/source-review/ftp-sites-inventory.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        for site in result["sites"]:
            print(f"Audited {site['root']}: {len(site['entries'])} directory entries; no file contents retrieved")
        return 0
    except Exception as exc:
        print(f"Read-only FTP audit failed ({type(exc).__name__}); no files modified")
        return 1
    finally:
        if ftp is not None:
            ftp.close()


if __name__ == "__main__":
    raise SystemExit(main())
