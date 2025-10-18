# RealityCheck – Interactive Country Comparison

## Überblick

**RealityCheck** ist ein datengetriebenes, interaktives Visualisierungsprojekt zur Analyse globaler Länderkennzahlen (KPIs) wie Wirtschaft, Gesellschaft, Umwelt und Politik. Ziel ist es, Trends sichtbar zu machen – im Sinne von *Factfulness* – und die weltweite Entwicklung faktenbasiert zu bewerten.

Das System kombiniert ein **Python-Backend** (Datenbeschaffung, -aufbereitung) mit einem **JavaScript-Frontend** (Visualisierung, Interaktion). Es nutzt Datenquellen wie die *World Bank API* und lokale CSV-Fallbacks, um robuste Vergleiche zwischen Ländern, Regionen und Weltaggregaten zu ermöglichen.

---

## Funktionsübersicht

### 🔧 Funktionale Anforderungen

* **Datenbeschaffung:**

  * Automatisches Fetchen von World Bank KPIs über `fetch_data.py`.
  * Verwendung lokaler CSV-Fallbacks in `/scripts/source_csv/`.
  * Generierung normalisierter JSON-Dateien in `/data/`.
* **Frontend-Visualisierung:**

  * Dynamische Tabelle aller Länder mit Filterung, Sortierung und Highlighting des Heimatlandes.
  * KPI-Auswahl mit automatischer Prüfung auf Datenverfügbarkeit.
  * Dynamische Skalierung von Werten (Tausender, Millionen, Milliarden).
  * Line Chart zur Zeitreihenvisualisierung von bis zu 3 Ländern.
  * Weltkarte zur geografischen Darstellung der KPI-Werte.
* **Sprachumschaltung (DE/EN):**

  * Geplant via API-gestützter Übersetzung (derzeit deaktiviert auf InfinityFree).
* **Tracking:**

  * Besucherstatistik über `tracking.php`, Ausgabe in Tabellenform im Footer.
* **Dark/Light Mode:**

  * Umschaltbar über `#mode-toggle`, Speicherung per Browserzustand.
* **Fehlerhandling:**

  * Robust gegenüber fehlenden API-Daten (Dummy-Erzeugung).
  * Visuelle Anzeige im Fehlerkasten über der Tabelle.

### ⚙️ Nichtfunktionale Anforderungen

* Vollständig clientseitig lauffähig auf Freehostern (InfinityFree, GitHub Pages, etc.).
* Datenpersistenz via JSON-Dateien (kein Datenbankserver nötig).
* Modulstruktur: Backend/Frontend strikt getrennt.
* Lesbare, erweiterbare Codebasis mit klarer Dateistruktur.

---

## Dateistruktur

```
RealityCheck/
│
├── index.html                → Hauptfrontend
├── style.css                 → Globales Design, inkl. Darkmode & Responsive Layout
├── script.js                 → Hauptlogik des Frontends
├── scripts/
│   ├── fetch_data.py         			→ Backend-Datenabfrage & Verarbeitung
│   ├── normalize_name.py     			→ Einheitliche Namenslogik (Backend)
│   ├── normalize_name.js     			→ Einheitliche Namenslogik (Frontend)
│   └── source_csv/           			→ Lokale CSV-Fallbackdaten
│   └── country_mappings.json      		→ Zuordnung inkompatibler Länderbezeichner
│   └── country_mapping_pending.json 	→ Ungeklärte Mapping-Fälle
│
├── data/                     → Generierte KPI-Daten (je KPI eine JSON-Datei)
│   ├── gdp.json
│   ├── population.json
│   ├── co2_emissions_kt.json
│   └── …
│   ├── fetch_log.txt         → Letztes Log der Datengenerierung
│   └── fetch_status.json     → Statusübersicht (Erfolg/Fehlschlag, Dummy etc.)

├── countries.json            → Stammdaten aller Länder (Name, ISO3, Koordinaten, Government etc.)
├── available_kpis.json        → Zentrale Steuerdatei aller KPI-Definitionen
├── impressum.html             → Rechtliche Angaben
├── privacy.html               → Datenschutzerklärung
└── tracking.php               → Besuchertracking (Serverseitig)
```

---

## Dateibeschreibungen

### 🐍 Backend

#### `fetch_data.py`

