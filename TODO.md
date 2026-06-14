# TODO

## Next Improvements

- Add automated validation for deployment bundle exclusions.
- Add CI check that validates standards/compliance-output-schema.json format for audit outputs.
- Add smoke checks for core pages to tests/.

## Migration Tasks

- Completed: framework anchors and standards baseline (Phase A+B).
- Completed: deployment transition script and runbook (Phase C baseline).
- Completed: mirrored release cycles and parity verification (cycle 2/2 completed, see docs/deployment_parity_2026-06-14.md and docs/deployment_parity_2026-06-14_cycle2.md).
- In progress: primary handover on build/deployment with legacy mirror as rollback fallback.
- In progress: first probation cycle evidence recorded locally (docs/deployment_probation_cycle_2026-06-14.md); production upload/monitoring outcome still pending.
- Pending: run post-cutover compliance audit and update report artifact.

## Open Questions

- Keep deployment/full_deployment and deployment/delta_deployment as permanent mirror or retire after stabilization?
- Should deployment state file be retained between release cycles or reset per tagged release?
