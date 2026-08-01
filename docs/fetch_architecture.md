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
builtin_adapters.py  -- registers and normalizes built-in source adapters
        |
        v
fetch_data.py        -- CLI, legacy source clients, persistence and post-processing
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

## Compatibility boundary

The existing World Bank, OWID, CSV, UNHCR and IMF client functions remain in
`fetch_data.py` for this migration step. `AdapterServices` injects them into
the built-in adapters, avoiding circular imports and allowing them to move
into individual modules later without changing the orchestrator or CLI.

The following remain unchanged:

- `python scripts/fetch_data.py` and all existing switches
- JSON/CSV dataset schemas and filenames
- `data/fetch_status.json` structure
- test output under `data/test/`
- analysis, consolidation and deployment handover paths

## Adding a source type

1. Add the source type and metadata requirements to `source_contracts.py`.
2. Implement the handler in `builtin_adapters.py` or a dedicated adapter
   module. It must accept `AdapterRequest` and return `AdapterResult`.
3. Register its execution mode in `build_builtin_adapter_registry()`.
4. Add a small mocked adapter test; network calls are not permitted in CI.
5. Run `python scripts/run_tests.py` and then an explicitly selected live smoke
   test outside pull-request CI.

Registry completeness intentionally fails until all these steps agree, so an
accepted metadata type cannot silently fall into a dummy or unknown-source
branch.
