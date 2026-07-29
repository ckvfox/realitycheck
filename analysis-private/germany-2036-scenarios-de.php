<?php
declare(strict_types=1);

if (isset($_SERVER['SCRIPT_FILENAME']) && realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    header('X-Robots-Tag: noindex, nofollow, noarchive', true);
    http_response_code(404);
    exit;
}

$data = require __DIR__ . '/germany-2036-scenarios.php';
$data['meta']['title'] = 'Deutschland 2036 – drei mögliche Zukünfte';
$data['meta']['warning'] = 'Szenarien sind keine Prognosen. Die Werte sind modellierte Indexbereiche mit 2026 = 100. Sie sind weder Eurobeträge noch Wahrscheinlichkeiten.';

$metricText = [
    'prosperity'=>['label'=>'Wohlstand je Einwohner','unit'=>'Index'],
    'income'=>['label'=>'Reales verfügbares Einkommen','unit'=>'Index'],
    'employment'=>['label'=>'Stabilität der Beschäftigung','unit'=>'Index'],
    'energy'=>['label'=>'Belastung durch Energie und Mobilität','unit'=>'Belastungsindex'],
    'climate'=>['label'=>'Klimaschäden und Anpassungskosten','unit'=>'Belastungsindex'],
    'state'=>['label'=>'Handlungsfähigkeit des Staates','unit'=>'Index'],
];
foreach ($data['metrics'] as &$metric) $metric = array_replace($metric, $metricText[$metric['id']]);
unset($metric);

$data['strategicPrinciples'] = [
    ['title'=>'Demokratische Selbstverteidigung ermöglichen','text'=>'Deutschland muss seine Bevölkerung, seine Verfassungsordnung und seine berechtigten Sicherheitsinteressen schützen können. Wenn nötig, gehört dazu auch militärische Stärke. Sie bleibt an Grundgesetz, Völkerrecht, parlamentarische Kontrolle und Bündnisse gebunden. Ihr Hauptzweck ist Abschreckung: Ein Angriff soll weniger attraktiv werden. Krieg darf dadurch nicht zum Normalzustand werden.'],
    ['title'=>'Handel ohne strategische Naivität','text'=>'Handel und gegenseitige Abhängigkeit bleiben wertvoll. Die Idee „Wandel durch Handel“ reicht jedoch nicht als Sicherheitsstrategie. Wirtschaftlicher Austausch hat autoritäre Unterdrückung und militärische Angriffe nicht zuverlässig verhindert. Europa braucht deshalb offenen Handel, breiter verteilte Lieferketten, durchsetzbare Regeln und Schutz vor gefährlichen Abhängigkeiten.'],
    ['title'=>'Erneuerbare Energie ist Sicherheitspolitik','text'=>'Erneuerbare Energie aus Deutschland und Europa, stärkere Netze, Speicher, Effizienz und flexible Nachfrage verringern die Abhängigkeit von importierten fossilen Energien. Das schützt vor Lieferdruck und Preisschocks. Gleichzeitig sinken Klima- und Umweltschäden. Neue Abhängigkeiten bei Rohstoffen und Technik müssen trotzdem breit verteilt werden.'],
];

