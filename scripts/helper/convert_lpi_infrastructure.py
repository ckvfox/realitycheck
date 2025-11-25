import re
from decimal import Decimal, ROUND_HALF_UP
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

RAW_PATH = Path("scripts/source_raw/International_LPI_from_2007_to_2023_0.xlsx")
TARGET_PATH = Path("scripts/source_csv/lpi_infrastructure.csv")
NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def select_column(columns, candidates):
    lowered = {col.lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    raise KeyError(f"None of the expected columns {candidates} were found. Available columns: {list(columns)}")


def column_index(cell_reference: str) -> int:
    match = re.match(r"([A-Z]+)", cell_reference)
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_reference}")
    letters = match.group(1)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def load_shared_strings(zfile: ZipFile) -> list[str]:
    try:
        shared = ET.fromstring(zfile.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [t.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t").text or "" for t in shared]


def parse_sheet(zfile: ZipFile, sheet_path: str, shared_strings: list[str]) -> pd.DataFrame:
    sheet = ET.fromstring(zfile.read(f"xl/{sheet_path}"))
    rows: list[dict[int, str]] = []

    for row in sheet.findall("main:sheetData/main:row", NS):
        row_data: dict[int, str] = {}
        for cell in row.findall("main:c", NS):
            ref = cell.get("r")
            if not ref:
                continue
            value_elem = cell.find("main:v", NS)
            if value_elem is None:
                continue
            value = value_elem.text
            if cell.get("t") == "s":
                value = shared_strings[int(value)]
            row_data[column_index(ref)] = value
        if row_data:
            rows.append(row_data)

    if not rows:
        return pd.DataFrame()

    header_row_index = 0
    candidate_values = {
        "country",
        "economy",
        "country or area",
        "country/area",
        "country name",
        "country name ",
    }
    for idx, row in enumerate(rows):
        lowered_values = {str(value).strip().lower() for value in row.values() if value}
        if lowered_values & candidate_values:
            header_row_index = idx
            break

    header_map = rows[header_row_index]
    headers = {idx: header_map[idx] for idx in sorted(header_map)}

    records = []
    for row in rows[header_row_index + 1 :]:
        record = {headers[idx]: row.get(idx, "") for idx in headers}
        if any(value != "" for value in record.values()):
            records.append(record)

    return pd.DataFrame(records)


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Source file not found: {RAW_PATH}")

    with ZipFile(RAW_PATH) as zfile:
        workbook = ET.fromstring(zfile.read("xl/workbook.xml"))
        relationships = ET.fromstring(zfile.read("xl/_rels/workbook.xml.rels"))

        rel_map = {
            rel.get("Id"): rel.get("Target")
            for rel in relationships.findall(
                "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
            )
        }

        shared_strings = load_shared_strings(zfile)

        frames = []
        for sheet in workbook.find("main:sheets", NS):
            sheet_name = sheet.get("name", "").strip()
            relationship_id = sheet.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            sheet_target = rel_map.get(relationship_id)
            if not sheet_target or not sheet_name.isdigit():
                continue

            year = int(sheet_name)
            df = parse_sheet(zfile, sheet_target, shared_strings)
            if df.empty:
                continue

            country_col = select_column(
                df.columns,
                [
                    "country",
                    "economy",
                    "country or area",
                    "country/area",
                    "country name",
                    "country name ",
                ],
            )
            value_col = select_column(
                df.columns,
                [
                    "lpi score",
                    "score",
                    "lpi score (1=low to 5=high)",
                    "infrastructure score",
                    "lpi score ",
                ],
            )

            frames.append(
                df[[country_col, value_col]]
                .rename(columns={country_col: "country", value_col: "value"})
                .assign(year=year)
            )

    if not frames:
        raise ValueError("No data extracted from workbook")

    data = pd.concat(frames, ignore_index=True)
    data = data.dropna(subset=["country", "year", "value"])

    data["year"] = data["year"].astype(int)
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["value"])

    data["value"] = data["value"].map(
        lambda val: f"{Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    )

    data = (
        data[["country", "year", "value"]]
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(TARGET_PATH, index=False)
    print(f"Saved {len(data)} rows to {TARGET_PATH}")


if __name__ == "__main__":
    main()
