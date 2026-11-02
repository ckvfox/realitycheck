# NOAA IBTrACS verification — 2026-10-12

## Outcome

Runner fetch and FTP publication are verified. The current dataset is structurally consistent but **not complete**: North Atlantic is missing due to a reproduced CSV parsing defect. Production selection is connected, but full map correctness is not established. This audit changes documentation only.

## Evidence and fulfilled checks

- Reviewed main commit `25c0244e735c845f07e6c04e4cbd1f3deac3159c`.
- [Monthly run 36843630183](https://github.com/ckvfox/realitycheck/actions/runs/36843630183), October 1, 2026: completed/success; runner input commit `bdf3f724385923f7f0634b4af0dc6500188258ea`.
- Job `110308425765`: log at 09:35:44 UTC confirms `[OK] IBTrACS KPI saved: tropical_cyclone_activity_basin (233 rows)`; zero errors and KPI promotion are logged. FTP deploy and data commit steps succeed. At 09:39:02 UTC the log explicitly uploads the 26,528-byte cyclone JSON and confirms upload success. This proves transfer, not subsequent HTTP-byte parity or map correctness.
- `data/fetch_status.json`: last fetch 2026-10-01T09:35:44Z, data year 2025, summary 21 updated / 80 skipped / 0 errors. `data/fetch_state.json` includes the indicator among 21 updated KPIs.
- JSON and CSV contain identical 233 records, with unique region/year/scenario/horizon keys, finite positive integer counts, historical scenario and empty horizon; years are 1980–2025 and exclude 2026.
- Repository wiring: active `ibtracs` source and `geo_type: region` / `region_set: ocean_basins` in `data/meta/available_kpis.json`; climate `storm_impact` category loads the KPI, region-year selection and `renderWorldMapRegionLayer` in `scripts/script_world.js`; region-set metadata points to seven basin geometries. All six dataset codes match geometry codes.

## Completeness and methodological gaps

| Basin | Rows | Years | Finding |
| --- | ---: | --- | --- |
| EP, NI, SI, SP, WP | 46 each | 1980–2025 | One record per season in each basin |
| SA | 3 | 2004, 2010, 2011 | Missing seasons are absent, not explicit zeros |
| NA | 0 | None | Defect: valid basin code discarded |

For 2025 the stored counts are EP 28, NI 17, SI 24, SP 11, WP 34. These are audit reference values, not independently NOAA-validated counts.

### Reproduced North Atlantic defect

`pd.read_csv` in `scripts/adapters/ibtracs.py` retains default missing-value recognition even with `dtype=str`. A minimal CSV with basin `NA` parses that field as NaN; the subsequent `dropna(subset=["SID", "BASIN", "SEASON"])` removes it. An EP control row survives. This directly explains the absent North Atlantic series. A successful fetch status does not detect this semantic loss.

Follow-up acceptance: preserve `NA` while handling real blanks, add an adapter regression using repeated track fixes and a valid North Atlantic row, regenerate datasets, and compare basin-season totals with the authoritative source. Do not patch output files manually or fill NA with zeros.

### Metric meaning

The adapter reads only SID, SEASON and BASIN. It counts unique storm/basin/season combinations without checking NAME, storm nature or intensity. “Named storms per year” is therefore not established by the implementation. Decide the intended definition and align adapter, KPI metadata and UI; distinguish cyclone activity from landfall, damage and human impact. A cross-basin storm can count once in each basin, so basin sums are not unique global storm totals. Verify SEASON meaning (including Southern Hemisphere season boundaries) before presenting it as a calendar-year count. `source_date` is synthesized from the latest season, not an independently observed release date.

[NOAA documentation](https://www.ncei.noaa.gov/products/international-best-track-archive) identifies since1980 as the satellite-era subset and states that systems occurring within a basin are included there. No raw-source count reconciliation was completed in this audit. Missing SA seasons must remain distinct from verified zero activity until source coverage is checked.

## Production inspection

Inspected https://realitycheck.great-site.net/world.html on October 12, 2026 through the live browser:

- Climate Hazards & Exposure → Storm Impact (tropical cyclones) is selectable.
- The selected KPI exposes years 1980–2025, defaults to 2025 and absolute values; geography is disabled in region mode.
- The production geography option still reads “Regions (coming soon, country fallback)”. The global chart list includes “Tropical Cyclone Activity by Ocean Basin” with “No global values in dataset”. This confirms metadata/selection availability, not valid global aggregation.
- A completed polygon/tooltip/visual legend check was not obtained. Do not mark the production map as verified from selector availability or successful FTP alone.

Follow-up acceptance: verify deployed JS/HTML/metadata/GeoJSON parity, seven basin polygons and their simplified non-official geometry attribution, NA after regeneration, sparse SA no-data messaging, tooltips matching the selected dataset/year, legend/source/coverage, year changes and accessible text alternative. Review the inappropriate global-value card and the region placeholder wording. Wildfire, Flood, Heat and Drought remain sourcing placeholders.

## Scope and validation

Documentation only: TODO, AGENTS, CHANGELOG and this evidence note. No adapter, generated data, frontend, workflow or deployment changes. Structural checks and the minimal pandas parsing reproduction were run locally; the FPF baseline result is recorded in the accompanying PR. Full offline CI remains the repository PR check. No production deployment is needed for these documentation changes.
