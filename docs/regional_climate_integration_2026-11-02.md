# PR #109 integration — 2026-11-02

Status: integrated and locally regression-tested; keep Draft pending full CI and real desktop/mobile browser acceptance. No merge into main or production upload.

## Compared revisions and actual conflicts

PR head: `360b11ca5b8b2ec338229989689e654adfab830b` (two feature commits).
Main: `3bd4a37cee31b293030bdcbba5df2603af52def3` (25 commits ahead).
A real `git merge --no-commit --no-ff origin/main` produced conflicts in:

| File | Conflict and resolution |
| --- | --- |
| CHANGELOG.md | Concurrent additions; preserve both histories, update obsolete frontend assumptions. |
| README.md | Regional status versus security/deployment documentation; retain both, describe current marker/color behavior. |
| TODO.md | Original outstanding parser work versus completed reconciliation/deployment work; retain completed work and current visual acceptance requirement. |
| world.html | Cache versions, geography label, legend element identity and script imports; retain current core/environment scripts and scale-note ID, add PR legend IDs and fresh cache versions. |
| scripts/script_world.js | Cyclone definition, value validation, renderer/legend and exports; retain main season semantics, regional charts, circle markers, exact-count table and environmental colors; add coverage/provenance, escaped tooltip content, missing-value guards and async request invalidation. |

`style.css` auto-merged cleanly; overlap alone was not a conflict. Other files merged automatically. No whole-file replacement from the old branch was used to resolve runtime conflicts.

## Preserved current behavior and protected files

- All files under data/, scripts/adapters/ and .github/workflows/ match main byte-for-byte; deploy_ftps.py and prepare_deployment.py also remain unchanged.
- 279 committed cyclone observations, including exactly 46 NA seasons covering 1980–2025. No data regeneration or live NOAA fetch.
- Recorded systems include unnamed systems; cross-basin systems count in each basin, so basin counts are not a unique global total. Southern Hemisphere seasons use July–June and the ending year. Units come from current KPI metadata.
- Main's seven separate regional chart series, basin locator circles, count table and environmental scale remain. Circle locations are not storm tracks, footprints or official boundaries.
- Active country wildfire, flood, heat and drought categories remain active; the placeholder regression uses a synthetic unconnected category, rather than reverting these new datasets.
- Current FTPS allowlist, validation gates, encrypted transfers, size/hash checks, staging recovery and deployment concurrency are inherited without modification.

## Verification

- `node --test tests/*.test.js`: 40 passing tests, including 13 regional tests. Current NA series, gaps, marker/table retention, source attribution, season definitions, active country hazards, invalid inputs and async races are covered.
- `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`: 137 tests passed, including IBTrACS parser/publication gates and FTPS/deployment regressions. Dependencies installed from requirements.txt in the repository venv.
- `.venv/bin/python scripts/validation.py --no-log`: passed.
- Node syntax and `git diff --check`: passed.
- FPF apache-shared-hosting production baseline: passed.
- Local package generation succeeded (385 productive files). Default delta selection had no previous local deployment manifest and therefore selected the complete package; it is not a validated three-file upload delta. No package was uploaded.
- Complete `scripts/run_tests.py` stops at its prerequisite check because PHP is unavailable locally. GitHub CI must run the complete PHP-inclusive baseline.
- The original CodeQL hostname warning was already fixed by `360b11c`: `/www\.ncei\.noaa\.gov/`. GitHub reports the review thread resolved/outdated and all six checks for that original head successful, including CodeQL. Fresh checks are still required for the integration commit.

## Browser acceptance remains open

The Browser skill was followed; no extension control tool was exposed, so the cloud browser fallback was attempted against a locally served world.html. It returned `Missing or invalid bearer token` instead of the local site. This browser cannot currently reach the workspace server. No visual acceptance is claimed; DOM/Leaflet test simulations do not replace it.

Before Ready for review: serve the integrated branch in a reachable browser; inspect desktop and mobile. Verify seven basin circles/table, NA in 1980/2004/2025, missing SA versus observed SA (2004), exact values against JSON, relative environmental colors and grey missing states, sources, tooltips, URL/year synchronization, disabled regional summaries, regional chart series and rapid switching to active country hazards/groups. Check wrapping/overflow and source links. After an independently authorized deployment, verify live behavior separately.

## Review and rollback

The feature branch update is a non-rewriting merge with main as second parent. Only three productive frontend files differ from main: world.html, scripts/script_world.js and style.css. Rollback of these frontend changes must restore those three files together from the current main baseline; never restore old data, adapters, workflows or KPI definitions. README, TODO, changelog and historical PR evidence were reconciled; AGENTS, SECURITY, robots and sitemap require no functional changes.

Framework candidate: integration tests must protect current data completeness, definitions, active categories and rendering semantics, rather than retaining obsolete assertions from a formerly correct feature branch.
