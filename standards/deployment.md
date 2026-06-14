# Deployment Standard

Version: 2.0.0

## Single Source of Truth

Deployment packaging rules are defined only in this file.

## Positive list (allowed)

- *.html
- *.css
- *.js
- *.json
- *.xml
- *.svg
- *.png
- *.jpg
- *.webp
- robots.txt
- sitemap.xml
- .htaccess
- images/
- data/

## Negative list (excluded)

- README*
- CHANGELOG*
- TODO*
- SECURITY*
- docs/
- tests/
- scripts/
- .github/
- .git*
- .env*
- *.md

## Deployment folders

Framework target folders:

- build/deployment/full/
- build/deployment/delta/

Project transition note:

- During migration, deployment/full_deployment/ and deployment/delta_deployment/ stay operational.

## Minimum release checks

- target folder cleared before repopulation
- package contains only productive artifacts
- no secrets in deployment package
- full or delta variant explicitly labeled
