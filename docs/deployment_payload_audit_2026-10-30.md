# RealityCheck deployment payload audit — 2026-10-30

The audit compares the 456 paths in the first automatic upload receipt
(run 41084172389) with product references and the current registries.
The tightened package contains 386 paths; it adds none to that historical set.

## Scope and decisions

- Keep explicit public pages, verification files, Apache configuration, browser
  JavaScript, server-side dossier includes and the license.
- Keep three referenced images, country metadata flags, fixed DE/GB language
  flags and the question-mark fallback. Exclude six unused image variants and
  56 flags outside the supported country list. Canonical logo: `images/logo.png`.
- Keep every registered KPI JSON that exists, the gzip parts named by
  `all_kpis_index.json`, public analyses/rankings and required metadata/geometries.
  Registry-driven selection accommodates future monthly bundle splits and KPI
  additions; it does not accept arbitrary JSON files.
- Exclude eight backend-only artifacts: `data/analysis.json`,
  `data/overall_ranking.json`, `data/meta/world.json`, both `data/master/` JSONs,
  both `country_mappings_pending.json` files and
  `data/meta/country_analysis_context.json`. Runtime uses the explicit public
  alternatives; pending mappings and generation context remain in the repository.
- Secret-bearing paths are rejected before inventory content reads. No credential
  values or private server configuration were inspected. Productive symlinks,
  unsafe registry names and missing declared gzip parts fail closed.

## Upload routes

All nine productive workflows build the same package. Main pushes select the
full inventory and skip unchanged hashes/sizes. Five fetch workflows and manual
FTP sync select only its `data/` subset. Manual partial upload accepts only paths
already in the validated package. Explicit manual full upload can force transfers.
All use certificate-verified FTPS to `/realitycheck.great-site.net/htdocs`, share
the production lock and never issue remote deletion commands. Checkpoints are
separate for full, data-only and partial selections. `FTP_DIR` is unused.

The shared `publish_package` API is preserved. EnergyPlanning's pinned transport
and its independent allowlist are unaffected by this RealityCheck change.

## Verification and limits

Regression coverage checks static page asset closure, registered data/flag/region
selection, rejection of unregistered/internal files and traversal, missing gzip
parts, data/partial scoping, every upload workflow, retry/checkpoint integrity and
cross-site destination isolation. Full offline suite and FPF production baseline
must pass before publication. Both handover folders are recreated from scratch.

This audits future deployment selection, not every historical file on the FTP
account. Previously uploaded excluded files are not deleted or overwritten by
this change. No new source retrieval or forced full upload is needed for this
policy-only change. New static assets must be deliberately registered and tested.

Framework candidate: one project-owned, dependency-aware payload manifest across
all deployment entry points, with shared transport and no implicit server cleanup.

## Read-only live inventory

`audit-ftp.yml` can be dispatched on main to list MLSD directory metadata in the
two explicitly authorized RealityCheck/EnergyPlanning webroots. It retrieves no
file contents, follows no symlinks and has no upload/delete operations. The
seven-day artifact contains paths, types, sizes and modification timestamps only.
Credentials remain runtime-only GitHub secrets. This helper is excluded from
the productive deployment package. Its tests use a metadata-only FTP double.

## User-approved cleanup

The user subsequently explicitly authorized backing up the surplus files,
deleting them by FTP and checking both sites live. The frozen
`scripts/ftp_cleanup_plan_2026_10_30.json` contains exactly 109 RealityCheck and
two EnergyPlanning candidates. Current deployment checkpoints, RealityCheck's
server-side access configuration and visitor counter remain protected.

`cleanup-ftp-reviewed.yml` has separate backup/delete stages. Backups go into
each domain's `htdocs/.ftp-backups/2026-10-30-reviewed-cleanup/` archive, protected
by its own deny-all Apache configuration. InfinityFree rejected the initial
sibling-directory backup attempt before copying/deleting any candidates. The
separate prepare stage creates only the guard and a harmless marker; HTTP 403
for both marker URLs must be checked before starting backup. Size and SHA-256 are checked after copying. Before any
deletion, both sites' backups and remaining originals are checked again; changed
candidate metadata/content or missing preserved files abort the operation.
Deletion uses only individual frozen paths, never recursive directory removal.
Artifacts contain metadata receipts, never backup file contents or credentials.
Normal deployments remain non-deleting. This one-off helper is not deployed.

The delayed pre-delete verification detected a changed `images/photo.png` backup
and stopped before any deletion. All ten image backups were then copied under
opaque `.original` storage names and matched against the initial verified source
hashes. The other backup files were retained. No source hash was replaced or
accepted with weaker checks.

Recovery uses each archive's `snapshot.json`: `path` is the original destination;
`storage_path`, when present, is the archive filename to restore, otherwise use
`path`. Check `size` and `sha256` before copying back. Ignore archive files not
selected by this mapping, including superseded image copies. Never upload the
whole archive blindly to the webroot.

Framework candidate: reverify backups after storage and before deleting originals;
use opaque binary storage names with an explicit restoration manifest when an
image copy changes after its initial upload verification.

## Completed cleanup and live acceptance

The final receipt from [run 41104448784](https://github.com/ckvfox/realitycheck/actions/runs/41104448784)
confirms exactly 109 RealityCheck and two EnergyPlanning deletions, after the
repaired backups passed the complete preflight. All 389 RealityCheck and 23
EnergyPlanning original product/server files selected for preservation remain.
These counts exclude the protected backup archives, which remain on FTP.

Initial backup receipt: run 41101182550. Opaque-image repair receipt:
run 41103890793. All 111 original hashes remained unchanged by repair. Both
archive marker URLs returned HTTP 403 after the complete backup.

Live checks after deletion: RealityCheck country values and visitor counter,
NOAA basin table, wildfire/flood/heat/drought data and environmental legends,
plus the public Germany dossier; EnergyPlanning calculation and funding hints,
scenario switching and winter charts. Screenshots and the operational receipt
are local artifacts under `build/source-review` and the session visual folder.
The full offline suite passed (124 tests, one Windows symlink test skipped),
including JavaScript/PHP checks; the FPF production baseline passed.

The one-off cleanup workflow was then disabled in GitHub Actions. Automatic
main deployment and the monthly fetch workflow remain active and non-deleting.
