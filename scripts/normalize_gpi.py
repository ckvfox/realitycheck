#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – Normalize GPI (Global Peace Index, sheet 'Overall Scores')
Input : /scripts/source_raw/GPI_public_release_2025.xlsx
Sheet : "Overall Scores"
Output: /scripts/source_csv/global_peace_index.csv
Format: country,year,value
Notes : Auto-detect header row, keep only *_score columns, ignore *_rank.
"""

import os
import pandas as pd
import re

INFILE  = os.path.join("source_raw", "GPI_public_release_2025.xlsx")
OUTFILE = os.path.join("source_csv", "global_peace_index.csv")

def find_header_row(path, max_rows=50):
    """Scan up to `max_rows` rows in sheet 'Overall Scores' to find one containing 'country'."""
    df_raw = pd.read_excel(path, sheet_name="Overall Scores", header=None, nrows=max_rows)
    for i in range(len(df_raw)):
        row = [str(x).strip().lower() for x in df_raw.iloc[i].values if isinstance(x, str)]
        if any("country" in cell for cell in row):
            return i
    return None

def main():
    header_row = find_header_row(INFILE)
    if header_row is None:
        raise RuntimeError("❌ Could not find a header row containing 'country' in sheet 'Overall Scores'.")

    print(f"🧭 Detected header row at Excel row {header_row + 1}")

    # Datei mit korrektem Sheet & Header einlesen
    df = pd.read_excel(INFILE, sheet_name="Overall Scores", header=header_row)
    df.columns = [str(c).strip().replace("\u200b", "") for c in df.columns]

    # Land-Spalte erkennen
    possible_country = [c for c in df.columns if re.search(r"country", c, re.IGNORECASE)]
    if not possible_country:
        raise RuntimeError(f"❌ No 'country' column found after header detection. Columns: {df.columns.tolist()}")
    country_col = possible_country[0]

    # Nur *_score-Spalten behalten (2008_score ... 2025_score)
    score_cols = [c for c in df.columns if re.match(r"^\d{4}_score$", str(c))]
    if not score_cols:
        raise RuntimeError(f"❌ No *_score columns found. Columns: {df.columns.tolist()}")

    # Wide → Long
    df_long = df.melt(id_vars=[country_col], value_vars=score_cols,
                      var_name="year_raw", value_name="value")
    df_long["year"] = df_long["year_raw"].str.extract(r"(\d{4})").astype(int)

    # Komma in Punkt umwandeln und zu float casten
    df_long["value"] = (
        df_long["value"].astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")

    # Finale Struktur
    df_long = df_long[[country_col, "year", "value"]].dropna()
    df_long = df_long.rename(columns={country_col: "country"})
    df_long = df_long.sort_values(["country", "year"])

    # Export
    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
    df_long.to_csv(OUTFILE, index=False)

    print(f"✅ Wrote {OUTFILE} ({len(df_long)} rows, {df_long['year'].min()}–{df_long['year'].max()})")

if __name__ == "__main__":
    main()
