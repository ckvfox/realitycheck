# Security Baseline

Hinweis fuer FPF 2.0: Die kanonische Quelle fuer Security-Lifecycle-Regeln ist `standards/security.md`.

Dieses Dokument bleibt als ergaenzende Baseline aus 1.x bestehen.

## HTTPS

- oeffentliche Anwendungen verwenden durchgaengig HTTPS
- unverschluesselter Zugriff wird auf HTTPS umgeleitet

## HSTS

- produktive Webprojekte setzen `Strict-Transport-Security`, wenn HTTPS stabil verfuegbar ist
- Preload wird nur aktiviert, wenn Subdomains und Langzeitfolgen geprueft sind

## CSP

- `Content-Security-Policy` wird moeglichst restriktiv gesetzt
- inline Skripte und unsichere Quellen werden vermieden

## X-Frame-Options

- `X-Frame-Options: DENY` oder `SAMEORIGIN`, sofern Embedding nicht benoetigt wird

## X-Content-Type-Options

- `X-Content-Type-Options: nosniff` ist fuer Webprojekte Standard

## Referrer-Policy

- nutze mindestens `strict-origin-when-cross-origin`, sofern keine strengere Policy moeglich ist

## Permissions-Policy

- ungenutzte Browser-APIs werden explizit deaktiviert
- projektspezifische Ausnahmen werden dokumentiert

## Sichere Cookies

- Session- und Auth-Cookies verwenden `Secure`, `HttpOnly` und passende `SameSite`-Einstellungen
- Cookie-Lebensdauer wird auf das fachlich notwendige Minimum begrenzt

## .env und Secrets

- `.env` und andere Secret-Dateien gehoeren in `.gitignore`
- `.env.example` enthaelt nur Platzhalter und Erklaerungen
- Secrets werden ueber Hosting- oder CI-Secret-Stores bereitgestellt

## Debug-Ausgaben

- Debug-Ansichten, Stacktraces und sensible Logs sind in Produktion deaktiviert
- Fehlerbehandlung fuer produktive Systeme zeigt nur kontrollierte Informationen

## Mindestmassnahmen

- Abhaengigkeiten regelmaessig aktualisieren
- externe Eingaben validieren und escapen
- Uploads, APIs und Formulare gegen Missbrauch absichern
- Security-Annahmen im Projekt dokumentieren

## Kontext statt Maximalhaertung

- Header-Profile werden an Anwendung, Hosting, SEO, Accessibility und externe Dienste angepasst
- Audits bewerten dokumentierte, getestete Abweichungen nicht automatisch als Fehler
- JS-Challenges und Bot-Weichen duerfen indexierbare Inhalte nicht ungetestet blockieren
