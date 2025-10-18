# ✅ RealityCheck – To-Dos & Roadmap

> Ongoing task list for the RealityCheck platform.  
> Updated: October 2025

## 🔹 Core Development
- [ ] Refactor `script_overall_ranking_countries.js` → `/scripts/overall_ranking.js`
- [ ] Externalize data to `/data/overall_ranking.json`
- [ ] Introduce cluster toggles & weight presets
- [ ] Implement “relevance” field across all KPIs (`available_kpis.json`)
- [ ] Consolidate JSON sources → `/data/`
- [ ] Standardize schema `{ country, iso2?, year, value }`

## 🔹 Chatbot
- [ ] Extract inline chatbot logic → `/scripts/chatbot.js`
- [ ] Integrate fuzzy country resolver (`country_mappings.json`)
- [ ] Enable group/cluster queries (EU, G7, G20 …)

## 🔹 Fetch & Automation
- [ ] Move fetch scripts to `/scripts/fetch/`
- [ ] Implement GitHub Action for monthly fetch
- [ ] Add fetch-report mail notification (optional)

## 🔹 Analysis & Data Glossary
- [ ] Add `analysis.html` (AI-based trend summary)
- [ ] Automate `fetch_status.json` + `analysis_outliers.json`
- [ ] Ensure glossary color-legend consistency

## 🔹 UX / Frontend
- [ ] Mobile scroll fix (iframe horizontal lock)
- [ ] Add country search box in dropdown
- [ ] Implement mode-switch (Serious / Fun / Safe Haven)
- [ ] Update favicon / header logo

—

🧩 **Next milestone:**  
Set up GitHub Actions + Secrets (`OPENAI_API_KEY`, `FTP_USER`, `FTP_PASS`)  
so monthly fetches and FTP uploads run automatically.