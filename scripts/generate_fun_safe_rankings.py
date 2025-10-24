#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – AI-based Fun & Safe Haven Rankings
-------------------------------------------------
Generates two AI-evaluated rankings and saves them as:
  • data/fun_ranking.json
  • data/safe_haven_ranking.json
Uses the modern OpenAI client (>=1.0.0)
"""

import os
import json
from openai import OpenAI

# === Model & Config ===
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.4
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
FUN_FILE = os.path.join(DATA_DIR, "fun_ranking.json")
SAFE_FILE = os.path.join(DATA_DIR, "safe_haven_ranking.json")

# === Initialize client ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=api_key)

# === Prompts ===
FUN_PROMPT = """
Create a JSON list of the Top 10 countries that best match the idea of a 'Fun & Easy Living' lifestyle.

Criteria (orientation targets, not hard thresholds):
1. Pleasant average annual temperature (~18–26°C, like Southern France)
2. Many sunny days per year (~300, like Southern France)
3. Few rainy days per year (<70)
4. High happiness index (top 40%)
5. Low cost of beer (<3.50$ in Restaurant)
6. Optionally: access to beaches or outdoor lifestyle

Respond ONLY with JSON in this format:
[
  { "rank": 1, "country": "Portugal", "score": 91.2 },
  ...
]
"""

SAFE_PROMPT = """
Create a JSON list of the Top 10 safest and most resilient countries to live in.

Criteria:
1. Strong human rights record
2. Low risk of war, internal conflict or political instability
3. Low to moderate climate risk (e.g. from Germanwatch Climate Risk Index)
4. High resilience score (e.g. INFORM Resilience Index)
5. Stable democratic institutions
6. Avoid countries bordering current warzones

Respond ONLY with JSON in this format:
[
  { "rank": 1, "country": "Switzerland", "score": 94.0 },
  ...
]
"""

# === Helper ===
def query_openai(prompt):
    try:
        res = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )
        text = res.choices[0].message.content.strip()

        # --- Clean possible markdown fences or text wrappers ---
        if "```" in text:
            import re
            match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()

        # --- Try parse ---
        return json.loads(text)
    except json.JSONDecodeError as je:
        print("⚠️ JSON parse failed:", je)
        print("Raw output sample:\n", text[:400])
        return []
    except Exception as e:
        print("❌ GPT call failed:", e)
        return []

# === Main ===
def generate_rankings():
    print("🧠 Generating Fun & Safe Haven rankings...")

    fun = query_openai(FUN_PROMPT)
    safe = query_openai(SAFE_PROMPT)

    os.makedirs(DATA_DIR, exist_ok=True)

    if fun:
        with open(FUN_FILE, "w", encoding="utf-8") as f:
            json.dump(fun, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {FUN_FILE}")
    else:
        print("⚠️ No Fun ranking returned.")

    if safe:
        with open(SAFE_FILE, "w", encoding="utf-8") as f:
            json.dump(safe, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {SAFE_FILE}")
    else:
        print("⚠️ No Safe Haven ranking returned.")

if __name__ == "__main__":
    generate_rankings()
