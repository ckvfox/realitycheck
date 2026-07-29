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
- HTTP response headers enforce HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and a restrictive Permissions-Policy.
- Debug outputs and verbose internal diagnostics must be disabled in production.
- Public-facing uploads exclude non-productive artifacts and secret-bearing files.
- The menu-linked Germany Dossier is currently public. Its former PHP session gate remains disabled behind `RC_DOSSIER_ACCESS_PROTECTION` for possible reuse and must be retested before reactivation.
- Income benchmark data are loaded server-side from an HTTP-denied PHP include; calculator inputs stay in the browser and are not submitted or tracked.
- The separate war stress test is public through the dossier but its source include remains HTTP-denied. It deliberately excludes target-level infrastructure details, coordinates and tactical guidance. Its conscription map is a non-operational policy comparison using public country boundaries only.
- Analysis includes are denied direct HTTP access, while the runtime password-hash file is excluded from version control.
- When enabled, the retained gate uses idle expiry, CSRF tokens, session ID regeneration, per-session attempt locking and delayed failures. The current public page keeps no-store caching and robots exclusion headers without starting a login session.

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
