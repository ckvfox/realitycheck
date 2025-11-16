#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Smart CSV Update Check (Nov 2025)
─────────────────────────────────────────────
Fragt GPT (via OpenAI 1.54.x) ab, ob für CSV-basierte KPIs neuere Versionen existieren.
"""

import sys
import json
import re
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from env_utils import get_openai_client
from prompt_templates import build_csv_update_prompt
from script_utils import ensure_utf8_stdout, setup_logger

# === UTF-8 ===
ensure_utf8_stdout()

# === Pfade & Logging ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
META_PATH = DATA_DIR / "meta" / "available_kpis.json"
FETCH_STATUS_PATH = DATA_DIR / "fetch_status.json"
LOGFILE_PATH = DATA_DIR / "fetch_log.txt"

logger = setup_logger("csv_update", LOGFILE_PATH)

# === Silence internal OpenAI/httpx request logs ===
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("openai._client").setLevel(logging.WARNING)

# === OpenAI ===
# === GPT Lookup ===
def _parse_latest_year_payload(raw: str, *, current_year: int) -> int | None:
    """Extract a valid year from the JSON payload returned by GPT."""
    clean = raw.strip().strip("` ")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()

    candidate = clean
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    latest = data.get("latest_year") if isinstance(data, dict) else None
    if isinstance(latest, str) and latest.isdigit():
        latest = int(latest)
    if isinstance(latest, int) and 1900 < latest <= current_year + 2:
        return latest
    return None


def gpt_lookup_latest_year(meta: dict, last_year: int | None) -> int | None:
    current_year = datetime.now(timezone.utc).year
    title = meta.get("title", "Unknown dataset")
    source_field = meta.get("source", "")
    source_url = source_field if isinstance(source_field, str) and source_field.startswith("http") else None
    publisher = None if source_url else source_field

    prompt = build_csv_update_prompt(
        title=title,
        last_year=last_year,
        source_url=source_url,
        publisher=publisher,
        source_code=meta.get("source_code"),
        description=meta.get("description"),
    )

    client = get_openai_client()
    messages = [
        {"role": "system", "content": "You return JSON only and never hallucinate years."},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(2):
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_completion_tokens=200,
            )
        except Exception as e:
            logger.warning(f"⚠️ GPT error for '{title}' (attempt {attempt+1}): {e}")
            time.sleep(1)
            continue

        text = (rsp.choices[0].message.content or "").strip()
        logger.info(f"🤖 GPT response for '{title}': {text}")
        parsed_year = _parse_latest_year_payload(text, current_year=current_year)
        if parsed_year is not None:
            return parsed_year

        messages.append({
            "role": "user",
            "content": "Your previous reply was invalid or missing `latest_year`. Reply again with JSON only.",
        })

    return None


# === Main ===
def main():
    try:
        available = json.loads(META_PATH.read_text(encoding="utf-8"))
        fetch_status = json.loads(FETCH_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"❌ Load error: {e}")
        sys.exit(1)

    kpi_list = available if isinstance(available, list) else list(available.values())
    csv_kpis = [m for m in kpi_list if str(m.get("source_type", "")).lower() == "csv"]
    logger.info(f"➡️ Starting CSV update check for {len(csv_kpis)} KPIs…")

    for meta in csv_kpis:
        title = meta.get("title", "Unknown")
        fname = meta.get("filename", "unknown")
        last_year = int((fetch_status.get("kpis", {}).get(fname, {}).get("data_year") or 0))

        logger.info(f"🔍 Checking '{title}' (last known year: {last_year or 'None'})")
        latest = gpt_lookup_latest_year(meta, last_year or None)
        time.sleep(3)

        if latest is None:
            logger.info(f"❓ No newer version for '{title}' found.")
        elif not last_year:
            logger.warning(f"🆕 Possibly updated: '{title}' → {latest}.")
        elif latest > last_year:
            logger.warning(f"🆕 Possibly updated: '{title}' → {latest} > {last_year}.")
        else:
            logger.info(f"⏸️ Up-to-date ({latest} = {last_year})")

    logger.info("✅ Smart CSV update check completed.")


if __name__ == "__main__":
    main()
