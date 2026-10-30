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
- Generated Markdown and AI summaries are sanitized or inserted as text before entering the DOM.
- Visitor-count updates accept POST only and serialize concurrent file writes with an exclusive lock.

## Pipeline and Deployment Security

- Direct dependencies are version-pinned and GitHub Actions are pinned to immutable commit SHAs.
- Fetch errors, dummy datasets and validation failures stop the workflow before analysis or FTP deployment.
- Force mode never removes the last known-good data snapshot before replacement data succeeds.
- All production uploads (main push, monthly/manual fetch, full/sync/partial) use the same explicit static-file and validated registry allowlist. Partial and data selections are filtered only after package validation. Unknown files, unsafe registry paths, symlinks and missing indexed gzip parts block publication; the destination webroot is fixed. No remote deletion is performed.
- Production fetches, automatic deployments and FTP-only workflows share the same concurrency group, preventing overlapping writes.
- Automatic main deployments test the exact checked-out snapshot before packaging. FTPS uses certificate verification, encrypted data connections and runtime-only GitHub secrets; transfer errors do not print server replies or credentials. A remote hash checkpoint advances only after successful transfers and size checks; no remote files are deleted.
- Test-mode datasets, status, logs, hashes and pending mappings are isolated below `data/test/`; automatic production mapping updates are disabled in test mode.
- Deployment packaging explicitly excludes the complete `data/test/` subtree.
- Pull requests run the complete network-free source-contract, adapter-isolation, snapshot and deployment regression baseline before merge.
- Fetch startup fails closed when source metadata and the explicit adapter registry differ; unknown types cannot enter a fallback dispatch branch.
- Source-specific network clients receive output paths through an injected runtime boundary; mocked tests cover every supported source family without live network access.
- Failed or empty adapter results preserve both the last known-good dataset and its previous fetch-status entry.

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

## Hosting versus project evidence

The read-only `scripts/security_audit.py` separates InfinityFree's upstream
JavaScript challenge, identified application responses, marked project denials,
HTTP redirects and unknown denials. Only application HTML with the project-policy
marker is scored. Other responses stay inconclusive; UA differences are observed
without claiming causality. No cookies, raw headers, response bodies or challenge
execution are logged. UA strings never verify a crawler's identity.

The CSP uses the measured Google TE_20261014 bootstrap hash, scoped Translate
frames/connections and no inline event attributes. Existing CDNs, Leaflet styles,
map tiles and same-origin forms remain supported. Referrer-Policy stays
strict-origin-when-cross-origin. HSTS is unchanged. No local bot gate or UA
branching is installed. The retired challenge URL redirects server-side.

Framework candidate: combine application identity, project policy markers and
hoster challenge detection before scoring security headers; keep an inconclusive
state instead of merging evidence from different responses.
