# 🗂️ RealityCheck – Directory Structure (October 2025)

## 📁 data/

### ▶ dynamic/
Contains **live or fetched KPI datasets** (updated regularly via fetch scripts):
- gdp.json
- fertility_rate.json
- epi_index.json
- recycling_rate.json
- etc.

### ▶ meta/
Contains **stable metadata and mappings** that define project logic:
- available_kpis.json ← master KPI definition list
- countries.json ← base list of all countries
- groups.json ← group definitions (EU, G7, BRICS, etc.)
- country_mappings.json ← alias mapping for fuzzy load

### Root-level files:
- analysis_outliers.json ← auto-generated outlier overview
- fetch_status.json ← freshness of each dataset
- overall_ranking.json ← combined ranking results

---

## 📁 scripts/
Contains logic for data fetching, processing, ranking, and chatbot modules.

---

## 📁 ai_workspace/
Contains documentation, prompts, and project planning files.
- `structure_plan.md` (this file)
- `team_overview.md`
- `todos.md`

---

## 💡 Notes
- Fetch scripts load `data/meta/available_kpis.json` instead of root-level files.
- Dynamic KPI data should never overwrite meta definitions.
- All analysis results are stored under `/data/` to remain visible for glossary & dashboard.