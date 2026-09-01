# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Fixed
- Fixed Google Translate widget being fully blocked by the Content-Security-Policy: added the sha256 hash for the widget's fixed inline bootstrap script (executed inside its `about:srcdoc` iframe) to `script-src`, so the translate panel initializes instead of failing with CSP violations and `Cannot read properties of undefined (reading 'height')` errors.
- Fixed horizontal overflow on the World dashboard at iPhone widths by allowing KPI clusters and Chart.js cards to shrink below their desktop intrinsic width and wrapping descriptive text inside the viewport.

## 3.4.0 - 2026-08-01

### Added
- Added eight guarded automated KPI definitions for median income/consumption, inadequate urban housing, healthy-diet affordability, energy-import dependence, electricity-grid losses, interpersonal trust, government trust and suicide mortality.
- Completed the first live fetch for all eight additions, activated them atomically, regenerated consolidated data, Overall and editorial rankings, global analysis, 100 per-KPI analyses and outlier evidence.
- Added first-fetch publication staging: incomplete new KPIs stay out of the browser, consolidated data, rankings and AI analysis until JSON and CSV artifacts both validate; successful fetches promote them automatically.
- Extended the Fun, Safe Haven and Immigration evidence sets with the new living-condition, cohesion, climate-loss and energy-exposure dimensions; volatile climate damage uses a five-year average in editorial rankings.
- Added simultaneous World-map group comparison with blue/orange exclusive membership, purple overlap, within-group KPI choropleth intensity, side-by-side group summaries, and guarded absolute/per-capita plus median/sum modes. Comparison and mode state are included in shareable URLs.
- Added a source-backed World-map group summary with member count, world population/GDP/CO₂ shares, selected country-KPI median, actual data year and per-metric coverage. Grouping, group/category, KPI and year are persisted in shareable URL parameters.
- Replaced unreliable model-selected Fun and Safe Haven Bottom lists with deterministic, coverage-gated percentile rankings. Safe Haven is now anchored in the Global Peace Index and uses conflict counts only as supporting context; automated contracts reject duplicate countries and implausible legacy false positives.
- Added an accessible Overall Ranking analysis panel that explains the standard user-weighted result and shows source-constrained Top/Bottom-20 reasons plus standard-rank comparisons for the Fun, Safe Haven and Immigration lenses. Counter-lists use distinct ☔, 💥 and 🚧 symbols and exclude countries already present in the matching Top list.
- Added a source/as-of-gated country context extension for future weather, conflict-exposure and immigration-access evidence, plus a documented analysis-coverage and World-map roadmap.
- Added seven automated global-only indicators for forced displacement, climate-disaster deaths, affected people, disaster losses relative to GDP, NOAA satellite sea level, ocean heat and atmospheric CO₂; activated existing military spending on the World dashboard.
- Added evidence-bound candidate construction for Fun, Safe Haven and Immigration rankings, plus stable country context for languages, geography and memberships. These modes remain explicitly editorial hybrids and do not invent exact external prices, city ranks, conflict probabilities or immigration rules.
- Added country extremes, comparison-group medians, five-year anomaly candidates and non-causal cross-KPI rank associations to global and individual KPI analysis inputs, with metric-direction, target and scope guardrails.
- Added `docs/analysis_methodology.md` describing the separation between measured evidence, hypotheses and qualitative editorial context.
- Added visible per-KPI analysis timestamps, with exact UTC generation times for new analyses and a backward-compatible date display for legacy entries.
- Added an always-generated monthly workflow summary and 30-day diagnostic artifact containing fetch console/log, status, state and validation evidence on both successful and failed runs.
- Added ten open World Bank world-state indicators for sanitation, electricity, secondary completion, undernourishment, hosted refugees, real GDP-per-capita growth, women in parliament, protected land, net migration and statistical-system performance.
- Added reviewed Overall Ranking defaults for seven directionally comparable new indicators while excluding migration counts and the statistical-performance guardrail from the score.
- Added explicit acquisition contracts for all 12 locally maintained CSV KPIs, including Summer and Winter Olympic medals, with access constraints and reviewed official release-page checks.
- Added a reproducible world-state KPI gap and freshness audit report covering automated-source replacements, discontinued series and high-value missing indicators.
- Added a demand-driven KPI loader, request deduplication, native streaming gzip decoding with compatibility fallback, shareable `?kpi=` routes and frontend performance regression contracts.
- Added keyboard-sortable country table headers, live loading feedback, automatic skip links, global focus visibility and reduced-motion handling.
- Added fail-closed pipeline guards and unit tests for fetch errors, dummy results, empty selections, output-format requirements and isolated test KPIs.
- Added automatic pull-request and `main` CI for Python compilation, data validation, JavaScript tests and PHP checks.
- Added the pushed rollback tag `baseline-pre-safety-refactor-2026-07-31` for the complete pre-Sofortschutz state.
- Added a network-free test baseline with 22 Python regression tests for source contracts, KPI selection, adapter output isolation, transformations, key-page assets, deployment allowlisting and delta detection.
- Added `scripts/run_tests.py` as the shared local and CI entry point plus `docs/testing.md` for extending KPI and source coverage.
- Added a typed fetch core, explicit built-in adapter registry and architecture documentation for immediate, batch and special source execution.
- Added network-free contract tests for CSV, Data360, UNHCR, IMF and geopolitical-risk adapters; all supported source families now have focused adapter coverage.

