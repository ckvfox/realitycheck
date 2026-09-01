"""Special world-level source adapters."""
from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from adapters.runtime import SourceRuntime

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"


def fetch_geopolitical_risk_index(
    *,
    output_dir: Path,
    runtime: SourceRuntime,
    http_get=requests.get,
) -> dict[str, Any] | None:
    """Download monthly GPR values and publish the established annual JSON series."""
    kpi_id = "geopolitical_risk_index"
    runtime.log(f"[FETCH] Geopolitical Risk Index -> {GPR_URL}")
    try:
        response = http_get(GPR_URL, timeout=30)
        response.raise_for_status()
        frame = pd.read_excel(io.BytesIO(response.content), sheet_name="Sheet1")
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if not {"month", "gpr"}.issubset(frame.columns):
            raise ValueError(f"Unexpected GPR columns: {frame.columns.tolist()}")

        frame["month"] = pd.to_datetime(frame["month"], format="%d.%m.%Y", errors="coerce")
        frame["value"] = pd.to_numeric(frame["gpr"], errors="coerce")
        frame = frame.dropna(subset=["month", "value"])
        frame["year"] = frame["month"].dt.year
        current_year = datetime.now(UTC).year
        past = frame[frame["year"] < current_year].groupby("year", as_index=False)["value"].mean()
        current = frame[frame["year"] == current_year].sort_values("month").tail(1)[["year", "value"]]
        annual = pd.concat([past, current], ignore_index=True)
        if annual.empty:
            raise ValueError("GPR workbook contains no usable observations")
        annual["value"] = annual["value"].round(2)
        annual["country"] = "World"
        records = annual[["country", "year", "value"]].to_dict(orient="records")
        runtime.write_json(output_dir / f"{kpi_id}.json", records)
        runtime.log(f"[OK] GPR saved: {len(records)} records")
        return {
            "source": "https://www.matteoiacoviello.com/gpr.htm",
            "url": GPR_URL,
            "source_date": datetime.now(UTC).strftime("%Y-%m-%dT00:00:00Z"),
            "data_year": int(annual["year"].max()),
            "last_fetch": runtime.now_utc(),
        }
    except Exception as exc:
        runtime.log(f"[ERROR] GPR fetch failed: {exc}")
        return None
