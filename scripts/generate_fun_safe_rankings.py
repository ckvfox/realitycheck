#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 RealityCheck – Fun & Safe Haven Rankings (Nov 2025)
─────────────────────────────────────────────
Erzeugt:
 • fun_ranking.json
 • safe_haven_ranking.json
Verwendet dieselbe GPT-Logik wie analysis.py (OpenAI 1.54.x)
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from env_utils import get_openai_key
from httpx import Client as HttpxClient  # 🔧 Fix für Python 3.13 Proxy-Bug

# === UTF-8 Fix ===
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# === OpenAI Setup ===
load_dotenv()
OPENAI_API_KEY = get_openai_key()
client = OpenAI(api_key=OPENAI_API_KEY, http_client=HttpxClient())  # eigener Client für Python 3.13

# === Pfade ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_FILE = DATA_DIR / "fetch_log.txt"

# === Safe Write Helpers ===
def safe_write_text(path: Path, content: str):
    """Garantiert UTF-8-Schreiben mit automatischer Ordnererstellung."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write(content or "")
    except Exception as e:
        print(f"❌ Failed to write text file {path}: {e}")

def safe_write_json(path: Path, data):
    """Garantiert sicheres Schreiben von JSON-Dateien (UTF-8, exist_ok)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON saved: {path.relative_to(Path(__file__).resolve().parent.parent)} ({len(data)} entries)")
    except Exception as e:
        print(f"❌ Failed to write JSON file {path}: {e}")

# === Helper ===
def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def save_json(data, path: Path):
    """Schreibt JSON-Datei sicher mit Logging."""
    if not data:
        log(f"⚠️ No data to save for {path.name}")
        return
    try:
        safe_write_json(path, data)
        log(f"💾 Saved {path.relative_to(ROOT_DIR)} ({len(data)} entries)")
    except Exception as e:
        log(f"❌ Failed to save {path.name}: {e}")
def save_json(data, path: Path):
    """Schreibt JSON-Datei sicher mit Logging."""
    if not data:
        log(f"⚠️ No data to save for {path.name}")
        return
    try:
        safe_write_json(path, data)
        log(f"💾 Saved {path.relative_to(ROOT_DIR)} ({len(data)} entries)")
    except Exception as e:
        log(f"❌ Failed to save {path.name}: {e}")


# === Prompts ===
PROMPT_FUN = """
You are an analyst generating the **Fun Ranking** – create a JSON list of the Top 10 countries that best match a 'Fun & Easy Living' lifestyle.
Criteria: pleasant climate (18–26 °C), many sunny days (280-300), few rainy days (60-90), high happiness (e.g. World Happiness Index), low beer price in restaurants (< 3.50 USD). If a country has a city that is listed in the top 5 most livable cities according to the EIU Global Liveability Index, Mercer Quality of Living Index, or Monocle Quality of Life Survey, that country should receive an additional bonus in the fun ranking.
Return the full, valid JSON array and make sure all brackets are properly closed.
""".strip()

PROMPT_SAFE = """
You are an analyst generating the **Safe Haven Ranking** – create a JSON list of the Top 10 safest and most resilient countries to live in.
Criteria: human rights (e.g. Human Rights Index), low conflict risk (e.g. Geopolitical Risk Index), moderate climate risk (e.g. Climate Risk Index), resilience (e.g. Inform Resilience Index), stable democracy (e.g. Democracy Index).
Return the full, valid JSON array and make sure all brackets are properly closed.
""".strip()

# === Core (fixed) ===
def generate_ranking(mode: str, prompt: str, path: Path):
    log(f"➡️ Generating {mode} via GPT-4-Turbo …")
    try:
        # Kein erzwungenes response_format → GPT darf Array [ ... ] zurückgeben
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a geopolitical and socioeconomic analyst."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1000
        )
        text = response.choices[0].message.content.strip()
    except Exception as e:
        log(f"❌ GPT request failed in {mode}: {e}")
        return []

    if not text:
        log(f"⚠️ Empty response for {mode}")
        return []

    # === Flexible Parsing (funktioniert mit Array oder Objekt) ===
    import re
    clean = text.strip("` \n")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()

    match = re.search(r"(\[.*\]|\{.*\})", clean, re.DOTALL)
    if not match:
        log(f"⚠️ No JSON found in GPT response for {mode}")
        log(f"Raw excerpt: {clean[:200]}")
        return []

    raw_json = match.group(1)
    try:
        data = json.loads(raw_json)
    except Exception as e:
        log(f"⚠️ JSON parse error in {mode}: {e}")
        log(f"Raw excerpt: {raw_json[:200]}")
        return []

    save_json(data, path)
    return data



# === Main ===
if __name__ == "__main__":
    FUN = DATA_DIR / "fun_ranking.json"
    SAFE = DATA_DIR / "safe_haven_ranking.json"

    log("🎬 Starting Fun & Safe Haven ranking generation…")
    fun = generate_ranking("Fun Mode", PROMPT_FUN, FUN)
    safe = generate_ranking("Safe Haven Mode", PROMPT_SAFE, SAFE)

    if fun and safe:
        log("✅ Both rankings generated successfully.")
    elif fun:
        log("⚠️ Only Fun ranking generated successfully.")
    elif safe:
        log("⚠️ Only Safe Haven ranking generated successfully.")
    else:
        log("❌ No ranking data generated.")
