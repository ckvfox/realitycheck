# Analysis coverage review

## Current analytical foundation

RealityCheck currently provides 100 KPIs across economy and labour, education, environment, health and society, infrastructure and technology, security and defence, governance, and culture. Sixteen indicators are global-only. The eight household, housing, energy, trust and mental-health additions passed their first live JSON/CSV fetch on 1 August 2026 and are active. The catalogue supports a broad first assessment of country outcomes, world trends and the Germany dossier.

The main analytical risk is no longer simply too few indicators. It is that some questions important to everyday life, migration and geopolitical exposure are represented only indirectly, while adding another composite index would duplicate existing evidence.

## Highest-value gaps

1. **Housing affordability and household purchasing power.** The new urban inadequate-housing and healthy-diet-affordability indicators add direct outcomes, but a globally comparable rent burden or price-to-income series is still missing. Inadequate housing covers only 45 countries and therefore has no default Overall weight.
2. **Real disposable income and distribution.** Median income or consumption per day is now registered and is materially closer to typical living standards than GDP. It still mixes income and consumption surveys and is not a uniform disposable-income-after-housing measure.
3. **Country-level daily climate exposure.** Global warming, water stress and resilience are present, but heat days, flood/drought/wildfire exposure and observed disruption to daily life are not consistently available by country.
4. **Conflict proximity and spillover exposure.** Domestic peace and geopolitical risk exist, but distance to active conflict, conflict-affected neighbours, trade/energy exposure and alliance deterrence/obligations are not structured country evidence.
5. **Migration accessibility and integration policy.** Destination quality is well covered; visa/work/residence accessibility and policy-based integration conditions are not. Migrant share and net migration are outcomes, not proof of low barriers or social openness.
6. **Energy affordability, reliability and import dependence.** Net energy imports and grid losses are now registered as guarded proxies. Comparable household prices, supplier concentration and outage frequency remain missing.
7. **Institutional trust, polarisation and social cohesion.** Interpersonal and national-government trust are now registered; survey-wave comparability and incomplete coverage mean polarisation and social isolation remain open gaps.
8. **Mental health and subjective everyday stress.** Suicide mortality is now registered as a severe outcome with an explicit underreporting guardrail. It does not replace prevalence, access-to-care or everyday-stress measures.

## First-source activation policy

New automated KPIs are not exposed in the browser, consolidated payload, Overall Ranking or AI analysis until both productive JSON and CSV files exist and are non-empty. `scripts/promote_ready_kpis.py` removes `pending_first_fetch` only after those checks. The fetch pipeline runs this promotion before consolidation, analysis and validation, so a successful first fetch activates a KPI atomically while a failed source remains hidden and cannot break the current site.

For Germany, the dossier adds richer narrative and specialist evidence, but more of its real-wage, housing, productivity, infrastructure, energy-security, demographic and defence-readiness evidence should eventually become comparable time series with explicit Germany/EU/OECD benchmarks.

## Overall Ranking design

The standard Overall scenario remains the primary score and is calculated in the browser from the user's KPI list-box weights. Fun, Safe Haven and Immigration are alternative editorial lenses: they explain separately generated Top and Bottom 20 lists, but never replace or silently modify the standard score. The counter-lists describe weaker fit for a lens and deliberately avoid judgments about populations.

The optional `data/meta/country_analysis_context.json` file is the controlled input for source-bound context that is not represented by normal KPIs. Entries without a value, source and as-of date are ignored. Composite third-party relocation rankings should be used for external comparison only when they largely duplicate the existing catalogue or omit actual immigration barriers.

## World map roadmap

Recommended order:

1. **Completed:** two-group comparison and overlap colouring, including countries belonging to both groups.
2. **Completed:** group summary panel with member count, population/GDP/CO₂ world shares, selected-KPI median, actual year and coverage.
3. **Completed:** KPI choropleth within selected groups; hue identifies exclusive/overlapping membership and intensity preserves country differences.
4. **Completed:** absolute/per-capita and sum/median switches with guardrails that prevent summing rates, scores or indices and prevent redundant per-capita conversion.
5. Add conflict- and climate-exposure lenses only after their source-bound country datasets exist. Country-level climate classes may reuse the existing country polygons, but must expose their component indicators, year and coverage.
6. **Completed:** grouping, both groups, KPI, year, value mode and aggregation persist in the URL for reproducible shared views.
7. Add keyboard-operable controls, colour-blind-safe overlap styling and a text alternative listing the selected members and excluded/missing countries.
8. Treat low-lying coasts, river deltas, flood zones, heat, drought and wildfire areas as separate subnational hazard overlays backed by spatial GeoJSON/raster sources. Never model partial-country exposure as an ordinary whole-country group.

The map should avoid implying that international groups are homogeneous. Every aggregate must state its year, coverage and whether it is a sum, median, weighted average or simple member count.
