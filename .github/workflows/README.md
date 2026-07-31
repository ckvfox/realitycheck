# RealityCheck GitHub Actions

The workflows cover offline CI, source refreshes, validated deployment packaging and FTP handover.

## Safety model

- External actions are pinned to immutable commit SHAs.
- Fetch workflows share the `realitycheck-data-pipeline` concurrency group, so two refreshes cannot write or deploy data simultaneously.
- FTP-only workflows share the `realitycheck-production-deploy` concurrency group.
- Fetch errors, dummy datasets, empty test selections and validation errors return non-zero exit codes and stop all later steps.
- Force mode refetches data but never deletes the last known-good snapshot first.
- Full and partial uploads are sourced from the allowlisted `build/deployment/full/` package.
- Full upload is non-destructive; obsolete remote files require an explicit, separately reviewed cleanup.

## Workflows

### `ci.yml`

Runs for pull requests and pushes to `main`:

- Python compilation and pipeline safety unit tests
- committed data-snapshot validation
- JavaScript tests
- PHP lint and PHP data/auth tests

CI never calls external data sources, OpenAI or FTP.

### Fetch workflows

- `monthly-fetch.yml`: scheduled full refresh on the first day of each month
- `manual-fetch.yml`: manual full refresh with analyses
- `manual-fetch-fast.yml`: manual refresh without AI analysis
- `manual-fetch-force.yml`: forced source refresh while preserving existing files until replacements succeed
- `manual-fetch-force-fast.yml`: forced refresh without AI analysis
- `manual-fetch-test.yml`: isolated two-KPI adapter test using `--test`; writes only to `data/test/` and never deploys

Every production fetch must pass the pipeline guard and final data validation before FTP and Git push can run.

### FTP workflows

- `manual-ftp-full.yml`: validates data, builds the productive allowlist and uploads the complete package without remote clean-slate deletion
- `manual-ftp-sync.yml`: validates the committed data snapshot and synchronizes productive `/data/` files
- `manual-partial-upload.yml`: accepts comma-separated productive paths, rejects traversal/absolute paths and uploads only files present in the generated deployment allowlist

Example partial input:

```text
germany-dossier.php,data/overall_ranking.json
```

Logs, Markdown, Python, CSV sources and other non-productive files cannot be selected for partial deployment.

## Required secrets

| Secret | Used for |
|---|---|
| `OPENAI_API_KEY` | Optional analysis/ranking stages in fetch workflows |
| `FTP_SERVER` | FTPS server |
| `FTP_USERNAME` | FTPS account |
| `FTP_PASSWORD` | FTPS password |
| `FTP_DIR` | Productive server root |

Status details and logs remain available in the GitHub Actions run and uploaded artifacts.

Last reviewed: 2026-07-31.
