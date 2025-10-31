#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Smart CSV Update Check (Enhanced, Okt 2025)
─────────────────────────────────────────────
Fragt GPT ab, ob für CSV-basierte KPIs (source_type=csv)
neuere Daten oder Jahrgänge verfügbar sind.

Neu:
  ✅ Zukunftssichere UTC-Zeit (datetime.now(timezone.utc))
  ✅ Intelligenter Prompt mit Beispielen (Olympics, Big Mac etc.)
  ✅ Loggt GPT-Antworten für Nachvollziehbarkeit
  ✅ Einheitliche Emojis und klare Ergebnis-Meldungen
"""

import os
import json
import sys
import logging
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

# === Pfade ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
META_PATH = os.path.join(BASE_DIR, "data", "meta", "available_kpis.json")
FETCH_STATUS_PATH = os.path.join(BASE_DIR, "data", "fetch_status.json")
LOGFILE_PATH = os.path.join(BASE_DIR, "data", "fetch_log.txt")

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {message}",
    style="{",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGFILE_PATH, encoding="utf-8", mode="a"),
    ],
)
log = logging.getLogger("smart_csv_update")

# === GPT Setup ===
if os.path.exists(os.path.join(BASE_DIR, ".env")):
    load_dotenv(os.path.join(BASE_DIR, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    log.error("❌ OPENAI_API_KEY not found. Please define it in .env or GitHub Secrets.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================================================================
# 🤖 GPT-Suche nach potenziell neueren Jahrgängen
# ======================================================================
def gpt_lookup_latest_year(title: str, last_year: int) -> int | None:
    """Fragt GPT, ob es neuere Jahrgänge oder Updates zu einem CSV-basierten KPI gibt."""
    current_year = datetime.now(timezone.utc).year

prompt = f"""
    Du bist ein präziser Datenanalyst, der erkennt, ob es zu einem bekannten Datensatz neuere Jahrgänge gibt.

    Ich möchte nur wissen, **aus welchem Jahr die aktuellste verfügbare Version** des folgenden Datensatzes stammt.
    Antworte **ausschließlich mit dem Veröffentlichungsdatum (TT MMM YYYY)** oder, falls unbekannt, **"Unknown"**.

    Beispiele:
    - Big Mac Index → 18 Feb 2025
    - Environmental Performance Index → 3 Jun 2024
    - INFORM Resilience Index → 15 Mar 2024
    - World Happiness Index → 20 Mar 2025
    - Olympic Games (Summer) → 11 Aug 2024
    - Olympic Games (Winter) → 20 Feb 2022
    - Global Peace Index → 22 Feb 2023

    Datensatz: "{title}"
    Letzter bekannter Jahrgang: {last_year}

    Wenn du kein aktuelles Datum kennst, gib exakt "Unknown" zurück.
    """

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Datenassistent."},
                    {"role": "user", "content": prompt.strip()},
                ],
                max_completion_tokens=60,
            )

            text = response.choices[0].message.content.strip()
            log.debug(f"🤖 GPT-Antwort für '{title}': {text}")

            # Numerische Jahreswerte herausfiltern
            year_candidates = [
                int(s)
                for s in text.replace(",", " ").replace(".", " ").split()
                if s.isdigit() and 1900 < int(s) <= current_year + 2
            ]

            if year_candidates:
                return max(year_candidates)
            elif "unknown" in text.lower():
                return None
            else:
                return None

        except Exception as e:
            err = str(e)
            if "429" in err:
                wait = 15 + attempt * 10
                log.warning(f"⚠️ 429 Rate limit for '{title}' (try {attempt+1}/{max_retries}) — waiting {wait}s …")
                time.sleep(wait)
                continue
            elif "insufficient_quota" in err or "quota" in err.lower():
                log.error(f"💸 Quota exhausted for '{title}'. Abbruch des Checks.")
                return None
            else:
                log.warning(f"⚠️ GPT lookup failed for '{title}': {e}")
                return None
    else:
        log.error(f"🚫 Too many retries for '{title}' — skipping.")
        return None


# ======================================================================
# 🚀 Main-Routine
# ======================================================================
def main():
    # --- Dateien laden ---
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            available = json.load(f)
        with open(FETCH_STATUS_PATH, "r", encoding="utf-8") as f:
            fetch_status = json.load(f)
    except Exception as e:
        log.error(f"❌ Datei-Ladefehler: {e}")
        sys.exit(1)

    kpi_list = available if isinstance(available, list) else list(available.values())
    log.info("➡️ Starte smarten CSV-Update-Check …")

    csv_kpis = [m for m in kpi_list if str(m.get("source_type", "")).lower() == "csv"]

    for meta in csv_kpis:
        title = meta.get("title", "Unknown")
        fname = meta.get("filename", "unknown")
        last_year = None
        kpi_status = fetch_status.get("kpis", {}).get(fname, {})

        try:
            if kpi_status.get("data_year") and str(kpi_status["data_year"]).isdigit():
                last_year = int(kpi_status["data_year"])
        except Exception:
            last_year = None

        log.info(f"🔍 Prüfe '{title}' (last data year: {last_year})")

        latest_year = gpt_lookup_latest_year(title, last_year or 0)
        # 🕐 kleine Pause, um 429-Fehler zu vermeiden
        time.sleep(3)

        if latest_year and (not last_year or latest_year > last_year):
            log.warning(f"🆕 Mögliche Aktualisierung: '{title}' (neuer Jahrgang {latest_year} > {last_year})")
        elif latest_year:
            log.info(f"⏸️ Kein neuer Jahrgang: {latest_year} ≤ {last_year}")
        else:
            log.info(f"❓ Keine Information über neueste Version gefunden für '{title}'")

    log.info("✅ Smarter CSV-Update-Check abgeschlossen.")


# === Start ===
if __name__ == "__main__":
    main()
