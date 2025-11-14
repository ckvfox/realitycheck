#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 RealityCheck – Fun, Safe Haven & Immigration Rankings (Nov 2025)
─────────────────────────────────────────────
Erzeugt:
 • fun_ranking.json
 • safe_haven_ranking.json
 • immigration_ranking.json
Verwendet dieselbe GPT-Logik wie analysis.py (OpenAI 1.54.x)
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from env_utils import get_openai_client
from script_utils import ensure_utf8_stdout, safe_write_json, setup_logger

# === UTF-8 Fix ===
ensure_utf8_stdout()

# === Pfade ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_FILE = DATA_DIR / "fetch_log.txt"

# === Logging ===
logger = setup_logger("fun_safe_rankings", LOG_FILE)


def log(msg: str) -> None:
    logger.info(msg)

def save_json(data, path: Path):
    if not data:
        log(f"⚠️ No data to save for {path.name}")
        return
    try:
        safe_write_json(
            path,
            data,
            logger=logger,
            note=f"💾 Saved {path.relative_to(ROOT_DIR)} ({len(data)} entries)",
        )
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

PROMPT_IMMIGRATION = f"""
You are an international migration and labor-mobility analyst.

Your task: Identify and rank the **Top 10 countries that are easiest and most attractive for immigration in {datetime.now().year}**, based on realistic and data-driven reasoning.

Consider these key dimensions:
• Openness of immigration policies (visa, work permits, permanent residence options)
• Job opportunities and demand for skilled workers
• Integration friendliness and social acceptance of migrants
• Language accessibility (English or major world language)
• Quality of life and long-term stability

Base your reasoning on global indexes such as:
– Migration Policy Index
– Global Talent Competitiveness Index
– UN Migration Data Portal
– World Happiness Index
– Rule of Law, Safety, and Economic Stability

Output STRICTLY as valid JSON array, no comments or text.
Each entry must have:
  {{
    "rank": <int>,
    "country": "<string>",
    "reason": "<string>"
  }}
Example:
[
  {{"rank": 1, "country": "Canada", "reason": "open immigration policies"}},
  ...
]
""".strip()


# === Core ===
def _attempt_json_load(raw_json: str, mode: str) -> Optional[Any]:
    """Try to parse ``raw_json`` and repair common minor issues."""
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        # Handle trailing commas before ``]`` or ``}``
        cleaned = re.sub(r",(\s*[}\]])", r"\1", raw_json)
        if cleaned != raw_json:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        # Replace fancy quotes with straight quotes – occasionally returned by the model
        normalized = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
        if normalized != cleaned:
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                pass

        log(f"⚠️ JSON parse error in {mode}: {exc}")
        snippet = raw_json[:200].replace("\n", " ")
        log(f"Raw excerpt: {snippet}")
        return None


def generate_ranking(mode: str, prompt: str, path: Path):
    log(f"➡️ Generating {mode} via GPT-4-Turbo …")
    client = get_openai_client()
    try:
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

    clean = text.strip("` \n")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()

    match = re.search(r"(\[.*\]|\{.*\})", clean, re.DOTALL)
    if not match:
        log(f"⚠️ No JSON found in GPT response for {mode}")
        log(f"Raw excerpt: {clean[:200]}")
        return []

    raw_json = match.group(1)
    parsed = _attempt_json_load(raw_json, mode)
    if parsed is None:
        return []

    save_json(parsed, path)
    return parsed

# === Main ===
if __name__ == "__main__":
    FUN = DATA_DIR / "fun_ranking.json"
    SAFE = DATA_DIR / "safe_haven_ranking.json"
    IMMIG = DATA_DIR / "immigration_ranking.json"

    log("🎬 Starting Fun, Safe & Immigration ranking generation…")
    fun = generate_ranking("Fun Mode", PROMPT_FUN, FUN)
    safe = generate_ranking("Safe Haven Mode", PROMPT_SAFE, SAFE)
    immigr = generate_ranking("Immigration Mode", PROMPT_IMMIGRATION, IMMIG)

    if fun and safe and immigr:
        log("✅ All three rankings generated successfully.")
    elif fun or safe or immigr:
        log("⚠️ Partial success – at least one ranking generated.")
    else:
        log("❌ No ranking data generated.")
