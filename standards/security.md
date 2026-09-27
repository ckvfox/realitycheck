# Security Standard

Version: 2.1.0

## Ziel

Dieser Standard konsolidiert Security-Lifecycle-Regeln fuer Projekte, Audits und Migrationen.

## Mindestinhalte fuer SECURITY.md

Jedes Projekt muss in `SECURITY.md` mindestens folgende Abschnitte enthalten:

- Supported Versions
- Vulnerability Reporting
- Secret Handling
- Production Hardening
- Backup Strategy
- Installer Policy
- Disclosure Policy
- Response Targets

## Secret Handling

- Keine Secrets im Repository.
- Secrets nur ueber Laufzeitkonfiguration oder Secret-Store.
- Nur `${{ secrets.* }}` in GitHub Actions.

## Production Hardening

- HTTPS, sichere Header und kontrollierte Fehlermeldungen.
- Debug-Ausgaben in Produktion deaktivieren.

## HTTP Security Header Baseline

Security-Header sind Pflicht fuer oeffentliche Webprojekte, aber ihre konkrete Auspraegung ist projekt- und hostingabhaengig. Audits duerfen keine starren Maximalwerte verlangen, wenn dadurch legitime Funktionen, SEO, Accessibility oder Shared-Hosting-Betrieb brechen.

### Mindestheader fuer Webprojekte

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin` oder eine bewusst strengere dokumentierte Alternative
- `Content-Security-Policy` mit mindestens `default-src`, `base-uri`, `object-src` und passenden `script-src`/`style-src`/`img-src`/`connect-src` Regeln
- `X-Frame-Options` oder `frame-ancestors` in CSP, passend zur Embedding-Anforderung
- `Strict-Transport-Security`, wenn HTTPS fuer die Produktionsdomain stabil aktiv ist
- `Permissions-Policy` fuer nicht genutzte Browser-APIs

### Kontextabhaengige Entscheidungen

- HSTS `preload` und `includeSubDomains` nur setzen, wenn Subdomains, Staging-Hosts und Rollback-Folgen geprueft sind.
- `X-Frame-Options: DENY` nur verwenden, wenn Embedding fachlich ausgeschlossen ist; sonst `SAMEORIGIN` oder CSP `frame-ancestors` dokumentiert waehlen.
- `style-src 'unsafe-inline'` ist zu vermeiden, kann aber fuer bestehende statische Seiten oder CMS-Layouts zulaessig sein, wenn der Umbau unverhaeltnismaessig waere und das Risiko dokumentiert ist.
- CSP-Hashes oder Nonces sind fuer Inline-Skripte zu bevorzugen. Bei dynamischen Templates muss die Wartbarkeit gegen die Härtung abgewogen werden.
- Externe Dienste wie Karten, Captchas, CDNs, Google Translate, Kalender, OpenGraph-Bilder oder API-Endpunkte muessen explizit in CSP und Dokumentation abgebildet werden.
- COOP/CORP sind sinnvoll fuer isolierte Anwendungen, duerfen aber keine benoetigten Cross-Origin-Ressourcen blockieren.

## SEO- und Accessibility-Kompatibilitaet

- Security-Massnahmen duerfen indexierbare Inhalte nicht ohne dokumentierte Ausnahme vor Suchmaschinen, Accessibility-Tools oder lokalen Webchecks verstecken.
- JavaScript-Challenges, Bot-Weichen und User-Agent-basierte Auslieferung sind nur erlaubt, wenn normale Nutzer, verifizierte Crawler, Accessibility-Tools und Audit-Tools getestete Pfade haben.
- Wenn Crawler einen statischen Snapshot erhalten, muss `Vary: User-Agent` gesetzt und die Snapshot-Erzeugung dokumentiert werden.
- Einfache Crawler-Markierung fuer CDN/WAF-Ausnahmen ist gegenueber serverseitigen Umleitungen oder JS-Gates zu bevorzugen.

## Apache/.htaccess Regeln

- Apache-Projekte schuetzen nicht-oeffentliche Verzeichnisse wie `includes/`, `database/`, `backups/`, `docs/`, `scripts/`, `build/`, `.git/`, `.github/` und `.vscode/`, sofern diese im Webroot liegen.
- Upload-Verzeichnisse blockieren ausfuehrbare Skripte, z.B. `php`, `phtml` und `phar`.
- Secret- und Schluesseldateien wie `.env*`, `*.pem`, `*.key`, `*.pfx`, `*.p12`, SQL-Dumps, Logs, Backups und lokale Skripte duerfen nicht direkt auslieferbar sein.
- HTTPS-Rewrites beruecksichtigen Shared-Hosting- und Proxy-Header wie `X-Forwarded-Proto` oder `X-Forwarded-SSL`, um Redirect-Loops zu vermeiden.

## security.txt

Pfad:

`/.well-known/security.txt`

### Pflichtregeln

- `Contact:` muss mindestens einen `mailto:`-Eintrag enthalten.
- `Contact:` soll zusaetzlich eine `https://`-Kontaktadresse enthalten.
- Keine Platzhalter wie `example.com` oder `noreply@example.com`.
- `Expires:` darf maximal 12 Monate in der Zukunft liegen und nicht abgelaufen sein.

### Empfohlener Standard

- GitHub Security Advisories URL als zusaetzlicher Kontakt oder Policy-Verweis.

## Validator-Verhalten

Validatoren muessen erkennen:

- fehlende Eintraege
- ungueltige Eintraege
- abgelaufene `Expires`-Werte
