# AI Agent Standard

## Pflichtlektuere vor Aenderungen

Vor jeder Aenderung muss der Agent mindestens folgende Dateien des Zielprojekts lesen:

- `README.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `TODO.md`

## Pflichtpruefung nach Aenderungen

Nach jeder Aenderung muss der Agent pruefen, ob folgende Bereiche aktualisiert oder validiert werden muessen:

- `README.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `TODO.md`
- `SECURITY.md`
- `robots.txt`
- `sitemap.xml`
- `build/deployment/full`
- `build/deployment/delta`

## Pflichtpruefung nach Abschluss jeder Aufgabe

Nach Abschluss jeder Aufgabe muss der Agent zusaetzlich pruefen:

- Wurde ein neues Problem geloest?
- Wuerde mindestens ein weiteres Projekt davon profitieren?

Wenn beide Fragen mit Ja beantwortet werden koennen, erzeugt der Agent:

- eine Lesson Learned
- einen Framework Candidate

Der Agent darf dabei nicht automatisch das Framework selbst aendern.

## Pflichtpruefung nach jedem Audit

Nach jedem Audit muss der Agent pruefen:

- Koennte diese Erkenntnis das Framework verbessern?

Wenn Ja, ist ein Framework Candidate zu erzeugen.

## Sicherheitsgrenzen

- keine Secrets ausgeben, kopieren oder einchecken
- keine produktiven Dateien ohne Kontext oder Validierung riskant umbauen
- Unsicherheiten und Annahmen offen benennen

## Arbeitsweise

- zuerst den Standard verstehen, dann lokal und minimal aendern
- nach der ersten substanziellen Aenderung sofort eine passende Validierung ausfuehren
- keine Deployments mit Dokumentationsdateien erzeugen
- bekannte Probleme in AGENTS, TODO oder Troubleshooting-Dokumentation nachziehen
- wiederverwendbare Erkenntnisse als Lessons Learned und Framework Candidates erfassen