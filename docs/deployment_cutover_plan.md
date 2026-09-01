# Deployment Cutover Plan

> Historical record — completed. The root-level legacy `deployment/` mirror
> was retired on 2026-08-01. Current commands and paths are defined in
> `standards/deployment.md` and `docs/deployment_runbook.md`.

## Objective

Switch primary FTP handover from legacy folders to framework target folders with minimal operational risk.

## Scope

- Current legacy handover:
  - deployment/full_deployment/
  - deployment/delta_deployment/
- Framework target handover:
  - build/deployment/full/
  - build/deployment/delta/

## Preconditions

- Packaging command succeeds without manual corrections:
  - python scripts/prepare_deployment.py --mode both --mirror-legacy
- Full bundle contains only productive artifacts.
- Delta bundle behavior is understood and tracked across releases.

## Cutover Criteria

All criteria below must be true:

1. Two consecutive mirrored release cycles complete successfully.
2. File parity checks between framework target and legacy mirror are clean for each cycle.
3. No production incidents attributable to packaging path differences.
4. Deployment operator confirms runbook readability and repeatability.

## Execution Phases

### Phase 1: Mirror Validation (completed)

- Use build/deployment as generated source.
- Keep --mirror-legacy enabled.
- Upload from legacy folders as operational fallback.
- Log parity and any mismatches.

Current status:

- Cycle 1 completed successfully on 2026-06-14.
- Parity evidence: docs/deployment_parity_2026-06-14.md
- Cycle 2 completed successfully on 2026-06-14.
- Parity evidence: docs/deployment_parity_2026-06-14_cycle2.md
- Cutover criterion for mirrored parity is satisfied (2/2).

### Phase 2: Primary Switch (active)

- Upload from build/deployment paths.
- Use legacy mirror only as fallback or explicit verification mode.
- Keep rollback instructions ready for immediate reactivation.
- Execute and archive the checklist in docs/deployment_probation_cycle_checklist.md.

Current evidence:

- Local probation evidence recorded: docs/deployment_probation_cycle_2026-06-14.md
- Remaining for phase completion: production-side upload and monitoring outcome.

### Phase 3: Stabilization

- If no regressions: keep build/deployment as primary handover.
- Optionally retire legacy deployment folders from active process.

## Rollback

If cutover cycle fails:

- Use Git tag `baseline-pre-safety-refactor-2026-07-31` to restore the complete pre-Sofortschutz code baseline when a code rollback is required.
- Re-enable upload from deployment/full_deployment and deployment/delta_deployment.
- Keep packaging command unchanged with --mirror-legacy.
- Document failure mode and corrective action before next attempt.

## Ownership and Tracking

- Track progress in TODO.md migration section.
- Record each phase transition in CHANGELOG.md.
- Re-run compliance audit after successful primary switch.
