# RealityCheck status audit — 2026-10-12

## Findings and evidence

The open issue inventory contains 31 machine-created run notifications: 12 monthly
and 19 manual/force records. All were created by github-actions[bot], carry the
automation and corresponding run labels, and have no comments, assignees or
milestones. Five existing open pull requests are development work and are excluded.

- #97 (run 30683253802, 2026-08-01) and #99 (run 33464865124,
  2026-09-01) failed dependency installation: numpy==2.5.1 requires Python >=3.12
  while these workflows used Python 3.11. The fetch/deploy/push steps were skipped.
- #101 (run 33492113001, 2026-09-01) and #106 (run 36843630183,
  2026-10-01) have successful jobs and successful installation, full pipeline,
  CSV checks, FTP deployment and data commit/push steps.
- The additional September run 33491485744 failed its fetch and notification
  steps, producing no status issue. The later September success supersedes its
  pipeline failure too. This is why issue counts alone are not a complete run audit.
- Older monthly failures #89/#90 precede successful monthly record #91.
  Historical manual failures precede successful runs of their respective workflows
  (#87 regular manual; #81 force). Their run metadata was checked directly against
  Actions, including workflow path, main branch and final conclusion.
- Some older jobs no longer expose step details. Their original failure causes are
  not asserted as diagnosed or fixed; their run notifications are superseded by
  later successful runs of the same workflow.

## Cleanup decisions

Each listed notification receives an explanatory comment with a verified Actions
link before closure as completed. Bodies and run links remain intact. No issues are
deleted and no independent source, data-quality or development tasks are resolved.

| Issue | Recorded status | Workflow | Evidence / disposition |
|---|---|---|---|
| #106 | success | monthly | Archive completed status; reference #106 |
| #101 | success | monthly | Archive completed status; reference #106 |
| #99 | failure | monthly | Superseded by successful #101 |
| #97 | failure | monthly | Superseded by successful #101 |
| #96 | success | monthly | Archive completed status; reference #106 |
| #95 | success | monthly | Archive completed status; reference #106 |
| #94 | success | monthly | Archive completed status; reference #106 |
| #93 | success | monthly | Archive completed status; reference #106 |
| #92 | success | monthly | Archive completed status; reference #106 |
| #91 | success | monthly | Archive completed status; reference #106 |
| #90 | failure | monthly | Superseded by successful #91 |
| #89 | failure | monthly | Superseded by successful #91 |
| #87 | success | manual | Archive completed status; reference #87 |
| #86 | success | manual | Archive completed status; reference #87 |
| #82 | success | manual | Archive completed status; reference #87 |
| #81 | success | manual force | Archive completed status; reference #81 |
| #80 | success | manual | Archive completed status; reference #87 |
| #79 | success | manual force | Archive completed status; reference #81 |
| #78 | failure | manual force | Superseded by successful #81 |
| #77 | success | manual | Archive completed status; reference #87 |
| #76 | success | manual | Archive completed status; reference #87 |
| #75 | failure | manual | Superseded by successful #87 |
| #74 | failure | manual | Superseded by successful #87 |
| #73 | failure | manual | Superseded by successful #87 |
| #72 | failure | manual | Superseded by successful #87 |
| #71 | failure | manual | Superseded by successful #87 |
| #70 | failure | manual | Superseded by successful #87 |
| #69 | failure | manual | Superseded by successful #87 |
| #68 | failure | manual | Superseded by successful #87 |
| #67 | failure | manual | Superseded by successful #87 |
| #58 | failure | manual | Superseded by successful #87 |

## Workflow policy

Use the existing monthly github-script step and permissions; add no extra scheduled
workflow, service or dependency. Preserve one durable issue per default-branch run.
Success records are closed immediately. Failure/cancellation records remain open
until a later successful monthly run. Reruns reuse the run marker, retain previous
attempts as comments and reopen on failure. Recovery comments link the successful
run and its issue. Pagination covers all records and comments.

Only labelled bot records with the exact status title and ownership marker are
managed. Human discussion, assignments and milestones protect both rerun and
historical recovery updates. Feature-branch dispatches cannot close production
records; an old rerun cannot close a newer failure. Unexpected states and API
failures fail the status step visibly instead of being swallowed.

Legacy notifications are cleaned in this audit; future reconciliation deliberately
requires the ownership marker and does not claim unrelated legacy/manual tasks.
The manual workflows themselves are outside this monthly-workflow change and
retain their existing notification policy.

A successful workflow does not certify source completeness or freshness. Existing
TODO items (including NOAA/IBTrACS verification and placeholder hazard sources)
remain open. The existing Actions summary and diagnostic upload remain intact;
artifacts expire after 30 days, while closed status issues preserve the run history.

## Validation

- Nine Node offline tests exercise success, failure, cancellation, reruns,
  idempotency, partial API retry, human-task protection and branch/order guards.
- Workflow YAML parses; git diff whitespace check and FPF production baseline pass.
- The new Node test is automatically discovered by the existing CI runner.
- Broader local Python discovery is incomplete: the available environment lacks
  requests and python-dotenv; PHP is unavailable. No full-suite success is claimed.
- No live data fetch or FTP deployment was triggered for this housekeeping change.

## Framework candidate

Ownership-marked bot status records, recovery links and protection of human-owned
follow-ups are reusable across scheduled project workflows. No framework or
parallel automation was changed here.
