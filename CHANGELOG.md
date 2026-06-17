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
- Added UN Security Council permanent members as a World map country grouping.

### Changed
- Updated AGENTS.md with controlled deployment bundle generation command.
- Extended SECURITY.md to include FPF 2.0 minimum lifecycle sections.
- Hardened HTTP delivery with HSTS, a restrictive CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy headers.
- Removed inline script allowance from CSP and set Referrer-Policy to strict-origin-when-cross-origin for Mozilla Observatory compliance.
- Documented controlled migration path from deployment/full_deployment and deployment/delta_deployment to build/deployment/full and build/deployment/delta.
- Hardened deployment packaging selector to allowlist-only productive artifacts and robust Windows cleanup behavior.
- Updated compliance report findings and score after validated packaging run.
- Activated build/deployment as primary handover command, keeping legacy mirror as fallback mode.
- Set `index.html` language metadata to `en-US` to match the page's primary language.
- Removed the Apache JS challenge gate so search bots, audits, and assistive technology can reach real HTML pages without JavaScript verification.
- Kept trusted crawler and `webcheck-bot` detection markers in `.htaccess` for audit-friendly future rewrite handling.
- Promoted the countries dashboard to the canonical homepage at `/` and kept `countries.html` as a backward-compatible redirect.
- Updated sitemap, canonical URLs, OpenGraph/Twitter URLs, manifest start URL, and navigation to use the canonical production domain and homepage.
- Confirmed security headers remain active without blocking crawlers, audits, or non-JavaScript accessibility checks.
- Updated deployment packaging to include only productive frontend JavaScript files from `scripts/`.
- Updated the NATO country grouping to include Sweden.

### Fixed
- Fixed prepare_deployment.py syntax and cleanup robustness issues that blocked packaging runs.
- Added accessible labels for homepage comparison selectors.
