# Compliance Scoring Standard

Version: 2.0.0

## Areas and weights

| Area | Weight |
| --- | --- |
| Security | 30% |
| Governance | 25% |
| Deployment | 20% |
| SEO/Crawling | 15% |
| CI/GitHub | 10% |

## Score formula

Score = 0.30 * Security + 0.25 * Governance + 0.20 * Deployment + 0.15 * SEO + 0.10 * CI

## Gates

- Security Gate: minimum 70
- Governance Gate: minimum 60
- Deployment Gate: minimum 60

If any gate is below threshold, status is red regardless of total score.

## Status without gate violation

- green: score >= 85
- yellow: score >= 65 and < 85
- red: score < 65

## Fail-fast

If PROJECT_MASTER.md or standards/ is missing:

- abort scoring
- status = framework-unverifizierbar
- no estimated score allowed
