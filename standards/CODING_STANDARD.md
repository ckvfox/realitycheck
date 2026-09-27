# Coding Standard

## Grundsaetze

- bevorzuge einfache, gut lesbare Loesungen
- behebe Ursachen statt nur Symptome, wenn der Aufwand vertretbar ist
- vermeide unnoetige Abstraktion und Copy-Paste

## Struktur

- Quellcode liegt in `src/`, Tests in `tests/`
- Fachlogik, Infrastruktur und Konfiguration sollen sinnvoll getrennt sein
- Dateien und Ordner sollen klar benannt sein

## Qualitaet

- Eingaben validieren, Fehler explizit behandeln, Seiteneffekte begrenzen
- Logging und Fehlermeldungen muessen fuer Betrieb und Analyse hilfreich sein
- tote oder auskommentierte Altlogik wird nicht konserviert, wenn sie keinen Zweck mehr erfuellt

## Tests

- neue oder geaenderte Kernlogik soll nach Moeglichkeit mit Tests abgesichert werden
- wenn Tests fehlen, muss das Risiko dokumentiert werden

## Dokumentation

- oeffentliche Schnittstellen, Build-Besonderheiten und bekannte Risiken muessen dokumentiert sein
- relevante Architekturentscheidungen gehoeren in README oder docs/