# TODO

## Next Improvements

- Review both editorial language versions of the Germany 2036 Reform Agenda at least annually and after major German legislation or new OECD/EU comparative evidence; keep country mechanisms distinct from transferability claims, compass scores distinct from source metrics and both B2 versions equivalent in meaning.
- Revisit the military-duty versus universal-civic-year comparison after relevant German legislation, constitutional case law or new controlled evaluations; do not infer compulsory-service effects directly from voluntary-service participants.
- Review the conscription map at least annually and after service-law or V-Dem regime changes; keep selective, suspended, registration-only and actively enforced systems methodologically distinct.
- Review the war stress-test evidence matrix after material NATO, BBK, BfV, EU, OSCE or arms-control updates; keep fictional escalation assumptions visibly separate from official assessments.
- Refresh the household gross-income benchmark after each EU-SILC household-type release; keep the DINKs asterisk until the source explicitly identifies two earners, and do not label household-type bands as percentiles without a matching official distribution.
- Review the Germany 2036 source/assumption matrix at least annually and after material Destatis, UBA, IEA, OECD, EU or NATO updates; keep model assumptions separate from projections.
- Refresh the income-pyramid thresholds after each annual Destatis full-time earnings and EU-SILC release; never infer a current net top-10 threshold without a published source.
- Refresh and review the server-side Destatis real-wage snapshot and OECD wage dataset when either source revises its annual series or price base.
- Completed: fail-closed data validation, deployment allowlist enforcement and pipeline safety regression tests.
- Completed: Testbasis phase with source metadata contracts, isolated adapter tests, key-page smoke checks and one shared local/CI runner.
- Completed: core fetch refactoring with typed adapter requests/results, explicit execution modes, complete source registry and centralized status policy.
- Gradually move the remaining legacy HTTP client implementations from `fetch_data.py` into dedicated adapter modules behind the stable `AdapterServices` boundary.
- Add CI check that validates standards/compliance-output-schema.json format for audit outputs.

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

## Structure Harmonization

- [ ] Decide after stabilization whether legacy `deployment/full_deployment/` and `deployment/delta_deployment/` can be retired.
- [ ] Keep README structure inventory aligned when data, scripts or deployment folders change.
- [ ] Ensure WebCheck/FPF audits classify productive `scripts/` browser code as a documented exception.

