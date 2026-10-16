# Regional climate frontend correction — 2026-10-14

Status: frontend implemented; browser acceptance and production upload pending.
Base: main 25c0244e735c845f07e6c04e4cbd1f3deac3159c. Related audit: PR #108
(e81f4bbd095523ba91e476cbd96ebea2c0451ea7), documentation-only and still open
when inspected. This change does not incorporate or supersede that audit.

## Evidence and scope

- Current cyclone JSON: 233 records, 1980–2025, six observed basin codes.
- Ocean GeoJSON: seven unique basin codes, valid closed rings with coordinates
  in longitude/latitude bounds. South Pacific is a MultiPolygon split at ±180°;
  neither part crosses the dateline with a >180° segment.
- All available regional observations join to a geometry. North Atlantic (`NA`)
  has no rows in the snapshot. South Atlantic has only sparse observations.
  These gaps remain missing, never zero and never inferred from adjacent years.
- Boundaries are hand-authored rectangular illustrations, not an official NOAA
  polygon product or warning areas. They can overlap (notably NA/EP) and include
  land. No geometric correction is justified by the existing files alone;
  precise basin-boundary sourcing is a separate decision. Their simplification
  and non-official nature are now visible in the map legend.
- The registry also contains IPCC reference-region and river-basin GeoJSON.
  These parse as FeatureCollections; hazard datasets for wildfire/flood/heat/
  drought are not connected. No hazard layer or country fallback is invented.

## Corrections

- Replaced stale region/country-fallback wording and the country-only metric label.
- Regional-only World cards explain that a global series is absent while regional
  data are usable, retain the measurement-source link and link to the map.
- Regional year/value helpers reject null, blank and non-finite inputs. Zero is valid.
- Selected-year coverage, missing region names, unmapped values and unsupported
  country/per-capita/summary modes are separate states.
- Colour semantics disclose relative within-year percentile ranking; colours do
  not imply risk classes or an absolute scale comparable across years.
- Tooltips show name/code, metric, value/missing state, year and measurement source.
  Dataset-derived markup is escaped. Hover does not make missing regions look filled.
- Legend separates measurement source from geometry attribution/license and notes
  the unreviewed count definition. Frontend cyclone units use neutral wording;
  stored metadata, counting implementation and generated data are unchanged.
- Unconnected categories clear previous data/year/legend; async request guards
  prevent outdated KPI or geometry responses from restoring a previous selection.
- Cache versions bumped for World JS/CSS. No SEO route/security policy change.

## Validation

Passed:

- 32 JavaScript tests, including 11 regional tests. Renderer/selection tests use
  a small DOM and Leaflet boundary simulation, not an actual browser engine.
- 82 Python tests, including page asset smoke and deployment packaging tests.
- `scripts/validation.py --no-log`: all required snapshots parse and are non-empty.
- Node syntax, git diff whitespace check, FPF apache-shared-hosting production baseline.

Incomplete:

- Complete shared `scripts/run_tests.py` cannot finish here: PHP executable absent.
- Local Chromium installation failed because the browser archive download was
  invalid/truncated. No local screenshot-based acceptance is claimed.
- Production browser opened the existing page and showed the previous labels,
  but the operation stalled for over an hour and did not validate interactive
  polygon/tooltip/legend behavior. Production has not been modified.

Required browser acceptance before marking ready:

1. Serve locally; open Storm Impact via UI and regional card link, desktop/mobile.
2. Confirm all seven polygon features and both South Pacific parts; inspect
   tooltips for EP and missing NA, plus missing SA in 1980 and observed SA in 2004.
3. Switch 1980/2004/2025; compare displayed values to JSON, coverage to geometry,
   year to shared URL and verify legend/source links and disabled summary modes.
4. Switch rapidly between storm, placeholder, country climate and country groups;
   confirm no stale year, old layer or misleading country legend remains.
5. Verify mobile wrapping and actual colour/grey swatches; rerun after FTP upload.

## Deployment and rollback

A delta deployment needs only world.html, scripts/script_world.js and style.css.
Full and delta handover folders are generated locally below build/deployment;
no FTP upload is authorized or performed by this PR. Rollback restores these
three frontend files together. Tests/docs are excluded from productive packaging.

## Lesson learned / framework candidate

Maps must model dataset geography separately from missing global observations,
missing regional observations and unsupported views. Null-to-zero coercion and
out-of-order responses need explicit regression cases. Candidate for reuse:
require scope/coverage/provenance/async selection tests in data-map acceptance
checklists. No framework files or other repositories are changed.
