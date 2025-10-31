#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📘 RealityCheck – Append Source Sentences to KPI Descriptions
──────────────────────────────────────────────────────────────
Reads /data/meta/available_kpis.json and appends a standardized
data-source sentence at the end of each KPI description based
on the KPI title. 

Creates: /data/meta/available_kpis_with_sources.json
"""

import json, os
from pathlib import Path

# === Pfade ===
BASE_DIR = Path(__file__).resolve().parent.parent
META_PATH = BASE_DIR / "data" / "meta" / "available_kpis.json"
OUTPUT_PATH = BASE_DIR / "data" / "meta" / "available_kpis_with_sources.json"

# === Mapping-Tabelle: KPI Title → Quellensatz ===
SOURCE_SENTENCES = {
    "Land Area": "These data are provided by the World Bank’s World Development Indicators database.",
    "Population": "These data are provided by the World Bank’s World Development Indicators database.",
    "Population Growth": "These data are provided by the World Bank’s World Development Indicators database.",
    "Median Age": "These data are compiled by Our World in Data based on the United Nations World Population Prospects.",
    "Fertility Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Urbanization Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Democracy Index": "These data are compiled by Our World in Data based on the Economist Intelligence Unit’s Democracy Index.",
    "Press Freedom Index": "These data are compiled by Our World in Data based on Reporters Without Borders (RSF).",
    "World Happiness Index": "These data are provided by the World Happiness Report published by the UN Sustainable Development Solutions Network.",
    "GDP": "These data are provided by the World Bank’s World Development Indicators database.",
    "GDP per Capita": "These data are provided by the World Bank’s World Development Indicators database.",
    "GNI per capita": "These data are provided by the World Bank’s World Development Indicators database.",
    "Gini Index": "These data are provided by the World Bank’s World Development Indicators database.",
    "Public Debt": "These data are provided by the World Bank’s World Development Indicators database.",
    "Tax Revenue": "These data are provided by the World Bank’s World Development Indicators database.",
    "Unemployment Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Big Mac Index": "These data originate from The Economist’s Big Mac Index and have been preprocessed for comparison.",
    "Human Development Index": "These data are compiled by Our World in Data based on the United Nations Development Programme’s Human Development Reports.",
    "Health Expenditure per Capita": "These data are provided by the World Bank’s World Development Indicators database.",
    "Physicians": "These data are provided by the World Bank’s World Development Indicators database.",
    "Hospital Beds": "These data are provided by the World Bank’s World Development Indicators database.",
    "Infant Mortality Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Maternal Mortality Ratio": "These data are provided by the World Bank’s World Development Indicators database.",
    "Life Expectancy at Birth": "These data are provided by the World Bank’s World Development Indicators database.",
    "Adult Literacy Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Homelessness Rate": "These data are compiled by Our World in Data based on OECD and national statistical agencies.",
    "Old-Age Dependency Ratio": "These data are compiled by Our World in Data based on the World Bank’s World Development Indicators.",
    "Age Dependency Ratio": "These data are compiled by Our World in Data based on the World Bank’s World Development Indicators.",
    "Overall Immunization Coverage": "These data are provided by the World Bank’s World Development Indicators database.",
    "Extreme Poverty": "These data are provided by the World Bank’s World Development Indicators database.",
    "Access to Basic Drinking Water": "These data are provided by the World Bank’s World Development Indicators database.",
    "CO₂ Emissions": "These data are compiled by Our World in Data based on the Global Carbon Project and CDIAC.",
    "Air Quality": "These data are provided by the World Bank’s World Development Indicators database.",
    "Renewable Energy Share": "These data are provided by the World Bank’s World Development Indicators database.",
    "Internet Penetration Rate": "These data are provided by the World Bank’s World Development Indicators database.",
    "Mobile Subscriptions": "These data are provided by the World Bank’s World Development Indicators database.",
    "Railway Length": "These data are provided by the World Bank’s World Development Indicators database.",
    "Inflation (Consumer Price Index)": "These data are provided by the World Bank’s World Development Indicators database.",
    "Employment-to-population ratio": "These data are provided by the World Bank’s World Development Indicators database.",
    "Female Labor Force Participation": "These data are provided by the World Bank’s World Development Indicators database.",
    "Political Corruption Index": "These data are compiled by Our World in Data based on the Varieties of Democracy (V-Dem) dataset.",
    "Military Spending": "These data are compiled by Our World in Data based on the Stockholm International Peace Research Institute (SIPRI).",
    "Number of Armed Conflicts": "These data are compiled by Our World in Data based on the Uppsala Conflict Data Program (UCDP).",
    "Global Conflict Deaths": "These data are compiled by Our World in Data based on the Uppsala Conflict Data Program (UCDP).",
    "Road Traffic Deaths": "These data are provided by the World Bank’s World Development Indicators database.",
    "Fixed Broadband Subscriptions": "These data are provided by the World Bank’s World Development Indicators database.",
    "Education Expenditure": "These data are provided by the World Bank’s World Development Indicators database.",
    "Mean Years of Schooling": "These data are compiled by Our World in Data based on the United Nations Development Programme’s Human Development Reports.",
    "Military Expenditure": "These data are provided by the World Bank’s World Development Indicators and SIPRI.",
    "Recycling Rate": "These data are compiled from OECD Waste Statistics and national environmental agencies.",
    "Environmental Performance Index": "These data are published by Yale University & Columbia University – Environmental Performance Index (EPI).",
    "Global Peace Index": "These data are provided by the Institute for Economics and Peace (IEP).",
    "Olympic Medals (Summer)": "These data are based on Kaggle – Athlete Events Dataset preprocessed by RealityCheck.",
    "Olympic Medals (Winter)": "These data are based on Kaggle – Athlete Events Dataset preprocessed by RealityCheck.",
    "Living Planet Index": "These data are compiled by Our World in Data based on WWF and Zoological Society of London – Living Planet Index (2024).",
    "Electric Vehicle Stock": "These data are compiled by Our World in Data based on the International Energy Agency (IEA) – Global EV Data Explorer.",
    "Number of Recorded Natural Disasters": "These data are compiled by Our World in Data based on EM-DAT – International Disaster Database.",
    "Global CO₂ Emissions": "These data are compiled by Our World in Data based on the Global Carbon Project and CDIAC datasets.",
    "Global Supply Chain Stress Index": "These data are published by the Federal Reserve Bank of New York – Global Supply Chain Pressure Index (GSCPI).",
    "Global Temperature Anomaly": "These data are compiled by Our World in Data based on Berkeley Earth and NASA GISTEMP temperature records.",
    "Resilience Index": "These data are provided by the European Commission – INFORM Risk and Resilience Index (JRC DRMKC).",
    "Climate Risk Index": "These data are published annually by Germanwatch – Global Climate Risk Index Report.",
    "Geopolitical Risk Index": "These data are published by Matteo Iacoviello – Geopolitical Risk Index (2024 edition)."
}


# === Hauptlogik ===
def append_source_sentences():
    with META_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for kpi in data:
        title = kpi.get("title", "").strip()
        desc = kpi.get("description", "").strip()
        addendum = SOURCE_SENTENCES.get(title)

        if addendum and addendum not in desc:
            # Punkt am Ende prüfen
            if not desc.endswith((".", "!", "?")):
                desc += "."
            kpi["description"] = f"{desc} {addendum}"
            updated += 1

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Appended source sentences to {updated} KPIs.")
    print(f"💾 Saved updated file to: {OUTPUT_PATH}")

# === Start ===
if __name__ == "__main__":
    append_source_sentences()
