#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 RealityCheck – ISO-A3 Mapper (combined sources)
─────────────────────────────────────────────────────────────
Ergänzt für jedes Land in /data/meta/countries.json
das passende iso_a3-Feld.  Nutzt zuerst country_mappings.json,
dann world_countries_geo.json (Fallback).

Struktur nachher:
"Germany": {
  "capital": "Berlin",
  "government": "Federal Republic",
  "lat": 52.52,
  "lon": 13.4,
  "iso_a3": "DEU"
}
"""

import json
from pathlib import Path
import difflib

# === Pfade ===
ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "data" / "meta"

COUNTRIES_FILE = META / "countries.json"
MAPPINGS_FILE = META / "country_mappings.json"
GEOJSON_FILE = META / "world_countries_geo.json"
OUTPUT_FILE = META / "countries_with_iso.json"

# === Laden ===
print(f"📘 Lade {COUNTRIES_FILE.name} …")
countries = json.loads(COUNTRIES_FILE.read_text(encoding="utf-8"))

print(f"📘 Lade {MAPPINGS_FILE.name} …")
mappings = json.loads(MAPPINGS_FILE.read_text(encoding="utf-8"))

print(f"📘 Lade {GEOJSON_FILE.name} …")
geo = json.loads(GEOJSON_FILE.read_text(encoding="utf-8"))
features = geo.get("features", [])
print(f"🌍 {len(features)} GeoJSON-Einträge gefunden")

# === GeoJSON Hilfsindex nach ISO-A3 und Namen ===
geo_by_name = {}
geo_by_iso = {}

for f in features:
    p = f.get("properties", {})
    iso = p.get("ISO_A3")
    names = [p.get(k) for k in ["ADMIN", "NAME", "SOVEREIGNT", "BRK_NAME", "NAME_EN"] if p.get(k)]
    for n in names:
        geo_by_name[n.strip().lower()] = iso
    if iso:
        geo_by_iso[iso.strip().upper()] = iso

# === Schritt 1: ISO aus country_mappings übernehmen ===
print("🔗 Verbinde country_mappings.json …")
reverse_map = {}
for alias, canon in mappings.items():
    reverse_map.setdefault(canon, []).append(alias.upper())

added = 0
for cname in countries.keys():
    iso = None
    aliases = reverse_map.get(cname, [])
    for a in aliases:
        if len(a) == 3 and a.isupper():  # typischer ISO_A3
            iso = a
            break
    if iso:
        countries[cname]["iso_a3"] = iso
        added += 1

# === Schritt 2: Fallback mit GeoJSON (falls kein ISO gefunden) ===
unresolved = [c for c in countries if "iso_a3" not in countries[c]]
if unresolved:
    print(f"🧭 {len(unresolved)} Länder ohne Mapping – prüfe GeoJSON …")

    for cname in unresolved:
        key = cname.lower()
        iso = geo_by_name.get(key)
        if not iso:
            # Fuzzy
            match = difflib.get_close_matches(key, geo_by_name.keys(), n=1, cutoff=0.8)
            if match:
                iso = geo_by_name[match[0]]
        if iso:
            countries[cname]["iso_a3"] = iso
            added += 1
        else:
            countries[cname]["iso_a3"] = None  # leer, aber vorhanden

# === Ergebnisse ===
OUTPUT_FILE.write_text(json.dumps(countries, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"✅ ISO-Codes ergänzt: {added} / {len(countries)} Länder")
unresolved_final = [c for c in countries if not countries[c].get("iso_a3")]
if unresolved_final:
    print(f"⚠️ {len(unresolved_final)} Länder ohne ISO-Code:")
    for u in unresolved_final[:15]:
        print("   –", u)
print(f"💾 Gespeichert als {OUTPUT_FILE.name}")