$scenarioText = [
    'renewal'=>[
        'label'=>'Erneuerung / europäische Souveränität','short'=>'Erneuerung',
        'story'=>'Deutschland und Europa erkennen, dass frühes Handeln günstiger ist als die dauernde Verwaltung von Engpässen. Verlässliche Investitionen in Netze, Verkehr, Bildung, Verteidigung, digitale Infrastruktur und Klimaanpassung verstärken sich gegenseitig. Unternehmen können besser planen. Europäische Zusammenarbeit verringert kritische Abhängigkeiten. Mehr Menschen können am Arbeitsmarkt teilnehmen. Krisen verschwinden nicht. Produktivität und finanzieller Spielraum der Haushalte wachsen aber wieder, weil der Staat mehrere Engpässe gemeinsam bearbeitet und nicht nur auf den nächsten Notfall reagiert.',
        'premise'=>'Deutschland und Europa investieren verlässlich, verteilen kritische Lieferketten breiter und verbinden Klima, Sicherheit, Qualifikation und Technologie.',
        'drivers'=>['climate'=>'Vorsorge und Anpassung begrenzen Schäden. Extremereignisse treten trotzdem auf.','security'=>'Die NATO bleibt handlungsfähig. Europa baut zugleich mehr eigene Fähigkeiten auf.','economy'=>'Energie, Netze und Rohstofflieferungen werden breiter verteilt.','technology'=>'Mehr europäische Rechen-, Cloud- und Chipkapazität erreicht auch kleinere Unternehmen.','society'=>'Mehr Erwerbsbeteiligung, qualifizierte Zuwanderung und Weiterbildung dämpfen die Folgen der Alterung.'],
    ],
    'pressure'=>[
        'label'=>'Anpassung unter Druck – Basisszenario','short'=>'Basisszenario',
        'story'=>'Deutschland bleibt ein wohlhabendes und grundsätzlich stabiles Land. Ein wachsender Teil seiner Kraft wird jedoch dafür gebraucht, das bestehende Niveau zu erhalten. Reformen und Investitionen kommen meist erst, wenn der Druck deutlich sichtbar ist. Sie verhindern einen breiten Absturz, lösen aber keinen starken Aufschwung aus. Alterung, Verteidigung, Klimaschäden und industrieller Umbau konkurrieren um Geld und Fachkräfte. Für viele Haushalte fühlt sich das Jahrzehnt deshalb wie eine lange Stagnation an: Verbesserungen werden oft durch höhere Preise, Steuern, Beiträge oder schwächere öffentliche Leistungen aufgezehrt.',
        'premise'=>'Investitionen und Reformen wirken teilweise, kommen aber zu langsam. Demografie, Klima, Verteidigung und industrieller Umbau konkurrieren um knappe Mittel.',
        'drivers'=>['climate'=>'Schäden und Anpassungskosten steigen gleichzeitig. Vorsorge bleibt lückenhaft.','security'=>'Die Bündnisse halten. Europas militärische und finanzielle Last wächst aber.','economy'=>'Lieferketten werden breiter. Große Risiken bei China, Energie und Rohstoffen bleiben bestehen.','technology'=>'KI erhöht in Teilen der Wirtschaft die Produktivität. Hohe Abhängigkeiten bleiben.','society'=>'Zuwanderung und höhere Erwerbsbeteiligung dämpfen den Rückgang der Arbeitskräfte, gleichen ihn aber nicht aus.'],
    ],
    'loss'=>[
        'label'=>'Verlust der Handlungsfähigkeit','short'=>'Stressfall',
        'story'=>'Mehrere lösbare Probleme werden zu einer gemeinsamen Krise, weil Entscheidungen zu spät kommen und Zusammenarbeit zerfällt. Teure Energie, gestörte Lieferketten, Klimaschäden und schwache Produktivität beschleunigen industrielle Verluste. Gleichzeitig steigen Ausgaben für Sicherheit und Soziales. Populistisch-autoritäre Politik richtet Frust gegen Institutionen, Minderheiten und europäische Partner. Das schwächt Investitionen und gemeinsames Handeln weiter. Entscheidend ist nicht ein einzelner Zusammenbruch, sondern eine negative Spirale: Nach jedem Schock können Staat, Wirtschaft und Gesellschaft den nächsten Schock schlechter auffangen.',
        'premise'=>'Mehrere Risiken verstärken sich: geopolitische Spaltung, Sicherheitskrisen, verspätete Infrastruktur und Klimaanpassung, schwache Produktivität und demokratischer Rückschritt.',
        'drivers'=>['climate'=>'Häufige Extremereignisse treffen auf große Lücken bei der Anpassung.','security'=>'Ein Rückzug der USA und eine Eskalation an Europas Grenzen sind ausdrückliche Stressannahmen.','economy'=>'Lieferstörungen und teure Energie beschleunigen industrielle Verluste.','technology'=>'Die Abhängigkeit von außereuropäischen Cloud-, Chip- und KI-Systemen steigt.','society'=>'Populistisch-autoritäre Kräfte gewinnen Macht. Druck auf Gerichte, freie Medien, Minderheitenrechte und Zugewanderte schwächt Kontrolle und Vertrauen. Eine Blockade oder ein Austritt aus der EU verringert gemeinsame Fähigkeiten. Ähnliche Ideologien verhindern dabei keine Konflikte zwischen nationalistischen Regierungen.'],
    ],
];
foreach ($scenarioText as $id => $translation) $data['scenarios'][$id] = array_replace_recursive($data['scenarios'][$id], $translation);

