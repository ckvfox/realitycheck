"""Fail-closed validation for generated RealityCheck datasets."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_META_FILE = DEFAULT_DATA_DIR / "meta" / "available_kpis.json"


def log(message: str, log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat()}] {message}\n")
    print(message)


def expected_extensions(kpi: dict[str, Any]) -> tuple[str, ...]:
    """Return required generated formats for a KPI.

    The special geopolitical-risk source intentionally publishes JSON only.
    All regular adapters currently promise both JSON and CSV output.
    """
    if str(kpi.get("source_type", "")).strip().lower() == "special":
        return ("json",)
    return ("json", "csv")


def validate_json_file(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"INVALID JSON: {path} ({exc})"
    if not isinstance(payload, list):
        return f"INVALID DATASET: {path} must contain a JSON array"
    if not payload:
        return f"EMPTY DATASET: {path}"
    return None


def validate_csv_file(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            first_row = next(reader, None)
    except OSError as exc:
        return f"INVALID CSV: {path} ({exc})"
    if not header or not first_row:
        return f"EMPTY DATASET: {path}"
    return None


def validate_datasets(
    data_dir: Path,
    meta_file: Path = DEFAULT_META_FILE,
    *,
    test_kpis_only: bool = False,
) -> list[str]:
    """Return blocking validation errors for the requested dataset snapshot."""
    try:
        kpis = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"INVALID KPI REGISTRY: {meta_file} ({exc})"]
    if not isinstance(kpis, list) or not kpis:
        return [f"INVALID KPI REGISTRY: {meta_file} must contain a non-empty array"]

    selected: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_filenames: set[str] = set()
    for item in kpis:
        if not isinstance(item, dict):
            errors.append("INVALID KPI REGISTRY: every entry must be an object")
            continue
        test_flag = str(item.get("test", "")).strip()
        if test_flag == "o":
            continue
        if test_kpis_only and test_flag != "*":
            continue
        filename = str(item.get("filename", "")).strip()
        if not filename:
            errors.append("INVALID KPI REGISTRY: entry without filename")
            continue
        if filename in seen_filenames:
            errors.append(f"DUPLICATE KPI FILENAME: {filename}")
            continue
        seen_filenames.add(filename)
        selected.append(item)

    if not selected:
        errors.append("NO KPI DATASETS SELECTED")
        return errors

    for kpi in selected:
        filename = str(kpi["filename"])
        for extension in expected_extensions(kpi):
            path = data_dir / f"{filename}.{extension}"
            if not path.is_file():
                errors.append(f"MISSING: {path}")
                continue
            if path.stat().st_size == 0:
                errors.append(f"EMPTY FILE: {path}")
                continue
            error = validate_json_file(path) if extension == "json" else validate_csv_file(path)
            if error:
                errors.append(error)
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a RealityCheck data snapshot")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--meta-file", type=Path, default=DEFAULT_META_FILE)
    parser.add_argument("--test-kpis-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    log_file = data_dir / "validation_log.txt"
    log("==== RealityCheck Data Validation Started ====", log_file)
    errors = validate_datasets(data_dir, args.meta_file.resolve(), test_kpis_only=args.test_kpis_only)
    if errors:
        for error in errors:
            log(f"ERROR: {error}", log_file)
        log(f"ERROR: Validation blocked publication: {len(errors)} error(s).", log_file)
        return 1
    log("OK: Validation passed: all required datasets are present, non-empty and parseable.", log_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
