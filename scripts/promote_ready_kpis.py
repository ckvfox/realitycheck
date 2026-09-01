"""Publish staged KPI metadata only after complete data artifacts exist."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from script_utils import safe_write_json


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_META_FILE = DEFAULT_DATA_DIR / "meta" / "available_kpis.json"


def _json_ready(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, list) and bool(payload)


def _csv_ready(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            return next(reader, None) is not None and next(reader, None) is not None
    except OSError:
        return False


def promote_ready(entries: list[dict[str, Any]], data_dir: Path) -> list[str]:
    """Activate pending KPIs only when JSON and CSV are both usable."""
    promoted: list[str] = []
    for entry in entries:
        if entry.get("publication_status") != "pending_first_fetch":
            continue
        filename = str(entry.get("filename") or "")
        if _json_ready(data_dir / f"{filename}.json") and _csv_ready(data_dir / f"{filename}.csv"):
            entry.pop("publication_status", None)
            promoted.append(filename)
    return promoted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--meta-file", type=Path, default=DEFAULT_META_FILE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = json.loads(args.meta_file.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("KPI registry must be an array")
    promoted = promote_ready(entries, args.data_dir)
    if promoted:
        safe_write_json(args.meta_file, entries)
        print("Promoted ready KPI(s): " + ", ".join(promoted))
    else:
        print("No pending KPI was ready for publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
