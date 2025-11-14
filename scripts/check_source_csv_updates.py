#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Smart CSV Update Check (Nov 2025)
─────────────────────────────────────────────
Fragt GPT (via OpenAI 1.54.x) ab, ob für CSV-basierte KPIs neuere Versionen existieren.
"""

import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from env_utils import get_openai_client
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
def gpt_lookup_latest_year(title: str, last_year: int) -> int | None:
    current_year = datetime.now(timezone.utc).year
    prompt = f"""
You are a precise data analyst. Determine if there is a newer dataset version.
Only answer with the **latest available year (YYYY)** or "Unknown".

Dataset: "{title}"
Last known year: {last_year}
""".strip()

    try:
        client = get_openai_client()
        rsp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a precise data analyst."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=50
        )
        text = (rsp.choices[0].message.content or "").strip()
        logger.info(f"🤖 GPT response for '{title}': {text}")

        years = [
            int(s) for s in text.replace(",", " ").split()
            if s.isdigit() and 1900 < int(s) <= current_year + 2
        ]
        if years:
            return max(years)
        if "unknown" in text.lower():
            return None
        return None

    except Exception as e:
        logger.warning(f"⚠️ GPT error for '{title}': {e}")
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
        latest = gpt_lookup_latest_year(title, last_year)
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
