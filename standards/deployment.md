# Deployment Standard

Version: 2.1.0

## Single Source of Truth

Deployment-Regeln werden ausschliesslich in diesem Dokument definiert. `AGENTS.md` darf nur auf diese Regeln verweisen.

## Positivliste (erlaubte Artefakte)

- `*.html`
- `*.css`
- `*.js`
- `*.json`
- `*.xml`
- `*.svg`
- `*.png`
- `*.jpg`
- `*.webp`
- `favicon.ico`
- `robots.txt`
- `sitemap.xml`
- `.htaccess`
- `.well-known/`
- `assets/`
- `images/`
- `fonts/`
- `api/`
- produktive Frontend-Skripte aus `scripts/`, wenn das Projekt diesen Pfad bewusst fuer Browser-Code nutzt

## Negativliste (nicht erlaubt)

- `README*`
- `CHANGELOG*`
- `TODO*`
- `SECURITY*`
- `docs/`
- `tests/`
- nicht-produktive Skripte, Fetcher, Build-Helfer und lokale Automatisierung
- `.github/`
- `.git*`
- `.vscode/`
- `.env*`
- `*.py`
- `*.md`
- `*.ps1`
- `*.sql`
- `database/`
- `backups/`
- `install.php`
- `setup.php`

Ausnahme:

- `LICENSE`

## Full Deployment

Pfad:

`build/deployment/full`

Enthaelt das vollstaendige Produktionspaket.

## Delta Deployment

Pfad:

`build/deployment/delta`

Enthaelt nur geaenderte Dateien.

## Bestehende Deployment-Pfade

Neue Projekte verwenden `build/deployment/full` und `build/deployment/delta`.

Bestehende Projekte duerfen dokumentierte Altpfade weiterverwenden, wenn produktive Prozesse, FTP-Uebergaben, GitHub Pages oder Hosting-Abläufe davon abhaengen. Beispiele sind `builds/full-deployment`, `deployment/full_deployment`, `full`, `delta`, `deploy-paket` oder `delta-deploy-paket`.

Altpfade muessen in README oder AGENTS dokumentiert werden. Eine Umstellung auf den Zielstandard ist eine Deployment-Migration und benoetigt Test, Rollback und Changelog-Eintrag.

Eigenstaendige WordPress-Plugin-Repositories duerfen einen dokumentierten
externen Artefakt-Workspace verwenden. In diesem Fall sind interne
`build/deployment`-Ordner nicht erforderlich. Das Paket muss reproduzierbar
erzeugt werden, darf nur produktive Plugin-Dateien enthalten und wird nicht im
Plugin-Repository versioniert.

## Reproduzierbarkeit

Vor jeder Erzeugung gilt:

1. Zielordner vollstaendig leeren.
2. Paket vollstaendig neu erzeugen.

Teilweises manuelles Nachkopieren ohne dokumentierten Prozess ist nicht erlaubt.

## Delta-Erzeugung

- Delta-Pakete verwenden standardmaessig einen expliziten Vergleichs-Ref und duerfen nicht unbeabsichtigt leer sein, nur weil `HEAD` mit `HEAD` verglichen wurde.
- Wenn das letzte Commit als Delta ausgeliefert werden soll, muss dies als eigener Modus oder Parameter dokumentiert sein.
- Gross-/Kleinschreibung und tatsaechliche Dateinamen muessen beim Kopieren erhalten bleiben, besonders unter Windows mit case-insensitivem Dateisystem und Linux/Apache-Zielhosting.
- CSS-referenzierte Assets werden bei Delta-Paketen mitgenommen, wenn eine geaenderte CSS-Datei neue oder geaenderte URLs referenziert.

## Installations- und Datenbankartefakte

- Installer, Setup-Skripte, Datenbank-Schemas, Seed-Daten, Imports und Migrationshilfen gehoeren nicht ins normale Produktionspaket, sofern sie nicht fuer den laufenden Betrieb zwingend erforderlich sind.
- Wenn solche Artefakte fuer eine Erstinstallation benoetigt werden, werden sie als separater, dokumentierter Installationsschritt behandelt und nach Abschluss gesperrt oder entfernt.
