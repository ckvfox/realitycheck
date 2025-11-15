#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – Winter Olympics Medal Importer (perfect TAB version)
------------------------------------------------------------------
Reads a copied medal table from the clipboard:

1924 Chamonix (France) Winter Olympics Medal Tally by Country
Rank    Country    Gold  Silver  Bronze  Total
1       Norway (NOR)   4  7  6  17

Automatically:
 • extracts year
 • removes headline
 • parses true TAB-separated table
 • outputs RealityCheck format:
       country,year,value

Saved at:
   /scripts/source_csv/olympia_medals_winter.csv
"""

import pandas as pd
import pyperclip
from pathlib import Path
import os
import re
import io


# -----------------------------------
# Paths
# -----------------------------------
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR  = BASE_DIR / ".." / "source_csv"
OUT_FILE = OUT_DIR / "olympia_medals_winter.csv"


# -----------------------------------
# Helpers
# -----------------------------------

def extract_year(raw: str) -> int:
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", raw)
    if years:
        return int(years[0])
    raise ValueError("Kein Jahr gefunden.")


def extract_noc(country: str) -> str:
    m = re.search(r"\(([A-Z]{3})\)", country)
    return m.group(1) if m else country[-3:].upper()


def load_table_after_headline(raw: str) -> pd.DataFrame:
    """
    We remove all lines before the actual header:
    Detect the first line that starts with "Rank".
    Then read the remaining text as TAB-separated CSV.
    """
    lines = raw.splitlines()

    # find header line
    start_index = None
    for i, line in enumerate(lines):
        if line.lower().startswith("rank"):
            start_index = i
            break

    if start_index is None:
        raise ValueError("Header 'Rank' nicht gefunden.")

    table_text = "\n".join(lines[start_index:])

    try:
        return pd.read_csv(io.StringIO(table_text), sep="\t")
    except Exception:
        raise ValueError("Konnte Tabelle nicht als TAB-Datei lesen.")


def convert_to_realitycheck(df, year):
    df = df.copy()
    df["noc"]   = df["Country"].apply(extract_noc)
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0).astype(int)

    return pd.DataFrame({
        "country": df["noc"],
        "year": year,
        "value": df["Total"]
    })


# -----------------------------------
# Main Loop
# -----------------------------------

def main():
    print("🏅 RealityCheck – Winter Olympics Importer (perfect TAB version)")
    print("📋 Bitte komplette Tabelle inkl. Überschrift kopieren.")
    print("➡️ Danach ENTER drücken.\n")

    os.makedirs(OUT_DIR, exist_ok=True)

    while True:
        input("➡️ ENTER, wenn kopiert … ")

        raw = pyperclip.paste()

        # 1. Jahr extrahieren
        year = extract_year(raw)
        print(f"📆 Jahr erkannt: {year}")

        # 2. Tabelle laden
        df = load_table_after_headline(raw)
        print("\n📊 Tabellen-Preview:")
        print(df.head())

        # 3. Konvertieren
        out = convert_to_realitycheck(df, year)

        # 4. Speichern
        header = not OUT_FILE.exists()
        out.to_csv(OUT_FILE, mode="a", index=False, header=header)

        print(f"\n✅ {len(out)} Zeilen gespeichert in: {OUT_FILE}")
        print(out)

        # 5. Weiter?
        cont = input("\n🔁 Weiteres Jahr? (ja/nein): ").strip().lower()
        if cont not in ["ja", "j", "yes", "y"]:
            print("\n👋 Fertig.")
            break

        print("\n⏳ Bereit für die nächste Tabelle …\n")


if __name__ == "__main__":
    main()
