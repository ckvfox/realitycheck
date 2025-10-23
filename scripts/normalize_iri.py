import pandas as pd

def convert_inform_excel_to_csv(input_path, output_path):
    # INFORM Excel laden
    xls = pd.ExcelFile(input_path)
    df = xls.parse("INFORM2025_2nd_edition_Trend")

    # Nur den "INFORM Risk Index" behalten
    df = df[df["IndicatorName"] == "INFORM Risk Index"].copy()

    # Struktur vereinfachen
    df["country"] = df["Iso3"]
    df["year"] = df["Year of the release"]
    df["value"] = df["IndicatorScore"]

    df_final = df[["country", "year", "value"]].sort_values(["country", "year"])
    df_final.to_csv(output_path, index=False)
    print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    convert_inform_excel_to_csv(
        "source_raw/INFORM2024_TREND_2015_2024_v70_ALL.xlsx",
        "source_csv/inform_resilience_index.csv"
    )
