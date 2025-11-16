#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

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
from prompt_templates import (
    build_fun_ranking_prompt,
    build_safe_haven_prompt,
    build_immigration_prompt,
)
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


def _validate_ranking_payload(data: Any) -> tuple[bool, str]:
    if not isinstance(data, list):
        return False, "Response is not a JSON array"
    if len(data) == 0:
        return False, "JSON array is empty"
    if len(data) > 10:
        return False, "JSON array exceeds 10 entries"

    for entry in data:
        if not isinstance(entry, dict):
            return False, "Entry is not an object"
        rank = entry.get("rank")
        country = entry.get("country")
        reason = entry.get("reason")
        if not isinstance(rank, int):
            return False, "Missing integer rank"
        if not isinstance(country, str) or not country.strip():
            return False, "Missing country string"
        if not isinstance(reason, str) or not reason.strip():
            return False, "Missing reason string"
        if len(reason) > 220:
            return False, "Reason exceeds 220 characters"
    return True, ""


def _extract_json_snippet(text: str) -> str | None:
    clean = text.strip("` \n")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()
    match = re.search(r"(\[.*\]|\{.*\})", clean, re.DOTALL)
    if match:
        return match.group(1)
    return clean if clean.startswith("[") else None


def generate_ranking(mode: str, prompt: str, path: Path):
    log(f"➡️ Generating {mode} via GPT-4o-Mini …")
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "You answer with JSON arrays that follow the requested schema."},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_completion_tokens=1000,
            )
        except Exception as e:
            log(f"❌ GPT request failed in {mode} (attempt {attempt+1}): {e}")
            continue

        text = (response.choices[0].message.content or "").strip()
        if not text:
            log(f"⚠️ Empty response for {mode} (attempt {attempt+1})")
            messages.append({
                "role": "user",
                "content": "Reply again with a JSON array matching the schema.",
            })
            continue

        snippet = _extract_json_snippet(text)
        if not snippet:
            log(f"⚠️ No JSON found in GPT response for {mode}")
            log(f"Raw excerpt: {text[:200]}")
            messages.append({
                "role": "user",
                "content": "No valid JSON array detected. Reply with array only.",
            })
            continue

        parsed = _attempt_json_load(snippet, mode)
        if parsed is None:
            messages.append({
                "role": "user",
                "content": "Previous JSON was invalid. Provide a clean JSON array only.",
            })
            continue

        valid, reason = _validate_ranking_payload(parsed)
        if not valid:
            log(f"⚠️ Validation failed for {mode}: {reason}")
            messages.append({
                "role": "user",
                "content": f"Your JSON did not match the schema ({reason}). Return a corrected JSON array.",
            })
            continue

        save_json(parsed, path)
        return parsed

    log(f"❌ Unable to generate valid JSON for {mode} after retries.")
    return []

# === Main ===
if __name__ == "__main__":
    FUN = DATA_DIR / "fun_ranking.json"
    SAFE = DATA_DIR / "safe_haven_ranking.json"
    IMMIG = DATA_DIR / "immigration_ranking.json"

    log("🎬 Starting Fun, Safe & Immigration ranking generation…")
    fun = generate_ranking("Fun Mode", build_fun_ranking_prompt(), FUN)
    safe = generate_ranking("Safe Haven Mode", build_safe_haven_prompt(), SAFE)
    immigr = generate_ranking("Immigration Mode", build_immigration_prompt(datetime.now().year), IMMIG)

    if fun and safe and immigr:
        log("✅ All three rankings generated successfully.")
    elif fun or safe or immigr:
        log("⚠️ Partial success – at least one ranking generated.")
    else:
        log("❌ No ranking data generated.")
