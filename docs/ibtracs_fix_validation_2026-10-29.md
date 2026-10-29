# IBTrACS import correction and source reconciliation — 2026-10-29

## Result and scope

Candidate based on main `55c945474e2b1fc7ab4c290706d14bf8c946f558`. The adapter now preserves NOAA basin `NA`, treats empty CSV cells and whitespace-only SID/BASIN as missing, and continues coercing missing/nonnumeric SEASON to missing before dropping incomplete keys. NOAA uses empty text fields; no inferred named-storm, intensity or nature filter was added. Repeated track observations count once per SID/BASIN/SEASON.

279 historical records replace 233: 46 North Atlantic seasons are restored. All 279 adapter aggregates equal an independent Python stdlib csv.DictReader/set/Counter enumeration of the original NOAA observations, without pandas. JSON/CSV round-trip equality, unique basin-season keys and positive integer values pass. No missing season is filled with zero.

## Source provenance

- URL: https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.since1980.list.v04r01.csv
- Retrieved on 2026-10-29; response HTTP 200, Last-Modified `Thu, 29 Oct 2026 09:02:17 GMT`, ETag `"8a852c6-65ef6efc0a6d9"`.
- Bytes: 145,248,966; observation rows excluding header/units: 312,134.
- SHA-256: `54b9e0cca66f9a019818d1b2452a84355ba4fd224149c8e440765ea2db9d5b11`.
- SEASON >= 2026 is excluded, matching the existing completed-season-label policy. This policy is not proof of final NOAA revisions or calendar-year completeness, especially in the Southern Hemisphere.

| Basin | Rows | Season labels | Sum of storm/basin/seasons | Added rows | Revised existing rows | Latest count |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| EP | 46 | 1980–2025 | 1136 | 0 | 1 | 29 |
| NA | 46 | 1980–2025 | 743 | 46 | 0 | 13 |
| NI | 46 | 1980–2025 | 471 | 0 | 0 | 17 |
| SA | 3 | 2004, 2010, 2011 | 3 | 0 | 0 | 1 |
| SI | 46 | 1980–2025 | 893 | 0 | 0 | 24 |
| SP | 46 | 1980–2025 | 535 | 0 | 0 | 11 |
| WP | 46 | 1980–2025 | 1507 | 0 | 1 | 36 |

The only changes to previously present values are EP/2025 28 → 29 and WP/2025 34 → 36, reproduced by both aggregators from the current NOAA release. No existing keys are removed. NI, SI, SP and SA are unchanged. SA remains sparse (2004, 2010, 2011); absent seasons remain unknown rather than verified zero activity. These sums are not unique global storm totals because cross-basin storms count in each basin.

## Definition correction

The previous “named storms per year” claim was false for this implementation: only SID, BASIN and SEASON are read. Metadata and visible World category/metric text now say recorded storms per basin-season, explicitly disclosing no name/intensity filter, NOAA season labels, cross-basin duplication and the absence of damage/landfall measurement. The internal KPI ID and `storm_impact` route key remain stable. This change does not choose a new scientific cyclone definition or infer calendar-year semantics. The synthetic source_date remains unchanged and must not be interpreted as a NOAA release timestamp.

## Reproduction and publication boundary

Download the official source to an external working location, retain its response headers, then run from the repository root:

```sh
.venv/bin/python scripts/verify_ibtracs.py /path/to/ibtracs.csv --output-dir /tmp/ibtracs-verified
.venv/bin/python -m unittest discover -s tests -p test_builtin_adapters.py -v
.venv/bin/python -m unittest discover -s tests -p test_ibtracs_snapshot.py -v
```

The verification script writes only to the explicitly selected output directory after all raw-source aggregate comparisons pass. The committed JSON and CSV were copied from that validated output. It does not run fetch_data.py, AI analysis or FTP; fetch-status timestamps are deliberately not fabricated. The NOAA raw download is not committed (139 MiB); its checksum identifies this exact validation input. Later downloads may contain revisions.

The next scheduled monthly job is November 1, 2026 at 03:00 UTC (04:00 Europe/Berlin). This PR adds the mocked adapter regression gate before fetch and a historical coverage/JSON-CSV gate after fetch and before FTP. The latter protects the verified 1980–2025 coverage in six basins while allowing later seasons and leaving SA sparse. These gates are limited semantic checks, not independent scientific validation of every future NOAA revision. They become effective only after merge to main. No schedule was changed and no workflow was manually dispatched.

## Validation

- Targeted adapter tests and persisted snapshot gate: pass.
- Full Python discovery: 92 tests pass.
- Node tests: 21 pass.
- Committed snapshot validation: pass.
- FPF production baseline: pass.
- Full shared runner cannot start locally because PHP is not installed; no PHP code was changed. The PR CI must run the complete runner including PHP before merge.
- No production FTP upload, merge or live map acceptance performed. UI changes are wording/cache version only; basin polygon/tooltip rendering and deployed parity remain separate acceptance work.

## Reusable lesson

Provider category codes can collide with parser missing-value defaults even when dtype=str. Define source-specific missing-value policy and test a valid sentinel-like code plus empty keys. Pair parser tests with historical coverage gates: a successful HTTP/save status cannot detect silently dropped categories.
