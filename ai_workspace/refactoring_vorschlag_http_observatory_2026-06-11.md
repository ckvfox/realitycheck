# Refactoring-Vorschlag: SEO, Security, Performance

Stand: 2026-06-11  
Basis: HTTP Observatory Report fuer `realitycheck.great-site.net` mit Score `F`, 10/100, 5/10 Tests bestanden.

## Kurzfazit

Der groesste Hebel liegt nicht im Frontend-Code, sondern in der Auslieferung: Im Repository existiert bereits eine `.htaccess` mit CSP, `X-Frame-Options`, `X-Content-Type-Options` und `Referrer-Policy`, der Observatory-Scan sieht diese Header aber nicht. Das spricht dafuer, dass die Datei nicht auf dem gescannten Host aktiv ist, der Hoster `Header`-Direktiven nicht ausfuehrt, die falsche Domain gescannt wurde oder ein Redirect/Proxy die Header entfernt.

Vor fachlichem Refactoring sollte deshalb zuerst die Deployment- und Header-Wirksamkeit geklaert werden. Ohne diesen Schritt werden Code-Aenderungen den Observatory-Score kaum verbessern.

## Prioritaet 1: Header-Auslieferung und HTTPS erzwingen

### Problem

- Observatory meldet fehlende CSP-, HSTS-, Referrer-, `nosniff`- und Frame-Protection-Header.
- Die lokale `.htaccess` enthaelt bereits mehrere dieser Header.
- Observatory meldet zusaetzlich: HTTP leitet nicht zuerst auf HTTPS derselben Domain weiter.

### Ziel

Alle sicherheitsrelevanten Header muessen auf der finalen HTTPS-Antwort sichtbar sein. HTTP-Aufrufe muessen zuerst sauber auf dieselbe HTTPS-Hostadresse zeigen.

### Vorschlag

1. Deployment pruefen:
   - Sicherstellen, dass `.htaccess` auf `realitycheck.great-site.net` im tatsaechlichen Webroot liegt.
   - Per `curl -I http://realitycheck.great-site.net/` und `curl -I https://realitycheck.great-site.net/` pruefen, welche Header wirklich ankommen.
   - Falls InfinityFree/Hosting `mod_headers` nicht erlaubt, alternative Header-Konfiguration des Hosters nutzen oder Hosting wechseln.

2. HTTPS-Redirect vorziehen:
   - HTTP muss zuerst auf `https://realitycheck.great-site.net/...` gehen.
   - Erst danach sollten optionale Canonical- oder Zielhost-Redirects greifen.

3. HSTS stufenweise einfuehren:
   - Start: `Strict-Transport-Security: max-age=86400`
   - Nach Validierung: `max-age=31536000; includeSubDomains`
   - Preload erst spaeter, wenn Domain und Subdomains dauerhaft HTTPS-sicher sind.

