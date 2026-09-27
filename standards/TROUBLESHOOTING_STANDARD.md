# Troubleshooting Standard

## Ziel

Bekannte Probleme werden dauerhaft dokumentiert, damit dieselben Ausfaelle nicht immer wieder neu analysiert werden muessen.

## Dokumentationsregeln

- jeder Eintrag beschreibt Symptom, wahrscheinliche Ursache, Workaround und nachhaltige Loesung
- betroffene Plattform oder Umgebung wird benannt
- offene Restunsicherheiten werden markiert

## Windows- und PowerShell-Probleme

- Pfadlaengen, Berechtigungen, Ausfuehrungsrichtlinien und Zeilenenden explizit beachten
- PowerShell-spezifische Build- oder Skriptunterschiede dokumentieren

## Pfadprobleme

- relative und absolute Pfade in Build-, Deploy- und Tooling-Skripten pruefen
- Leerzeichen in Pfaden und unterschiedliche Separatoren bedenken

## Abhaengigkeitsprobleme

- Versionkonflikte, fehlende Pakete und plattformspezifische Binaerdateien dokumentieren
- bekannte Minimalversionen von Laufzeit und Tooling festhalten

## Hosting-Probleme

- Limits von Shared Hosting, Dateirechten, Rewrite-Regeln und Laufzeitversionen beschreiben
- Unterschiede zwischen lokaler Umgebung und Zielhosting sichtbar machen

## API-Probleme

- Authentifizierung, Ratenlimits, CORS und Fehlerantworten dokumentieren
- bekannte Ausfallmodi und Retry-Strategien festhalten

## Lokale Entwicklungsprobleme

- Setup-Fallen, fehlende Variablen, Ports, Dateirechte und OS-Unterschiede dokumentieren
- Wege fuer schnelles Onboarding und Reproduktion priorisieren