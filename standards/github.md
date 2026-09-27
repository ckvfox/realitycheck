# GitHub Standard

Version: 2.1.0

## Mindestanforderungen

- Mindestens ein Workflow muss im Projekt vorhanden sein.
- Workflows setzen `permissions` explizit; Standard ist `contents: read`.
- Deployments verwenden klare Guards wie Branch-Bedingungen, Environments, manuelle Freigabe oder `workflow_dispatch`.

## Python-Projekte

Pflichtjobs in CI:

- Ruff
- JSON Schema Validation

## WordPress-Plugins

Pflichtpruefungen in CI:

- FPF-Manifest und Profil-Compliance mit dem vendorten Framework-Pruefer;
- Syntaxpruefung aller versionierten PHP-Dateien;
- vorhandene projektspezifische Tests;
- explizite Workflow-Berechtigung `contents: read`.

Die Vorlage unter
`templates/.github/workflows/wordpress-plugin-ci.yml` ist der Ausgangspunkt
und wird um die vorhandenen Testbefehle des Plugins ergaenzt.

Der Statuscheck `FPF compliance` soll fuer den Hauptbranch verpflichtend sein.
Wenn der GitHub-Tarif Branch-Schutz fuer ein privates Repository nicht
unterstuetzt, wird diese technische Grenze dokumentiert; der Workflow bleibt
trotzdem bei Push und Pull Request aktiv.

Die Manifestwerte sind `branch_protection: required` oder, ausschliesslich
nach bestaetigter GitHub-API-Ablehnung,
`branch_protection: unavailable-private-repo-plan`. Der lokale Pruefer
validiert die Deklaration; die tatsaechliche GitHub-Regel wird separat ueber
die Repository-Einstellungen beziehungsweise API kontrolliert.

## Security in Workflows

- Nur `${{ secrets.* }}` ist fuer Geheimnisse zulaessig.
- Hardcodierte Zugangsdaten oder Tokens sind nicht erlaubt.
- Actions duerfen nicht ueber mutable Referenzen wie `@main`, `@master` oder `@latest` eingebunden werden.
- Drittanbieter-Actions sollen auf Vertrauenswuerdigkeit und, wenn sinnvoll, SHA-Pinning geprueft werden.
- Dependency-Review, SCA oder SAST werden empfohlen, sobald passende Manifestdateien und ein reifer Projektstand vorliegen.

## Standardvorlagen

Jedes Repository sollte folgende Templates bereitstellen:

- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

Wenn GitHub Copilot im Projekt genutzt wird, werden zusaetzlich empfohlen:

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md` fuer stack- oder dateitypspezifische Regeln

## Governance

- Pull Requests enthalten Scope, Risiko und Testhinweise.
- Security-, Deployment- und Compliance-relevante Aenderungen erhalten erhoehte Review-Sorgfalt.
- AI-Tooling-Regeln muessen mit `AGENTS.md`, Security- und Deployment-Standards konsistent bleiben.
