# Climate source review — 2026-10-30


## Current integration status (supersedes the earlier source survey below)

All four previously pending categories are now active country views; the cyclone view remains basin-based. They do not display subnational flood/drought/fire footprints.

| KPI | Published observations | Country coverage across history | Years | Latest-year coverage | Source release |
| --- | ---: | ---: | --- | ---: | --- |
| Flood-affected people | 3,315 | 179 | 1900–2025 | 63 (2025) | 2026-10-21 |
| Modelled Heat Index >35°C days | 7,961 | 194 | 1960–2024 | 135 (2024) | 2026-06-24 |
| 12-month SPEI | 12,159 | 190 | 1960–2023 | 190 (2023) | 2026-06-24 |

- Flood: [EM-DAT via OWID](https://ourworldindata.org/grapher/natural-disasters-people-affected?impact=total_affected&metric=total_number&timespan=annual&type=flood), column `total_affected_flood_yearly`. Injured + people requiring immediate assistance + homeless. Reporting is incomplete and uneven; absent country-years remain missing, and reported zero does not establish safety. Current partial years and aggregates are excluded using the existing OWID guards.
- Heat: [World Bank ESG metadata](https://databank.worldbank.org/metadataglossary/environment-social-and-governance-(esg)-data/series/EN.CLC.HEAT.XD), indicator `EN.CLC.HEAT.XD`, source 75. Model-derived annual days whose daily mean heat index exceeds 35°C, incorporating humidity. The provider notes an RCP 8.5 basis; this is explicitly modelled hazard data, not observed deaths, maximum air temperature or a real-time warning. Country coverage/latest years vary; do not silently backfill a selected year.
- Drought: [World Bank ESG / SPEIbase metadata](https://databank.worldbank.org/metadataglossary/environment-social-and-governance-(esg)-data/series/EN.CLC.SPEI.XD), indicator `EN.CLC.SPEI.XD`, source 75. A 12-month moisture anomaly, with negatives drier and positives wetter. Annual country averages can conceal regional extremes. Provider metadata declares CC BY 4.0 for both World Bank indicators. SPEI changes use absolute index units rather than percentage changes through zero.

New records were staged through the existing adapters and promoted only after JSON/CSV parity, finite-value/range checks and unique country-year keys. Source CSV/JSON caches, SHA-256 evidence and a no-secret importer are under ignored `build/source-review/`. World Bank refreshes now select source 75 for both data and release metadata, retaining the response release date and rejecting partial pagination.

### Environmental color convention

`scripts/environment_colors.js` is shared by both dashboard maps and deployed as a productive browser asset. For directionally interpretable environmental indicators, red indicates higher pressure/worse outcomes and green lower pressure/better outcomes. Missing observations are gray. Generic scales use the displayed comparison's 5th–95th percentile range (log1p only for broad nonnegative ranges), not universal safety thresholds. Positive outcomes (e.g. protected area/renewables) reverse the numeric direction. Equal nonzero values use neutral yellow. Unclassified/target metrics retain their existing presentation instead of receiving an invented good/bad direction. Group-comparison borders preserve membership while fills show environmental values. Country-comparison line colors still identify countries/basins.

SPEI is independent of the comparison range: ≤−2 red (extremely dry), −1 yellow, ≥0 green (no negative moisture anomaly). Green describes drought pressure only and says nothing about flood safety. Sparse reported impacts likewise cannot certify that a green country is safe.

The red–green palette, scale direction, missing/zero behavior, negative values, neutral ties and fixed SPEI thresholds have offline regressions. Local browser QA covers all three new categories, selected-year coverage and both dashboards. Existing AGENTS/security policy/robots/sitemap require no changes: there is no new public route, credential or browser data origin. Framework candidate: couple each hazard metric to explicit direction, coverage, source date and scale semantics; never infer global safety from relative ranks or missing impact reports.

## Earlier cyclone corrections and source survey

The World page now renders cyclone activity as separate basin time series, without manufacturing a global total. A system may occur in several basins. NOAA SEASON is not universally a calendar year: Southern Hemisphere seasons run July–June and use the ending year. The adapter counts recorded SID/basin/season combinations, including unnamed systems, rather than named storms or impacts.

The map replaces the hand-authored rectangular surfaces with illustrative basin location circles and a text table. Circle locations are labels, not storm coordinates, tracks, boundaries or affected areas. Missing observations remain missing, including sparse South Atlantic seasons. Source: [NOAA variable documentation](https://www.ncei.noaa.gov/sites/default/files/2025-09/IBTrACS_v04r01_column_documentation.pdf) and [technical details](https://www.ncei.noaa.gov/sites/default/files/2025-04/IBTrACS_version4r01_Technical_Details.pdf).

The NA parsing fix preserves the valid North Atlantic code. Offline coverage checks repeated fixes, cross-basin systems, blank identifiers, unknown basins, invalid seasons and future seasons. The full 145,263,024-byte NOAA since1980 CSV was downloaded with curl and resumed after the bounded first transfer timed out. The completed file was processed through the existing adapter into staging and independently reconciled using Python standard-library CSV parsing and distinct SID/basin/season tuples. All 279 observations agree, including every North Atlantic season from 1980 through 2025. Raw SHA-256: `e22f9f36d9b9e01cb552708a0c204007dd52f7e8fef83e46cf0d31f556fd93f7`. NOAA HTTP modification date: 2026-10-30. The cached directory listing was slightly older than the live HTTP content length. South Atlantic absent seasons remain missing. No production deployment is established by these local changes. The October 12 verification note remains historical evidence.

## Earlier source candidates (superseded by current integration above)

| Category | Concrete source | Access and meaningful integration |
| --- | --- | --- |
| Wildfire | [OWID/GWIS annual burned area](https://ourworldindata.org/grapher/annual-area-burnt-by-wildfires) | Public CSV successfully downloaded and parsed locally: 3,900 rows, 260 entities, 2012–2026. Country map now active: 2,772 observations, 198 recognized countries, 2012–2025. The adapter excludes partial current years and non-country aggregates. Separately coded territory aliases cannot overwrite or duplicate parent-country values (Northern Cyprus/Cyprus regression). Explicit zero values remain zero. GWIS and OWID are attributed; upstream source reuse terms apply. This does not establish an IPCC-region layer or human/economic impact. |
| Flood | [Copernicus GloFAS/GFM](https://emergency.copernicus.eu/data/) and [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api) | Real flood-monitoring and modelled discharge sources exist. River discharge is not flooded area, losses or people affected. Select the metric and aggregation first; regional coverage, historical consistency and download access still need a pipeline check. |
| Heat | [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api) / ERA5 | Suitable for temperature/heat-day indicators, not direct mortality or damage. A few capital-city coordinates cannot represent whole countries or climate regions. Regional grids, thresholds, baseline and weighting must be defined and validated. |
| Drought | [Copernicus global drought indicators](https://emergency.copernicus.eu/data/) | Real global drought products exist. Choose an indicator, spatial coverage and time aggregation; drought hazard must remain distinct from crop damage or affected people. No regional download was validated in this review. |
| Cross-hazard impacts | [EM-DAT](https://doc.emdat.be/docs/data-accessibility/) | Country/event deaths, affected people and losses are available via registered access. Not an anonymous drop-in feed; review access, reuse terms, missingness and reporting biases before integrating. |

[Copernicus CDS API setup](https://cds.climate.copernicus.eu/en/how-to-api) requires account/API configuration and manual acceptance of applicable dataset terms. Free data does not necessarily mean anonymous automated access. Open-Meteo's API documentation also distinguishes free access and commercial service access.

The blanket claim that no usable sources exist is obsolete. These are viable source candidates with different readiness levels; the wildfire country KPI is now fetched, validated and active. Flood, Heat and Drought remain pending. The UI now says “source integration pending” instead of promising a delivery date.

## Validation

Targeted Python adapter tests and JavaScript group/basin regressions pass. Local static browser inspection confirmed seven basin circles, the source/method text and the season/count table. The World cyclone card contains its regional chart instead of the global-values error. The Python adapter/source/pipeline tests, JavaScript suites, PHP checks and data validation pass; the monthly workflow test was repaired for CRLF compatibility and the interrupted suite completed. Browser QA confirmed the active wildfire category, 2012–2025 selectors, 198-country coverage, distinct map intensities, a 2024 year change and the refreshed 2025 North Atlantic count (13). The FPF production baseline passes. Frontend/metadata/data publication remains a separate FTP action.


## Earlier handover evidence (replaced by the final packages below)

The raw CSVs, cache importer and detailed import/test evidence remain under ignored `build/source-review/`; they are excluded from both upload sets. Both adapters run without calling the credential-loading fetch CLI. The metadata is promoted only after staged JSON/CSV validation; published JSON/CSV have unique country/basin-season keys. The changed consolidated bundle contains both datasets. Unchanged decompressed bundles retain their previous bytes to avoid needless FTP changes. No AI analysis, rankings or unrelated source datasets were regenerated.

Security policy, AGENTS, robots and sitemap need no updates: no new route, credential, external browser origin or access model is introduced. Framework candidate: validate semantic entity identifiers (such as `NA`) and reject territory-alias collisions before publishing aggregates; structurally valid CSV is insufficient evidence of completeness.


Handover prepared and SHA-256 verified: `build/deployment/full/` contains 450 files (78,155,339 bytes); `build/deployment/delta/` contains 9 files (1,442,407 bytes). Delta baseline is the previous local 449-file package manifest, preserved under `build/source-review/previous-deployment-state.json`; this is not proof of the currently uploaded server state. The delta paths are:

- `world.html`
- `scripts/script_world.js`
- `data/meta/available_kpis.json`
- `data/meta/region_sets.json`
- `data/tropical_cyclone_activity_basin.json`
- `data/wildfire_burned_area.json`
- `data/fetch_status.json`
- `data/all_kpis_index.json`
- `data/all_kpis_part5.json.gz`

The full package and delta contain productive artifacts only; raw CSVs, Python scripts, tests, local reports, server-owned tracking state and authentication configuration are excluded. Both datasets in the consolidated bundle were compared with their individual packaged JSON. No FTP upload was performed; Git publication is recorded in repository history.


## Final cumulative upload packages

Full: 455 productive files (80558753 bytes). Delta: 17 files (4020071 bytes). Both folders were cleared and regenerated using `scripts/prepare_deployment.py --mode both --baseline-manifest build/source-review/previous-deployment-state.json`. The preserved 449-file local manifest keeps the earlier, still-unuploaded cyclone/wildfire corrections in this cumulative delta. All package file sets and SHA-256 hashes match their source manifests. All five climate datasets match their consolidated packaged JSON; the index includes the newly required sixth bundle.

The explicit baseline option is covered by a regression that rejects missing/empty baselines. Python tests were completed after repairing a missing fixture counter in the new World Bank test; all JavaScript, PHP, data-validation and FPF checks pass. Browser checks confirmed all three new selectors, accurate latest-year coverage, shared map colors, and the SPEI previous-year tooltip in index units. No production upload was performed; Git publication is recorded in repository history.


## Monthly automation acceptance

GitHub reports `monthly-fetch.yml` as active. Its existing schedule is day 1 of each month at 03:00 UTC; the full, unfiltered `fetch_data.py` command runs before the guarded data upload and data commit. All five climate indicators are enabled in the normal production selection. No manually dispatched production run was triggered during this work.

Two release-discovery defects were corrected before Git publication: World Bank WDI (source 2) and ESG (source 75) now use separate release-date cache entries, and OWID metadata requests retain the selected chart dimensions. A real provider metadata check returned flood release 2026-10-21 and ESG release 2026-06-24. An isolated full-orchestrator regression proves that a fresh ESG release is fetched even when WDI is unchanged; additional tests protect the five enabled sources, monthly command, partial-year guards and flood metadata query. The complete offline runner and FPF production baseline pass.

Generated build outputs and review caches remain local and excluded from Git. The cumulative FTP delta remains based on the preserved 449-file pre-change local package manifest; only productive runtime files are included. The application/backend changes and source registrations are committed to GitHub, while the user performs the separate FTP handover.
