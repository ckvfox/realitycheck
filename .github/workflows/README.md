# RealityCheck GitHub Actions

The workflows cover offline CI, source refreshes, validated deployment packaging and FTP handover.

## Safety model

- External actions are pinned to immutable commit SHAs.
- Fetch workflows share the `realitycheck-data-pipeline` concurrency group, so two refreshes cannot write or deploy data simultaneously.
- Automatic and manual FTP workflows use the same `realitycheck-data-pipeline` concurrency group as production fetches. Only one production writer runs at a time.
- Fetch errors, dummy datasets, empty test selections and validation errors return non-zero exit codes and stop all later steps.
- Force mode refetches data but never deletes the last known-good snapshot first.
- Full and partial uploads are sourced from the allowlisted `build/deployment/full/` package.
- Full upload is non-destructive; obsolete remote files require an explicit, separately reviewed cleanup.

## Workflows

### `ci.yml`

Runs for pull requests and pushes to `main`:

- pinned Python dependency installation
- Python compilation, source-contract, fetch-isolation and deployment unit tests
- committed data-snapshot validation
- key-page local asset smoke tests
- JavaScript tests
- PHP lint and PHP data/auth tests

CI calls `python scripts/run_tests.py`, the same entry point used locally. It
never calls external data sources, OpenAI or FTP and does not update the
committed validation log.

### Fetch workflows

- `monthly-fetch.yml`: scheduled full refresh on the first day of each month at 03:00 UTC, followed by validation, safe `/data` FTPS synchronization and a data commit
- `manual-fetch.yml`: manual full refresh with analyses
- `manual-fetch-fast.yml`: manual refresh without AI analysis
- `manual-fetch-force.yml`: forced source refresh while preserving existing files until replacements succeed
- `manual-fetch-force-fast.yml`: forced refresh without AI analysis
- `manual-fetch-test.yml`: isolated two-KPI adapter test using `--test`; writes only to `data/test/` and never deploys

Every production fetch must pass the pipeline guard and final data validation before FTP and Git push can run.

The normal monthly selection includes `tropical_cyclone_activity_basin`,
`wildfire_burned_area`, `flood_affected_people`, `extreme_heat_days` and
`drought_spei`. NOAA is checked each run; the OWID sources retain their complete
chart query when checking release dates, and World Bank ESG source 75 has a
separate release-date cache from WDI source 2. Unchanged provider releases may
be skipped; failed replacements preserve the existing snapshot and block
publication. Partial-year exclusion and country-identity guards remain active.
The full pipeline promotes ready sources, rebuilds consolidated bundles and
validates data before uploading JSON/gzip files. These contracts are covered by
`tests/test_monthly_climate_refresh.py` and the adapter regressions in CI.

The monthly FTPS destination is explicitly
`/realitycheck.great-site.net/htdocs/data/`, matching the verified domain webroot.
All production workflows now use the same strict package allowlist and fixed
webroot; `FTP_DIR` is no longer used. Monthly/manual fetches build the package
then invoke `scripts/deploy_ftps.py --scope data`. The filtered data selection
includes registered climate JSONs, public analysis, metadata and indexed gzip
bundles. Frontend changes are published by the separate main-push deployment.
Data and partial uploads use separate checkpoints; all transport modes verify
TLS and uploaded sizes and never delete remote files.

The monthly workflow also checks the configured official release pages for
maintained CSV sources. This is notification-only and never replaces a local
CSV. Its shell pipeline uses `pipefail`, so writing the console output through
`tee` cannot hide a failing fetcher exit code.

### Monthly result and diagnostics

The monthly run provides three levels of feedback on both success and failure:

1. The Actions job summary shows workflow status, fetch time, updated/skipped/error counts, manual CSV hints and every updated KPI with its latest data year.
2. A 30-day `realitycheck-fetch-diagnostics-<run-id>` artifact contains the complete fetch console output, `fetch_log.txt`, `fetch_status.json`, `fetch_state.json`, `validation_log.txt` and the manual-source audit when available. Its upload uses `if: always()`, so a failed fetch does not suppress the evidence.
3. The workflow creates a GitHub issue with the final job status, run link and artifact name. The Actions run itself retains the verbose FTP client log.

