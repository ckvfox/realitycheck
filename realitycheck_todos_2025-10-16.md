# RealityCheck – Consolidated To-dos (as of 2025-10-16)

## Phase 1 – Fehler & Performance (User-Facing First)
- [ ] Chatbot deaktivieren (countries.html → `const chatbotEnabled = false;`)
- [ ] Group-Aggregation korrigieren (Summe statt Durchschnitt bei additiven KPIs)
- [ ] Rundungslogik verbessern (Million / Milliarde / Billion, 1 Nachkommastelle)
- [ ] Leaflet Scroll-Lock fixen (Map nur per Tap aktivieren)
- [ ] Glossary-Styling vereinheitlichen (nur style.css verwenden)

## Phase 2 – Neue KPIs
- [ ] Resource Consumption per Capita
- [ ] Protected Land Area (% of total land area)
- [ ] Government Debt (% of GDP)
- [ ] Trade Balance (Exports minus Imports, % of GDP)
- [ ] Supply Chain Risk Index
- [ ] Recycling Rate (EPI)
- [ ] Environmental Performance Index (EPI)
- [ ] Olympic Medals (Summer + Winter)

## Phase 3 – Analysis-Prompt (Low Effort, High Value)
- [ ] Prompt-Level B2 (statt B1)
- [ ] Gruppen/Regionen + Regierungsformen (Demokratien vs Autokratien)
- [ ] Integration neuer KPIs (Environment, Economy)
- [ ] Zusatzfrage: „Who performs better and why?“

## Phase 4 – Struktur & Refactor
- [ ] Filename-Umstellung (`normalize_name` → `available.filename`)
- [ ] JSON-Konsolidierung (`/data/`-Pfad)
- [ ] Overall Ranking Refactor (irrelevant = 0, /data/overall_ranking.json)
- [ ] Cluster-Toggles & Weight Presets (Fun & Safe Haven, später)
- [ ] Chatbot-Extraktion in /scripts/chatbot.js
- [ ] Fuzzy Load Mechanismus implementieren

## Phase 5 – Cleanup & README
- [ ] Alte Dateien entfernen (normalize_name.*, Kopien)
- [ ] Pfade vereinheitlichen
- [ ] README aktualisieren (Struktur, Presets, Gewichtungslogik)

## Phase 6 – Performance & QA
- [ ] PageSpeed/CLS prüfen
- [ ] Lazy-Init Map/Chart.js aktivieren
- [ ] Mobile Layout & Scroll-Verhalten testen
- [ ] Regression-Test für Rundung, Gruppen-Logik, KPI-Neuheiten

## Phase 7 – UI/UX Polish
- [ ] Logo links oben in index.html (PNG, Tech/Data-Stil)
- [ ] Optional: Klick auf Logo → Startseite
- [ ] Mobile Variante: Schrift ausblenden unter 600px