$householdText = [
    'family'=>['label'=>'Familie mit zwei Erwerbstätigen','daily'=>'Kinderbetreuung, Arbeitswege, Wohnen und Sozialbeiträge entscheiden, ob Produktivitätsgewinne die Familie erreichen.','tax'=>'Anreize für die zweite erwerbstätige Person und Sozialbeiträge beeinflussen zusätzliche Arbeitsstunden stark.','energyText'=>'Zwei Arbeitswege und mehr Wohnfläche erhöhen die Belastung.','housing'=>'Miete oder Finanzierung kommen zu Sanierungskosten. Versicherungen werden wichtiger.','transfers'=>'Kindergeld, Betreuung und gezielte Hilfe wirken besser als pauschale Zuschüsse.','training'=>'Planbare und familienfreundliche Weiterbildung erleichtert einen Berufswechsel.','risk'=>'Fehlende Betreuung, Mobilitätskosten und der Wandel von Berufen können gleichzeitig belasten.','help'=>'Ganztagsbetreuung, verlässlicher Nahverkehr, Weiterbildung und gezielte Entlastung.'],
    'single'=>['label'=>'Alleinlebende Person mit mittlerem Einkommen','daily'=>'Eine Person trägt feste Wohn- und Energiekosten allein. Ein Arbeitsplatzverlust wirkt sofort.','tax'=>'Kein zweites Einkommen fängt höhere Beiträge oder Einkommensverluste ab.','energyText'=>'Feste Energiekosten werden nicht geteilt. Mobilitätskosten hängen stark vom Wohnort ab.','housing'=>'Warmmiete bindet besonders in Städten einen hohen Teil des Einkommens.','transfers'=>'Trotz hoher Fixkosten besteht oft kein Anspruch auf Unterstützung.','training'=>'Kurze, anerkannte und übertragbare Lernmodule helfen bei einem schnellen Branchenwechsel.','risk'=>'Hohe Fixkosten treffen auf schwaches Lohn- oder Beschäftigungswachstum.','help'=>'Bezahlbares Wohnen, tragbare Netzentgelte und flexible Weiterbildung.'],
    'retired'=>['label'=>'Haushalt im Ruhestand','daily'=>'Rentenanpassung, Pflege, Hitzeschutz und Gebäudekosten sind entscheidend.','tax'=>'Beiträge für Gesundheit und Pflege sind wichtiger als Arbeitsanreize.','energyText'=>'Mehr Zeit zu Hause erhöht den Bedarf an Heizung und Kühlung.','housing'=>'Barrierefreiheit, Hitzeschutz, Sanierung und Versicherbarkeit können teuer sein.','transfers'=>'Rente, Wohngeld, Pflegeleistungen und kommunale Dienste sind zentral.','training'=>'Digitale Teilhabe und Beratung treten an die Stelle beruflicher Weiterbildung.','risk'=>'Pflege- und Klimakosten treffen auf begrenzte Anpassungsmöglichkeiten.','help'=>'Pflegekapazität, Hitzeschutz, barrierearme Sanierung und verlässliche öffentliche Dienste.'],
    'industrial'=>['label'=>'Haushalt einer Industriefachkraft','daily'=>'Exportnachfrage, Energiepreise und Technikwechsel bestimmen Arbeitsplätze und Schichtmodelle.','tax'=>'Kurzarbeit, Lohnersatz und Beiträge prägen den Übergang.','energyText'=>'Arbeitswege und Autoabhängigkeit im ländlichen Raum erhöhen das Mobilitätsrisiko.','housing'=>'Wohnung und Arbeitsplatz hängen oft an derselben Region. Wert- und Jobverluste können sich verstärken.','transfers'=>'Übergangshilfe kauft Zeit, ersetzt aber keinen neuen Arbeitsplatz.','training'=>'Frühe, anerkannte Kenntnisse für Elektrifizierung, Software und Instandhaltung.','risk'=>'Strukturbrüche in Auto-, Chemie- oder Zulieferregionen.','help'=>'Weiterbildung, regionale Investitionen und breiter verteilte Absatzmärkte.'],
];
foreach ($data['households'] as &$household) $household = array_replace($household, $householdText[$household['id']]);
unset($household);

