# ======================================================================
# 🏅 normalize_olympics.py
# ----------------------------------------------------------------------
# Erzeugt drei CSV-Dateien:
# 1. olympic_medals_summer.csv  → nur Sommer
# 2. olympic_medals_winter.csv  → nur Winter
# 3. olympic_medals.csv         → kombiniert (Sommer + zugehöriger Winter)
#
# Quelle: Kaggle "athlete_events.csv"
# ----------------------------------------------------------------------

import os
import csv
from collections import defaultdict

# === Pfade definieren ===
INFILE  = os.path.join("source_raw", "dataset_olympics.csv")
OUTDIR  = os.path.join("source_csv")
OUT_SUM = os.path.join(OUTDIR, "olympic_medals_summer.csv")
OUT_WIN = os.path.join(OUTDIR, "olympic_medals_winter.csv")
OUT_ALL = os.path.join(OUTDIR, "olympic_medals.csv")


# ======================================================================
# 🧮 Hilfsfunktion: Zuordnung Winter → Sommerjahr
# ======================================================================
def cycle_year(year: int, season: str) -> int:
    """Ordnet Winterspiele dem passenden Sommerzyklus zu."""
    if season == "Summer":
        return year
    # bis 1992 fanden Sommer & Winter im selben Jahr statt
    if year <= 1992:
        return year
    # ab 1994 alle 2 Jahre versetzt, daher Winterjahr + 2 → Sommerjahr
    return year + 2


# ======================================================================
# 🧹 Hauptfunktion
# ======================================================================
def main():
    assert os.path.exists(INFILE), f"❌ Input file not found: {INFILE}"

    # Zähler und Dedup-Sets
    seen_keys = set()
    per_summer = defaultdict(int)
    per_winter = defaultdict(int)
    per_all    = defaultdict(int)

    # === Daten einlesen ===
    with open(INFILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            medal  = (row.get("Medal") or "").strip()
            if medal not in ("Gold", "Silver", "Bronze"):
                continue

            games  = (row.get("Games") or "").strip()
            event  = (row.get("Event") or "").strip()
            noc    = (row.get("NOC") or "").strip()
            team   = (row.get("Team") or "").strip() or noc
            season = (row.get("Season") or "").strip()
            year_s = (row.get("Year") or "").strip()

            try:
                year = int(year_s)
            except ValueError:
                continue

            # Dedup-Schlüssel: EIN Eintrag je (Games, Event, Medal, NOC)
            key = (games, event, medal, noc)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Zählen nach Saison
            if season == "Summer":
                per_summer[(team, year)] += 1
            elif season == "Winter":
                per_winter[(team, year)] += 1

            # Kombinierter Zyklus
            cy = cycle_year(year, season)
            per_all[(team, cy)] += 1

    # === Ausgabe schreiben ===
    os.makedirs(OUTDIR, exist_ok=True)

    def write_csv(path, data_dict):
        rows = [{"country": k[0], "year": k[1], "value": v} for k, v in data_dict.items()]
        rows.sort(key=lambda x: (x["country"], x["year"]))
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["country", "year", "value"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Wrote {path} ({len(rows)} rows)")

    write_csv(OUT_SUM, per_summer)
    write_csv(OUT_WIN, per_winter)
    write_csv(OUT_ALL, per_all)

    print("\n=== Olympic Medals Normalization Completed ===")
    print(f"Summer: {len(per_summer)} records")
    print(f"Winter: {len(per_winter)} records")
    print(f"Combined: {len(per_all)} records")


# ======================================================================
# 🚀 Startpunkt
# ======================================================================
if __name__ == "__main__":
    main()
