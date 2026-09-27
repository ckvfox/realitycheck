# SEO Baseline

## Title

- jede relevante Seite hat einen eindeutigen, beschreibenden Titel
- Titles sollen Suchintention und Markenbezug sinnvoll kombinieren

## Meta Description

- jede oeffentliche Zielseite enthaelt eine eigenstaendige Meta Description
- Beschreibungen sollen Inhalt und Nutzen klar wiedergeben

## Canonical

- kanonische URLs werden fuer indexierbare Inhalte gesetzt
- Duplikate durch Varianten, Parameter oder Parallelpfade werden vermieden
- `/index.html` oder `/index.php` werden auf `/` normalisiert, wenn das Hosting dies unterstuetzt

## robots.txt

- Webprojekte pflegen eine bewusste `robots.txt`
- unproduktive oder nicht oeffentliche Bereiche werden gezielt gesteuert

## sitemap.xml

- indexierbare Seiten stehen in `sitemap.xml`
- die Sitemap wird aktuell gehalten und bei Bedarf automatisiert erzeugt

## Crawler und Audits

- indexierbare Inhalte muessen fuer Suchmaschinen, Accessibility-Tools und lokale Webchecks erreichbar sein
- JS-Challenges, CDN/WAF-Regeln und Bot-Weichen brauchen dokumentierte Ausnahmen oder Tests
- bei User-Agent-abhaengigen Snapshots wird `Vary: User-Agent` gesetzt

## OpenGraph

- zentrale Seiten erhalten `og:title`, `og:description`, `og:type`, `og:url` und passende Vorschaubilder

## Strukturierte Daten

- strukturierte Daten werden eingesetzt, wenn sie fachlich sinnvoll und valide sind
- Schema-Markup soll zur realen Seitenfunktion passen

## Alt-Texte

- informative Bilder erhalten aussagekraeftige Alt-Texte
- dekorative Bilder werden korrekt neutral behandelt

## Sprechende URLs

- URLs sollen kurz, stabil und inhaltlich lesbar sein
- kryptische Parameterstrukturen fuer zentrale Inhalte sind zu vermeiden
