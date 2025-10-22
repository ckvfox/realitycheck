#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – Normalize Yale EPI (wide format 1995–2022, incl. Recycling)
Input : /scripts/source_raw/YALE-EPI.xlsx
Output: /scripts/source_csv/environmental_performance_index.csv
        /scripts/source_csv/recycling_rate.csv
"""

import os
import pandas as pd

INFILE   = os.path.join("source_raw", "YALE-EPI.xlsx")
OUT_EPI  = os.path.join("source_csv", "environmental_performance_index.csv")
OUT_RECY = os.path.join("source_csv", "recycling_rate.csv")

def main():
    df = pd.read_excel(INFILE, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]

    # Spalten erkennen
    country_col   = next((c for c in df.columns if "Economy" in c or "Country" in c), None)
    indicator_col = next((c for c in df.columns if c.lower().startswith("indicator")), None)

    if not country_col or not indicator_col:
        raise RuntimeError(f"Unexpected structure: {df.columns.tolist()}")

    # Jahres-Spalten (1995–2022)
    year_cols = [c for c in df.columns if c.isdigit()]
    if not year_cols:
        raise RuntimeError("No year columns found.")

    # Wide → Long
    df_long = df.melt(
        id_vars=[country_col, indicator_col],
        value_vars=year_cols,
        var_name="year",
        value_name="value"
    ).dropna(subset=["value"])
    df_long["year"] = df_long["year"].astype(int)
    df_long["indicator"] = df_long[indicator_col].astype(str)

    # Filterdefinitionen
    epi_mask = df_long["indicator"].str.contains("YALE.EPI.EPI", case=False, na=False) | \
               df_long["indicator"].str.contains("Environmental Performance Index", case=False, na=False)
    rec_mask = df_long["indicator"].str.contains("YALE.EPI.REC", case=False, na=False) | \
               df_long["indicator"].str.contains("Recycling", case=False, na=False)

    # --- EPI ---
    epi_df = df_long.loc[epi_mask, [country_col, "year", "value"]].rename(
        columns={country_col: "country"}
    ).sort_values(["country", "year"])
    os.makedirs(os.path.dirname(OUT_EPI), exist_ok=True)
    epi_df.to_csv(OUT_EPI, index=False)
    print(f"✅ Wrote {OUT_EPI} ({len(epi_df)} rows)")

    # --- Recycling ---
    rec_df = df_long.loc[rec_mask, [country_col, "year", "value"]].rename(
        columns={country_col: "country"}
    ).sort_values(["country", "year"])
    if not rec_df.empty:
        rec_df.to_csv(OUT_RECY, index=False)
        print(f"✅ Wrote {OUT_RECY} ({len(rec_df)} rows)")
    else:
        print("ℹ️ No Recycling indicator found (YALE.EPI.REC).")

if __name__ == "__main__":
    main()
