# Documentation Standard

## Ziel

Jedes Projekt muss fuer Menschen und KI-Agenten schnell lesbar, pruefbar und wartbar sein. Dokumentation ist Teil des Lieferumfangs und kein optionaler Nachtrag.

## README-Regeln

- beschreibt Zweck, Zielgruppe und Scope des Projekts
- enthaelt Setup, Konfiguration, lokale Entwicklung, Build und Deployment
- erklaert Struktur, Abhaengigkeiten und bekannte Grenzen
- verweist auf weiterfuehrende Dokumentation in `docs/`
- unterscheidet bei Bestandsprojekten zwischen bestehender produktiver Struktur und FPF-Zielstruktur fuer neue Projekte
- dokumentiert Abweichungen von `standards/structure.md`, wenn produktive Pfade nicht risikoarm umbenannt werden koennen

## AGENTS-Regeln

- beschreibt Projektart, Hosting, Deployment-Ziel und relevante Tools
- dokumentiert lokale Entwicklung, Build- und Deploy-Schritte
- listet bekannte Probleme, Workarounds und agentenspezifische Regeln
- hilft KI-Agenten, risikoarme Aenderungen vorzunehmen
- benennt Bestandsschutz fuer produktive Pfade, Hosting-Prozesse und Deployment-Ordner

## CHANGELOG-Regeln

- fuehrt relevante Aenderungen pro Version oder Release-Einheit auf
- trennt mindestens `Added`, `Changed`, `Fixed`, `Removed`, wenn sinnvoll
- dokumentiert auch migrationsrelevante oder sicherheitsrelevante Aenderungen

## TODO-Regeln

- sammelt naechste Aufgaben, technische Schulden und offene Entscheidungen
- markiert Prioritaet, Status oder Kontext, wenn dies fuer die Arbeit wichtig ist
- unterscheidet klar zwischen Muss-Aufgaben und spaeteren Verbesserungen

## SECURITY-Regeln

- beschreibt Security-Basis, Secret-Handling, Meldeweg und Risiken
- nennt projektspezifische Schutzmassnahmen und bekannte Einschraenkungen
- wird aktualisiert, wenn sich Sicherheitsannahmen aendern

## Troubleshooting-Regeln

- wiederkehrende Probleme werden dokumentiert statt nur ad hoc geloest
- Eintraege sollen Ursache, Symptom, Workaround und nachhaltige Loesung trennen
- betroffene Umgebungen wie Windows, Linux, CI oder Hosting sollen klar benannt werden

## docs/README.md

Wenn `docs/` existiert, soll `docs/README.md` als kurzer Index gepflegt werden:

- Zweck des Ordners
- wichtigste Dokumente und Runbooks
- Hinweis, ob `docs/` reine Zusatzdokumentation oder produktiver Webroot ist
- Struktur- oder Bestandsschutzhinweise, wenn relevant
