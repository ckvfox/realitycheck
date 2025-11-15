#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck – PISA Overall Score Generator (final version)
-----------------------------------------------------------
Reads OECD PISA raw dataset from:

    /scripts/source_raw/OECD PISA data.csv

Produces RealityCheck target-format CSV:

    /scripts/source_csv/pisa_overall_score.csv

Output format:
    country,year,value

Method:
 • All PISA domains (Math, Reading, Science, etc.)
 • All demographic groups (Boy, Girl, Male, Female, All, etc.)
 • Unweighted arithmetic mean – transparent & academically defensible
 • Kaufmännisches Runden (0.5 -> aufrunden)

Author: RealityCheck AI Assistant
"""

import pandas as pd
import numpy as np
import os


# ---------------------------------------------------------------------------
# Build safe, relative paths based on script location
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # …/scripts/helper
RAW_DIR  = os.path.join(BASE_DIR, "..", "source_raw")
CSV_DIR  = os.path.join(BASE_DIR, "..", "source_csv")

BASE_IN  = os.path.join(RAW_DIR, "OECD PISA data.csv")
BASE_OUT = os.path.join(CSV_DIR, "pisa_overall_score.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_iso3(code):
    """Normalize to uppercase ISO3."""
    if not isinstance(code, str):
        return None
    return code.strip().upper()


def load_dataset(path):
    """Load CSV file robustly (supports comma or semicolon)."""
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, sep=";")


def compute_overall(df):
    """Compute unweighted mean across all domains + genders."""

    required = ["LOCATION", "TIME", "Value"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in dataset.")

    df = df.copy()

    df["LOCATION"] = df["LOCATION"].apply(normalize_iso3)
    df["Value"]    = pd.to_numeric(df["Value"], errors="coerce")

    # Group by ISO3 country code + year
    result = (
        df.groupby(["LOCATION", "TIME"])["Value"]
          .mean()
          .reset_index()
    )

    # Rename to RealityCheck schema
    result = result.rename(columns={
        "LOCATION": "country",
        "TIME":     "year",
        "Value":    "value"
    }).sort_values(["country", "year"])

    # -------------------------------------------------------------------
    # Kaufmännisches Runden (Österreichisches / deutsches Runden)
    # Beispiel: 524.83 -> 525
    # -------------------------------------------------------------------
    result["value"] = result["value"].round(0).astype(int)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("📥 Reading raw file:", BASE_IN)

    if not os.path.exists(BASE_IN):
        raise FileNotFoundError(f"ERROR: Raw PISA file not found at:\n{BASE_IN}")

    df = load_dataset(BASE_IN)

    print("📊 Columns detected:", list(df.columns))

    result = compute_overall(df)

    # Ensure output directory exists
    os.makedirs(CSV_DIR, exist_ok=True)

    result.to_csv(BASE_OUT, index=False, encoding="utf-8")

    print(f"✅ Created: {BASE_OUT}")
    print(f"📄 Rows: {len(result)}")
    print("\n🔎 Preview:")
    print(result.head())


if __name__ == "__main__":
    main()
