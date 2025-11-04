#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Smart CSV Update Check (Nov 2025)
─────────────────────────────────────────────
Fragt GPT (via OpenAI 1.54.x) ab, ob für CSV-basierte KPIs neuere Versionen existieren.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from env_utils import get_openai_key

# === UTF-8 ===
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# === Pfade & Logging ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
META_PATH = DATA_DIR / "meta" / "available_kpis.json"
FETCH_STATUS_PATH = DATA_DIR / "fetch_status.json"
LOGFILE_PATH = DATA_DIR / "fetch_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[{asctime} UTC] {message}",
    datefmt="%Y-%m-%dT%H:%M:%S",
    style="{",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGFILE_PATH, encoding="utf-8", mode="a"),
    ],
)

log = logging.getLogger("csv_update")

# === Silence internal OpenAI/httpx request logs ===
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("openai._client").setLevel(logging.WARNING)

# === OpenAI ===
from httpx import Client as HttpxClient  # <- wichtig: import ergänzen
load_dotenv()
OPENAI_API_KEY = get_openai_key()

# eigener httpx-Client verhindert den "proxies"-Fehler unter Python 3.13
client = OpenAI(api_key=OPENAI_API_KEY, http_client=HttpxClient())

# ======================================================================
# 💾 Safe Write Helpers
# ======================================================================
def safe_write_text(path: Path, content: str):
    """Garantiert UTF-8-Schreiben mit automatischer Ordnererstellung."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write(content or "")
        log.info(f"💾 Wrote text file: {path.name}")
    except Exception as e:
        log.error(f"❌ Failed to write text file {path}: {e}")

def safe_write_json(path: Path, data):
    """Garantiert sicheres Schreiben von JSON-Dateien."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"💾 JSON saved: {path.name} ({len(data)} keys)")
    except Exception as e:
        log.error(f"❌ Failed to write JSON {path}: {e}")


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
        rsp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a precise data analyst."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=50
        )
        text = (rsp.choices[0].message.content or "").strip()
        log.info(f"🤖 GPT response for '{title}': {text}")

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
        log.warning(f"⚠️ GPT error for '{title}': {e}")
        return None


# === Main ===
def main():
    try:
        available = json.loads(META_PATH.read_text(encoding="utf-8"))
        fetch_status = json.loads(FETCH_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"❌ Load error: {e}")
        sys.exit(1)

    kpi_list = available if isinstance(available, list) else list(available.values())
    csv_kpis = [m for m in kpi_list if str(m.get("source_type", "")).lower() == "csv"]
    log.info(f"➡️ Starting CSV update check for {len(csv_kpis)} KPIs…")

    for meta in csv_kpis:
        title = meta.get("title", "Unknown")
        fname = meta.get("filename", "unknown")
        last_year = int((fetch_status.get("kpis", {}).get(fname, {}).get("data_year") or 0))

        log.info(f"🔍 Checking '{title}' (last known year: {last_year or 'None'})")
        latest = gpt_lookup_latest_year(title, last_year)
        time.sleep(3)

        if latest is None:
            log.info(f"❓ No newer version for '{title}' found.")
        elif not last_year:
            log.warning(f"🆕 Possibly updated: '{title}' → {latest}.")
        elif latest > last_year:
            log.warning(f"🆕 Possibly updated: '{title}' → {latest} > {last_year}.")
        else:
            log.info(f"⏸️ Up-to-date ({latest} = {last_year})")

    log.info("✅ Smart CSV update check completed.")


if __name__ == "__main__":
    main()
