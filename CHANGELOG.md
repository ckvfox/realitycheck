# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- Added Fox Project Framework v2.0.0 anchors: PROJECT_MASTER.md and standards/ baseline.
- Added framework governance files: TODO.md, .env.example and LICENSE.
- Added machine-readable compliance artifacts and Apache shared hosting profile.
- Added deployment transition script: scripts/prepare_deployment.py.
- Added deployment migration runbook: docs/deployment_runbook.md.
- Added deployment cutover plan with criteria and rollback: docs/deployment_cutover_plan.md.
- Added deployment parity report for mirrored cycle validation: docs/deployment_parity_2026-06-14.md.
- Added deployment parity report for mirrored cycle 2 validation: docs/deployment_parity_2026-06-14_cycle2.md.
- Added probation-cycle execution checklist for primary deployment switch: docs/deployment_probation_cycle_checklist.md.
- Added local probation evidence report for primary deployment cycle: docs/deployment_probation_cycle_2026-06-14.md.
- Added compliance audit artifact: docs/compliance_report_2026-06-13.json.

### Changed
- Updated AGENTS.md with controlled deployment bundle generation command.
- Extended SECURITY.md to include FPF 2.0 minimum lifecycle sections.
- Documented controlled migration path from deployment/full_deployment and deployment/delta_deployment to build/deployment/full and build/deployment/delta.
- Hardened deployment packaging selector to allowlist-only productive artifacts and robust Windows cleanup behavior.
- Updated compliance report findings and score after validated packaging run.
- Activated build/deployment as primary handover command, keeping legacy mirror as fallback mode.

### Fixed
- Fixed prepare_deployment.py syntax and cleanup robustness issues that blocked packaging runs.
