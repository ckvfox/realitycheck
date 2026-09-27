# Structure Standard

Version: 2.2.0-candidate

## Ziel

Dieser Standard definiert eine wiedererkennbare Projektstruktur fuer neue Projekte und einen risikoarmen Umgang mit bestehenden Projekten. Strukturharmonisierung darf bestehende Funktionen, produktive Pfade, Hosting-Prozesse oder Deployment-Automation nicht unbeabsichtigt veraendern.

## Grundprinzipien

- Neue Projekte verwenden die Zielstruktur dieses Standards direkt.
- Bestehende Projekte erhalten Bestandsschutz fuer produktive Pfade, etablierte Ordnernamen und dokumentierte Hosting-Prozesse.
- Abweichungen in Bestandsprojekten sind dokumentationspflichtig, aber nicht automatisch ein Fehler.
- Umbenennungen produktiver Dateien oder Ordner sind Migrationen und benoetigen Audit, Plan, Test und Rollback.
- Dokumentation, Inventar und Checklisten sind bevorzugte Quick Wins.

## Zielstruktur fuer neue Projekte

Neue Projekte sollen folgende Struktur verwenden, soweit der Projekttyp sie benoetigt:

- Root: `README.md`, `AGENTS.md`, `CHANGELOG.md`, `TODO.md`, `SECURITY.md`, `LICENSE`, Entry-Dateien
- `docs/`: Architektur, Deployment, Runbooks, Auditberichte und Troubleshooting
- `assets/css`, `assets/js`, `assets/img`: produktive Web-Assets fuer Web- und PHP-Projekte
- `data/`: fachliche, versionierte Datenquellen
- `database/`: Schema, Migrationen und Seeds
- `scripts/`: lokale Automatisierung, Fetcher, Tests und Analyse
- `tools/`: manuelle Wartungs- und Hilfswerkzeuge
- `reports/`: generierte Pruefergebnisse und lokale Reports
- `build/deployment/full`: vollstaendiges Deployment-Paket
- `build/deployment/delta`: Delta-Deployment-Paket

Nicht jeder Projekttyp braucht jeden Ordner. Nicht verwendete Ordner werden nicht leer angelegt.

Eigenstaendige WordPress-Plugins verwenden die enger zugeschnittene Struktur
aus `project-types/WORDPRESS_PLUGIN_PROJECT_TEMPLATE.md`. Websiteweite Dateien
und leere Deployment-Ordner werden dort nicht dupliziert.

## Bestandsprojekte

Bei bestehenden Projekten gilt:

- Bestehende produktive Pfade bleiben erhalten, wenn sie von URLs, Includes, Assets, Hosting, Deployments oder Dokumentation referenziert werden.
- Alternative Pfade wie `images/`, Root-`style.css`, produktives Browser-JS in `scripts/`, `builds/`, `deployment/`, `full/`, `delta/`, `deploy-paket/` oder `delta-deploy-paket/` koennen gueltiger Projektstandard sein, wenn sie dokumentiert sind.
- README oder AGENTS dokumentieren die aktuelle Struktur und ordnen sie gegen den FPF-Zielstandard ein.
- TODO dokumentiert optionale spaetere Angleichungen mit Risikohinweis.
- Changelog dokumentiert Struktur- und Dokumentationsanpassungen.
- `docs/README.md` soll als Index angelegt werden, wenn `docs/` existiert.

## Bewertung in Audits

Audits muessen zwischen Bestandsprojekt und Neuprojekt unterscheiden:

- In neuen Projekten ist die Zielstruktur Sollzustand.
- In bestehenden Projekten ist dokumentierte Abweichung vom Zielstandard eine Warnung oder Information, kein automatischer Fehler.
- Fehlende Dokumentation ueber produktive Abweichungen ist ein Finding.
- Vorschlaege mit Pfadumbenennungen, URL-Aenderungen oder Deployment-Prozesswechseln sind mindestens mittleres Risiko.

## WebCheck-Integration

WebCheck sollte Strukturregeln maschinenlesbar bewerten:

- Projekttyp und Hostingprofil erkennen.
- Produktive Standardpfade und dokumentierte Bestandsausnahmen erfassen.
- `docs/README.md` und Strukturinventar pruefen.
- Deployment-Pfade gegen Zielstandard und dokumentierte Bestandsausnahmen vergleichen.
- Findings nach `new-project-target`, `existing-project-documented-exception` und `undocumented-deviation` klassifizieren.
