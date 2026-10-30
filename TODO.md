# TODO

## Next Improvements

- Continue the World-map roadmap in `docs/analysis_coverage_review.md` with source-backed conflict/climate lenses and an accessible text alternative; group comparison, overlap colouring, KPI choropleth, guarded aggregation modes, summaries and shareable URL state are complete.
- Add a dedicated climate-exposure map mode: first a transparent country-level risk classification, then separately switchable subnational hazard layers for low-lying coasts, floods/deltas, heat, drought and wildfire. These layers must retain source, year, resolution and coverage metadata and must not be labelled as country groups.
- Region-based hazard map architecture is implemented (`region_sets.json`, region GeoJSON files, `region_csv`/`ibtracs` adapters, `renderWorldMapRegionLayer` in `scripts/script_world.js`). Tropical Cyclone Activity is backed by NOAA IBTrACS; Wildfire — Burned Area is now active as a country view backed by OWID/GWIS (198 countries, 2012–2025, current partial year excluded). Flood, Heat and Drought are now active country categories using reported flood impacts, modelled heat-index days and 12-month SPEI moisture anomalies. Subnational hazard footprints remain a separate roadmap item. See `docs/climate_sources_2026-10-30.md`.
- Completed: NOAA IBTrACS runner reachability, fetch/save and FTP upload were verified by the successful [October 1, 2026 monthly run](https://github.com/ckvfox/realitycheck/actions/runs/36843630183): 233 records, 21 updated KPIs and zero fetch errors. JSON/CSV consistency and repository climate-map wiring were checked on October 12; see `docs/ibtracs_verification_2026-10-12.md`.
- Completed locally (2026-10-30): fixed the North Atlantic parser defect and refreshed the complete NOAA since1980 source. All 279 published basin/season counts reconcile with an independent raw CSV parse, including 46 North Atlantic seasons (1980–2025). Sparse South Atlantic seasons remain missing, not zero.
- Completed (2026-10-30): FileZilla publication of the 17-file climate delta to `/realitycheck.great-site.net/htdocs`; live QA confirmed all ten climate categories, the NOAA basin series/count table and red–yellow–green map colors on World and Countries. Historical evidence: `docs/ibtracs_verification_2026-10-12.md`; current source review: `docs/climate_sources_2026-10-30.md`.

- Completed and activated the first source-bound tranche for typical household resources, housing adequacy, healthy-diet affordability, energy dependence/efficiency, social trust and suicide mortality; all eight passed their first live JSON/CSV fetch and generated KPI analyses.
- Continue source work for comparable rent burden, disposable income after housing, household energy prices/outages, daily climate exposure, conflict spillover, migration accessibility, polarisation and mental-health prevalence before adding further broad composite indices.
- Add release-bound structured sources, where licensing and stable access permit, for sunshine/climate comfort, representative beer affordability, liveable-city recognition, conflict proximity/spillover exposure and immigration-accessibility rules. Until then these dimensions remain explicitly qualitative editorial context.

- Completed: extended World from seven to 15 series by activating global military spending and adding automated displacement, climate-disaster impact, NOAA sea-level, ocean-heat and atmospheric-CO₂ indicators with explicit source metadata.
- Completed: fetched and validated all ten registered world-state KPIs and regenerated the consolidated gzip parts; production upload remains an explicit FTP workflow action.
- Migrate Government Effectiveness to the revised WGI history and Road Traffic Deaths to the WHO country table after adding full-history/schema regression tests.

- Review both editorial language versions of the Germany 2036 Reform Agenda at least annually and after major German legislation or new OECD/EU comparative evidence; keep country mechanisms distinct from transferability claims, compass scores distinct from source metrics and both B2 versions equivalent in meaning.
- Revisit the military-duty versus universal-civic-year comparison after relevant German legislation, constitutional case law or new controlled evaluations; do not infer compulsory-service effects directly from voluntary-service participants.
- Review the conscription map at least annually and after service-law or V-Dem regime changes; keep selective, suspended, registration-only and actively enforced systems methodologically distinct.
- Review the war stress-test evidence matrix after material NATO, BBK, BfV, EU, OSCE or arms-control updates; keep fictional escalation assumptions visibly separate from official assessments.
- Refresh the household gross-income benchmark after each EU-SILC household-type release; keep the DINKs asterisk until the source explicitly identifies two earners, and do not label household-type bands as percentiles without a matching official distribution.
- Review the Germany 2036 source/assumption matrix at least annually and after material Destatis, UBA, IEA, OECD, EU or NATO updates; keep model assumptions separate from projections.
- Refresh the income-pyramid thresholds after each annual Destatis full-time earnings and EU-SILC release; never infer a current net top-10 threshold without a published source.
- Refresh and review the server-side Destatis real-wage snapshot and OECD wage dataset when either source revises its annual series or price base.
- Completed: fail-closed data validation, deployment allowlist enforcement and pipeline safety regression tests.
- Completed: Testbasis phase with source metadata contracts, isolated adapter tests, key-page smoke checks and one shared local/CI runner.
- Completed: core fetch refactoring with typed adapter requests/results, explicit execution modes, complete source registry and centralized status policy.
- Completed: moved all source-specific clients and parsers from `fetch_data.py` into independently tested modules under `scripts/adapters/`.
- Completed: demand-driven frontend KPI loading, request caching, world-page payload reduction, keyboard sorting, skip links, reduced-motion handling and versioned production assets.
- Add CI check that validates standards/compliance-output-schema.json format for audit outputs.

## Migration Tasks

- Completed: framework anchors and standards baseline (Phase A+B).
- Completed: deployment transition script and runbook (Phase C baseline).
- Completed: mirrored release cycles and parity verification (cycle 2/2 completed, see docs/deployment_parity_2026-06-14.md and docs/deployment_parity_2026-06-14_cycle2.md).
- Completed: primary FTP handover uses only `build/deployment/`; the duplicate legacy mirror was retired.
- In progress: first probation cycle evidence recorded locally (docs/deployment_probation_cycle_2026-06-14.md); production upload/monitoring outcome still pending.
- Pending: run post-cutover compliance audit and update report artifact.

## Open Questions

- Should deployment state file be retained between release cycles or reset per tagged release?

## Structure Harmonization

- [x] Retired legacy `deployment/full_deployment/` and `deployment/delta_deployment/` after the controlled cutover.
- [x] Keep README structure inventory aligned when data, scripts or deployment folders change.
- [x] Ensure WebCheck/FPF audits classify productive `scripts/` browser code as a documented exception.


## HTTP delivery acceptance (2026-10-19)

- Implemented locally: Translate native chooser/readiness, measured Google CSP
  bootstrap hash, DirectoryIndex-safe canonical redirects and source-aware audit.
- Live verified after manual FTP upload on 2026-10-19: shared script version
  20261019-translate-2, populated language selector and actual German translation.
- Pending: prove root 200 and aliases one-hop 301 with query preservation, confirm
  the exact CSP response header and compare the central Webcheck UA. Cookie-free
  HTTP probes still receive the InfinityFree hoster challenge.
- Central Webcheck integration is separate; this repository provides the local
  source-selection helper without modifying that service.

- Completed and live verified (2026-10-30): flood/heat/drought country views, explicit coverage and shared environmental map colors. Follow-up tooltip wrapping is validated locally; its separate FTP publication is pending. Monthly FTPS destination is now explicit and regression-tested.
