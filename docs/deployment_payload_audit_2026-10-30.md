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
