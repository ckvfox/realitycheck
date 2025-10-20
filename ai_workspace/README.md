# 🧠 RealityCheck – AI Workspace

> Companion space for GPT-assisted development, documentation, and automation of the **RealityCheck** project.  
> Updated: **20 Oct 2025**

—

## 📂 Purpose

This folder contains all **AI-related project artifacts** —  
prompt templates, analytical notes, KPI documentation, and current to-do lists.  
It serves as a transparent log of how ChatGPT supports code, data, and analytical reasoning across the RealityCheck platform.

—

## 🧩 Folder Overview

| File | Purpose |
|——|-———|
| `analysis_notes.md` | Concept drafts and topic outlines for AI-based global analyses (used by `analysis.html`). |
| `prompts.md` | Library of reusable ChatGPT prompt templates (for data analysis, writing, code, and automation). |
| `realitycheck_kpi_baseline_2025-10-16.md` | Master KPI list with full metadata, units, relations, and clusters (source: `available_kpis.json`). |
| `realitycheck_kpi_titles_2025-10-20.md` | Compact KPI title list (titles only, incl. new KPIs like EPI, GPI, Olympic Medals, Recycling Rate, etc.). |
| `realitycheck_todos_2025-10-20.md` | Current consolidated to-do roadmap (status and phase tracking). |
| `structure_plan.md` | Conceptual overview of data flows, script dependencies, and JSON layout for the current architecture. |

—

## 🧮 Data References

All KPI data and metadata originate from `/data/available_kpis.json`.  
This file defines each indicator’s:
- `title`, `unit`, `relation`, `cluster`
- `source`, `source_type`, `filename`
- and relevance classification (`very high`, `normal`, `irrelevant`).

Recent additions (Oct 2025):
- Environmental Performance Index (EPI)  
- Global Peace Index (GPI)  
- Recycling Rate  
- Government Debt (% of GDP)  
- Olympic Medals (Summer + Winter)  
- Resource Consumption per Capita  

—

## ⚙️ Current AI-Integrated Workflows

| Workflow | Description |
|————|—————|
| **Analysis Generation** | `analysis.html` loads and renders AI-generated text (`data/analysis.md`) derived from the current dataset. |
| **Prompt Library** | `prompts.md` defines reusable templates for OpenAI API or manual ChatGPT sessions. |
| **Todo Automation** | `realitycheck_todos_*.md` documents tasks for fetchers, refactors, UI polish, and QA. |
| **KPI Synchronization** | KPI baseline and title lists auto-reflect updates from `available_kpis.json`. |

—

## 🔧 Upcoming AI / Data Tasks

- Implement **Tap-to-Activate Leaflet Fix** for mobile map interaction.  
- Add **Combine Script** to merge all KPI JSONs → single `kpi_data.json` for faster loads.  
- Migrate chatbot logic to `/scripts/chatbot.js` (isolated).  
- Integrate automated **fetch + combine + upload** via GitHub Actions.  
- Maintain KPI updates through GPT-assisted data checks and prompt-based summaries.

—

## 🧾 Notes

This workspace replaces the former “ChatGPT Drafts” area and is now part of the  
official documentation layer of the RealityCheck repository.  
All files use plain Markdown for readability and Git version tracking.

—

**Maintainer:** Carsten Winterling  
**AI Companion:** ChatGPT (GPT-5)  
**Updated:** 20 Oct 2025