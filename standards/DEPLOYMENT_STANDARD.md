# Deployment Standard

Hinweis fuer FPF 2.0: Die kanonische Quelle fuer Deployment-Packaging-Regeln ist `standards/deployment.md`.

Dieses Dokument bleibt als historische Referenz aus 1.x bestehen.

## Ziel

Dieser Standard trennt Quellcode, Build-Ausgabe und auslieferbare Deployment-Pakete. Jedes Projekt muss Full- und Delta-Deployment sauber unterscheiden koennen.

## Full Deployment

- `build/deployment/full/` enthaelt das vollstaendige produktive Paket.
- Der Inhalt wird aus dem aktuellen Build oder dem freigegebenen Quellstand erzeugt.
- Vor dem Befuellen wird der Ordner vollstaendig geleert.
- Es duerfen nur Dateien enthalten sein, die auf dem Zielsystem benoetigt werden.

## Delta Deployment

- `build/deployment/delta/` enthaelt ausschliesslich Dateien der letzten Aenderung.
- Der Ordner dient fuer schnelle Hotfixes oder kleine Releases.
- Vor dem Befuellen wird der Ordner vollstaendig geleert.
- Delta-Inhalte muessen nachvollziehbar zum letzten Release passen.

## Build-Ordner

- Deployment-Artefakte werden nur unter `build/deployment/` abgelegt.
- Build-Skripte muessen dokumentieren, wie Full und Delta erstellt werden.
- Artefakte werden nicht manuell gesammelt, wenn ein reproduzierbarer Script-Schritt moeglich ist.

## FTP-Upload

- FTP oder FTPS ist nur fuer Hosting-Umgebungen ohne bessere Schnittstelle zu verwenden.
- Vor Uploads ist zu pruefen, dass keine Dokumentations- oder lokale Hilfsdateien im Paket enthalten sind.
- Fuer Delta-Uploads wird eine Dateiliste der Aenderungen empfohlen.

## GitHub Pages

- Fuer statische Sites kann GitHub Pages als Deployment-Ziel verwendet werden.
- Deployment-Dateien duerfen nur den publizierten Seiteninhalt enthalten.
- Build-Schritte muessen klar zwischen Quellstruktur und Auslieferungsstruktur trennen.

## Strato- und InfinityFree-Hinweise

- Beide Hosting-Umgebungen haben haeufig Einschränkungen bei Shell-Zugriff, Modulen und Server-Konfiguration.
- Apache-kompatible Projekte sollten eine gepruefte `.htaccess` bereitstellen.
- Relative Pfade, PHP-Versionen, Dateirechte und Rewrite-Regeln muessen vor dem Upload validiert werden.
- Delta-Deployments sind auf solchen Hostern besonders sorgfaeltig zu pruefen, weil partielle Uploads leicht Inkonsistenzen erzeugen.

## Ausschluesse

Folgende Inhalte gehoeren nie in Deployment-Pakete:

- `README.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `TODO.md`
- `SECURITY.md`
- lokale Testdaten
- Editor- oder IDE-Dateien
- Build-Skripte, sofern sie auf dem Zielsystem nicht benoetigt werden

## Mindestpruefung vor Release

- Zielordner wurden geleert.
- Paket enthaelt nur produktive Dateien.
- Secrets wurden nicht uebernommen.
- relevante Config-Dateien passen zur Zielumgebung.
- Full- oder Delta-Variante ist eindeutig gekennzeichnet.