A fetch, analysis or validation error stops FTP and Git push. An FTP error
leaves the generated diagnostics and issue available but prevents the later
data commit. The scheduled workflow deploys productive data only; frontend or
backend code changes require a reviewed full or partial FTP workflow.

### FTP workflows

- `auto-deploy.yml`: automatically runs on pushes to `main`, or manually on `main` with optional `force`. After acquiring the production lock it checks out the latest `main`, so a queued push cannot deploy an older snapshot over a completed monthly data update. It runs the complete offline test suite and FPF production baseline on that exact checkout, prepares the existing full allowlist and uploads to `/realitycheck.great-site.net/htdocs` with `scripts/deploy_ftps.py`. It never executes data fetches or AI analysis.

The automatic uploader uses `FTP_SERVER`, `FTP_USERNAME` and `FTP_PASSWORD`
only at the upload step. It verifies TLS certificates and encrypts data
connections. The first successful run uploads the whole productive package;
later runs compare SHA-256/size entries in `.realitycheck-auto-deploy.json` and
check remote sizes before skipping unchanged files. The checkpoint is written
only after all uploads and size checks pass. Transient connection failures
receive up to three bounded reconnects, retaining already size-verified files
in memory for the same run. Persistent failures stop the run; rerunning
retries unfinished changes. No files are deleted, including obsolete managed
files and server-owned state. Manual deletion remains a separate action.

The run summary records status, tested commit and fixed destination. A
30-day artifact stores the successful upload receipt (changed paths, counts,
commit and destination, without credentials). `force` re-uploads the complete
allowlist, useful after manual server edits that are invisible to the hash
checkpoint. Adding a manual FTP upload does not update that checkpoint.

GitHub does not start another push workflow for commits created with its
`GITHUB_TOKEN`; monthly fetches already publish their own data directly. Pull
requests and feature branches never receive this automatic production upload.
CI failures prevent upload, and test secrets are not required.

Live acceptance on 2026-10-30: [run 41084172389](https://github.com/ckvfox/realitycheck/actions/runs/41084172389)
passed the full suite and FPF baseline and uploaded all 456 tracked productive
files to the verified webroot with zero deletions. Its receipt identifies
tested commit `0f238a336ab8f85a126b51af5a25b3ec660ec5c6`. The upload file set was
compared with Git's productive allowlist: no untracked or missing paths.
The earlier first attempt timed out; bounded reconnects are regression-tested.

Reusable transport: `scripts/deploy_ftps.py` also exposes `publish_package` for
other static sites. Callers supply their independently validated package,
fixed site root and separate checkpoint name; the RealityCheck CLI defaults
remain unchanged. EnergyPlanning consumes this API through a pinned sparse
checkout rather than maintaining a duplicate FTP implementation. Framework
candidate: shared certificate-verified transport with project-owned allowlists.

- `manual-ftp-full.yml`: validates data, builds the productive allowlist and uploads the complete package without remote clean-slate deletion
- `manual-ftp-sync.yml`: validates the committed data snapshot and synchronizes productive `/data/` files
- `manual-partial-upload.yml`: accepts comma-separated productive paths, rejects traversal/absolute paths and uploads only files present in the generated deployment allowlist

Example partial input:

```text
germany-dossier.php,data/kpi_analysis.json
```

Logs, documentation, Python, CSV sources and unregistered files cannot be selected for partial deployment. The public `data/analysis.md` is an explicit exception.

## Required secrets

| Secret | Used for |
|---|---|
| `OPENAI_API_KEY` | Optional analysis/ranking stages in fetch workflows |
| `FTP_SERVER` | FTPS server |
| `FTP_USERNAME` | FTPS account |
| `FTP_PASSWORD` | FTPS password |

Status details and logs remain available in the GitHub Actions run and uploaded artifacts.

Last reviewed: 2026-10-30.

Payload audit on 2026-10-30 tightened the historical 456-file set to 386 files:
eight backend data artifacts, six unused image variants and 56 unreferenced flags
are no longer selected. Existing remote files remain untouched. Details and
limitations: `docs/deployment_payload_audit_2026-10-30.md`.
