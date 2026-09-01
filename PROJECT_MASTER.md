# PROJECT_MASTER

Project: RealityCheck
Framework Target: Fox Project Framework v2.0.0
Last Updated: 2026-08-01

## Purpose

RealityCheck is an interactive, data-driven country comparison platform with a static web frontend and Python-based data pipelines.

## Project Type

- Type: Web + Data Project
- Status: Active

## Hosting Profile

- Primary hosting: Apache-compatible shared hosting (InfinityFree)
- Audit profile: profiles/apache-shared-hosting.yml

## Compliance Anchors

The project uses the following machine-readable compliance artifacts:

- standards/compliance-checklist.yml
- standards/compliance-scoring.md
- standards/compliance-output-schema.json

## Mandatory Files

The repository maintains these governance files:

- README.md
- AGENTS.md
- CHANGELOG.md
- TODO.md
- SECURITY.md
- .env.example
- .gitignore
- LICENSE
- robots.txt
- sitemap.xml
- .htaccess (for Apache-compatible hosting)

## Mandatory Directories

The framework target structure is:

- docs/
- src/
- tests/
- build/deployment/full/
- build/deployment/delta/

## Deployment Rules

- Canonical packaging rules are defined in standards/deployment.md.
- Framework packaging targets are build/deployment/full/ and build/deployment/delta/.
- Deployment bundles are generated with scripts/prepare_deployment.py.
- The controlled transition is complete; only `build/deployment/` is used for FTP handover packages.

## Security Rules

- No secrets in repository files.
- Runtime secrets are provided via environment variables or GitHub secrets.
- Public deployment follows HTTPS-only access and hardened production settings.

## Existing Project Strategy

- Migrate in small, non-destructive steps.
- Keep productive assets stable while improving governance and auditability.
- Re-run compliance audit after each migration phase.
