import re

def normalize_name(title: str) -> str:
    """
    Einheitliche Normalisierung für KPI-Dateien (Backend & Frontend identisch).
    Regeln (müssen 1:1 mit normalize_name.js übereinstimmen):
      - Kleinschreibung, Trim
      - Subskript-Ziffern ₀–₉ -> 0–9
      - "co₂" -> "co2"
      - "% of gdp" / "percent of gdp" -> "of gdp"
      - Zahlen mit Punkt (z. B. 2.5) -> 2_5
      - "1,000" oder "1.000" -> "1_000"
      - Nicht alphanumerische Zeichen -> "_"
      - Bindestriche -> "_"
      - Mehrfache "_" reduzieren, führende/Trailing "_" entfernen
    """
    if not title:
        return "unknown_kpi"

    s = title.lower().strip()

    # Subskript-Zahlen vereinheitlichen
    sub_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    s = s.translate(sub_map)

    # Ersetzungen/Korrekturen
    s = s.replace("co₂", "co2")

    # "(% of gdp)" / "percent of gdp" -> "of gdp"
    s = re.sub(r'\s*(%|percent)\s*of\s*gdp', ' of gdp', s)

    # Punkt zwischen Ziffern (2.5) -> Unterstrich
    s = re.sub(r'(?<=\d)\.(?=\d)', '_', s)

    # "1,000" oder "1.000" -> "1_000"
    s = re.sub(r'1[.,]000', '1_000', s)

    # Unnötige Zeichen entfernen
    s = s.replace("(", "").replace(")", "").replace(",", "")

    # Nicht alphanumerische Zeichen -> "_"
    s = re.sub(r'[^a-z0-9._-]', '_', s)

    # Bindestriche -> Unterstriche
    s = s.replace("-", "_")

    # Doppelte Unterstriche reduzieren
    s = re.sub(r'_+', '_', s)

    # Führende/trailing "_" entfernen
    s = s.strip('_')

    return s