### Changed
- Made the World-map comparison overlap card span the full summary width and wrap long group names instead of clipping them.
- Corrected the World-map comparison layout: desktop controls now use a balanced two-row grid, tablet/mobile breakpoints collapse predictably, the mode explanation no longer overlaps its select, and comparison metrics render as readable two-column cards instead of one compressed row.
- Made Overall Ranking lenses mutually exclusive and clarified that they highlight editorial comparisons without replacing or modifying the list-box-driven standard score.
- Restored the intended character of Fun, Safe Haven and Immigration: Fun is mildly humorous and considers climate, sunshine, beer and liveable cities; Safe Haven considers conflict proximity, alliance exposure and daily climate effects; Immigration explicitly considers visa, work and residence barriers.
- Expanded per-KPI and global prompts to surface notable country and regional changes, potential best-practice candidates and traceable cross-domain hypotheses without presenting correlation as causation.
- Clarified the lower-secondary completion KPI as a gross intake ratio that may exceed 100%, changed country scoring from unbounded `higher` to a 100% target, reduced its default weight, regenerated its AI interpretation and advanced the stored-default schema so the corrected weight takes effect.
- Replaced the model-specific GPT-4 notice on Global Analysis with the generic AI and source-responsibility disclaimer used across the public dashboards.
- Removed the browser-generated rectangular focus outline around mouse-selected Leaflet country shapes and bumped shared frontend assets to `20260801-frontend-8`.
- Changed Overall Ranking normalization from outlier-sensitive min/max values to direction-aware percentile ranks, fixed declared-target scoring, excluded aggregate entities and calculated weights and coverage consistently. Revised defaults prioritize direct outcomes and institutions while de-emphasizing duplicate composites and the Big Mac proxy.
- Changed the global AI synthesis from updated-only lifetime means to all 92 registered KPI snapshots using representative latest years, country coverage and comparable trends; volatile disaster indicators use adjacent five-year averages and incremental KPI summaries receive their validated data snapshot instead of metadata alone.
- Extended the monthly refresh with official-page notifications for maintained CSV editions and pipefail-safe console capture; failed fetches still block FTP and Git push.
- Replaced the model-based manual CSV update guesser with a deterministic offline schema/year/checksum audit and an optional official-page-only notification mode; it never downloads or overwrites maintained inputs.
- Replaced only the opaque `teamwork_wunder.png` with its supplied JPG equivalent; transparent logos and translator assets remain PNG to preserve their alpha channel.
- Completed the FPF deployment cutover: `build/deployment/full/` and `build/deployment/delta/` are now the only FTP handover paths, and legacy mirroring was removed from the packaging command.
- Changed the Countries dashboard from loading the complete consolidated dataset to loading one selected KPI and lazy relation denominators.
- Changed the World dashboard to load only its 15 world datasets, parallelized independent metadata requests and removed unused Pako downloads from pages that do not read consolidated gzip data.
- Changed the floating scroll-to-top control to appear after meaningful scrolling and made the mobile primary navigation horizontally usable without compressing its links.
- Versioned shared frontend assets as `20260801-frontend-1` for deterministic cache refresh on InfinityFree.
- Changed force refreshes to preserve the last known-good data snapshot instead of deleting productive data before fetching replacements.
- Changed full and partial FTP workflows to deploy only from the generated productive allowlist; full upload no longer performs remote clean-slate deletion.
- Pinned direct Python dependencies and all GitHub Actions, serialized overlapping data/deployment workflows and removed token-bearing Git push URLs.
- Pinned browser CDN libraries and added Subresource Integrity checks to previously unverified Marked, Chart.js and Pako loads.
- Changed the manual fetch test to use the isolated `--test` mode and validate only its two marked KPI outputs.
- Changed CI to install pinned dependencies and execute the same complete offline test runner used locally.
- Replaced the source-type `if/elif` dispatcher with `AdapterRequest`/`AdapterResult` contracts, registry completeness checks and centralized status resolution.
- Changed source-date resolution to run once per KPI and limited special-source work to fetch runs that actually selected that source.
- Moved all World Bank, OWID, Data360, maintained CSV, UNHCR, IMF and geopolitical-risk clients/parsers into dedicated `scripts/adapters/` modules behind an injected runtime boundary.
- Reduced `fetch_data.py` to source-neutral orchestration, persistence, status and safety processing, and removed the unused `sdmx1` dependency.