* Kernskript zur Datenbeschaffung.
* Liest KPI-Definitionen aus `available_kpis.json`.
* Nutzt `normalize_name.py` zur Dateinamensvereinheitlichung.
* Speichert Ergebnisse als `data/<kpi>.json` & `.csv`.
* Erkennt lokale CSVs in `/scripts/source_csv/`.
* Führt Logging in `fetch_log.txt`.
* Nutzt Mapping-Dateien zur Harmonisierung von Ländernamen.

#### `normalize_name.py`

* Einheitliche Konvertierung von KPI-Titeln in Dateinamen.
* Beispiel: `CO2 emissions (kt)` → `co2_emissions_kt`.

#### `country_mappings.json`

* Zentrale Steuerdatei, um unterschiedliche Schreibweisen zu harmonisieren.

  ```json
  {
    "United States": "United States of America",
    "Russia": "Russian Federation"
  }
  ```

#### `available_kpis.json`

* Enthält Meta-Informationen aller KPI.
* Strukturbeispiel:

  ```json
  [
  {
    "title": "Land Area",
    "description": "Total land area of the country (rounded to thousands, millions, billions as applicable).",
    "unit": "km²",
    "relation": "",
    "sort": "neutral",
    "cluster": "Demographics & Society",
    "source": "https://data.worldbank.org/indicator/AG.SRF.TOTL.K2",
    "source_type": "worldbank",
    "source_code": "AG.SRF.TOTL.K2",
    "scale": "auto",
    "filename": "area"
  },
  ```
  ]


### 💻 Frontend

#### `index.html`

* Einstiegspunkt der Anwendung.
* Enthält:

  * KPI-Auswahl (`#kpi-select`)
  * Länder-Auswahl (`#country1-select`, `#country2-select`, `#country3-select`)
  * Heimatland-Auswahl (`#homecountry-select`)
  * Chart-Bereich (`#kpi-chart`)
  * Tabelle (`#data-table`)
  * Darkmode-Schalter (`#mode-toggle`)
  * Tracking-Table (`#tracking-table`)

#### `script.js`

* Lädt Länder, Gruppen und KPI.
* Baut Tabelle, Karte und Chart.
* Nutzt `normalize_name.js` für konsistente Dateinamen.
* Fehlerhandling bei fehlenden Daten (graue/italic KPIs).
* `populateKpiSelect()` blockiert Auswahl, bis Verfügbarkeit geprüft.

#### `normalize_name.js`

* Spiegelfunktion zu `normalize_name.py` (Frontend).
* Gewährleistet, dass `fetch_data.py` und `script.js` identisch arbeiten.

#### `style.css`

