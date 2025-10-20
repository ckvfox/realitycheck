# 🧭 RealityCheck – Consolidated To-Dos (as of 2025-10-20)

—

## ✅ PHASE 1 – Fehler & Performance (User-Facing)
- [x] Chatbot deaktiviert (countries.html → `const chatbotEnabled = false`)
- [x] Group-Aggregation korrigiert → Summe statt Durchschnitt bei additiven KPIs
- [x] Rundungslogik vereinheitlicht (Million / Milliarde / Billion, 1 Nachkommastelle)
- [x] Leaflet Scroll-Lock gefixt (kein horizontales Scrollen mehr mobil)
- [ ] **Leaflet Scroll Jail Fix (Mobile Tap-to-Activate)** → verhindern, dass Nutzer auf kleinen Geräten in der Map „gefangen“ sind (Map zunächst deaktiviert, Aktivierung per Tap)
- [x] Glossary-Styling zentralisiert in `style.css`
- [x] Hover-/Tooltip-Verhalten in Charts optimiert
- [x] World-Page Lazy-Loading deaktiviert → stabiler Iframe-Render

—

## ✅ PHASE 2 – Neue KPIs & Data Integration
- [x] Environmental Performance Index (EPI, Yale 2024)
- [x] Recycling Rate (EPI / OECD)
- [x] Olympic Medals (Summer + Winter) → als CSV integriert (source_csv + fetchfähig)
- [x] Resource Consumption per Capita vorbereitet (noch unvollständige Datenbasis)
- [x] Government Debt (% of GDP) integriert (World Bank)
- [x] Trade Balance (% of GDP) integriert
- [ ] Supply Chain Risk Index → Quelle noch offen
- [ ] Protected Land Area (% of total land area) → UNEP-API prüfen
- [ ] 5G Coverage / Fiber Penetration / EV Charging Stations → Datenquelle (Kaggle / ITU) recherchieren

—

## ✅ PHASE 3 – Analysis (Prompt & Output)
- [x] Analysis-Prompt auf **B2-Level** aktualisiert
- [x] Regierungsformen (Demokratien vs Autokratien) integriert
- [x] Gruppen / Regionen (EU, G7, G20, BRICS, AU etc.) in Prompt & Auswertung eingebunden
- [x] Zusatzfrage „Who performs better and why?“ in der Analyse enthalten
- [x] Visuelle und strukturelle Vereinheitlichung von `analysis.html`
- [x] Markdown-Rendering stabil (`data/analysis.md`)

—

## ⚙️ PHASE 4 – Struktur & Refactor
- [x] `filename`-Feld vollständig in `available_kpis.json` integriert
- [x] `normalize_name` (JS & PY) außer Betrieb genommen → Archivstatus
- [x] Pfade für `available_kpis.json`, `countries.json`, `groups.json` angepasst → `/data/`
- [x] `fetch_overall_ranking.py` hinzugefügt (funktional, Output folgt)
- [x] Overall Ranking Refactor abgeschlossen (aktualisiertes Layout + Cluster-Boxen)
- [x] Relevance-Feld (`very high` / `normal` / `irrelevant`) implementiert
- [ ] **KPI-Konsolidierung in eine Gesamtdatei (`kpi_data.json`)**
  - Combine-Skript nach Fetch-Lauf implementieren (`combine_kpis_to_single_json.py`)
  - Frontend (script.js, overall_ranking.js, analysis.js) auf zentrale Datei umstellen
  - Einzel-JSONs nur noch als Fetch-Zwischenschritt behalten
- [ ] Cluster-Toggles & Weight-Presets (Fun / Safe Haven) → geplant
- [ ] Chatbot-Auslagerung in `/scripts/chatbot.js` (derzeit inline)
- [ ] Fuzzy-Load-Mechanismus (Aliase & Fallbacks) → noch offen

—

## 🧹 PHASE 5 – Cleanup & Documentation
- [x] Doppelte Dateien („-Kopie.json“) entfernt
- [x] Fetch- & Datenpfade angeglichen (`/data/`, `/scripts/`)
- [x] README aktualisiert (Struktur, Presets, Gewichtungslogik)
- [x] `/ai_workspace` geprüft und archivfähig
- [ ] Finales Umbenennen zu `/docs/ai_workspace` (Archivstatus)
- [ ] fetch_overall_ranking.py Dokumentation ergänzen

—

## 🔧 PHASE 6 – Performance & QA
- [x] PageSpeed & CLS geprüft → stabile Performance auf Mobile
- [x] Lazy-Init für Map & Chart.js implementiert
- [ ] Regression-Test für Gruppen-Logik & neue KPIs
- [ ] Fallback-Mechanismus für Fetch-Fehler (Dummy JSON + Logfile)
- [ ] Prüfung globaler Daten-Jahrgänge (Data-Freshness-Check automatisieren)

—

## 🎨 PHASE 7 – UI / UX Polish
- [x] Logo links oben (Tech/Data-Stil) integriert
- [x] Logo-Klick → Startseite (`index.html`)
- [x] Einheitliches Intro-Layout (`countries.html`, `world.html`, `overall_ranking_countries.html`)
- [x] Cluster-/Intro-Blöcke visuell harmonisiert
- [ ] Dropdown-Suche im Home-Country-Feld (Autocomplete)
- [ ] Mode-Switch (Serious / Fun / Safe Haven) → UX-Konzept
- [ ] Tooltips & Icons vereinheitlichen (Tabelle & Legende)
- [ ] Mobile Titelkürzung <600 px (optional)

—

## 🚧 PHASE 8 – Automation & Future Tasks
- [ ] GitHub Actions für monatliches Fetch + FTP Upload
- [ ] Automatische Generierung von `fetch_status.json` + `analysis_outliers.json`
- [ ] Benachrichtigung bei veralteten CSV-Daten („Update available“)
- [ ] Versionsstempel im Footer (Build- & Fetch-Datum)
- [ ] Optional: Auto-Analyse-Mail-Report

—

## 🗂️ ARCHIVIERTE / ABGESCHLOSSENE PHASEN

### ✅ Fertiggestellte Hauptkomponenten
- Countries-Dashboard (stabil, alle Selektoren + Chart + Map)
- World-Dashboard (OWID Iframes + eigener Stil)
- Overall Ranking Dashboard (Refactor abgeschlossen)
- Analysis Page (Markdown + Style)
- Data Glossary (automatische Outlier- & Freshness-Integration)
- CSS vereinheitlicht (`style.css` Final)
- Länder- & Gruppenlisten konsolidiert (`countries.json`, `groups.json`, `country_mappings.json`)
- Projekt-README aktualisiert & konsistente Ordnerstruktur