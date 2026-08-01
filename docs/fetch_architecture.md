# Fetch Core Architecture

The fetch pipeline keeps its existing command line and generated file formats,
but source orchestration is now split into explicit layers.

```text
available_kpis.json
        |
        v
source_contracts.py  -- validates and selects KPI metadata
        |
        v
fetch_core.py        -- plans adapter mode, dispatches, resolves status/force policy
        |
        v
builtin_adapters.py  -- registers concrete source modules
        |
        v
adapters/*.py        -- downloads and normalizes one source family each
        |
        v
fetch_data.py        -- CLI, persistence, status and post-processing
```

## Stable contracts

- `SourceAdapter` declares one source type, execution mode, optional source-date
  resolver and immediate handler.
- `AdapterRequest` carries all run-scoped metadata, mappings, statistics and
  the requested output directory.
- `AdapterResult` returns source date, data year and record count consistently.
- `AdapterRegistry.ensure_complete()` blocks startup unless every allowed
  source type has exactly one registered adapter.
- `build_status_entry()` preserves last-known metadata without allowing an
  adapter to mutate historical status implicitly.

`IMMEDIATE` adapters run per KPI. `BATCH` adapters, currently IMF, are queued
for their shared import. `SPECIAL` adapters, currently the geopolitical-risk
series, run only when that source was actually selected. A single-KPI run no
longer triggers unrelated special-source work.

## Adapter boundary

Every source-specific HTTP client and parser lives in `scripts/adapters/`:

- `worldbank.py` handles API requests and ZIP fallback.
- `owid.py` handles metadata, Grapher CSV payloads and the official indicator
  API used when a Grapher export omits still-published projection years.
- `noaa.py` annualizes NOAA's current multi-mission satellite sea-level CSV
  while averaging overlapping mission observations during handovers.
- `data360.py` handles paginated API data and maintained CSV fallback.
- `csv_source.py` handles local maintained CSV files and isolated hashes.
- `unhcr.py` handles plain and zipped population CSV payloads plus the global
  forced-displacement total assembled from non-overlapping official API groups.
- `imf.py` handles the shared IMF DataMapper batch.
- `special.py` handles the world-level geopolitical-risk workbook.

`SourceRuntime` injects mapping, persistence, logging and output paths. This
keeps adapters independently testable without network access and prevents a
test adapter from selecting productive paths implicitly. `fetch_data.py` no
longer contains legacy source clients.

Known provider-side redistribution blocks are declared with
`fetch_policy: "provider_restricted"`. They produce a visible non-error skip
and preserve the last known-good dataset; this policy is contract-validated
instead of being hidden in source-specific exception handling.

Optional, contract-validated source metadata controls exceptional provider
behaviour without adding KPI-specific orchestration code:

- `refresh_hours` throttles sources that do not expose reliable update dates;
  `--force` always bypasses the interval.
- `fallback_file` lets an adapter compare a maintained source snapshot with
  the live result and use whichever has the newer usable year.
- `owid_variable_id` selects OWID's official indicator API when its compact
  data payload is more complete than the public Grapher CSV.
- `owid_value_column`, `owid_sum_columns`, `owid_time_column` and
  `owid_aggregation` select, combine and annualize multi-column or sub-annual
  Grapher data without KPI-specific orchestration.

Persistence applies the same safety rules to every adapter: non-finite values
are discarded, observations outside 1900 through the current year are trimmed,
and an incoming snapshot cannot replace stored data with an older latest year.

New source definitions can use `publication_status: pending_first_fetch`.
They remain fetchable but are excluded from browser metadata consumers,
consolidation, rankings, analysis and required-snapshot validation while both
productive JSON and CSV artifacts are absent. After a successful fetch,
`promote_ready_kpis.py` verifies both formats and atomically removes the pending
marker before downstream generation. This prevents a source registration from
publishing an empty selector or breaking the last known-good site.

The following remain unchanged:

- `python scripts/fetch_data.py` and all existing switches
- JSON/CSV dataset schemas and filenames
- `data/fetch_status.json` structure
- test output under `data/test/`
- analysis, consolidation and deployment handover paths

## Maintained CSV source audit

The twelve `source_type: csv` KPIs are local, reviewed inputs rather than
download adapters. This includes both `olympic_medals_summer` and
`olympic_medals_winter`. Their acquisition contracts live in
`data/meta/manual_csv_sources.json`.

`python scripts/check_source_csv_updates.py` performs an offline audit of file
existence, the canonical `country,year,value` schema, row count, latest year,
SHA-256 checksum and modification time. `--online` additionally requests only
the official URLs whose source-specific release-year patterns have been
reviewed in that contract. It does not discover sources, use an AI model,
authenticate, scrape gated downloads, download datasets or replace local CSVs.
The ignored report `data/manual_source_status.json` is therefore a notification
and provenance aid, not an ingestion step.

Sources delivered by e-mail, assembled manually, requiring registration or
lacking a stable official endpoint remain explicit manual-review items. A
release-year match is only evidence that a new edition may exist; schema,
definition, licence and normalization still require human review before import.

## Adding a source type

1. Add the source type and metadata requirements to `source_contracts.py`.
2. Implement the handler in a dedicated `scripts/adapters/` module. It must
   accept `AdapterRequest`, use the injected `SourceRuntime` and return
   `AdapterResult`.
3. Register its execution mode in `build_builtin_adapter_registry()`.
4. Add a small mocked adapter test; network calls are not permitted in CI.
5. Run `python scripts/run_tests.py` and then an explicitly selected live smoke
   test outside pull-request CI.

Registry completeness intentionally fails until all these steps agree, so an
accepted metadata type cannot silently fall into a dummy or unknown-source
branch.
