import os
import json
from normalize_name import normalize_name  # ✅ zentrale Namenslogik importieren

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Root-Verzeichnis
DATA_DIR = os.path.join(BASE_DIR, "data")
AVAILABLE_FILE = os.path.join(BASE_DIR, "available_kpis.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "overall_ranking.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_values(entries):
    """Get the most recent KPI value per country."""
    latest = {}
    for e in entries:
        country = e.get("country")
        year = e.get("year")
        value = e.get("value")
        if not country or value is None:
            continue
        if country not in latest or year > latest[country]["year"]:
            latest[country] = {"year": year, "value": value}
    return latest


def main():
    available = load_json(AVAILABLE_FILE)

    # ✅ Include KPIs with valid sorting (now also "target") and not marked as world-only ("e")
    valid_kpis = {}
    for k in available:
        sort = k.get("sort")
        world_kpi = k.get("world_kpi")

        if sort not in ["higher", "lower", "target"]:
            continue
        if world_kpi == "e":
            continue

        # 🔧 Use normalize_name(title) to get the file reference
        title = k.get("title")
        if not title:
            continue
        filename = normalize_name(title)

        # --- Special case: GDP filename is simply "gdp" ---
        if filename.startswith("gdp"):
            filename = "gdp"

        valid_kpis[filename] = k

    print(f"✅ {len(valid_kpis)} KPIs considered for ranking")

    all_ranks = {}

    for filename, meta in valid_kpis.items():
        filepath = os.path.join(DATA_DIR, f"{filename}.json")
        if not os.path.exists(filepath):
            print(f"⚠️ Missing file: {filename}.json")
            continue

        try:
            data = load_json(filepath)
        except Exception as e:
            print(f"⚠️ Could not read {filename}: {e}")
            continue

        latest = get_latest_values(data)

        # === 🧠 Neue Logik: target-Sortierung unterstützen ===
        sort_type = meta.get("sort")
        target_val = float(meta.get("target_value", 0))

        # Werte extrahieren
        values = [v["value"] for v in latest.values() if isinstance(v.get("value"), (int, float))]
        if not values:
            print(f"⚠️ No numeric values for {filename}")
            continue
        min_val, max_val = min(values), max(values)

        # Sortiervorschrift definieren
        if sort_type == "higher":
            sorted_countries = sorted(
                latest.items(),
                key=lambda x: x[1]["value"],
                reverse=True
            )
        elif sort_type == "lower":
            sorted_countries = sorted(
                latest.items(),
                key=lambda x: x[1]["value"]
            )
        elif sort_type == "target":
            # 📈 Nähe zum Zielwert: je kleiner die Abweichung, desto besser
            sorted_countries = sorted(
                latest.items(),
                key=lambda x: abs(x[1]["value"] - target_val)
            )
        else:
            continue  # sollte nicht vorkommen

        # Rangvergabe
        for rank, (country, _) in enumerate(sorted_countries, start=1):
            if country not in all_ranks:
                all_ranks[country] = {"ranks": {}, "kpi_count": 0}
            all_ranks[country]["ranks"][filename] = rank
            all_ranks[country]["kpi_count"] += 1

    # === JSON schreiben ===
    result = [
        {
            "country": country,
            "ranks": info["ranks"],
            "kpi_count": info["kpi_count"]
        }
        for country, info in all_ranks.items()
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ overall_ranking.json written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
