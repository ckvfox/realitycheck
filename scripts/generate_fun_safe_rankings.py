# ==============================================================
# 🌍 RealityCheck – Fun & Safe Haven Rankings (AI-based)
# ==============================================================
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# === Setup ===
if os.path.exists(".env"):
    load_dotenv()
    print("✅ Loaded local .env")
else:
    print("🔒 Using GitHub Secrets / Environment Variables")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found. Define in .env or GitHub Secrets.")

client = OpenAI(api_key=OPENAI_API_KEY)


# === Helper functions ===
def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved {path} ({len(data)} entries)")


def log_top20(mode_name: str, ranking: list):
    """Logs ranks 11–20 for transparency/debugging."""
    if not ranking or len(ranking) < 11:
        print(f"⚠️  {mode_name}: not enough entries for logging.")
        return
    print(f"\n🏁 {mode_name} — Places 11–20:")
    for entry in ranking[10:20]:
        print(f"{entry['rank']:>2}. {entry['country']} ({entry['score']:.3f})")


# === Prompt definitions ===
prompt_fun = """
You are an analyst generating the **Fun Ranking** — Create a JSON list of the Top 10 countries that best match the idea of a 'Fun & Easy Living' lifestyle.

Criteria (orientation targets, not hard thresholds):
1. Pleasant average annual temperature (~18–26°C, like Southern France)
2. Many sunny days per year (~300, like Southern France)
3. Few rainy days per year (<70)
4. High happiness index (top 40%)
5. Low cost of beer (<3.50$ in Restaurants)
6. Optionally: access to beaches or outdoor lifestyle

Return only JSON:
[
  {"rank": 1, "country": "Spain", "score": 0.95},
  {"rank": 2, "country": "Portugal", "score": 0.94},
  ...
]
Make sure scores range roughly between 0.6 and 1.0.
"""

prompt_safe = """
You are an analyst generating the **Safe Haven Ranking** — Create a JSON list of the Top 10 safest and most resilient countries to live in.

Criteria:
1. Strong human rights record
2. Low risk of war, internal conflict or political instability (e.g. Geopolitical Risk Index)
3. Low to moderate climate risk (e.g. from Germanwatch Climate Risk Index)
4. High resilience score (e.g. INFORM Resilience Index)
5. Stable democratic institutions
6. Avoid countries bordering current warzones


Return only JSON:
[
  {"rank": 1, "country": "Switzerland", "score": 0.98},
  {"rank": 2, "country": "New Zealand", "score": 0.97},
  ...
]
Ensure scores range between 0.6 and 1.0 and are logically consistent.
"""

# === Core execution ===
def generate_ranking(mode: str, prompt: str, output_path: str):
    print(f"\n➡️ Generating {mode} ranking via GPT-5…")

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a geopolitical and socioeconomic analyst."},
            {"role": "user", "content": prompt.strip()}
        ],
        max_tokens=400,     # 🔹 reicht locker für 20 JSON-Einträge
        temperature=0.6,    # 🔹 moderate Kreativität, stabilere Reihenfolge
    )

    # ⚠️ Fallback-Sicherheitsprüfung
    if not response.choices or not response.choices[0].message or not response.choices[0].message.content.strip():
        print("⚠️ Empty API response – check API key, model name, or rate limit.")
        return []

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except Exception as e:
        print("❌ JSON parse error:", e)
        print("Response was:", content[:400])
        return []

    save_json(data, output_path)
    log_top20(mode, data)
    return data
