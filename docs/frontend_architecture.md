# Frontend Architecture

RealityCheck keeps its no-bundler shared-hosting structure while limiting the
amount of data and work required for the first useful view.

## Loading strategy

- `core.js` owns `loadJSON()`, `loadKPIData()` and `loadAllKPIData()`.
- `loadJSON()` deduplicates identical requests for the lifetime of a page and
  uses HTTP revalidation rather than a unique timestamp on every request.
- The Countries dashboard loads metadata in parallel and then fetches only the
  selected KPI. Population, GDP and area datasets are lazy relation inputs.
- The World dashboard fetches only KPIs marked `world_kpi: y` or `world_kpi: e`.
- The Overall Ranking intentionally keeps the split consolidated dataset
  because it calculates across many KPIs. Its five gzip parts load in parallel,
  use native `DecompressionStream` where available and retain Pako/plain-text
  compatibility for shared-hosting response differences.
- Overall scores use direction-aware percentile ranks, target-distance scoring,
  relevance weights and weighted data coverage. Aggregate regions and global
  series cannot enter the country table.

KPI identifiers are restricted to `[a-z0-9_]+` before they become data paths.
Each KPI selection is reflected in `?kpi=<filename>`, so a view can be shared or
reloaded without downloading unrelated datasets first.

## Interaction and accessibility contracts

- Dynamic pages expose loading changes through polite live regions.
- Sortable table headings support click, Enter and Space and update
  `aria-sort`.
- `core.js` inserts one skip link targeting the first main content region.
- All interactive controls receive a visible keyboard focus indicator and a
  minimum touch target height.
- The scroll-to-top button stays outside keyboard navigation until the visitor
  has scrolled, and smooth motion is disabled when reduced motion is requested.
- Mobile navigation remains a single horizontally scrollable row so link text
  and touch targets are not compressed.

## Extension rules

Use `loadKPIData(filename)` for a page that needs one or a few datasets. Use
`loadAllKPIData()` only when the feature genuinely calculates across many
indicators. Independent resources should be requested with `Promise.all()`.
Do not add timestamp cache busters; update the shared asset version for code
releases and let JSON requests revalidate normally.

Run `python scripts/run_tests.py` before packaging. The public-page smoke tests
also assert the demand-driven loading and accessibility markup contracts.
