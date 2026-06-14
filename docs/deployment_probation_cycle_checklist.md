# Deployment Probation Cycle Checklist

## Purpose

Use this checklist for the first production cycle after switching primary handover to build/deployment.

## Pre-Deployment

- [ ] Generate bundles with primary command:
  - python scripts/prepare_deployment.py --mode both
- [ ] Verify full bundle folder is populated:
  - build/deployment/full/
- [ ] Verify delta bundle expectation (empty or changed files) is understood:
  - build/deployment/delta/
- [ ] Confirm no governance/helper artifacts are included in full bundle.

## Deployment Execution

- [ ] Upload from build/deployment/full/ or build/deployment/delta/ according to release scope.
- [ ] Keep rollback option ready using fallback mirror command:
  - python scripts/prepare_deployment.py --mode both --mirror-legacy
- [ ] Keep legacy folders available but not primary.

## Post-Deployment Validation

- [ ] Landing page and navigation work as expected.
- [ ] Core pages load correctly:
  - index.html
  - countries.html
  - world.html
  - overall_ranking_countries.html
  - analysis.html
- [ ] robots.txt and sitemap.xml are reachable in production.
- [ ] No deployment-related incident observed in first monitoring window.

## Decision Gate

- [ ] Pass: keep build/deployment as primary and continue fallback mirror as optional.
- [ ] Fail: rollback to legacy handover path and document failure cause.

## Evidence to Record

- Date and operator
- Command used
- Bundle file counts
- Validation result summary
- Rollback required: yes/no
