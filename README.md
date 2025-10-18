🌍 RealityCheck – Interactive Country Comparison
Project by Carsten Winterling & ChatGPT (GPT-5)

⸻

🧭 Purpose
RealityCheck is a static, data-driven web application hosted on InfinityFree.
It visualizes how countries perform in key areas — democracy, economy, environment, and society — using publicly available KPIs (World Bank, OWID, UNHCR, Yale EPI …).
“Nothing is destiny. Humanity built this world – and humanity can change it.”

⸻

📁 Current File / Folder Structure  (2025-10)

/
├── index.html                        ← Main shell (nav + iframe loader)
├── style.css                         ← Global layout & responsive design
│
├── countries.html                    ← Country dashboard + table + chart + map + chatbot
├── world.html                        ← Global OWID trend dashboards
├── overall_ranking_countries.html    ← Overall KPI-based ranking (UI shell)
├── data_glossary.html                ← Source & freshness overview
├── impressum.html / privacy.html     ← Legal / privacy pages
│
├── script.js                         ← Main frontend logic (Countries page)
├── script_overall_ranking_countries.js ← Overall ranking logic (frontend)
│
├── available_kpis.json               ← KPI metadata (master)
├── countries.json                    ← Country list (ISO, names)
├── groups.json                       ← Groups (EU, G7, G20 …)
├── country_mappings.json             ← Alias map for Chatbot & Fuzzy Load
│
├── /scripts/
│   ├── normalize_name.js             ← Canonical filename normalizer (JS)
│   ├── normalize_name.py             ← Canonical filename normalizer (Python)
│   ├── fetch_overall_ranking.py      ← Generates /data/overall_ranking.json (planned)
│   ├── (chatbot.js / analysis.js planned)
│
└── /data/
├── area.json                     ← Example indicator file
├── … many other KPI files ({country, year, value})
└── (overall_ranking.json, fetch_status.json, analysis_outliers.json planned)

⸻

🧩 Main Pages & IDs

index.html
– #main-frame → loads subpages (countries.html, world.html, overall_ranking_countries.html, analysis.html)
– #frame-loader → overlay spinner
–  links → loadPage(page, link)
– Footer links → impressum.html | privacy.html | data_glossary.html | about.html

countries.html
Interactive page with table + chart + Leaflet map + chatbot.
Controls: #kpiSelect, #yearSelect, #relationSelect, #countrySelect
Table: #country-table (th [data-col])
Meta: #data-source, #data-date, #kpi-description, #warning-box
Chart: #kpi-chart, #country1Select/2/3Select
Map: #map-section > #map
Legend: #legend
Spinner: #overlay-spinner
Chatbot: #chatbot-button, #chatbot-window, #messages, #user-input, #send
Scripts loaded: scripts/normalize_name.js + script.js

overall_ranking_countries.html
Combined KPI ranking.
IDs: #priority-container, #overall-table, #legend, #overlay-spinner, #last-updated
Script: script_overall_ranking_countries.js

world.html
Static page with Our World in Data iframes (.graph-block)

data_glossary.html
Loads data/fetch_status.json + data/analysis_outliers.json
IDs: #glossary-table, #glossary-body   Classes: .fresh . warn . stale . outlier

⸻

🧮 Core Data Structures

available_kpis.json
Each KPI entry defines metadata. Example:
{ “title”:“Fertility Rate”, “description”:“Average number of children per woman.”, “unit”:“births per woman”, “relation”:”*”, “cluster”:“Society & Governance”, “source”:“https://data.worldbank.org/indicator/SP.DYN.TFRT.IN”, “source_type”:“worldbank”, “source_code”:“SP.DYN.TFRT.IN”, “filename”:“fertility_rate”, “relevance”:“normal” }
filename = normalize_name(title) → /data/.json

countries.json / groups.json
Base lists used for filtering and aggregations.

country_mappings.json  (critical control file)
Maps all aliases (DE/EN/ISO/legacy) to canonical names.
Used by chatbot input parsing, data normalization, and Python fetchers.
Rule: add new aliases here first before editing datasets.

normalize_name.js / normalize_name.py
Identical normalization logic for filenames & lookup keys.
Rules: lowercase, CO₂→co2, remove accents, punctuation → underscore.

⸻

⚙️ Functional Overview

Countries page (script.js): loads KPI metadata, handles selectors, renders table/chart/map, integrates chatbot.
Chatbot: inline JS in countries.html → to be moved to /scripts/chatbot.js.
Overall ranking: combines weighted KPIs → planned refactor to /scripts/overall_ranking.js.
Data glossary: shows data freshness and outliers.

⸻

⸻

🧪 Fuzzy Load Mechanism (planned)

1  KPI Resolver → /data/${normalize_name(title)}.json + fallbacks.
2  Country Resolver → countries.json then country_mappings.json.
3  Schema Tolerance → accept array or object structures.
Logic → central in /scripts/script.js.

⸻

🧾 To-Dos (Consolidated & Prioritized)

1  Overall Ranking Refactor
– Move script_overall_ranking_countries.js → /scripts/overall_ranking.js
– Externalize data to /data/overall_ranking.json
– Keep UI IDs stable
– Add cluster toggles & weight presets

2  JSON Consolidation
– Move available_kpis.json, countries.json, groups.json → /data/
– Adjust fetch paths in all pages
– Standardize schema {country, iso2?, year, value}
– Normalize fetch_status.json + analysis_outliers.json

3  Chatbot Extraction
– Extract inline logic → /scripts/chatbot.js
– Remove temporary “-Kopie” JSONs
– Enable group/cluster queries

4  Fuzzy Load
– Implement fallback matching
– Centralize resolver in /scripts/script.js
– Log resolved aliases to console for debugging

5  Analysis Page
– Create analysis.html (frame loaded)
– Render data/analysis.md
– Style #analysis-content and footer gap

6  Glossary Automation
– Auto-generate fetch_status.json and analysis_outliers.json
– Preserve color legend consistency

7  Structural Cleanup
– Update all HTML src/fetch paths
– Remove deprecated files
– Keep normalize scripts identical (JS ↔ PY)

⸻

🧩 Cross-File Dependencies

script.js → available_kpis.json + countries.json + normalize_name.js
Chatbot → available_kpis.json + countries.json + country_mappings.json
overall_ranking_countries.html → script_overall_ranking_countries.js
data_glossary.html → data/fetch_status.json + data/analysis_outliers.json
normalize_name.py → Python fetchers (must mirror JS)

⸻

🧠 Collaboration Rules (ChatGPT)

If any of the following change: folder structure, filenames, IDs, normalizer logic, data schemas or dependencies →

ChatGPT must immediately inform Carsten Winterling:
“⚠️ RealityCheck structure changed — README update required.”
Include summary of changes + affected files + required edits.
Always deliver an updated README in the same chat.

⸻

📊 Status Snapshot (Oct 2025)

Countries Dashboard    ✅ Stable
Chatbot                  🟡 Inline version
Overall Ranking          🟡 Operational, refactor pending
Data Glossary            ✅ Functional
World Dashboard        ✅ Static
JSON Consolidation      🟡 Pending
Fuzzy Load              🔴 Open
Analysis Page            🟡 Prototype

⸻

🧾 Credits
Project Lead                        Carsten Winterling
AI Collaboration                   ChatGPT (GPT-5)
Hosting                            InfinityFree
Libraries                           Chart.js, Leaflet
Inspiration                          Factfulness (Hans Rosling), Earth for All (Club of Rome), Yuval Noah Harari