* Definiert Layout, Tabellenfarben, Darkmode und Responsivität.
* Enthält Darkmode-Button (#mode-toggle) und Loading-Stile.

---

## ID-Glossar (nicht verändern)

| ID                                                         | Bedeutung                                    |
| ---------------------------------------------------------- | -------------------------------------------- |
| `#kpi-select`                                              | KPI-Auswahl (Cluster-basiert)                |
| `#country1-select`, `#country2-select`, `#country3-select` | Länder für Chart-Vergleich                   |
| `#homecountry-select`                                      | Heimatland in Tabelle hervorheben            |
| `#mode-toggle`                                             | Umschalter für Hell-/Dunkelmodus             |
| `#error-box`                                               | Anzeige fehlerhafter KPI oder Fetch-Probleme |
| `#data-table`                                              | Haupttabelle mit Ländern und Werten          |
| `#kpi-chart`                                               | Chart.js-Liniendiagramm für Zeitreihen       |
| `#tracking-table`, `#total-visitors`                       | Besucherstatistik                            |

---

## Fehlerhandling

* **Backend:**

  * Bei Fetch-Fehlern bleibt alte Datei erhalten.
  * `fetch_status.json` dokumentiert Dummy-Einträge.
  * Detaillierte Logs in `fetch_log.txt`.
* **Frontend:**

  * Fehlende KPI-Daten werden grau & kursiv angezeigt.
  * Anzeige im `#error-box`, Tabelle bleibt funktional.

---

## CSV-Fallback-Struktur

Lokale CSV-Dateien in `/scripts/source_csv/` müssen wie folgt aufgebaut sein:

| country | year | value |
| ------- | ---- | ----- |
| Germany | 2020 | 42000 |
| France  | 2020 | 38000 |

* Trennzeichen: Komma
* Encoding: UTF-8
* Header zwingend erforderlich

---

## Geplante Erweiterungen (Backlog)

### 🔹 Funktional

1. **Automatische Übersetzung** der KPI-Titel und Beschreibung über API (z. B. DeepL oder LibreTranslate) – derzeit deaktiviert (CORS auf InfinityFree).
2. **Ranking-Funktion**:

   * Aggregation aller KPI zu einem Gesamtbewertungssystem.
   * Gewichtung pro KPI (z. B. Wirtschaft 30 %, Umwelt 30 %, Soziales 40 %).
   * Ausgabe als Rangliste und Heatmap.
3. **World-KPI-Ansicht**:

   * Aggregierte globale Kennzahlen (z. B. CO₂-Ausstoß, Konflikte, Naturkatastrophen).
   * Darstellung im Tab „World Overview“.
4. **Backend-Migration auf dedizierten Server** (z. B. PythonAnywhere, Vercel, AWS Lambda).
5. **Live-Datenaktualisierung** via Cronjob / Scheduled Fetch.

### 🔹 Technisch

* Optimierung der `populateKpiSelect()` für asynchrone Batch-Ladung.
* Lazy Loading von KPI-Daten (on-demand statt preload).
* Erweiterte Error-Meldungen mit Tooltip-Erklärung.

---

## Installation & Nutzung

### Lokaler Start

1. Repository klonen oder ZIP entpacken.
2. Im Hauptverzeichnis ausführen:

   ```bash
   python scripts/fetch_data.py
   ```
3. Lokalen Server starten, z. B.:

   ```bash
   python -m http.server
   ```
4. Browser öffnen: [http://localhost:8000](http://localhost:8000)

### Deployment

* Alle Dateien 1:1 auf Webserver (InfinityFree, GitHub Pages, etc.) laden.
* Bei serverseitiger Nutzung (z. B. Tracking, Cronjobs): PHP aktiviert halten.

---

## Lizenz & Credits

© RealityCheck Project – 2025
Entwickelt von Carsten Winterling (Pulheim)
Datenquellen: [World Bank Open Data](https://data.worldbank.org), [Our World in Data](https://ourworldindata.org)


RealityCheck — Country KPIs Dashboard

A lightweight frontend + offline-fetch backend that aggregates worldwide KPIs (World Bank + curated CSVs), normalizes names consistently, and renders an interactive country comparison dashboard (table, line chart, basic map). Designed to run on static hosting (e.g., InfinityFree) by pre-generating JSON data offline and uploading it.

What this project does

Fetches KPI data from:

World Bank indicators (via API, offline in Python).

Local curated CSVs in /scripts/source_csv.

Normalizes KPI names identically in backend (Python) and frontend (JS) so the files the fetcher writes are the same files the UI loads.

Persists results as data/<kpi_id>.json and shows them in the UI:

Country table (sortable, trend arrow, comparison year).

Optional relations per capita, per GDP, per km² (using Population, GDP, Land Area).

Line chart for up to 3 countries.

Basic world map fly-to per country.

Tracks visitors via tracking.php (optional).

Dark/Light mode toggle with persistent preference.

Graceful handling of empty/missing datasets via dummy JSONs (prevents 404/CORS redirects on InfinityFree).

Functional requirements

Show KPIs grouped by cluster with a long select box:

While checking which KPIs have data (to gray out empties), the select shows “Loading KPIs…” and is disabled.

After loading, the select defaults to -- none -- (no auto-selection).

Home country:

Defaults to -- none --. User can highlight a country; it’s pinned to the top of the table.

Relations:

absolute (default), per capita, per GDP, per km².

Works off population, gdp, area data files (see “Global IDs and aliases”).

Sorting:

Rank (default, best-to-worst), Country name, Value. Persisted while switching KPIs.

Chart:

Up to 3 countries with the currently selected KPI (including chosen relation).

Map:

Click a row to fly to that country (needs lat/lon in countries.json).

Error box:

Shows if the fetcher flagged a KPI with status error.

Theme:

Light/Dark toggle (#mode-toggle), persisted in localStorage.

Non-functional requirements

Static hosting friendly (no server code needed at runtime).

Data files pre-generated offline and uploaded to /data.

Consistent naming across backend & frontend via shared normalization.

Avoid 404s on InfinityFree (404s redirect to errors.infinityfree.net and trigger CORS). The fetcher creates dummy JSONs (empty arrays + stub meta) so every referenced KPI has a file.

Reasonable performance (long KPI list prechecks done once; UI shows “Loading…” and disables the select while it works).

Project structure
/ (web root)
├─ index.html               # Main app
├─ styles.css               # Styles (incl. dark mode)
├─ script.js                # Frontend logic
├─ countries.json           # Country master (name → info incl. lat/lon)
├─ groups.json              # Optional country groups (for aggregate rows)
├─ available_kpis.json      # KPI registry (source, meta, cluster, relation)
├─ data/                    # Generated JSON outputs (one per KPI)
│  ├─ population.json
│  ├─ gdp.json
│  ├─ area.json
│  └─ ...
├─ scripts/
│  ├─ fetch_data.py         # Offline fetcher (WB + CSV → /data)
│  ├─ normalize_name.py     # Python normalization (used by fetcher)
│  ├─ normalize_name.js     # JS normalization (loaded before script.js)
│  ├─ country_mappings.json # Name mapping authoritative list
│  ├─ country_mapping_pending.json # Pairs pending manual review
│  └─ source_csv/           # Local CSV sources (manually curated)
│     └─ ...
├─ tracking.php             # Optional visitor tracking endpoint
├─ impressum.html           # Legal
└─ privacy.html             # Privacy

Central control files
available_kpis.json (KPI registry)

Each entry defines what to fetch, how to name it, how to display it.

Schema (per KPI entry):

{
  "title": "GDP (current US$)",
  "id": "gdp_current_us",             // optional; can be derived from title if omitted
  "filename": "gdp_current_us",       // optional; derived by normalization if omitted
  "source": {
    "type": "worldbank" | "csv",
    "wb_code": "NY.GDP.MKTP.CD",      // if worldbank
    "csv_file": "gdp_current_us.csv"  // if csv; file inside scripts/source_csv
  },
  "unit": "US$",
  "cluster": "Economy",
  "description": "Gross Domestic Product in current US$.",
  "relation": "default" | "*",        // "*" => relations disabled for this KPI
  "sort": "higher" | "lower"          // default higher (for ranking)
}


Notes:

filename and id are optional; the system will compute a canonical KPI id from title using the shared normalization (see below).

If you provide filename, it must already be normalized.

relation: "*" disables per-capita/per-GDP/etc. for that KPI (used e.g. for ratios/percentages).

countries.json (root)

Authoritative country catalog used by the UI (and helpful to the fetcher):

{
  "Jamaica": {
    "capital": "Kingston",
    "government": "Constitutional Monarchy",
    "lat": 17.99702,
    "lon": -76.79358
  },
}


Required by the UI:

lat, lon for the map fly-to popup.

capital, government for popup text.

Names here are the canonical country names the UI expects.

groups.json (root, optional)

Define group aggregates shown at the bottom of the table:

{
  "EU": {
    "title": "European Union",
    "members": [
      "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
      "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
      "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
      "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
      "Slovenia", "Spain", "Sweden"
    ]
}


Aggregation rule:

If unit contains % or KPI meta uses scale: "none", the group value is the mean of member values; else sum.

Countries mapping behavior (fetcher)

The fetcher reconciles country names from World Bank / CSV files to your canonical names in countries.json:

scripts/country_mappings.json: confirmed mapping dictionary from source name → canonical name.

scripts/country_mapping_pending.json: newly encountered names land here for manual review.

On each fetch run:

For any source country not recognized, the fetcher tries a few heuristics (trim, common aliases).

If still unknown, it writes an entry into country_mapping_pending.json for you to map.

Once you confirm a mapping (move it to country_mappings.json), rerun the fetch to apply.

Tip: Keep canonical names aligned with countries.json. The UI only displays countries present in countries.json.

Shared name normalization (critical)

Both languages expose the same rule so filenames written by the fetcher are exactly the ones the UI loads.

JS (frontend): scripts/normalize_name.js defines normalizeName(str).

Python (backend): scripts/normalize_name.py defines normalize_name(str).

What the rule does (canonical behavior):

Lowercase, trim.

Replace hyphens with underscores.

Replace any non [a-z0-9._-] with underscore.

Convert decimals inside tokens like 2.5 → 2_5.

Collapse multiple underscores and trim leading/trailing underscores.

Examples (input → id):

CO₂ Emissions (kt) → co2_emissions_kt

Air Quality PM2.5 Exposure → air_quality_pm2_5_exposure

Hospital beds per 1,000 people → hospital_beds_per_1000_people

Fiber-Optic Broadband Coverage → fiber_optic_broadband_coverage

Olympic Medals - All Time → olympic_medals_all_time

Important: Always load scripts/normalize_name.js before script.js in index.html.

<script src="scripts/normalize_name.js"></script>
<script src="script.js"></script>

Data formats
Output JSON (/data/<kpi_id>.json)

Minimal schema:

  {
    "country": "Afghanistan",
    "iso2": "",
    "year": 2010,
    "value": 4.76
  },

Output csv

Minimal schema:

country,iso2,year,value
Afghanistan,AFG,2024,27.265
Afghanistan,AFG,2023,26.933


Required keys: country (canonical), year (int), value (number or null).

The UI handles missing previous/comparison values gracefully.

Local CSV inputs (/scripts/source_csv/*.csv)

Header must contain:

country — source country label (will be mapped).

year — numeric year.

value — numeric value (dot-decimal).

Optional:

iso2 / iso3 — helps mapping (preferred, if present).

Additional columns are ignored by the fetcher.

Example:

country,year,value
Germany,2023,12.34
Germany,2022,11.20
France,2023,9.87


Name the CSV file per the KPI entry (see available_kpis.json → source.csv_file). If absent, the fetcher also looks for <normalized-id>.csv.

Frontend: global IDs you should not rename

Selects and controls

#kpi-select — KPI chooser (clustered, grays out empty datasets).

#homecountry-select — home country (pinned).

#relation-select — relation mode (absolute, percapita, pergdp, perkm2).

#compareyear-select — compare vs specific year.

#country1-select, #country2-select, #country3-select — chart countries.

#mode-toggle — light/dark theme toggle button.

Data & meta

#country-table — main results table.

#kpi-chart — line chart canvas.

#map — Leaflet map container.

#kpi-description, #kpi-source — meta panel.

#error-box — fetch error banner.

#rounding-info, #global-update — helper labels.

Tracking (optional)

#total-visitors, #tracking-table

Global KPI aliases for relations (do not change)

The UI’s relation modes depend on these filenames in /data:

Population → population.json

GDP → gdp.json
(fetcher saves World Bank GDP as gdp_current_us and writes an alias file gdp.json for the UI)

Land Area → area.json
(fetcher saves land_area and writes alias area.json)

You already have these generated correctly (see fetch log: “alias: gdp” and “alias: area”). 

fetch_log

Which KPIs are wired vs. missing

From the latest fetch run:

Saved OK (33) — e.g., population, gdp_current_us (alias: gdp), land_area (alias: area), employment_to_population_ratio, hospital_beds_per_1_000_people, air_quality_pm2_5_exposure, public_debt_of_gdp, tax_revenue_of_gdp, internet_penetration_rate, inflation_consumer_price_index, … 

fetch_log

Dummy created (24) — CSV missing/empty or external source failed; files still exist (empty arrays) so the UI won’t 404. Examples: olympic_medals_all_time, fiber_optic_broadband_coverage, education_expenditure_of_gdp, big_mac_index, 5g_coverage, … 

fetch_log

Error (1) — co2_emissions_kt World Bank endpoint returned unexpected format in that run; a dummy was also created so the UI stays stable. 

fetch_log

Why dummy files matter (InfinityFree): Missing files produce a 404 which InfinityFree redirects to errors.infinityfree.net and blocks with CORS. Having a dummy JSON file avoids that entirely — the UI can gray out the KPI and continue. 

fetch_log

Installation & usage
1) Frontend

Place index.html, styles.css, script.js, countries.json, groups.json, available_kpis.json in the web root.

Ensure load order in index.html:

<script src="scripts/normalize_name.js"></script>
<script src="script.js"></script>


Optional pages: impressum.html, privacy.html, tracking.php in root.

2) Backend fetch (offline)

Requirements: Python 3.10+; modules: requests (and stdlib).

Folder: scripts/.

Run:

cd scripts
python fetch_data.py


It will:

Read available_kpis.json.

Fetch World Bank indicators and/or read CSVs from /scripts/source_csv.

Normalize names via normalize_name.py.

Map country labels using country_mappings.json (+ stage unknowns in country_mapping_pending.json).

Write outputs to /data (including dummy JSONs when inputs are missing).

Upload /data (and any updated root JSONs) to your host.

Error handling & diagnostics

UI banner (#error-box) shows if a KPI has status: "error" in data/fetch_status.json.

KPI list graying: On page load, each KPI is checked; if its data/<kpi>.json is empty/missing values, it appears gray + italic. The select shows “Loading KPIs…” and is disabled until checks finish; afterward, it switches to -- none --.

InfinityFree CORS/404: Always upload dummy files generated by the fetcher to avoid CORS redirects.

Country not shown: Ensure the country exists in countries.json (canonical name) and is mapped by the fetcher.

Relations seem off: Check that population.json, gdp.json, area.json exist; the fetcher writes aliases for the UI.

Backlog (next steps)

Translation API (UI text & KPI titles)

Implement i18n with an external API (DeepL/Google).

Note: InfinityFree disallows server-side execution; translations must be pre-baked or done client-side (which leaks keys). Preferred: move backend to a small VM, pre-generate localized copies of available_kpis.json and/or a translation bundle.

Finish missing KPI bindings

Populate the CSVs listed as “Dummy created” in fetch_log.txt and re-run fetcher.

Where possible, switch to World Bank or another reliable API to reduce manual CSV maintenance. 

fetch_log

Move backend to a server

So scheduled fetches (cron) can keep data fresh automatically.

Expose a minimal read-only endpoint for fetch_status.json if desired.

Cross-KPI composite ranking (per country)

Compute a normalized score per KPI (z-score or min-max with direction from sort), then aggregate (weighted average).

UI: add a “Overall Ranking” KPI that shows the composite with drill-down into component contributions.

Configurable weights per cluster and per KPI in available_kpis.json.

“World view” KPIs (helicopter view)

KPIs where country isolation makes little sense (e.g., conflicts, global CO₂, biodiversity loss, ocean temperature anomalies).

Treat as non-country series:

New type: "global" in available_kpis.json.

Output schema: [{"year": 2023, "value": 123.4}, ...].

UI path: hide table, show time-series chart + annotations, maybe a small world heatmap if a regional breakdown is available.

Quality gates & validation

Add a CLI check_naming_consistency.py and a check_data_shapes.py to validate new CSVs, mapping coverage, and normalized IDs before producing /data.

Data provenance panel

Per KPI show source, last_fetched, coverage (% countries) and the list of countries excluded due to missing values or mappings.

File-by-file quick reference

index.html — hosts all controls and containers. Make sure normalize_name.js is loaded before script.js.

styles.css — UI styling; includes .dark-mode variants and disables/enables <select> states during “Loading KPIs…”.

script.js — UI logic:

Loads available_kpis.json, countries.json, groups.json, data/fetch_status.json.

Loads KPI data data/<kpi>.json on demand.

Relations use data/population.json, data/gdp.json, data/area.json.

Sorts, charts, map fly-to, tracking.

scripts/normalize_name.js — exposes normalizeName() globally (used to build file ids from titles).

scripts/fetch_data.py — offline fetcher; logs progress, writes /data, /data/fetch_status.json, and creates dummy files as needed.

scripts/normalize_name.py — backend counterpart of name normalization.

scripts/country_mappings.json — authoritative mapping source-name → canonical.

scripts/country_mapping_pending.json — new/unknown names awaiting your decision.

scripts/source_csv/*.csv — curated sources for CSV KPIs (see schema above).

countries.json — canonical country catalog (names used by the UI).

groups.json — optional group aggregates.

available_kpis.json — central KPI registry.

data/*.json — generated outputs per KPI.

tracking.php — optional visitor tracking endpoint.

impressum.html, privacy.html — legal pages.

Tips & gotchas

If you change title in available_kpis.json, the normalized filename changes too. Either:

Leave id/filename blank and let both sides normalize consistently (recommended), or

Pin filename and keep it stable, independent of title.

Run the fetcher whenever you:

Update mappings.

Add/modify CSVs.

Add/modify KPI entries.

Always upload all changed files: /data, available_kpis.json, countries.json, and any new CSV-driven KPI JSONs.

Check fetch_log.txt and data/fetch_status.json after a run to see which KPIs succeeded, errored, or are dummies. 

fetch_log

Current status snapshot

From your latest run:

KPIs loaded: 57

Saved OK: 33

Dummies: 24

Errors: 1 (World Bank response format for CO₂)
See fetch_log.txt for the full list and reasons. 

fetch_log

License & contributions

Internal project. If you share, please include this README and attribute external datasets to their original sources (World Bank, etc.).