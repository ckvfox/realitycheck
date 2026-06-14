# Security Policy

## Supported Versions

RealityCheck is maintained on the main branch. Security fixes are applied to the currently active production baseline.

## Vulnerability Reporting

If you discover a vulnerability, report it privately.

- Contact: ckvfox@gmail.com
- Do not open a public issue for undisclosed security vulnerabilities.

## Secret Handling

- Secrets are never committed to the repository.
- Runtime credentials are provided via environment variables or GitHub secrets.
- .env.example contains placeholder values only.

## Production Hardening

- Production deployment is HTTPS-only.
- Debug outputs and verbose internal diagnostics must be disabled in production.
- Public-facing uploads exclude non-productive artifacts and secret-bearing files.

## Backup Strategy

- Repository history in GitHub is the primary source of versioned code backup.
- Deployment payloads are prepared in dedicated local handover folders before upload.
- Critical generated data files are recoverable via fetch pipelines and repository snapshots.

## Installer Policy

- Dependencies are installed from pinned or minimum-version requirements.
- Untrusted installer sources or ad-hoc scripts are not allowed for production workflow changes.

## Disclosure Policy

- Vulnerability details remain private until mitigation is available.
- Public disclosure follows a coordinated fix-first approach.

## Response Targets

- Initial acknowledgement target: within 3 business days.
- Triage target: within 7 business days.
- Fix timeline depends on severity and operational risk.
