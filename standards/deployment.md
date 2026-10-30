# Deployment Standard

Version: 2.1.0

## Single Source of Truth

Deployment-Regeln werden ausschliesslich in diesem Dokument definiert. `AGENTS.md` darf nur auf diese Regeln verweisen.

## Positivliste (RealityCheck)

`scripts/prepare_deployment.py` ist die ausfuehrbare Positivliste. Eine passende
Dateiendung allein erlaubt keinen Upload. Erlaubt sind:

- explizite produktive Root-Dateien, Browser-Skripte und PHP-Includes;
- drei belegte Bilder: `logo.png`, `translate.png`, `teamwork_wunder.jpg`;
- benoetigte Flaggen aus der Laenderregistrierung sowie Sprach-/Fallback-Flaggen;
- registrierte KPI-JSONs und ausschliesslich die im Index genannten gzip-Teile;
- explizite oeffentliche Analysen/Rankings, Metadaten und registrierte Geometrien.

Neue statische Seiten/Assets muessen explizit aufgenommen werden. Neue KPI-Dateien,
Laenderflaggen und Datenpaketteile folgen automatisch den validierten Registern.
Unsichere Registerpfade, Symlinks und fehlende deklarierte gzip-Teile brechen ab.
Interne Masterdaten, Pending-Mappings, Analyse-Kontext und ungenutzte Bildkopien
bleiben ausgeschlossen. `data/analysis.md` und `LICENSE` sind produktive Ausnahmen.

Alle neun produktiven Upload-Workflows erzeugen dieses Paket. Datenlaeufe waehlen
anschliessend nur `data/`; manuelle Teilauswahl darf die Liste nicht umgehen.
FTPS-Ziel ist fest `/realitycheck.great-site.net/htdocs`. Es gibt keine Remote-
Loeschungen. Historische Serverdateien werden dadurch nicht nachtraeglich entfernt.

Separat genehmigte Einmalbereinigung: `cleanup-ftp-reviewed.yml` verwendet den
festen Plan vom 30.10.2026. Erst nach vollstaendiger, SHA-256-gepruefter Sicherung
beider Sites in einem separat per HTTP gesperrten Archiv darf die getrennte Loeschphase exakt diese
Dateien entfernen. Keine rekursive Loeschung, keine Serverkonfiguration und
keine Erweiterung der normalen Deployment-Rechte oder Upload-Positivliste.

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

Bestehende Projekte duerfen dokumentierte Altpfade weiterverwenden, wenn produktive Prozesse, FTP-Uebergaben, GitHub Pages oder Hosting-AblÃ¤ufe davon abhaengen. Beispiele sind `builds/full-deployment`, `deployment/full_deployment`, `full`, `delta`, `deploy-paket` oder `delta-deploy-paket`.

Altpfade muessen in README oder AGENTS dokumentiert werden. Eine Umstellung auf den Zielstandard ist eine Deployment-Migration und benoetigt Test, Rollback und Changelog-Eintrag.

Eigenstaendige WordPress-Plugin-Repositories duerfen einen dokumentierten
externen Artefakt-Workspace verwenden. In diesem Fall sind interne
`build/deployment`-Ordner nicht erforderlich. Das Paket muss reproduzierbar
erzeugt werden, darf nur produktive Plugin-Dateien enthalten und wird nicht im
Plugin-Repository versioniert.

## Reproduzierbarkeit

Vor jeder Erzeugung gilt:

1. Beide Zielordner vollstaendig leeren, auch bei Auswahl nur eines Paketmodus.
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
