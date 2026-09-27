# Versioning Standard

## Grundsatz

Fox Project Framework und abgeleitete Projekte sollen eine nachvollziehbare Versionierungsstrategie verwenden. Empfohlen ist semantische Versionierung.

## Semantische Versionierung

- Major: inkompatible Aenderungen
- Minor: neue kompatible Funktionen oder Standards
- Patch: Korrekturen und kleine Verbesserungen

## Release-Prozess fuer das Framework

- Major Release (`2.0`, `3.0`, ...), wenn konsolidierte Struktur, Compliance-System oder Standards mit potenziell brechender Wirkung eingefuehrt werden
- Minor Release (`2.x`), wenn neue Standards entstehen, neue Best Practices entstehen oder Lessons Learned in das Framework uebernommen werden
- Patch Release (`2.0.x` oder entsprechend aktueller Minor-Linie), wenn Dokumentation korrigiert oder Templates korrigiert werden

## Anwendung

- Framework-Versionen werden im README und CHANGELOG sichtbar gehalten
- Projekt-Releases sollten mit Tags, Changelog und Deployment-Stand korrespondieren
- Migrationsrelevante Aenderungen muessen im Changelog gekennzeichnet sein
- Framework Candidates wechseln erst nach Review und bewusster Freigabe in einen Release

## Fuer Bestandsprojekte

- wenn keine saubere Versionshistorie existiert, wird ein klarer Startpunkt definiert
- ab diesem Punkt werden Releases konsistent dokumentiert