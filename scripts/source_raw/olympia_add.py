#!/usr/bin/env python3
# scripts/source_csv/olympia_add.py
# 📋 Fügt kopierte Wikipedia-Medaillentabellen zu olympia_medals_raw.csv hinzu
# pip install pandas pyperclip

import pandas as pd
import pyperclip
from datetime import datetime
from pathlib import Path
import io, time

SRC = Path(__file__).resolve().parent
RAW_FILE = SRC / "olympia_medals_raw.csv"

print("🏅 RealityCheck – Olympia CSV Collector")
print("➡️  Kopiere auf Wikipedia den kompletten Medaillenspiegel (inkl. Header).")
print("➡️  Danach hier einfach Enter drücken.\n")

def process_clipboard():
    clip = pyperclip.paste()

    try:
        df = pd.read_clipboard(sep="\t")
    except Exception:
        df = pd.read_csv(io.StringIO(clip), sep="\t|,", engine="python")

    # --- Header-Erkennung & Bereinigung ---
    cols = [c.strip().lower() for c in df.columns]
    if not any("nation" in c or "noc" in c or "country" in c for c in cols):
        df.columns = ["Rank", "Nation", "Gold", "Silver", "Bronze", "Total"][:len(df.columns)]
    else:
        rename_map = {}
        for c in df.columns:
            cl = c.lower().strip()
            if "noc" in cl or "nation" in cl or "country" in cl:
                rename_map[c] = "Nation"
            elif "gold" in cl:
                rename_map[c] = "Gold"
            elif "silver" in cl:
                rename_map[c] = "Silver"
            elif "bronze" in cl:
                rename_map[c] = "Bronze"
            elif "total" in cl:
                rename_map[c] = "Total"
            elif "rank" in cl:
                rename_map[c] = "Rank"
        df.rename(columns=rename_map, inplace=True)

    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)

    year = input("🏅 Jahr der Spiele (z. B. 1936): ").strip()
    season = input("☀️  'Summer' oder 'Winter': ").strip().capitalize()

    df.insert(0, "year", year)
    df.insert(1, "season", season)
    df.insert(2, "timestamp", datetime.now().isoformat())

    mode = "a" if RAW_FILE.exists() else "w"
    header = not RAW_FILE.exists()
    df.to_csv(RAW_FILE, mode=mode, index=False, header=header)
    print(f"✅ {len(df)} Zeilen zu {RAW_FILE.name} hinzugefügt.\n")

# --- Hauptloop ---
while True:
    input("📋 Wenn du eine neue Tabelle kopiert hast, drücke Enter …")
    try:
        process_clipboard()
    except Exception as e:
        print(f"⚠️ Fehler beim Einfügen: {e}")
    cont = input("\nNeue Tabelle hinzufügen? (Y/N): ").strip().lower()
    if cont not in ("y", "yes", ""):
        print("👋 Fertig! Alle Tabellen wurden gespeichert unter:")
        print(RAW_FILE.resolve())
        break
    print("⏳ Bereit für die nächste Tabelle …\n")
    time.sleep(0.5)