$sliderText = [
    'climateStress'=>['label'=>'Klima- und Extremwetterbelastung','left'=>'geringer','right'=>'stärker'],
    'renewables'=>['label'=>'Erneuerbare Energie, Netze und Speicher','left'=>'stockend','right'=>'beschleunigt'],
    'fragmentation'=>['label'=>'Geopolitische Spaltung','left'=>'kooperativ','right'=>'stark'],
    'dependencies'=>['label'=>'Abhängigkeit von kritischen Importen','left'=>'breit verteilt','right'=>'konzentriert'],
    'technology'=>['label'=>'Europäische Technologie- und KI-Kapazität','left'=>'schwach','right'=>'stark'],
    'productivity'=>['label'=>'Produktivität und Wirkung von Reformen','left'=>'gering','right'=>'hoch'],
    'migration'=>['label'=>'Arbeitsmarktintegration und Zuwanderung','left'=>'unzureichend','right'=>'wirksam'],
    'investment'=>['label'=>'Fähigkeit zu öffentlichen Investitionen','left'=>'blockiert','right'=>'verlässlich'],
];
foreach ($data['sliders'] as &$slider) $slider = array_replace($slider, $sliderText[$slider['id']]);
unset($slider);

$data['measures'] = [
    ['area'=>'Klima','measure'=>'Kommunale Programme für Hitze, Hochwasser und Schwammstädte','effect'=>'Schäden und Ausfälle begrenzen','duration'=>'3–10 Jahre','cost'=>'hoch','worst'=>'hoch','robust'=>true],
    ['area'=>'Sicherheit','measure'=>'Europäische Beschaffung, Luftverteidigung und zivile Resilienz bündeln','effect'=>'Abhängigkeit und Stückkosten senken','duration'=>'5–10 Jahre','cost'=>'hoch','worst'=>'sehr hoch','robust'=>true],
    ['area'=>'Energie','measure'=>'Netze, Speicher, Effizienz und flexible Nachfrage beschleunigen','effect'=>'Preisspitzen und Importbedarf senken','duration'=>'2–10 Jahre','cost'=>'hoch','worst'=>'hoch','robust'=>true],
    ['area'=>'Technologie','measure'=>'Offene europäische Cloud-, Daten- und KI-Infrastruktur auch für den Mittelstand','effect'=>'Nutzung und Eigenständigkeit erhöhen','duration'=>'3–8 Jahre','cost'=>'mittel bis hoch','worst'=>'hoch','robust'=>true],
    ['area'=>'Arbeit','measure'=>'Betreuung, Weiterbildung, Anerkennung und Integration ausbauen','effect'=>'Arbeitsangebot und Übergänge verbessern','duration'=>'2–10 Jahre','cost'=>'mittel','worst'=>'hoch','robust'=>true],
    ['area'=>'Staat','measure'=>'Mehrjährige Investitionsbudgets, schnellere Planung und Wirkungsprüfung','effect'=>'Umsetzungsfähigkeit stabilisieren','duration'=>'1–6 Jahre','cost'=>'mittel','worst'=>'sehr hoch','robust'=>true],
];

$data['citizenActions'] = [
    ['lever'=>'Demokratie arbeitsfähig machen','action'=>'Bei Wahlen, Beteiligung, Verbänden und Initiativen konkrete Fragen stellen: Wer ist verantwortlich? Wie wird finanziert? Wann wird geprüft, ob die Maßnahme wirkt?','supports'=>'Handlungsfähiger Staat und langfristige Investitionen','prevents'=>'Symbolpolitik, Polarisierung und Vertrauensverlust'],
    ['lever'=>'Lokale Widerstandskraft aufbauen','action'=>'Hitzeschutz, Entsiegelung, Hochwasservorsorge, Zivilschutz und Nachbarschaftshilfe unterstützen oder mitorganisieren.','supports'=>'Klimaresilienz und sozialer Zusammenhalt','prevents'=>'Dass Extremereignisse zu vermeidbaren Gesundheits- und Versorgungskrisen werden'],
    ['lever'=>'Energie und Mobilität flexibler machen','action'=>'Dort sparen, wo es sich lohnt. Sanierung, Bürgerenergie, zeitlich flexible Nutzung, Nahverkehr, Rad und Teilen sinnvoll kombinieren.','supports'=>'Energiesicherheit und geringere Importabhängigkeit','prevents'=>'Dauerhaft hohe Fixkosten und starke Preisschock-Risiken'],
    ['lever'=>'Eigene Fähigkeiten erneuern','action'=>'Digitale, technische und soziale Kenntnisse regelmäßig aktualisieren. Weiterbildungsrechte nutzen und Wissen im Betrieb teilen.','supports'=>'Produktivität, Beschäftigungsfähigkeit und Techniknutzung','prevents'=>'Persönlichen Abstieg bei Strukturbrüchen'],
    ['lever'=>'Veränderung im Betrieb mitgestalten','action'=>'Betriebsräte, Berufsgruppen oder Verbesserungsprozesse nutzen, um Weiterbildung, Effizienz, sichere Lieferketten und sinnvolle KI früh voranzubringen.','supports'=>'Erneuerung der industriellen Basis','prevents'=>'Späte hektische Anpassung und vermeidbare Arbeitsplatzverluste'],
    ['lever'=>'Robust konsumieren und vorsorgen','action'=>'Haltbarkeit, Reparierbarkeit und nachvollziehbare Lieferketten beachten. Passende Notvorräte, Versicherungsschutz und finanzielle Rücklagen prüfen.','supports'=>'Widerstandskraft von Haushalt und Nachfrage','prevents'=>'Dass kurze Störungen sofort zu persönlichen Krisen werden'],
];

