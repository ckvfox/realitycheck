# -*- coding: utf-8 -*-
"""Deterministic audit for manually maintained CSV KPI sources.

The script never replaces source files.  Its default mode is completely local:
it validates the canonical CSV schema, derives the latest contained year and
records a checksum.  ``--online`` additionally checks only official URLs and
release-year patterns declared in ``data/meta/manual_csv_sources.json``.

No model is used for source discovery.  Restricted, e-mail-delivered and
manually compiled datasets remain explicit manual-review tasks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

from script_utils import ensure_utf8_stdout, setup_logger


ensure_utf8_stdout()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
META_PATH = DATA_DIR / "meta" / "available_kpis.json"
CONTRACT_PATH = DATA_DIR / "meta" / "manual_csv_sources.json"
SOURCE_CSV_DIR = BASE_DIR / "scripts" / "source_csv"
DEFAULT_OUTPUT_PATH = DATA_DIR / "manual_source_status.json"
LOGFILE_PATH = DATA_DIR / "fetch_log.txt"
MAX_PAGE_BYTES = 2_000_000
USER_AGENT = "RealityCheck-SourceAudit/1.0 (+https://realitycheck.great-site.net/)"

logger = setup_logger("csv_update", LOGFILE_PATH)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_local_csv(path: Path) -> dict[str, Any]:
    """Return a bounded, deterministic profile of one canonical source CSV."""
    result: dict[str, Any] = {
        "exists": path.is_file(),
        "valid": False,
        "row_count": 0,
        "latest_year": None,
        "columns": [],
        "sha256": None,
        "modified_at": None,
        "issues": [],
    }
    if not path.is_file():
        result["issues"].append("source CSV is missing")
        return result

    result["sha256"] = _sha256(path)
    result["modified_at"] = datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    ).isoformat()

    years: list[int] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = [str(column or "").strip().lower() for column in (reader.fieldnames or [])]
            result["columns"] = columns
            required = {"country", "year", "value"}
            missing = sorted(required - set(columns))
            if missing:
                result["issues"].append(f"missing required columns: {', '.join(missing)}")
                return result

            for row in reader:
                result["row_count"] += 1
                raw_year = row.get("year") or row.get("Year")
                try:
                    year = int(float(str(raw_year).strip()))
                except (TypeError, ValueError):
                    continue
                if 1900 <= year <= datetime.now(timezone.utc).year + 2:
                    years.append(year)
    except (OSError, UnicodeError, csv.Error) as exc:
        result["issues"].append(f"CSV read failed: {exc}")
        return result

    if not result["row_count"]:
        result["issues"].append("source CSV contains no data rows")
    if not years:
        result["issues"].append("source CSV contains no valid year")
    else:
        result["latest_year"] = max(years)
    result["valid"] = not result["issues"]
    return result


def extract_release_years(
    text: str,
    patterns: Iterable[str],
    *,
    current_year: int | None = None,
) -> list[int]:
    """Extract only years matched by source-specific, reviewed regex patterns."""
    upper_year = (current_year or datetime.now(timezone.utc).year) + 2
    years: set[int] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            candidates = match.groups() or (match.group(0),)
            for candidate in candidates:
                for raw_year in re.findall(r"\b(?:19|20)\d{2}\b", str(candidate or "")):
                    year = int(raw_year)
                    if 1900 <= year <= upper_year:
                        years.add(year)
    return sorted(years)


def _fetch_official_page(session: requests.Session, url: str, timeout: float) -> dict[str, Any]:
    try:
        response = session.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"ok": False, "url": url, "error": str(exc), "status_code": None}

    content_type = response.headers.get("Content-Type", "")
    body = response.content[:MAX_PAGE_BYTES]
    encoding = response.encoding or "utf-8"
    return {
        "ok": True,
        "url": response.url,
        "status_code": response.status_code,
        "content_type": content_type,
        "truncated": len(response.content) > MAX_PAGE_BYTES,
        "text": body.decode(encoding, errors="replace"),
    }


def audit_csv_source(
    meta: dict[str, Any],
    contract: dict[str, Any],
    *,
    online: bool,
    session: requests.Session | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    kpi_id = str(meta.get("filename") or "").strip()
    csv_name = str(meta.get("source_code") or f"{kpi_id}.csv").strip()
    profile = inspect_local_csv(SOURCE_CSV_DIR / csv_name)
    local_year = profile.get("latest_year")
    check_mode = str(contract.get("check_mode") or "manual_review")
    access_mode = str(contract.get("access_mode") or "unknown_manual")
    update_url = str(contract.get("update_url") or meta.get("source") or "").strip()
    patterns = contract.get("release_year_patterns") or []

    online_result: dict[str, Any] = {
        "status": "not_requested" if not online else "manual_review",
        "official_url": update_url or None,
        "matched_years": [],
        "latest_matched_year": None,
        "possible_update": False,
    }

    if online and check_mode == "official_page_pattern" and update_url and patterns:
        page = _fetch_official_page(session or requests.Session(), update_url, timeout)
        if page.get("ok"):
            years = extract_release_years(page.pop("text"), patterns)
            latest = max(years) if years else None
            online_result.update(
                {
                    "status": "checked",
                    "official_url": page.get("url") or update_url,
                    "status_code": page.get("status_code"),
                    "content_type": page.get("content_type"),
                    "truncated": page.get("truncated", False),
                    "matched_years": years,
                    "latest_matched_year": latest,
                    "possible_update": bool(latest and local_year and latest > local_year),
                }
            )
        else:
            online_result.update(
                {
                    "status": "check_failed",
                    "error": page.get("error"),
                    "status_code": page.get("status_code"),
                }
            )
    elif online and check_mode == "official_page_pattern":
        online_result.update(
            {"status": "contract_incomplete", "error": "update URL or release pattern missing"}
        )

    return {
        "kpi": kpi_id,
        "title": meta.get("title") or kpi_id,
        "csv_file": csv_name,
        "ingestion_mode": contract.get("ingestion_mode", "manual_import"),
        "access_mode": access_mode,
        "check_mode": check_mode,
        "local": profile,
        "online": online_result,
        "manual_action_required": bool(
            online_result.get("possible_update")
            or check_mode == "manual_review"
            or access_mode in {"email_delivery", "registration_required", "manual_compilation", "unknown_manual"}
        ),
        "notes": contract.get("notes") or "",
    }


def _parse_latest_year_payload(raw: str, *, current_year: int) -> tuple[bool, int | None]:
    """Backward-compatible parser retained for older callers; no longer used here."""
    clean = raw.strip().strip("` ")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if not match:
            return False, None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return False, None
    if not isinstance(data, dict) or "latest_year" not in data:
        return False, None
    latest = data.get("latest_year")
    if latest is None:
        return True, None
    if isinstance(latest, str) and latest.isdigit():
        latest = int(latest)
    if isinstance(latest, int) and 1900 < latest <= current_year + 2:
        return True, latest
    return False, None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--online",
        action="store_true",
        help="Check only configured official pages using reviewed release-year patterns.",
    )
    parser.add_argument("--metadata", type=Path, default=META_PATH)
    parser.add_argument("--contracts", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        available = _load_json(args.metadata)
        contract_payload = _load_json(args.contracts)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(f"CSV source audit configuration failed: {exc}")
        return 2

    kpi_list = available if isinstance(available, list) else list(available.values())
    csv_kpis = [item for item in kpi_list if str(item.get("source_type", "")).lower() == "csv"]
    contracts = contract_payload.get("sources", {}) if isinstance(contract_payload, dict) else {}
    session = requests.Session() if args.online else None

    audited = [
        audit_csv_source(
            meta,
            contracts.get(str(meta.get("filename") or ""), {}),
            online=args.online,
            session=session,
            timeout=args.timeout,
        )
        for meta in csv_kpis
    ]

    invalid = [item for item in audited if not item["local"]["valid"]]
    possible = [item for item in audited if item["online"].get("possible_update")]
    failed_checks = [item for item in audited if item["online"].get("status") == "check_failed"]
    report = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "online_check": bool(args.online),
        "summary": {
            "csv_sources": len(audited),
            "locally_valid": len(audited) - len(invalid),
            "locally_invalid": len(invalid),
            "possible_updates": len(possible),
            "online_check_failures": len(failed_checks),
            "manual_action_required": sum(bool(item["manual_action_required"]) for item in audited),
        },
        "sources": audited,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(
        "CSV source audit: %s sources, %s valid, %s possible updates, %s online failures",
        len(audited),
        len(audited) - len(invalid),
        len(possible),
        len(failed_checks),
    )
    for item in invalid:
        logger.error("CSV source invalid: %s (%s)", item["kpi"], "; ".join(item["local"]["issues"]))
    for item in possible:
        logger.warning(
            "Possible manual CSV update: %s local=%s official-page=%s",
            item["kpi"],
            item["local"]["latest_year"],
            item["online"]["latest_matched_year"],
        )
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if invalid else 0


if __name__ == "__main__":
    sys.exit(main())

