# Offline Test Baseline

The complete local and CI baseline is started from the repository root with:

```text
python scripts/run_tests.py
```

The runner is deliberately network-free. It compiles Python, discovers every
`tests/test_*.py` module, validates the committed production snapshot without
changing its validation log, executes all Node tests, lints non-restricted PHP
sources and runs all PHP assertion tests. A missing runtime or any failed check
returns a non-zero exit code.

## Coverage gates

- pipeline publication guards and last-known-good behavior
- KPI source metadata contracts and production/test selection
- World Bank, OWID, CSV, Data360, UNHCR, IMF and special-source adapter contracts
- requested-directory isolation for generated datasets and local CSV hashes
- country and numeric normalization, inversion and year trimming
- generated JSON/CSV format validation
- productive deployment allowlist and delta detection
- local asset references on the six key public pages
- existing dossier JavaScript and PHP data contracts

## Adding a KPI to an existing source type

1. Add the entry to `data/meta/available_kpis.json` with a unique lowercase
   underscore `filename`, a supported `source_type` and a non-empty
   `source_code`.
2. Use only an empty `test` value, `*` for isolated adapter smoke testing or
   `o` to disable the entry.
3. Add or extend a small fixture under `tests/fixtures/` when the metadata or
   payload shape introduces a new edge case.
4. Run `python scripts/run_tests.py` before starting a network fetch.
5. Run `python scripts/fetch_data.py --test` only for explicitly starred KPIs;
   its datasets, status, pending mappings, hashes and logs stay under
   `data/test/`.

## Adding a new source type

First register the type and its metadata requirements in
`scripts/source_contracts.py`. Then implement an `AdapterRequest` to
`AdapterResult` handler in a dedicated `scripts/adapters/` module and register
it in `scripts/builtin_adapters.py`. Add a network-free test that mocks the remote response and
proves normalized output plus requested-directory isolation. Registry
completeness blocks the run until contract and adapter agree. Live API
availability is a separate smoke test and must not be required by pull-request
CI. See `docs/fetch_architecture.md` for the complete boundary.
