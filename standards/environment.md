# Environment Standard

Version: 2.1.0

## Grundregeln

- `.env.example` ist Pflicht, sobald Environment-Variablen genutzt werden.
- Jede Variable muss dokumentiert sein.
- Keine echten Secrets in `.env.example`.
- Es sind nur Platzhalterwerte erlaubt.

## Dokumentationspflicht fuer Variablen

Jede Variable soll mindestens enthalten:

- Name
- Zweck
- erwartetes Format
- Beispiel-Platzhalter
- ob Pflicht oder optional

## Python-Abhaengigkeiten

- Alle Python-Abhaengigkeiten muessen in `requirements.txt` enthalten sein.
- Versionen sollen als Mindestversion angegeben werden.

Beispiel:

```text
requests>=2.31
```

## Validierung

- Audit prueft Vorhandensein von `.env.example` und `requirements.txt` (bei Python-Projekten).
- Secrets oder produktive Zugangsdaten im Repository sind nicht erlaubt.

## Lokale Toolchain und Dependencies

- Jedes Projekt dokumentiert die benoetigten lokalen Runtimes und Paketmanager, z.B. PHP, Composer, Node/npm, Python, PowerShell, WP-CLI oder Datenbank-CLI.
- Fuer jede Runtime soll ein Pruefbefehl angegeben werden, z.B. `php -v`, `python --version`, `node --version`, `npm --version`, `composer --version`.
- Dependency-Installationen muessen aus manifestierten Projektdateien erfolgen. Agenten pruefen zuerst vorhandene Manifestdateien und installieren nicht aus Vermutung.
- Lokale Installationspfade, globale Tools und IDE-spezifische Pfade werden nicht als verbindliche Projektvoraussetzung vorausgesetzt. Falls ein Projekt sie braucht, werden sie als optionale Host-Konfiguration dokumentiert.
- Wiederholte Installationsversuche ohne neuen Befund sind zu vermeiden. Wenn eine Dependency fehlt, wird Ursache, Befehl und Ergebnis im Projektkontext dokumentiert.
- Windows-Pfade mit Leerzeichen muessen in dokumentierten Befehlen gequotet oder durch repo-relative Pfade ersetzt werden.

## Setup-Check

Projekte sollen einen kurzen lokalen Setup-Check dokumentieren:

1. Repository-Root bestimmen.
2. Runtime-Versionen pruefen.
3. Dependency-Manifeste pruefen.
4. `.env.example` gegen benoetigte Variablen abgleichen.
5. Build-, Test- oder Deployment-Befehl trocken oder lokal validieren.

## Struktur- und Konfigurationsinventar

README oder AGENTS sollen fuer bestehende Projekte knapp dokumentieren:

- wo produktive Assets liegen
- wo fachliche Daten, Datenbankartefakte und generierte Reports liegen
- welche lokalen Skripte oder Tools nicht deployed werden
- welche Deployment-Pfade verwendet werden
- welche Abweichungen vom FPF-Zielstandard bewusst beibehalten werden
