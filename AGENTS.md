# AGENTS.md

Dieses Projekt folgt dem Fox Project Framework v2.0.0.

## Projekt

Name: RealityCheck
Typ: Web + Data Project
Hosting: Apache-compatible shared hosting (InfinityFree)
Deployment: FTP handover with full and delta packaging

## Lokale Entwicklung

- Work from repository root for Python scripts.
- Activate virtual environment before running fetch and analysis jobs.
- Frontend can be validated with local static serving.

## Build

- No classic bundler build.
- Deployable web artifacts are static HTML, CSS, JS, images and data JSON files.
- Data artifacts are generated via Python scripts in scripts/.

## Deployment

Deployment packaging rules are defined in standards/deployment.md.
Bundle generation command:

- Primary: python scripts/prepare_deployment.py --mode both
- Fallback mirror mode: python scripts/prepare_deployment.py --mode both --mirror-legacy

Project-specific operational fallback handover uses:

- deployment/full_deployment/
- deployment/delta_deployment/

Framework target primary handover path:

- build/deployment/full/
- build/deployment/delta/

## Bekannte Probleme

- Shared hosting environments may have FTP/rewrite constraints.
- Partial uploads can lead to inconsistent runtime state if delta scope is wrong.
- Country source aliases can require mapping maintenance.

## Framework Candidates

Potential candidates are tracked only when insights are reusable across projects.
No direct framework changes are made from this repository.

## Lessons Learned

Operational lessons should be documented after major migrations, audit cycles or recurring incidents.

## Restricted Files

Do not read, open, inspect, summarize, quote, print, or expose secret-bearing files.
Treat at least the following as restricted:

- .env
- .env.local
- .env.*.local
- .secrets
- credentials*
- *.pem
- *.key
- *.pfx
- *.p12
- id_rsa
- id_ed25519
- auth.json

## Allowed Work

Allowed work categories:

- development
- refactoring
- debugging
- testing
- documentation
- workflow creation

## Deployment Packaging Rules

- Create and maintain a local deployment folder structure with:
  - deployment/full_deployment/
  - deployment/delta_deployment/
- Only include files that are actually hosted productively on the web server.
- Exclude non-productive repository artifacts such as README files, notes, plans, and local helper docs.
- full_deployment must contain the complete current production upload set.
- delta_deployment must contain only the files changed in the latest change set to upload as delta.
- Before preparing a new deployment package, clear both deployment folders and repopulate them from scratch.
- These deployment folders are local FTP handover folders and must never be committed to GitHub.

## Known Constraints

- Existing productive deployments depend on current FTP folder conventions.
- Migration to framework target deployment paths must be controlled and reversible.

## Agent-Regeln

- Before changes, read README.md, AGENTS.md, CHANGELOG.md and TODO.md.
- After changes, verify whether README.md, AGENTS.md, CHANGELOG.md, TODO.md, SECURITY.md, robots.txt, sitemap.xml and deployment packaging need updates.
- If configuration is needed, use .env.example and never request or reveal real secret values unless explicitly required for secret debugging.
