# Deployment Standard

Version: 2.0.0

## Single Source of Truth

Deployment packaging rules are defined only in this file.

## Positive list (allowed)

- *.html
- *.css
- *.js
- *.json
- *.json.gz
- *.xml
- *.svg
- *.png
- *.jpg
- *.webp
- productive frontend scripts in scripts/
- robots.txt
- sitemap.xml
- .htaccess
- images/
- data/
- data/analysis.md (productive report consumed by analysis.html)

## Negative list (excluded)

- README*
- CHANGELOG*
- TODO*
- SECURITY*
- docs/
- tests/
- data/test/
- data/fetch_state.json
- data/manual_source_status.json
- data/meta/manual_csv_sources.json
- data/workflow_fetch_console.log
- data/workflow_fetch_summary.md
- tracking.json (server-owned runtime counter state)
- non-productive scripts, fetchers, helpers and raw sources
- .github/
- .git*
- .env*
- *.md (except the explicit productive file data/analysis.md)

## Deployment folders

Framework target folders:

- build/deployment/full/
- build/deployment/delta/

The former root-level `deployment/` mirror was retired after the controlled
cutover. It must not be recreated; all FTP handover packages originate below
`build/deployment/`.

## Minimum release checks

- target folder cleared before repopulation
- package contains only productive artifacts
- no secrets in deployment package
- full or delta variant explicitly labeled
