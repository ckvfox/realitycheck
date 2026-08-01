# Methodik: Datenaktualitäts-Audit vom 1. August 2026

## Lokale Bestandsaufnahme

Ausgangspunkt sind `data/meta/available_kpis.json`, die produktiven KPI-Dateien unter `data/` und `data/fetch_status.json`. Für jeden KPI wurde das höchste tatsächlich vorhandene Datenjahr ermittelt. Ein KPI gilt für dieses Audit als prüfbedürftig, wenn das höchste Jahr kleiner als 2025 ist.

Ergebnis: 42 von 75 KPI-Datensätzen enden vor 2025. Davon enden 1 im Jahr 2019, 1 im Jahr 2020, 1 im Jahr 2021, 7 im Jahr 2022, 15 im Jahr 2023 und 17 im Jahr 2024. Für die Handlungsanalyse wurden die 12 lokalen CSV-Quellen vollständig abgetrennt. Neun davon liegen vor 2025; damit verbleiben 33 automatisierte Reihen mit einem Höchstjahr vor 2025 und 30 automatisierte Reihen ab 2025.

## Manuelle CSV-Quellen

Alle zwölf CSV-Quellen bleiben bewusst lokale, geprüfte Importe. Dazu zählen `olympic_medals_summer` und `olympic_medals_winter`. `scripts/check_source_csv_updates.py` validiert offline Datei, Schema, Zeilen, Höchstjahr und SHA-256. Die Option `--online` prüft ausschließlich die in `data/meta/manual_csv_sources.json` festgelegten offiziellen Seiten mit quellenspezifischen Mustern. Sie lädt keine Datensätze, verwendet kein Sprachmodell und ersetzt keine Dateien.

Der Online-Lauf am 1. August 2026 bestätigte 12 gültige lokale Dateien und meldete vier mögliche neue Editionen: EPI 2026, World Happiness Report 2026, INFORM 2026 und Network Readiness Index 2025. Diese Meldungen sind keine Importfreigabe.

## Entscheidungsregeln

- **Sofort anbinden:** Eine offizielle, maschinenlesbare Quelle enthält ein neueres, weitgehend gleich definiertes Datenjahr.
- **Mit Vertrag/Migration:** Neuere Daten sind verfügbar, aber Abdeckung, Definition, Revisionsstatus oder Schätzung/Projektion müssen im Source Contract explizit behandelt werden.
- **Erst Endpoint klären:** Eine neuere offizielle Ausgabe existiert, aber der stabile Download- oder API-Endpunkt ist noch nicht ausreichend verifiziert.
- **Nicht automatisieren:** Neuere Daten sind zugangs- oder lizenzbeschränkt oder nur über eine problematische Scraping-Lösung erreichbar.
- **Kein Wechsel empfohlen:** Der lokale Stand entspricht der neuesten international vergleichbaren Ausgabe oder eine Alternative wäre fachlich nicht dieselbe Kennzahl.

## KPI-Lückenanalyse

Die Vorschläge wurden nicht nach bloßer Datenverfügbarkeit ausgewählt, sondern nach zusätzlichem Erklärungswert gegenüber dem bestehenden Portfolio. Priorität erhielten Grundbedürfnisse, Bildungsabschluss, Hunger, Vertreibung, politische Repräsentation, Wohlstandsdynamik, Biodiversität und Datenvertrauen. Reihen mit starker Doppelung zu bereits vorhandenen KPIs oder mit Login-, Konto- beziehungsweise instabilen Scraping-Anforderungen wurden zurückgestellt.

Für die einfache Anbindung wurden offizielle World-Bank-Indikatoren bevorzugt, weil der Adapter bereits produktiv vorhanden ist und die Daten ohne Konto als API/CSV verfügbar sind. Der Statistical Performance Indicator ist methodisch ein Vertrauens-Guardrail: Er soll Unsicherheit und Berichtskapazität eines Landes sichtbar machen, aber nicht als weiterer positiver Bestandteil in den Overall Score eingehen.

## Offizielle Gegenquellen

- Yale Environmental Performance Index: https://epi.yale.edu/epi-downloads
- World Happiness Report Data Sharing: https://www.worldhappiness.report/data-sharing/
- Network Readiness Index: https://networkreadinessindex.org/
- World Bank Worldwide Governance Indicators: https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators
- WHO Global Status Report on Road Safety 2023: https://www.who.int/teams/social-determinants-of-health/safety-and-mobility/global-status-report-on-road-safety-2023
- UNECE Railway density / length data portal: https://w3.unece.org/PXWeb/en/DataMap?IndicatorCode=42
- OECD municipal waste SDMX dataset: https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_MUNW@DF_MUNW,1.0/...
- UN World Population Prospects 2024: https://population.un.org/wpp/
- ILOSTAT labour productivity: https://ilostat.ilo.org/topics/labour-productivity/
- SIPRI Military Expenditure Database: https://www.sipri.org/databases/milex
- Social Progress Index: https://www.socialprogress.org/social-progress-index-2025-2
- UNODC homicide data portal: https://data.unodc.org/datareport/hom-victim
- World Bank Logistics Performance Index: https://lpi.worldbank.org/en/about
- UNDP Human Development data downloads: https://hdr.undp.org/data-center/documentation-and-downloads
- Living Planet Index: https://www.livingplanetindex.org/lpi
- WHO UHC monitoring: https://www.who.int/data/monitoring-universal-health-coverage
- World Bank Statistical Performance Indicator: https://data.worldbank.org/indicator/IQ.SPI.OVRL
- World Bank refugees by country of asylum: https://data.worldbank.org/indicator/SM.POP.RHCR.EA
- World Bank lower-secondary completion: https://data.worldbank.org/indicator/SE.SEC.CMPT.LO.ZS

## Grenzen

Das Audit verifiziert Verfügbarkeit und grundsätzliche technische Anbindbarkeit. Es führt noch keinen produktiven Import aus und prüft noch nicht für jede Quelle die vollständige Länderzuordnung, alle Lizenzdetails oder jedes Spaltenschema. Bei revidierten Reihen müssen historische Werte vollständig neu geladen werden; bei Definitionenwechseln ist ein neuer KPI oder eine klar versionierte Migration erforderlich.
