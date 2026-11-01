# IBTrACS PR #110 reconciliation — 2026-11-01

## Verified baseline

Main e5ef6fe4ede25f5d964b5e460c7d059e3a5fecb3 contains 279 JSON/CSV records: six basins with 46 seasons each (1980–2025), plus SA 2004/2010/2011. November run 41267571050 completed successfully, including its existing FTPS step; status issue #111 records completion. No new fetch or manual upload is needed.

## Existing work retained

Commit 03cdd1e already preserves NA with keep_default_na=False. Current main additionally trims identifiers, rejects unknown basins/blank SID, deduplicates SID/BASIN/SEASON, excludes incomplete years and tests NA/deduplication. Current data CSV matches PR #110 exactly. The October 30 climate changes already clarify basin series, unnamed systems, missing observations and non-global counting; the old frontend/metadata diff must not replace that newer implementation.

PR #110 predates allowlisted packaging and fixed-webroot FTPS. Its workflow file must not replace current main. Its historical report describes an earlier source comparison, not a new verification of NOAA today.

## Remaining changes

- Add PR's isolated regressions for whitespace/missing keys, all seven basin codes, season filtering, output routing and empty-input last-known-good fallback, without replacing the current adapter.
- Adapt verify_ibtracs.py into a read-only, network-free JSON/CSV validator. The former generator's independent raw-source reconciliation is useful for a future reviewed definition change but is unnecessary for this publication guard; no regeneration side effects are retained.
- Require all 279 verified historical keys, unique basin/seasons, valid completed years, positive finite integer counts and historical scenario metadata. Preserve sparse SA rather than inventing zeros. Values may legitimately be revised; additional observed keys are allowed.
- Run parsing regressions before monthly fetch. Run snapshot gate before packaging, upload and data commit in monthly and all four productive manual-fetch workflows. Existing complete CI/auto-deploy suite discovers the same tests automatically.
- Negative tests cover total NA loss even with matching CSV, loss of a sparse SA season, duplicates, invalid counts and JSON/CSV disagreement. Workflow-order tests prevent removal or late execution of the gate.

## Validation and limitations

Targeted offline tests and FPF production baseline pass. Full Python suite and remote CI are recorded in the replacement PR. Data files are byte-for-byte unchanged from the November main snapshot. No source download, fetch workflow dispatch or manual FTP upload is performed.

Coverage guards detect historical key loss, not every scientifically incorrect count with unchanged keys. NOAA value revisions remain allowed and require source review when suspicious. Existing main auto-deployment tests the production snapshot before FTPS; merging follows its established guarded process.

No frontend, sitemap, robots, security policy or deployment package contents changed. No browser acceptance is needed for this backend/test-only scope.

Framework candidate: shared source-specific historical-key guards before publication, separately from general schema validation and source freshness checks.
