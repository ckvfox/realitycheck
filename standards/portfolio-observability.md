# Portfolio Observability Standard

Version: 2.1.0

## Purpose

Fox Project Framework defines the governance contract for all maintained
projects. Webcheck is the operational companion that consumes this contract,
combines repository compliance with live production checks and presents the
result in one portfolio dashboard.

The two repositories remain independent:

- Fox Project Framework owns standards, profiles, schemas and maturity rules.
- Webcheck owns scheduled live checks, portfolio aggregation, issue
  synchronization and dashboard rendering.
- Product repositories own their code, local instructions, remediation and
  deployment decisions.

This separation prevents a monitoring application from becoming a hidden
framework dependency while still making it a first-class part of the standard.

## Project Registry

Webcheck maintains a registry based on `templates/project-portfolio.yml`.
Every actively maintained project declares at least:

- GitHub repository;
- project type and framework profile;
- production state;
- hosting provider;
- optional public production URL;
- local repository group for local portfolio scans;
- whether live Webcheck checks and automatic issue synchronization apply.

Projects in discovery or paused state remain visible only when explicitly
requested. They do not receive live checks or automatic remediation issues.

## Maturity Levels

Maturity is reported as a level, not as a guessed compliance percentage:

| Level | Name | Minimum evidence |
| --- | --- | --- |
| 0 | Discovery | Experiment or undecided continuation |
| 1 | Foundation | README and local development context |
| 2 | Governed | Core governance documents, license and validation strategy |
| 3 | Standardized | Verifiable FPF version/profile, security and deployment rules |
| 4 | Operational | Production state, CI and current live Webcheck evidence |
| 5 | Learning | Reusable lessons, framework candidates and cross-project reuse |

Fail-fast remains authoritative: when the required FPF basis is missing, the
project is `framework-unverifizierbar` even if a maturity level can describe
its current lifecycle state.

## Automatic Issues

Every actionable error receives a stable fingerprint. Issue synchronization
must be idempotent:

- create one issue for a new fingerprint;
- update or reopen the existing issue when it recurs;
- close the issue only after the finding is absent in a later successful run;
- never create duplicate issues for the same project and fingerprint;
- label automated issues with source, project, category and severity.

Sensitive security details for public repositories must not be published in a
public issue. Those findings are tracked in the private Webcheck repository by
default. Non-sensitive compliance findings may be created in the owning
repository when its registry entry explicitly allows that destination.

## Live Checks

Live checks apply only to production systems. At minimum they may cover:

- availability, redirects and TLS;
- security headers and external security scoring;
- performance and Core Web Vitals;
- SEO and crawler compatibility;
- accessibility basics;
- technology and hosting observations.

The absence of a production URL is not a compliance failure for a project that
is explicitly marked non-production.

## Cross-Project Learning

The dashboard should make repeated findings visible across projects. A
solution becomes a reuse candidate when it is applicable to at least one other
project. Reusable outcomes are documented as Lessons Learned and, when they
change the standard, as Framework Candidates. Product repositories must not
modify the framework automatically.

## Efficiency

Portfolio scans should reuse committed audit artifacts, fingerprints and
previous results. Agents should load only the standards and project files that
are relevant to the current finding. This reduces repeated repository scans,
duplicate implementation work and unnecessary model context usage.