$sourceText = [
    ['area'=>'Klima','kind'=>'amtliche Risikobewertung','claim'=>'Bei 31 von 102 untersuchten Klimafolgen besteht sehr dringender Handlungsbedarf. Anpassung braucht Vorlauf.','use'=>'Feste Rahmenbedingung in allen Szenarien'],
    ['area'=>'Klima','kind'=>'Beobachtung','claim'=>'2024 war in Deutschland das wärmste Jahr seit Messbeginn 1881.','use'=>'Historischer Kontext, keine Prognose für 2036'],
    ['area'=>'Demografie','kind'=>'amtliche Vorausberechnung','claim'=>'Bis 2035 sinkt die Bevölkerung im Erwerbsalter je nach Zuwanderung um 3,2 bis 4,9 Millionen. Ohne Nettozuwanderung wären es 6,2 Millionen.','use'=>'Zentraler amtlicher Korridor'],
    ['area'=>'Pflege','kind'=>'amtliche Vorausberechnung','claim'=>'Modelle erwarten für 2035 etwa 5,6 bis 6,3 Millionen pflegebedürftige Menschen.','use'=>'Druck auf Haushalte, Arbeitsmarkt und Staat'],
    ['area'=>'Wirtschaft','kind'=>'institutionelle Analyse','claim'=>'Alterung, schwache Produktivität und Investitionsbedarf begrenzen das mögliche Wachstum. Reformen können es erhöhen.','use'=>'Richtung der Wirkung, keine übernommene Punktschätzung'],
    ['area'=>'Finanzen','kind'=>'institutionelle Projektion','claim'=>'Die Alterung erhöht langfristig die Ausgabenrisiken für Rente, Gesundheit und Pflege.','use'=>'Druck auf die staatliche Handlungsfähigkeit'],
    ['area'=>'Energie','kind'=>'institutionelle Analyse','claim'=>'Hohe Strompreise, Netzausbau und Speicher sind zentrale Engpässe der Transformation.','use'=>'Energiepfade und Maßnahmen'],
    ['area'=>'Rohstoffe','kind'=>'EU-Ziele und Risikobild','claim'=>'Ziele für 2030: 10 % Förderung, 40 % Verarbeitung und 25 % Recycling in der EU; höchstens 65 % aus einem einzelnen Drittland.','use'=>'Annahmen zur breiteren Verteilung'],
    ['area'=>'Geopolitik','kind'=>'Stressanalyse','claim'=>'Eine starke geopolitische Spaltung kann die Wirtschaftsleistung im Euroraum deutlich senken und Preise erhöhen.','use'=>'Nur als Größenordnung für den Stressfall'],
    ['area'=>'Sicherheit','kind'=>'politische Verpflichtung','claim'=>'NATO-Ziel 2035: 3,5 % des BIP für Kernverteidigung plus bis zu 1,5 % für Sicherheit und Resilienz.','use'=>'Konkurrenz um Haushaltsmittel; ein Bündnisversagen bleibt eine Modellannahme'],
    ['area'=>'Technologie','kind'=>'EU-Bestandsaufnahme','claim'=>'Bei Cloud, Cybersicherheit und Halbleitern bestehen weiterhin deutliche Abhängigkeiten.','use'=>'Technologiepfade'],
    ['area'=>'Modell','kind'=>'RealityCheck-Annahme','claim'=>'Bereiche und Reglerwirkungen sind transparente Modellannahmen von RealityCheck. Sie stammen nicht aus den genannten Quellen.','use'=>'Sensitivitätsmodell, keine Wahrscheinlichkeit'],
];
foreach ($data['sources'] as $index => &$source) $source = array_replace($source, $sourceText[$index]);
unset($source);
return $data;
