# AGENTS Standard

Version: 2.1.0

## Pflichtabschnitte in AGENTS.md

- Projekt
- Lokale Entwicklung
- Build
- Deployment
- Bekannte Probleme
- Framework Candidates
- Lessons Learned
- Restricted Files
- Allowed Work
- Deployment Packaging Rules

## Empfohlener Abschnitt

- Known Constraints
- Local Toolchain
- Setup Check
- Copilot / AI Tooling

## Sicherheitsgrenzen

`AGENTS.md` darf niemals enthalten:

- Passwoerter
- API Keys
- Zugangsdaten
- Secrets

## Deployment-Hinweis

`AGENTS.md` soll fuer Deployment nur auf `standards/deployment.md` verweisen und keine abweichenden Packaging-Regeln definieren.

## Lokale Entwicklungsregeln fuer Agenten

- Agenten arbeiten vom Repository-Root aus und pruefen den aktuellen Pfad, bevor Build-, Test- oder Deployment-Befehle laufen.
- Agenten verwenden dokumentierte Projektbefehle aus README, AGENTS, package/composer/requirements-Dateien oder `scripts/`, bevor neue Befehle erfunden werden.
- Agenten pruefen vorhandene Dependency-Manifeste, bevor Installationen vorgeschlagen oder ausgefuehrt werden.
- Agenten dokumentieren fehlende lokale Tools als Known Constraint, statt dieselbe Diagnose in jeder Sitzung neu zu starten.
- Projekt-AGENTS sollen explizit nennen, ob globale Tools erlaubt sind oder ob lokale/venv/vendor/node_modules-Installationen bevorzugt werden.
- Pfade in Agent-Regeln sollen repo-relativ sein. Absolute lokale Pfade sind nur fuer projektspezifische Host-Ausnahmen erlaubt.

## Copilot- und AI-Tooling

- Projekte, die GitHub Copilot im Repository-Kontext nutzen, sollen `.github/copilot-instructions.md` aus `templates/.github/copilot-instructions.md` uebernehmen und projektspezifisch anpassen.
- Stack- oder dateitypspezifische Regeln sollen unter `.github/instructions/*.instructions.md` liegen.
- Empfohlene FPF-Vorlagen liegen unter `templates/.github/instructions/`.
- Copilot-Instructions duerfen AGENTS-Regeln konkretisieren, aber keine widerspruechlichen Sicherheits-, Deployment- oder Secret-Regeln definieren.
- Bestehende Projekte erhalten fehlende Copilot-Instructions zunaechst als Audit-Recommendation, nicht als harte Pflichtverletzung.