### Fixed
- Restored the Countries KPI controls to a compact centred layout instead of stretching the four selectors across the full viewport.
- Included the productive `data/analysis.md` report in FTP packages as an explicit exception to the repository Markdown exclusion.
- Exported the consolidated KPI loader before deferred page initialization and bumped frontend assets to `20260801-frontend-5`, fixing the Overall Ranking `loadAllKPIData is not defined` startup failure.
- Moved keyboard focus to the page heading before hiding the scroll-to-top control, preventing focused content from being placed below `aria-hidden`.
- Excluded server-owned `tracking.json` state from FTP packages so local testing or full uploads cannot overwrite the live visit counter.
- Declared Overall Ranking mode state before its DOM-ready callback, eliminating the `funOn` temporal-dead-zone crash that left the page blank.
- Corrected the web app manifest icon dimensions to the actual 128×128 pixel favicon and refreshed frontend cache versions.
- Removed the duplicate root-level `deployment/` package tree so FTP handover has one unambiguous source of truth.
- Removed the duplicate Overall Ranking calculate handler that recalculated and stored the same selection twice per click.
- Recovered gracefully from malformed locally stored ranking weights and exposed the ranking mode state with `aria-pressed`.
- Made data validation return a failing exit code for missing, empty or malformed required outputs while recognizing the geopolitical-risk source as intentionally JSON-only.
- Sanitized generated Markdown and rendered AI summaries as text to prevent untrusted generated content from becoming executable DOM markup.
- Serialized visitor-counter writes and restricted the counter endpoint to POST requests.
- Isolated OWID, World Bank, IMF, UNHCR, CSV status, log, hash and mapping side effects below `data/test/` during test runs instead of allowing writes into the productive data snapshot.
- Preserved the previous fetch-status entry when an adapter does not produce a successful replacement dataset.
- Accepted both legacy title-case and current short-name lowercase OWID CSV identity columns.
- Excluded isolated `data/test/` fetch artifacts from full and delta FTP packages.
- Adapted OWID world-only CSV parsing to sources without a country-code column and treated provider-declared non-redistributable datasets as explicit last-known-good skips.
- Updated the Data360 Press Freedom source to the current `RWB_PFI_OVRL` indicator and filtered the API to score observations so rank rows cannot enter the KPI series.
- Counted pending country aliases once per distinct new name instead of once per rejected observation.
- Added a year-regression guard that preserves a newer stored dataset when a provider returns an older snapshot.
- Made Data360 compare its live API result with the maintained raw fallback and select the source with the newer data year.
- Rejected non-finite numeric inputs (`NaN` and infinities) centrally before they can enter generated JSON datasets.
- Reused one HTTP session across immediate adapters and cached the database-wide World Bank source date once per run instead of requesting it for every KPI.
- Corrected OWID metadata discovery to the current `.metadata.json` endpoint so unchanged Grapher datasets can be skipped before downloading their CSV.
- Recorded provider-restricted KPIs explicitly in metadata so normal runs preserve them without repeatedly requesting a known-blocked download.
- Added contract-validated per-source refresh intervals for Data360, IMF and GPR; forced runs still bypass them.
- Made consolidated-data generation initialize UTF-8 output consistently on Windows.
- Stopped retrying valid CSV-update responses with `latest_year: null` and shortened the inter-source delay, reducing model calls and check duration.
- Added an explicit OWID indicator-API path for series whose Grapher CSV omits still-published projection years, restoring the schooling series through 2025 from official data.
- Fixed `--force` being reset when a populated fetch status existed, so forced workflows now reliably bypass freshness checks.
- Included generated `*.json.gz` KPI bundles in full and delta deployment packages; their index could previously be deployed without its referenced data parts.

