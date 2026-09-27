# GitHub Actions Standard

## CI

- jedes aktive Projekt sollte eine minimale CI fuer Validierung besitzen
- CI laeuft mindestens bei Pushes und Pull Requests auf relevante Branches
- Workflows setzen explizite `permissions`; Standard ist `contents: read`

## Tests

- automatisierte Tests werden in Workflows integriert, sobald das Projekt welche besitzt
- fehlende Tests sind im README oder TODO transparent zu machen

## Linting

- Linting oder statische Analyse sollen frueh ausfuehrbar sein und fehlerhafte Builds blockieren, wenn das Projekt reif genug ist

## Build

- Build-Workflows erzeugen reproduzierbare Artefakte
- Build-Fehler muessen klar sichtbar und diagnostizierbar sein

## Deployment

- Deployments aus GitHub Actions erfolgen nur mit klaren Guards, Environments und Secrets
- Full- und Delta-Deployment muessen bewusst getrennt werden
- Deployment-Jobs sollen `environment`, Branch-Bedingungen oder manuelle Freigabe nutzen, wenn sie produktive Systeme veraendern

## Secrets

- GitHub Secrets enthalten keine Testwerte, sondern echte geschuetzte Laufzeitkonfiguration
- Zugriff auf Secrets wird auf benoetigte Workflows und Environments begrenzt
- Secrets duerfen nicht in Logs geschrieben, als Artefakt hochgeladen oder in Build-Ausgaben eingebettet werden

## Supply Chain

- Action-Referenzen wie `@main`, `@master` oder `@latest` sind nicht zulaessig.
- Drittanbieter-Actions sollen geprueft und bei erhoehtem Risiko per Commit-SHA gepinnt werden.
- Dependency-Review, SCA oder SAST werden empfohlen, sobald passende Manifestdateien und ein reifer Projektstand vorliegen.

## Manuelle und geplante Workflows

- `workflow_dispatch` eignet sich fuer manuelle Freigaben oder Betriebsvorgaenge
- `schedule` eignet sich fuer regelmaessige Audits, Backups, Reports oder Wartungschecks
