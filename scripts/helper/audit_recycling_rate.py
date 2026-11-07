#!/usr/bin/env python3
"""Compare the current Recycling Rate with OECD material recycling, without publishing."""
import csv
import io
import json
import math
from pathlib import Path
from statistics import median
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
URL = ("https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_MUNW@DF_MUNW,1.0/"
       ".A.RECYCLING.PT_WST_TR?startPeriod=1995")


def compare(content):
    meta = ROOT / "data/meta"
    countries = json.loads((meta / "countries.json").read_text(encoding="utf-8"))
    aliases = json.loads((meta / "country_mappings.json").read_text(encoding="utf-8"))
    canonical = {name: info["iso_a3"] for name, info in countries.items()}
    canonical.update({code: code for code in canonical.values()})
    local = {}
    with (ROOT / "scripts/source_csv/recycling_rate.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            label = row["country"]
            code = canonical.get(label) or canonical.get(aliases.get(label))
            if code:
                key = code, row["year"]
                if key in local:
                    raise ValueError(f"Duplicate normalized local recycling key: {key}")
                local[key] = float(row["value"])

    oecd = {}
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        if (row["FREQ"], row["MEASURE"], row["UNIT_MEASURE"], row["UNIT_MULT"]) != (
            "A", "RECYCLING", "PT_WST_TR", "0"
        ):
            raise ValueError("Unexpected OECD recycling measure, denominator or unit")
        if row["REF_AREA"] not in canonical.values() or not row["OBS_VALUE"]:
            continue
        key = row["REF_AREA"], row["TIME_PERIOD"]
        value = float(row["OBS_VALUE"])
        if key in oecd or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"Invalid or duplicate OECD observation: {key}")
        oecd[key] = value
    overlap = local.keys() & oecd.keys()
    gaps = [abs(local[key] - oecd[key]) for key in overlap]
    if not gaps:
        raise ValueError("No comparable country-years")
    return {
        "source": URL,
        "local_countries": len({code for code, _ in local}),
        "oecd_countries": len({code for code, _ in oecd}),
        "overlap_countries": len({code for code, _ in overlap}),
        "overlap_observations": len(overlap),
        "median_absolute_gap_percentage_points": round(median(gaps), 2),
        "observations_within_one_percentage_point": sum(gap <= 1 for gap in gaps),
    }


if __name__ == "__main__":
    with urlopen(Request(URL, headers={"Accept": "text/csv"}), timeout=45) as response:
        print(json.dumps(compare(response.read().decode("utf-8-sig")), indent=2))