4. Header-Set vereinheitlichen:
   - `Content-Security-Policy`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-Content-Type-Options: nosniff`
   - `Permissions-Policy` fuer ungenutzte Browser-APIs
   - `Cross-Origin-Resource-Policy: same-origin` oder bewusst `cross-origin`, falls externe Einbettung benoetigt wird
   - `frame-ancestors 'self'` in CSP statt nur `X-Frame-Options`

### Akzeptanzkriterien

- Observatory erkennt CSP, HSTS, Referrer-Policy, `nosniff` und Frame-Schutz.
- HTTP-URL liefert einen 301/308-Redirect auf HTTPS.
- Keine Seite verliert durch die CSP Chart.js, Leaflet, Google Translate oder OpenStreetMap-Funktionalitaet.

## Prioritaet 2: CSP realistisch haerten

### Ist-Zustand

Die Seite nutzt externe Ressourcen von:

- `cdn.jsdelivr.net`
- `unpkg.com`
- `translate.google.com`, `translate.googleapis.com`, `*.gstatic.com`
- `*.tile.openstreetmap.org`
- `raw.githubusercontent.com` als GeoJSON-Fallback

Zusatzrisiko: Es gibt mehrere `innerHTML`-Stellen. Viele sind fuer Templates vertretbar, aber Markdown-Rendering in `page_analysis.js` und dynamische Datenanzeige sollten separat abgesichert werden.

### Vorschlag

1. CSP in zwei Stufen fuehren:
   - Stufe A: funktional kompatible CSP mit erlaubten externen Quellen.
   - Stufe B: strengere CSP nach Entfernen/Reduzieren externer Runtime-Abhaengigkeiten.

2. Externe Libraries lokal vendoren:
   - Chart.js, Leaflet, Pako und Marked lokal ablegen.
   - Versionen fixieren.
   - SRI fuer verbleibende CDN-Ressourcen ergaenzen.

3. Google Translate isoliert bewerten:
   - Die Integration braucht breite Script-/Style-/Connect-Freigaben.
   - Wenn Observatory-/Security-Score wichtiger ist als Auto-Translate, Feature optional deaktivieren oder hinter Consent nur auf Seiten laden, die es wirklich brauchen.

4. Markdown sanitizen:
   - `marked(...)`-Output nicht ungefiltert in `innerHTML` schreiben.
   - DOMPurify lokal vendoren oder Markdown server-/buildseitig in kontrolliertes HTML umwandeln.

5. `innerHTML` reduzieren:
   - Tabellen, Selects und KPI-Boxen schrittweise auf `createElement`/`textContent` umbauen.
   - Template-HTML nur fuer statische, kontrollierte Markups behalten.

### Akzeptanzkriterien

- CSP laeuft ohne Console-Violations auf `countries.html`, `world.html`, `analysis.html` und `overall_ranking_countries.html`.
- Keine dynamischen Inhalte aus JSON/Markdown werden ungefiltert als HTML gerendert.
- Externe CDN-Abhaengigkeiten sind entweder lokal oder mit SRI abgesichert.

## Prioritaet 3: Performance-Refactoring

### Beobachtungen

- `style.css` ist zentral und relativ gross.
- Mehrere Seiten laden grosse Daten- und Visualisierungsbibliotheken.
- `world.html` enthaelt Meta-Tags gegen Caching, waehrend `.htaccess` Caching aktivieren will.
- Nur wenige Bilder haben feste Dimensionen oder Lazy-Loading.

### Vorschlag

1. Seitenspezifisches CSS splitten:
   - `style.css` in `base.css`, `layout.css`, `components.css` und optionale Seiten-CSS aufteilen.
   - Kritische Above-the-fold-Regeln klein halten.

2. JavaScript nach Seitenbedarf laden:
   - Chart.js nur auf Seiten mit Charts.
   - Leaflet nur auf Seiten mit Karten.
   - Google Translate erst nach Consent dynamisch laden.
   - `core.js` aufteilen in Header/Footer, Tracking, Translate, Maps, KPI-Helpers.

3. Caching konsistent machen:
   - Keine globalen No-Cache-Meta-Tags in HTML, ausser fuer echte Debug-Seiten.
   - Statische Assets mit langer Cache-Zeit und Dateiversionierung ausliefern.
   - JSON-Daten differenzieren: Metadaten kurz cachen, versionierte Daten laenger cachen.

4. Bilder optimieren:
   - `width`/`height` fuer Logo, Translate-Icon und About-Bild setzen.
   - Nicht kritische Bilder mit `loading="lazy"` und `decoding="async"`.
   - PNGs pruefen und bei Bedarf WebP/AVIF-Varianten generieren.

5. Fallback-Requests reduzieren:
   - GeoJSON-Fallback von GitHub vermeiden oder lokal/versioniert halten.
   - Fehlende lokale Daten sollten im Build auffallen, nicht erst im Browser.

### Akzeptanzkriterien

- Lighthouse Performance verbessert sich messbar auf Mobile und Desktop.
- Kein Layout Shift durch Bilder ohne Groessenangaben.
- Wiederholte Besuche laden CSS/JS/Bilder aus Cache.
- Keine unnoetigen CDN-Requests auf Seiten ohne entsprechende Funktion.

## Prioritaet 4: SEO-Struktur bereinigen

### Beobachtungen

- Hauptseiten haben teils gute Titles und Descriptions.
- Einige Seiten wie `about.html`, `data_glossary.html`, `privacy.html`, `impressum.html` haben weniger vollstaendige SEO-Metadaten.
- OpenGraph-URLs zeigen auf `realitycheck.ckvfox.net`, gescannt wurde aber `realitycheck.great-site.net`.
- `index.html` ist nur ein sehr kleiner Script-Einstieg.

### Vorschlag

1. Canonical-Strategie festlegen:
   - Eine Hauptdomain definieren.
   - Alle `og:url`, `twitter:url`, Canonicals und Redirects darauf ausrichten.

2. `index.html` zu echtem HTML-Einstieg machen:
   - Mindestens Title, Description, Canonical, NoScript-Fallback und statischen Link zur Hauptseite.
   - Wenn Redirect per JS noetig bleibt, zusaetzlich serverseitig oder per Meta-Fallback absichern.

3. Meta-Daten vereinheitlichen:
   - Pro Seite eindeutiger Title.
   - Pro Seite konkrete Description.
   - Canonical-Link.
   - Optional `og:image` und `twitter:image` mit lokalem Preview-Bild.

4. Technische SEO-Dateien ergaenzen:
   - `robots.txt`
   - `sitemap.xml`
   - Konsistente 404-Seite, falls Hoster das erlaubt.

5. Semantik pruefen:
   - Genau ein sinnvoller `h1` pro Seite.
   - Navigation und Footer semantisch stabil.
   - Interaktive Controls mit Labels/ARIA, wo noetig.

### Akzeptanzkriterien

- Alle Hauptseiten haben Canonical, Title, Description und konsistente Social-Meta-Daten.
- Die Hauptdomain ist eindeutig.
- `robots.txt` und `sitemap.xml` sind erreichbar.
- Google Search Console meldet keine Canonical-Konflikte.

## Umsetzungsvorschlag in Etappen

### Etappe 1: Wirksame Server-Header

Aufwand: klein bis mittel, abhaengig vom Hoster  
Risiko: niedrig, wenn stufenweise getestet

- `.htaccess`-Deployment verifizieren.
- HTTPS-Redirect und HSTS ergaenzen.
- Header per Live-Request pruefen.
- Observatory erneut ausfuehren.

### Etappe 2: CSP-kompatible Frontend-Basis

Aufwand: mittel  
Risiko: mittel, wegen Google Translate, Leaflet und Markdown

- CSP-Report-Only lokal/auf Staging testen, falls moeglich.
- CDN-Versionen fixieren und SRI ergaenzen.
- `analysis.html`/`page_analysis.js` sanitizen.
- Console-Violations auf Hauptseiten beseitigen.

### Etappe 3: Performance-Schnitt

Aufwand: mittel bis gross  
Risiko: mittel

- `core.js` in Module/Funktionsbereiche aufteilen.
- CSS nach gemeinsam/seitenspezifisch trennen.
- Cache-Strategie vereinheitlichen.
- Bildgroessen und Lazy-Loading ergaenzen.

### Etappe 4: SEO-Konsolidierung

Aufwand: klein bis mittel  
Risiko: niedrig

- Hauptdomain entscheiden.
- Canonicals und Social-URLs aktualisieren.
- `index.html`, `robots.txt`, `sitemap.xml` erstellen/verbessern.
- Search-Console-relevante Seiten pruefen.

## Empfohlene Reihenfolge

1. Live-Header-Diagnose auf `realitycheck.great-site.net`.
2. `.htaccess` oder Hosting-Konfiguration so anpassen, dass Header wirklich ausgeliefert werden.
3. HTTPS-Redirect und HSTS testen.
4. CSP funktionsfaehig machen, danach haerten.
5. Performance-Aufteilung von CSS/JS.
6. SEO-Kanonisierung und Sitemap.

## Entscheidungspunkt

Vor dem eigentlichen Umbau sollte entschieden werden, welche Domain die kanonische Hauptdomain ist:

- `realitycheck.great-site.net`
- `realitycheck.ckvfox.net`
- eine andere Produktionsdomain

Diese Entscheidung beeinflusst Redirects, HSTS-Risiko, Canonicals, OpenGraph-URLs, Search Console und Observatory-Bewertung.
