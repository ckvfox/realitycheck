# Deployment Runbook

## Goal

Generate reproducible full and delta deployment bundles in framework-aligned target folders as primary handover path.

## Commands

Run from repository root:

- Validate the current data snapshot before every production package:
  - python scripts/validation.py

- Full and delta (primary):
  - python scripts/prepare_deployment.py --mode both
- Full only:
  - python scripts/prepare_deployment.py --mode full
- Delta only:
  - python scripts/prepare_deployment.py --mode delta

## Output Folders

- Framework target full: build/deployment/full/
- Framework target delta: build/deployment/delta/

## Safety Rules

- A failed fetch, dummy result or validation error blocks packaging and FTP deployment.
- Force fetches preserve the last known-good files until valid replacements are available.
- Target folders are cleared before each run.
- Only productive web artifacts are included via allowlist.
- Governance documentation, scripts and secret-bearing files are excluded.
- Server-owned `tracking.json` counter state is excluded so FTP uploads cannot reset live visits.
- Full and partial GitHub FTP workflows upload only from the generated allowlist package.
- Automated full upload does not perform a remote clean-slate deletion.

## Rollback Baseline

The pre-Sofortschutz state is available locally and on GitHub as:

- `baseline-pre-safety-refactor-2026-07-31`

Restore it only as an incident rollback after recording any newer production data that must be retained.

## Validation Snapshot (2026-06-13)

- Command executed successfully:
  - python scripts/prepare_deployment.py --mode both
- Result:
  - Full bundle populated and mirrored to legacy full folder.
  - Delta bundle empty (no changes since last state snapshot).

## Transition Note

Mirror validation completed successfully in two cycles. The transition is now
closed and the legacy root-level `deployment/` tree is retired. Rollback uses a
Git baseline and a newly generated package below `build/deployment/`, not a
second local copy of the same handover files.