## [3.3.0] - 2026-07-31

### Added
- Added a bilingual fourth Germany Dossier file, “Germany 2036 — Reform Agenda”, with eleven consistently structured reform fields, international democratic-country mechanisms, options, opportunities, risks, a six-dimension 2036 compass and direct institutional sources.
- Added an editorial EN/DE language switch for the public Germany Dossier, English by default, with a visible explanation of why precise German copy replaces Google Translate on this complex specialist page.
- Added bilingual reform-agenda schema validation and methodology documentation.
- Added a sourced “If war starts, I will just leave” reality check covering exit restrictions, disrupted routes, admission and status uncertainty, refugee living conditions, NATO burden-sharing and the limits of the 2026 US–Ukraine deportation example without stigmatising flight.
- Added a sourced “Why Germany?” introduction explaining the country's global economic weight, EU leverage, stated conventional-defence ambition, potential democratic counterweight, historical responsibility and the author's personal German perspective.
- Added a sourced two-model service debate to the war stress test: classic German military duty with conscientious-objector service versus an all-gender civic year, including potential social-learning effects, legal feasibility, implementation, enforcement, labour-market and fairness risks.
- Added a protected worldwide conscription map to the war stress test, distinguishing active conscription in V-Dem democracies and autocracies from no active service and unresolved data, with explicit definitions, review dates and democratic safeguards.
- Added a separately activated, non-probabilistic “Germany at War” security stress test below the three regular scenarios, with seven evidence-labelled phases, a BBK-based 72-hour view, five household perspectives, balanced deterrence and conscription debates, historical comparison limits and an HTTP-denied source matrix.
- Added `docs/germany_war_stress_test_method.md`, server-side schema tests, browser-logic tests, responsive/print styling and deployment allowlisting for the new module.
- Added an English, three-file Germany Dossier with a values-based editorial disclosure and card-index navigation for prosperity, 2036 scenarios and the war stress test.
- Restored the Earth Overshoot Day status on About using the announced 30 July 2026 date and added a matching, explicitly non-countdown Doomsday Clock card (85 seconds to midnight, 27 January 2026).
- Added a server-side household gross-income benchmark for singles, couples and families with one to three children using one combined annual household figure.
- Extended the Germany Dossier with the interactive “Deutschland 2036” three-scenario simulation, six macro index bands, eight sensitivity controls and four household perspectives.
- Added a visible source/assumption matrix, robust cross-scenario measures, an HTTP-denied model data include, pure-function model tests and `docs/germany_2036_scenario_method.md`.
- Added an analysis of German real average wages and an OECD PPP wage-level comparison, initially behind a PHP session gate and subsequently released through the public Germany Dossier.
- Added a reproducible OECD wage fetcher, HTTP-denied server-side data includes, a password configuration template, and targeted boundary/auth tests.
- Added methodology, access setup, limitations, and upload instructions in `docs/real_wages_analysis.md`.
- Added Fox Project Framework v2.0.0 anchors: PROJECT_MASTER.md and standards/ baseline.
- Added framework governance files: TODO.md, .env.example and LICENSE.
- Added machine-readable compliance artifacts and Apache shared hosting profile.
- Added deployment transition script: scripts/prepare_deployment.py.
- Added deployment migration runbook: docs/deployment_runbook.md.
- Added deployment cutover plan with criteria and rollback: docs/deployment_cutover_plan.md.
- Added deployment parity report for mirrored cycle validation: docs/deployment_parity_2026-06-14.md.
- Added deployment parity report for mirrored cycle 2 validation: docs/deployment_parity_2026-06-14_cycle2.md.
- Added probation-cycle execution checklist for primary deployment switch: docs/deployment_probation_cycle_checklist.md.
- Added local probation evidence report for primary deployment cycle: docs/deployment_probation_cycle_2026-06-14.md.
- Added compliance audit artifact: docs/compliance_report_2026-06-13.json.
- Added UN Security Council permanent members as a World map country grouping.
- Added structure harmonization notes that distinguish FPF target deployment paths from existing legacy fallback folders.
- Documented existing-project protection for productive root HTML, `scripts/`, `data/` and `images/` paths.

