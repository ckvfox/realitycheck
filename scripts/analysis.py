# =============================================
# 🌍 RealityCheck – Global KPI Analysis Script (B2 Version)
# =============================================

import json
import statistics
from pathlib import Path
import os
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI


def run_global_analysis():
    """
    Reads all KPI JSON files from /data, creates an AI-generated global analysis (B2-level reasoning),
    and saves the result as Markdown and JSON inside /data.
    Also extracts outlier information (min/max country & year) for data quality review.
    """

    # === 1. Load environment variables ===
    if os.path.exists(".env"):
        load_dotenv()
        print("✅ Loaded local .env file")
    else:
        print("🔒 Running with environment secrets (GitHub Actions)")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY not found. Please define it in .env or GitHub Secrets.")

    # === 2. Paths ===
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    output_md = data_dir / "analysis.md"
    output_json = data_dir / "analysis.json"
    output_outliers = data_dir / "analysis_outliers.json"

    print("➡️ Starting global AI analysis...")
    print("📁 Data folder:", data_dir.resolve())

    # === 3. OpenAI client ===
    client = OpenAI(api_key=OPENAI_API_KEY)

    # === 4. Collect KPI data files ===
    files = [
        f for f in data_dir.glob("*.json")
        if not any(x in f.name for x in ["available", "countries", "analysis"])
    ]
    print(f"🔍 Found {len(files)} KPI files to process")

    data_summary = {}
    outliers = {}

    # === 5. Parse KPI data and compute basic stats ===
    for f in tqdm(files, desc="📊 Processing KPI files", unit="file"):
        try:
            with f.open(encoding="utf-8") as infile:
                kpi_name = f.stem
                data = json.load(infile)

                if isinstance(data, dict) and "data" in data:
                    rows = data["data"]
                elif isinstance(data, list):
                    rows = data
                else:
                    rows = []

                values = [v.get("value") for v in rows if isinstance(v.get("value"), (int, float))]

                if not values or len(values) < 5:
                    continue

                mean = sum(values) / len(values)
                stdev = statistics.pstdev(values)
                min_val, max_val = min(values), max(values)

                min_entry = next((r for r in rows if r.get("value") == min_val), None)
                max_entry = next((r for r in rows if r.get("value") == max_val), None)

                flagged = []
                if stdev > 0:
                    for r in rows:
                        val = r.get("value")
                        if val is None:
                            continue
                        z = abs((val - mean) / stdev)
                        if z > 3:
                            flagged.append({
                                "country": r.get("country"),
                                "year": r.get("year"),
                                "value": val,
                                "z_score": round(z, 2)
                            })

                data_summary[kpi_name] = {
                    "count": len(values),
                    "avg": round(mean, 3),
                    "std": round(stdev, 3),
                    "min": min_val,
                    "max": max_val,
                    "outlier_count": len(flagged)
                }

                outliers[kpi_name] = {
                    "min": {
                        "value": min_val,
                        "country": min_entry.get("country") if min_entry else None,
                        "year": min_entry.get("year") if min_entry else None,
                    },
                    "max": {
                        "value": max_val,
                        "country": max_entry.get("country") if max_entry else None,
                        "year": max_entry.get("year") if max_entry else None,
                    },
                    "flagged": flagged[:20]
                }

        except Exception as e:
            print(f"⚠️ Error processing {f.name}: {e}")

    if not data_summary:
        print("⚠️ No KPI data found – please run fetch_data.py first.")
        return

    # === 6. Save outlier overview ===
    try:
        output_outliers.write_text(json.dumps(outliers, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"🧩 Outlier data saved to {output_outliers.name}")
    except Exception as e:
        print("❌ Error saving outliers:", e)

    # === 7. Prepare AI prompt (B2 reasoning) ===
    print("\n🧠 Sending KPI summary to AI for analysis (B2 level)...")
    prompt = (
        "Analyze the following global KPI summaries with a clear and reasoned tone (CEFR level B2). "
        "Explain global trends, improvements, deteriorations, and correlations across regions and clusters. "
        "Pay attention to differences between democracies and autocracies, and how political systems, "
        "economic power groups (EU, G7, G20, BRICS, OECD, etc.), and resource dependencies influence the results. "
        "Include reflections on key global challenges such as climate change, inequality, conflict, and migration, "
        "and identify which countries or groups show positive or negative exceptions.\n\n"
        "Structure your response as follows:\n"
        "- Overview (short paragraph)\n"
        "- Highlights (positive developments)\n"
        "- Lowlights (negative developments)\n"
        "- Political & Regional Differences\n"
        "- Interrelations & Global Dynamics\n"
        "- Forecast & Outlook\n"
        "- Short Global Conclusion\n\n"
        "Here is the aggregated KPI data:\n"
        f"{json.dumps(data_summary, indent=2)[:12000]}"
    )

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are an expert global data analyst specializing in socioeconomic and environmental trends."},
            {"role": "user", "content": prompt},
        ],
    )

    text = response.choices[0].message.content.strip()

    # === 8. Save results ===
    try:
        output_md.write_text(text, encoding="utf-8")
        output_json.write_text(
            json.dumps({"analysis_text": text, "summary": data_summary}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("\n✅ Global B2-level analysis saved successfully!")
        print("📄 Markdown:", output_md.resolve())
        print("📊 JSON:", output_json.resolve())
    except Exception as e:
        print("❌ Error while saving:", e)


if __name__ == "__main__":
    run_global_analysis()