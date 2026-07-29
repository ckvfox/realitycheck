# Deutschland 2036 – Szenariomethode

## Zweck und Lesart

Die Erweiterung auf `germany-dossier.php` ist eine explorative
Sensitivitätsanalyse. Sie ist keine Prognose, kein Haushaltsrechner und weist
keine Eintrittswahrscheinlichkeiten aus. Alle numerischen Ergebnisse sind
Indexbandbreiten mit `2026 = 100`. Breite Bänder sind Absicht: Sie machen
Unsicherheit sichtbar und vermeiden eine Genauigkeit, die die Quellen nicht
hergeben.

Das mittlere Szenario „Anpassung unter Druck“ ist der Standard. Es ist kein
arithmetischer Mittelwert. Es kombiniert fortgesetzte Klima- und
Demografiebelastungen mit teilwirksamen Investitionen, Migration, Energiewende
und Technologiediffusion.

Die Oberfläche öffnet dieses Standardszenario zuerst und stellt bei allen drei
Szenarien eine kurze Erzählung vor die einzelnen Treiber. Damit wird zuerst der
zusammenhängende gesellschaftliche Verlauf beschrieben; die nachfolgenden
Stichpunkte legen anschließend offen, aus welchen Annahmen diese Erzählung
gebildet wird.

## Evidenzklassen

- **Beobachtung:** bereits gemessene Entwicklung, etwa DWD-Klimadaten.
- **Amtliche Projektion:** Fortschreibung veröffentlichter Annahmen, etwa die
  Destatis-Bevölkerungsvorausberechnung.
- **Institutionelle Analyse:** begründet Wirkungsrichtung oder Risikokanal,
  etwa OECD, IEA, EZB und EU-Kommission.
- **Politische Verpflichtung:** beschlossenes Ziel, dessen Umsetzung offen
  bleibt, etwa das NATO-Ziel für 2035.
- **Eigene Modellannahme:** 2036-Bänder, Slidergewichte und Stressereignisse.

Die vollständige Quellen- und Annahmenmatrix wird auf der geschützten Seite
angezeigt und liegt in `analysis-private/germany-2036-scenarios.php`. Ein
US-Rückzug, eine Taiwan-Eskalation oder ein Bündnisbruch werden ausschließlich
als Stressannahmen behandelt, nie als Vorhersage.

## Rechenweg

Jedes Grundszenario besitzt für sechs Wirkungsgrößen ein unteres und oberes
2036-Ende. Die acht Regler laufen ganzzahlig von -2 bis +2. Für eine Kennzahl
`m` wird dasselbe transparente additive Delta auf beide Bandgrenzen angewandt:

`Delta_m = Summe((Regler_i - Grundwert_i) × Einfluss_i,m)`

Dadurch bleibt die Unsicherheitsbreite des gewählten Grundszenarios erhalten.
Die Regler sind absichtlich grob und deterministisch. Zwischen 2026 und den
Stützjahren 2030, 2033 und 2036 zeigt die Oberfläche lediglich schematische
lineare Verbindungen; sie behauptet keinen glatten realen Jahresverlauf.

Haushaltsbänder kombinieren Realeinkommen und Beschäftigung als Nutzen sowie
Energie- und Klimabelastung als Kosten. Die staatliche Handlungsfähigkeit wirkt
je nach Haushaltstyp unterschiedlich stark. Das Ergebnis heißt daher
„Haushalts-Spielraum“, nicht verfügbares Einkommen in Euro.

## Wartung und Tests

Bei einer Quellenaktualisierung sind Abrufstand, Befund und Verwendung in der
geschützten Datendatei gemeinsam zu prüfen. Änderungen an den numerischen
Bandbreiten oder Einflussgewichten benötigen einen Eintrag im Changelog.

- `node tests/germany_2036_scenarios.test.js`
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_2036_data_test.php`
- `php -l germany-dossier.php`
- `php -l analysis-private/germany-2036-scenarios.php`

Die Seite ist im Hauptmenü auffindbar, bleibt aber `noindex` und serverseitig
geschützt. Der Menülink ist ausdrücklich keine Sicherheitsbarriere. Der neue
Browsercode und die geschützte Datendatei gehören in Full- und Delta-Pakete;
die Methodendokumentation und Tests nicht.