### Changed
- Rewrote the German energy-reform chapter a second time in plain language, expanding compressed administrative phrases into complete explanations of renewable priority areas, environmental review, local participation, grid planning, flexible consumption and fusion research limits.
- Re-edited the complete German Reform Agenda as independent B2-level editorial copy instead of sentence-by-sentence translation: replaced opaque terms such as “employer pathways”, “project pipelines” and “continuity goals” with concrete explanations of actors, instruments, implementation and effects.
- Replaced the opaque “3+ adults” income-list labels with understandable “other household” labels, added EU-SILC child definitions and concrete examples, widened the form controls, and added option/select tooltips plus a permanently visible explanation for the selected household type.
- Replaced the real-wage chart's descriptive closing sentence with a substantive bilingual interpretation connecting long-run purchasing-power growth, near-stagnation since 2019, Germany's OECD average-wage rank and the distinction between a high national level and uneven household experience.
- Made the Germany Dossier publicly accessible without a login while retaining the complete session-authentication workflow behind the disabled `RC_DOSSIER_ACCESS_PROTECTION` feature flag for possible future modules.
- Eliminated the mixed German/English initial render by applying the curated UI dictionary server-side to visible untagged text nodes, while preserving bilingual spans, official source titles and embedded JSON; the browser module remains responsible for route switching and asynchronously inserted interface text.
- Replaced the income ladder's misleading EVS household-size family labels with six official Destatis EU-SILC 2025 household types. The two-adult/no-child option is shown as “DINKs*” with an explicit warning that the source does not prove two earners.
- Clarified the international wage map with an explicit indicator/unit/baseline/exclusions box, a descriptive title, wage-specific legend labels, clearer country statistics and fully localized popup fields.
- Reworked the Reform Agenda energy chapter after source review: replaced France/Sweden nuclear power as the apparent best-practice case with Denmark and Portugal's renewable-system experience, made reduced exposure to authoritarian fossil suppliers explicit, documented nuclear cost/time/waste/acceptance concerns and treated fusion as post-2040 research rather than 2036 supply.
- Kept all Reform Agenda navigation number markers perfectly circular by preventing flex compression beside longer chapter titles.
- Added British and German flag symbols to both Germany Dossier language controls for faster visual recognition.
- Expanded the entire Germany Dossier into an editorial English/German edition: all four files now use dedicated German data, localized interactive results and B2-level interface copy; the security file also receives a clearer English B2 copy.
- Expanded all eleven Reform Agenda chapters with fuller problem analysis, a 2036 outlook, detailed country-case implementation and results, Germany transfer notes and practical prerequisites; repaired the reform header styling that inherited the global site-header layout and made text unreadable.
- Marked `germany-dossier.php` as an intentional Google Translate exception and added the productive bilingual language module to deployment packaging.
- Converted the three Germany Dossier index cards into an accessible tabbed frame: one dossier file is visible at a time, card changes do not scroll the page, and direct links to nested sections still activate the correct file.
- Renamed the main route from `analysis-real-wages.php` to `germany-dossier.php` so the filename reflects its broader prosperity, scenarios and security scope.
- Added “soldiers are murderers” to the war stress test's serious objections, distinguishing Tucholsky's anti-war warning and protected expression from legal murder, while confronting soldiers' exposure to killing, death, conscience and individual responsibility without romanticising armed forces.
- Replaced the dossier page's flat Germany/Europe/module link row with three dossier-style index cards; grouped the Income Ladder into the prosperity analysis and removed the insufficiently modelled Europe 2036 excursion.
- Expanded the “better red than dead” objection with the asymmetry between rights protected by a democracy and potential coercive service under authoritarian control, using current EUAA and UN evidence while marking the Germany extrapolation as a risk rather than a forecast.
- Made the scenario analysis's normative security position explicit: lawful democratic self-defence may require credible military capability; trade remains useful but “change through trade” is insufficient as a security doctrine; renewable energy, grids, storage and efficiency are presented jointly as security, affordability and environmental policy.
- Clarified that the PPP ranking compares equally weighted countries rather than people or households; replaced the ambiguous “position in distribution” label, made “Adaptation under pressure” the visibly first baseline scenario, added an opening narrative to every Germany 2036 scenario and extended the page jump navigation to all major analysis modules.
- Replaced the clipped circular household marker in the income ladder with a high-contrast, fully labelled pill marker.
- Promoted the Earth Overshoot Day day count to the same large, bold visual hierarchy as the Doomsday Clock status.
- Replaced separate earner and optional household-net fields with one total annual household-gross input; the ladder now shows transparent distance from the official EVS household-size average and no longer claims unsupported family-type percentiles.
- Reframed the downside scenario so democratic backsliding and populist-authoritarian government reinforce economic, European, security and social risks rather than forming an unrelated fourth scenario.
- Converted the dossier page's primary interface and core scenario narratives to English.
- Reframed the dossier page around prosperity, purchasing power and 2036 scenarios; added a global World Bank GDP-per-capita PPP distribution context using the existing project KPI.
- Added annual-change bars to the real-wage chart, an explicit explanation of the 34-country OECD coverage and citizen action cards for resilience, skills, energy and democratic implementation.
- Added “Germany Dossier” to the main menu while retaining `noindex` and sitemap exclusion and keeping the existing general “Analysis” destination distinct.
- Extended deployment packaging for the Germany 2036 scenario browser module and server-side data include.
- Split the wage analysis sources: Destatis real-wage index for Germany's time series, OECD constant-PPP average wages for the international level map.
- Extended deployment packaging for the dossier and documented its structure and security behavior.
- Updated AGENTS.md with controlled deployment bundle generation command.
- Extended SECURITY.md to include FPF 2.0 minimum lifecycle sections.
- Hardened HTTP delivery with HSTS, a restrictive CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy headers.
- Removed inline script allowance from CSP and set Referrer-Policy to strict-origin-when-cross-origin for Mozilla Observatory compliance.
- Documented controlled migration path from deployment/full_deployment and deployment/delta_deployment to build/deployment/full and build/deployment/delta.
- Hardened deployment packaging selector to allowlist-only productive artifacts and robust Windows cleanup behavior.
- Updated compliance report findings and score after validated packaging run.
- Activated build/deployment as primary handover command, keeping legacy mirror as fallback mode.
- Set `index.html` language metadata to `en-US` to match the page's primary language.
- Removed the Apache JS challenge gate so search bots, audits, and assistive technology can reach real HTML pages without JavaScript verification.
- Kept trusted crawler and `webcheck-bot` detection markers in `.htaccess` for audit-friendly future rewrite handling.
- Promoted the countries dashboard to the canonical homepage at `/` and kept `countries.html` as a backward-compatible redirect.
- Updated sitemap, canonical URLs, OpenGraph/Twitter URLs, manifest start URL, and navigation to use the canonical production domain and homepage.
- Confirmed security headers remain active without blocking crawlers, audits, or non-JavaScript accessibility checks.
- Updated deployment packaging to include only productive frontend JavaScript files from `scripts/`.
- Updated the NATO country grouping to include Sweden.

### Fixed
- Restored the standard floating scroll-to-top button on the public Germany Dossier page.
- Replaced the dossier language toggle's Unicode flag emoji, which some Windows fonts rendered as separate country-code letters, with reliable British and German SVG flags.
- Fixed the Germany-at-War closing explanation inheriting white global-footer text on its pale-green background; all closing copy now uses explicit high-contrast dark colours.
- Corrected the Germany-at-War source link for Carlo Masala's *Wenn Russland gewinnt* to the verified C.H.Beck book page and added its ISBN for unambiguous identification.
- Fixed the prosperity dossier heading inheriting the global site-header layout and white text, restoring dark readable copy on the light cluster background.
- Fixed the household selector passing a DOM event into the scenario model, which caused repeated `sensitivity.income` console errors.
- Fixed prepare_deployment.py syntax and cleanup robustness issues that blocked packaging runs.
- Added accessible labels for homepage comparison selectors.


