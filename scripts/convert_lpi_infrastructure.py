import pandas as pd
from pathlib import Path

RAW_PATH = Path("scripts/source_raw/International_LPI_from_2007_to_2023_0.xlsx")
TARGET_PATH = Path("scripts/source_csv/lpi_infrastructure.csv")


def select_column(columns, candidates):
    lowered = {col.lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    raise KeyError(f"None of the expected columns {candidates} were found. Available columns: {list(columns)}")


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Source file not found: {RAW_PATH}")

    df = pd.read_excel(RAW_PATH)

    country_col = select_column(df.columns, ["country", "economy", "country or area", "country/area", "country name", "country name "])
    year_col = select_column(df.columns, ["year"])
    value_col = select_column(df.columns, ["lpi score", "score", "lpi score (1=low to 5=high)", "infrastructure score", "lpi score "])

    data = df[[country_col, year_col, value_col]].rename(columns={country_col: "country", year_col: "year", value_col: "value"})
    data = data.dropna(subset=["country", "year", "value"])
    data["year"] = data["year"].astype(int)
    data = data.sort_values(["country", "year"]).reset_index(drop=True)

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(TARGET_PATH, index=False)
    print(f"Saved {len(data)} rows to {TARGET_PATH}")


if __name__ == "__main__":
    main()
