#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealityCheck Meta Deep Scan – Extended Version (Oktober 2025)
──────────────────────────────────────────────────────────────
• Durchsucht alle World-Bank-Indikatoren aus available_kpis.json
• Testet API-JSON + ZIP-Metadateien auf Date/Updated/Accessed-Felder
• Erkennt problematische KPIs ohne valides Änderungsdatum
"""

import requests, json, re, io, zipfile, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
META_FILE = BASE_DIR / "data" / "meta" / "available_kpis.json"
REPORT_FILE = BASE_DIR / "data" / "meta" / "meta_scan_report.txt"


# ---------------------------------------------------------------------
def deep_scan_json(obj, path="root", results=None):
    """Rekursiver Scanner für alle Felder, die Datum, updated, accessed o.ä. enthalten."""
    if results is None:
        results = []

    key_patterns = re.compile(r"(date|updated|access|time|modified)", re.IGNORECASE)
    value_patterns = re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\s*\d{4}|"
        r"\d{4}-\d{2}-\d{2}|"
        r"Date\s*accessed|Last\s*updated)",
        re.IGNORECASE,
    )

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}"
            if key_patterns.search(k):
                results.append((new_path, str(v)))
            if isinstance(v, (dict, list)):
                deep_scan_json(v, new_path, results)
            elif isinstance(v, str) and value_patterns.search(v):
                results.append((new_path, v))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            deep_scan_json(item, f"{path}[{i}]", results)

    return results


# ---------------------------------------------------------------------
def scan_worldbank_api(code: str):
    """Scannt die World Bank API nach Feldern, die auf ein Datum hindeuten."""
    url = f"https://api.worldbank.org/v2/indicator/{code}?format=json"
    print(f"🌍 Scanning API for {code}")
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()[0] if isinstance(r.json(), list) else r.json()
        findings = deep_scan_json(data)
        return findings
    except Exception as e:
        print(f"❌ API fetch failed for {code}: {e}")
        return []


# ---------------------------------------------------------------------
def scan_worldbank_zip(code: str):
    """Scannt das ZIP-Metafile der World Bank nach 'date accessed'."""
    url = f"https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"
    print(f"💾 Scanning ZIP for {code}")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"❌ ZIP not available: HTTP {resp.status_code}")
            return "ZIP unavailable"

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            meta_files = [n for n in zf.namelist() if "Metadata_Indicator" in n]
            if not meta_files:
                return "No metadata CSV found"
            text = zf.read(meta_files[0]).decode("utf-8-sig", errors="ignore")

            match = re.search(
                r"date\s*accessed[:\s,]+([A-Za-z]+\s+\d{1,2},?\s*\d{4})",
                text,
                re.IGNORECASE,
            )
            if match:
                return match.group(1)
            else:
                return "No 'date accessed' found"
    except Exception as e:
        return f"ZIP error: {e}"


# ---------------------------------------------------------------------
def load_worldbank_kpis():
    """Lädt alle World Bank KPIs aus available_kpis.json"""
    if not META_FILE.exists():
        raise FileNotFoundError(f"❌ {META_FILE} not found")

    data = json.loads(META_FILE.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        kpis = [v for v in data.values() if v.get("source_type") == "worldbank"]
    else:
        kpis = [v for v in data if v.get("source_type") == "worldbank"]

    print(f"📊 Found {len(kpis)} World Bank KPIs to test")
    return kpis


# ---------------------------------------------------------------------
def main():
    kpis = load_worldbank_kpis()
    report_lines = []

    for meta in kpis:
        code = meta.get("source_code") or meta.get("code")
        title = meta.get("title", "Unknown KPI")
        if not code:
            continue

        print("\n" + "=" * 80)
        print(f"🔎 {title} ({code})")
        print("=" * 80)

        # === API-Test ===
        api_findings = scan_worldbank_api(code)
        has_date_field = any("last" in p.lower() or "date" in p.lower() for p, _ in api_findings)
        if api_findings:
            print(f"🧭 Found {len(api_findings)} potential date fields in API.")
        else:
            print("⚠️ No date fields found in API.")

        # === ZIP-Test ===
        zip_result = scan_worldbank_zip(code)
        print(f"🗂️ ZIP Result: {zip_result}")

        # --- Ergebnis ins Reportfile schreiben ---
        report_lines.append({
            "title": title,
            "code": code,
            "api_results": len(api_findings),
            "has_date_field": has_date_field,
            "zip_result": zip_result
        })

    # === Zusammenfassung speichern ===
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_lines, f, indent=2, ensure_ascii=False)

    print("\n📄 Report written to:", REPORT_FILE)
    print("✅ Meta Deep Scan completed.\n")


# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
