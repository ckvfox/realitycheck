(function () {
  "use strict";

  const STORAGE_KEY = "rc_germany_dossier_language";
  const SUPPORTED = new Set(["en", "de"]);

  // Curated interface translations. Long-form bilingual reform copy is rendered
  // in both languages by PHP and switched with the same page-level state.
  const de = new Map(Object.entries({
    "Protected working view": "Geschützte Arbeitsansicht",
    "Log out": "Abmelden",
    "RealityCheck Germany dossier": "RealityCheck Deutschland-Dossier",
    "Germany under pressure: prosperity and security towards 2036": "Deutschland unter Druck: Wohlstand und Sicherheit bis 2036",
    "Why Germany?": "Warum Deutschland?",
    "Germany · File 1": "Deutschland · Akte 1",
    "Germany · File 2": "Deutschland · Akte 2",
    "Germany · File 3": "Deutschland · Akte 3",
    "Germany · File 4": "Deutschland · Akte 4",
    "Prosperity analysis": "Wohlstandsanalyse",
    "Real wages · purchasing-power context · Income Ladder": "Reallöhne · Kaufkraftkontext · Einkommensleiter",
    "2036 Scenarios": "Szenarien 2036",
    "Three possible futures · assumptions · citizen choices": "Drei mögliche Zukünfte · Annahmen · Handlungsmöglichkeiten",
    "War Stress Test": "Kriegs-Stresstest",
    "Escalation chain · preparedness · defence and service": "Eskalationskette · Vorsorge · Verteidigung und Dienst",
    "2036 Reform Agenda": "Reformagenda 2036",
    "International evidence · options · trade-offs": "Internationale Evidenz · Optionen · Zielkonflikte",
    "Germany · Dossier file 1": "Deutschland · Dossierakte 1",
    "Germany · Dossier file 2": "Deutschland · Dossierakte 2",
    "Germany · Dossier file 3": "Deutschland · Dossierakte 3",
    "Germany over time": "Deutschland im Zeitverlauf",
    "Official real wage index": "Amtlicher Reallohnindex",
    "Three indicators, three different questions": "Drei Kennzahlen, drei unterschiedliche Fragen",
    "Germany’s economy remains at a high international level — even when wage growth is weak": "Deutschlands Wirtschaft bleibt international auf hohem Niveau – auch bei schwachem Lohnwachstum",
    "International level comparison": "Internationaler Niveauvergleich",
    "Comparison with Germany in the same reference year": "Vergleich mit Deutschland im selben Referenzjahr",
    "Interactive household-income position": "Interaktive Einordnung des Haushaltseinkommens",
    "Where does our household gross income stand?": "Wo steht unser Bruttohaushaltseinkommen?",
    "Method note": "Methodenhinweis",
    "Germany 2036 — three possible futures": "Deutschland 2036 – drei mögliche Zukünfte",
    "The scenario narrative": "Das Szenario",
    "What drives this story": "Was diese Entwicklung antreibt",
    "Macro effects in 2036": "Makroeffekte im Jahr 2036",
    "All three base scenarios": "Alle drei Basisszenarien",
    "Schematic path": "Schematischer Verlauf",
    "Robust measures — useful in all three scenarios": "Robuste Maßnahmen – in allen drei Szenarien sinnvoll",
    "What can I do as a citizen?": "Was kann ich als Bürgerin oder Bürger tun?",
    "Special scenario: Germany at War": "Sonderszenario: Deutschland im Krieg",
    "Why examine an extreme case?": "Warum einen Extremfall untersuchen?",
    "Real threat versus fictional escalation": "Reale Bedrohung und fiktive Eskalation",
    "The seven-phase escalation path": "Der Eskalationspfad in sieben Phasen",
    "What could have interrupted the chain?": "Was hätte die Kette unterbrechen können?",
    "The first 72 hours in Germany": "Die ersten 72 Stunden in Deutschland",
    "What could this mean for me?": "Was könnte das für mich bedeuten?",
    "Does rearmament make war more likely?": "Macht Aufrüstung Krieg wahrscheinlicher?",
    "Serious objections and responses": "Ernsthafte Einwände und Antworten",
    "Why defence needs people": "Warum Verteidigung Menschen braucht",
    "Five personnel models at a glance": "Fünf Personalmodelle im Überblick",
    "Democratic safeguards": "Demokratische Schutzmechanismen",
    "Historical comparisons — clues, not proofs": "Historische Vergleiche – Hinweise, keine Beweise",
    "Evidence and assumption matrix": "Evidenz- und Annahmenmatrix",
    "Source": "Quelle",
    "Sources:": "Quellen:",
    "Limit:": "Grenze:",
    "Evidence:": "Evidenz:",
    "Loading map …": "Karte wird geladen …",
    "Activate stress test": "Stresstest aktivieren",
    "Close stress test": "Stresstest schließen"
    ,"Countries": "Länder"
    ,"World": "Welt"
    ,"Overall Ranking": "Gesamtranking"
    ,"Analysis": "Analyse"
    ,"Germany Dossier": "Deutschland-Dossier"
    ,"Primary": "Hauptnavigation"
    ,"Translator": "Übersetzer"
    ,"Google Translate": "Google Übersetzer"
    ,"Google Translate is loading…": "Google Übersetzer wird geladen …"
    ,"Close translator": "Übersetzer schließen"
    ,"Visitors total: loading…": "Besucher insgesamt: wird geladen …"
    ,"Data Glossary": "Datenglossar"
    ,"About": "Über RealityCheck"
    ,"Privacy": "Datenschutz"
    ,"View on GitHub": "Auf GitHub ansehen"
    ,"Language": "Sprache"
    ,"Germany Dossier: Prosperity, 2036 Scenarios and Security | RealityCheck": "Deutschland-Dossier: Wohlstand, Szenarien 2036 und Sicherheit | RealityCheck"
    ,"Editorial disclosure — this is a values-based and deliberately simplified political narrative.": "Redaktioneller Hinweis – dies ist eine wertegebundene und bewusst vereinfachte politische Erzählung."
    ,"Source:": "Quelle:"
    ,"Private working analysis": "Private Arbeitsanalyse"
    ,"Germany Dossier: Prosperity and Scenarios": "Deutschland-Dossier: Wohlstand und Szenarien"
    ,"This data-based analysis and scenario page is password-protected.": "Diese datenbasierte Analyse- und Szenarioseite ist passwortgeschützt."
    ,"Password": "Passwort"
    ,"Open analysis": "Analyse öffnen"
    ,"An obscure URL is not security. The content is only delivered after server-side authentication.": "Eine unbekannte Adresse ist kein Schutz. Der Server liefert die Inhalte erst nach erfolgreicher Anmeldung aus."
    ,"The request could not be verified. Please reload the page.": "Die Anfrage konnte nicht geprüft werden. Bitte lade die Seite neu."
    ,"Too many failed attempts. Please try again in a few minutes.": "Zu viele fehlgeschlagene Versuche. Bitte versuche es in einigen Minuten erneut."
    ,"The protected area has not yet been configured.": "Der geschützte Bereich ist noch nicht eingerichtet."
    ,"Incorrect password.": "Falsches Passwort."
    ,"This dossier combines Germany's historical evidence, international purchasing-power context and plausible futures. Its central story is not collapse, but a wealthy society facing stagnation, uneven losses and security choices that can still change the direction of travel.": "Dieses Dossier verbindet historische Daten zu Deutschland, internationale Kaufkraftvergleiche und plausible Zukunftsbilder. Es beschreibt keinen sicheren Zusammenbruch. Es zeigt ein wohlhabendes Land, das mit Stillstand, ungleich verteilten Verlusten und wichtigen Sicherheitsentscheidungen ringt. Der weitere Weg ist noch veränderbar."
    ,"This dossier combines historical data about Germany, international purchasing-power comparisons and plausible future scenarios. It does not predict a certain collapse. It examines a wealthy country facing slow growth, unequal pressure and security choices that can still change its path.": "Dieses Dossier verbindet historische Daten zu Deutschland, internationale Kaufkraftvergleiche und plausible Zukunftsszenarien. Es sagt keinen sicheren Zusammenbruch voraus. Es untersucht ein wohlhabendes Land mit langsamem Wachstum, ungleich verteiltem Druck und Sicherheitsentscheidungen, die seinen Weg noch verändern können."
    ,"Global economic weight.": "Globales wirtschaftliches Gewicht."
    ,"With nominal GDP of about US$5.05 trillion in 2025, Germany remains one of the world's largest economies.": "Mit einem nominalen Bruttoinlandsprodukt von rund 5,05 Billionen US-Dollar im Jahr 2025 bleibt Deutschland eine der größten Volkswirtschaften der Welt."
    ,"European leverage.": "Einfluss in Europa."
    ,"It is the EU's most populous member and largest national economy. German choices shape the single market, industrial supply chains, energy networks and Europe's capacity to act.": "Deutschland ist das bevölkerungsreichste EU-Mitglied und die größte nationale Volkswirtschaft der Union. Deutsche Entscheidungen prägen Binnenmarkt, industrielle Lieferketten, Energienetze und Europas Handlungsfähigkeit."
    ,"A growing security role.": "Eine wachsende Sicherheitsrolle."
    ,"The federal government aims to build the Bundeswehr into Europe's strongest conventional army. That is an ambition and a responsibility — not yet an accomplished fact.": "Die Bundesregierung will die Bundeswehr zur stärksten konventionellen Armee Europas entwickeln. Das ist ein Ziel und eine Verantwortung, aber noch keine erreichte Tatsache."
    ,"A democratic counterweight.": "Ein demokratisches Gegengewicht."
    ,"In this dossier's value framework, a large, liberal and pluralist Germany can be a source of hope against authoritarian and totalitarian developments. Germany's history makes the democratic and European use of power especially consequential.": "Nach dem Werteverständnis dieses Dossiers kann ein großes, liberales und vielfältiges Deutschland autoritären und totalitären Entwicklungen entgegenwirken. Wegen seiner Geschichte trägt Deutschland besondere Verantwortung, Macht demokratisch und europäisch einzusetzen."
    ,"And a personal reason.": "Und ein persönlicher Grund."
    ,"I happen to be German. This is the country I know best, whose decisions affect me directly and for whose future I share civic responsibility. That proximity sharpens the analysis, while also making its perspective openly subjective.": "Ich bin Deutscher. Dieses Land kenne ich am besten, seine Entscheidungen betreffen mich direkt und für seine Zukunft trage ich Mitverantwortung. Diese Nähe verbessert das Verständnis, macht die Perspektive aber auch offen subjektiv."
    ,"Context:": "Kontext:"
    ,"Editorial disclosure — this is a values-based, deliberately simplified political narrative.": "Redaktioneller Hinweis – dies ist eine wertegebundene und bewusst vereinfachte politische Erzählung."
    ,"I regard democracy, the rule of law, separation of powers, human rights, a free press, pluralism, minority protection, liberal freedoms, social solidarity, the welfare state, European cooperation, scientific openness, sustainability and peaceful international cooperation as desirable foundations of a liveable society. Anyone who evaluates these values differently will reasonably evaluate the scenarios differently. Reality is vastly more complex: countless feedback loops, political choices and butterfly effects make exact prediction impossible. The ranges are therefore informed judgement — “cleverly guessed”, not foretold — grounded in serious sources and plausible causal links.": "Ich halte Demokratie, Rechtsstaat, Gewaltenteilung, Menschenrechte, freie Medien, Vielfalt, Minderheitenschutz, persönliche Freiheit, soziale Solidarität, Sozialstaat, europäische Zusammenarbeit, offene Wissenschaft, Nachhaltigkeit und friedliche internationale Kooperation für wichtige Grundlagen eines lebenswerten Landes. Wer diese Werte anders beurteilt, wird auch die Szenarien anders bewerten. Die Wirklichkeit ist viel komplexer. Rückkopplungen, politische Entscheidungen und kleine Auslöser machen genaue Vorhersagen unmöglich. Die Bereiche sind deshalb begründete Einschätzungen – klug geschätzt, nicht vorhergesagt – auf Basis seriöser Quellen und plausibler Zusammenhänge."
    ,"I see democracy, the rule of law, separation of powers, human rights, a free press, pluralism, minority protection, personal freedom, social solidarity, the welfare state, European cooperation, open science, sustainability and peaceful international cooperation as important foundations of a good society. People who value these things differently will also judge the scenarios differently. Reality is much more complex. Feedback loops, political choices and small events make exact prediction impossible. The ranges are informed estimates, not forecasts. They use serious sources and plausible links between causes and effects.": "Ich sehe Demokratie, Rechtsstaat, Gewaltenteilung, Menschenrechte, freie Medien, Vielfalt, Minderheitenschutz, persönliche Freiheit, soziale Solidarität, Sozialstaat, europäische Zusammenarbeit, offene Wissenschaft, Nachhaltigkeit und friedliche internationale Kooperation als wichtige Grundlagen einer guten Gesellschaft. Wer diese Werte anders gewichtet, beurteilt auch die Szenarien anders. Die Wirklichkeit ist viel komplexer. Rückkopplungen, politische Entscheidungen und kleine Ereignisse machen genaue Vorhersagen unmöglich. Die Bereiche sind begründete Schätzungen und keine Prognosen. Sie nutzen seriöse Quellen und plausible Verbindungen zwischen Ursachen und Wirkungen."
    ,"How to read it:": "So ist das Dossier zu lesen:"
    ,"facts and published projections anchor the starting point; scenario bands and probability-like judgements are RealityCheck assumptions. They simplify the largest change dynamics so they can be discussed, not because the world is simple.": "Fakten und veröffentlichte Projektionen bilden den Ausgangspunkt. Szenariobereiche und wahrscheinlichkeitsähnliche Einschätzungen sind Annahmen von RealityCheck. Sie vereinfachen die wichtigsten Entwicklungen, damit man sie diskutieren kann – nicht weil die Welt einfach wäre."
    ,"facts and published projections define the starting point. Scenario ranges and probability-like judgements are RealityCheck assumptions. They simplify the most important changes so that people can discuss them. They do not suggest that the real world is simple.": "Fakten und veröffentlichte Projektionen bestimmen den Ausgangspunkt. Szenariobereiche und wahrscheinlichkeitsähnliche Einschätzungen sind Annahmen von RealityCheck. Sie vereinfachen die wichtigsten Veränderungen, damit Menschen darüber diskutieren können. Sie behaupten nicht, dass die wirkliche Welt einfach ist."
    ,"Wage development, Germany's international economic position and the household Income Ladder belong to one question: how high is our material living standard, and how is it changing?": "Lohnentwicklung, Deutschlands internationale Wirtschaftsposition und die Einkommensleiter gehören zu einer gemeinsamen Frage: Wie hoch ist unser materieller Lebensstandard und wie verändert er sich?"
    ,"Index series with base year 2025 = 100. It shows changes in the purchasing power of earnings, not the absolute wage level. The line shows the level and the bars show year-on-year change.": "Die Indexreihe hat das Basisjahr 2025 = 100. Sie zeigt, wie sich die Kaufkraft der Verdienste verändert, nicht die absolute Lohnhöhe. Die Linie zeigt den Stand, die Balken die Veränderung zum Vorjahr."
    ,"Real wage index": "Reallohnindex"
    ,"How does the purchasing power of average gross wages change within Germany? The best of these indicators for the wage trend over time.": "Wie verändert sich die Kaufkraft durchschnittlicher Bruttolöhne in Deutschland? Von diesen Kennzahlen zeigt dieser Index den Lohntrend über die Zeit am besten."
    ,"OECD wage in PPP": "OECD-Lohn in Kaufkraftparitäten"
    ,"How high is the average annual gross wage per full-time equivalent? Useful for comparable wage levels, but before tax and without distribution.": "Wie hoch ist der durchschnittliche Bruttojahreslohn je Vollzeitkraft? Die Kennzahl vergleicht Lohnniveaus, aber vor Steuern und ohne Aussage über die Verteilung."
    ,"GDP per capita in PPP": "BIP je Einwohner in Kaufkraftparitäten"
    ,"How high is price-adjusted output per resident worldwide? Broad country coverage, but not disposable household income.": "Wie hoch ist die preisbereinigte Wirtschaftsleistung je Einwohner? Die Kennzahl umfasst viele Länder, ist aber kein verfügbares Haushaltseinkommen."
    ,"A complete household assessment would also need:": "Für eine vollständige Bewertung von Haushalten bräuchte man außerdem:"
    ,"median equivalised disposable income after taxes and transfers, housing cost, wealth and distribution. There is no methodologically uniform series covering nearly 200 countries.": "das mittlere bedarfsgewichtete verfügbare Einkommen nach Steuern und Transfers, Wohnkosten, Vermögen und Verteilung. Für fast 200 Länder gibt es dafür keine einheitliche Datenreihe."
    ,"How to read the country comparison:": "So ist der Ländervergleich zu lesen:"
    ,"each covered country counts once, regardless of population. Germany’s rank therefore describes its position among national GDP-per-capita values. It is not the income position of German households or of the German population.": "Jedes erfasste Land zählt einmal, unabhängig von seiner Bevölkerung. Deutschlands Rang zeigt deshalb seine Position unter nationalen BIP-pro-Kopf-Werten. Er zeigt nicht die Einkommensposition deutscher Haushalte oder der deutschen Bevölkerung."
    ,"Loading global PPP context …": "Globaler Kaufkraftvergleich wird geladen …"
    ,"This is context for the economic level, not a substitute for real wages or household income.": "Das ist ein Vergleich des wirtschaftlichen Niveaus und kein Ersatz für Reallöhne oder Haushaltseinkommen."
    ,"Only values from the same year and in the same unit are compared. Countries without comparable data remain grey.": "Verglichen werden nur Werte aus demselben Jahr und in derselben Einheit. Länder ohne vergleichbare Daten bleiben grau."
    ,"Household gross": "Bruttohaushaltseinkommen"
    ,"EVS 2023 reference": "EVS-Vergleich 2023"
    ,"One figure only:": "Nur eine Zahl:"
    ,"enter the total annual gross income of the entire household. The comparison changes with the selected household type. It deliberately does not estimate net income because taxes, social insurance, age, transfers and individual circumstances would make that result misleading.": "Gib das gesamte jährliche Bruttoeinkommen des Haushalts ein. Der Vergleich passt sich an den gewählten Haushaltstyp an. Ein Nettoeinkommen wird bewusst nicht geschätzt, weil Steuern, Sozialversicherung, Alter, Transfers und persönliche Umstände das Ergebnis leicht irreführend machen."
    ,"Household type": "Haushaltstyp"
    ,"Total annual household gross": "Gesamtes Bruttohaushaltseinkommen pro Jahr"
    ,"Use the combined annual gross income of all household members, including bonuses and other gross income sources where applicable.": "Nutze das gemeinsame jährliche Bruttoeinkommen aller Haushaltsmitglieder. Dazu gehören gegebenenfalls Boni und andere Bruttoeinnahmen."
    ,"This is a benchmark ladder, not a percentile pyramid. Current official data do not provide robust top-10 or bottom-10 thresholds for each of these exact family types. The bands show transparent distances from the official average for the matching household size.": "Dies ist eine Vergleichsleiter und keine Perzentilpyramide. Aktuelle amtliche Daten liefern für diese genauen Familientypen keine verlässlichen Grenzen für die obersten oder untersten zehn Prozent. Die Bereiche zeigen nachvollziehbare Abstände zum amtlichen Durchschnitt derselben Haushaltsgröße."
    ,"Data basis and limits": "Datengrundlage und Grenzen"
    ,"The comparison uses the Destatis 2023 Household Budget Survey (EVS). Its average covers all gross income sources and all household compositions of the same size. It does not deduct regional prices, housing costs, taxes or debt and says nothing about wealth. It is therefore a useful orientation, not a social-class diagnosis.": "Der Vergleich nutzt die Einkommens- und Verbrauchsstichprobe 2023 von Destatis. Der Durchschnitt umfasst alle Bruttoeinnahmen und alle Haushaltsformen derselben Größe. Regionale Preise, Wohnkosten, Steuern und Schulden werden nicht abgezogen. Über Vermögen sagt die Zahl nichts. Sie ist deshalb eine Orientierung und keine Diagnose der sozialen Schicht."
    ,"The chart uses the official Destatis real wage index; an index value is not an absolute amount of money. The OECD map indicator is an average per full-time equivalent. It measures a real wage level, but neither the median wage nor disposable household income. The map covers countries in the OECD source, not automatically every country in the world.": "Das Diagramm nutzt den amtlichen Reallohnindex von Destatis. Ein Indexwert ist kein Geldbetrag. Die OECD-Karte zeigt einen Durchschnitt je Vollzeitkraft. Sie misst ein reales Lohnniveau, aber weder den Medianlohn noch das verfügbare Haushaltseinkommen. Die Karte umfasst die Länder der OECD-Quelle und nicht automatisch alle Staaten der Welt."
    ,"Horizon 2026–2036": "Zeitraum 2026–2036"
    ,"Sources reviewed": "Quellen geprüft"
    ,"Core premise:": "Kernannahme:"
    ,"Energy and climate are burden indices: lower is better. Bars show midpoints; tooltips show the modelled range.": "Energie und Klima sind Belastungsindizes: Ein niedrigerer Wert ist besser. Balken zeigen den Mittelwert, Hinweise den modellierten Bereich."
    ,"Dashed lines connect only four support years. They do not claim a smooth annual trajectory.": "Gestrichelte Linien verbinden nur vier Stützjahre. Sie behaupten keinen gleichmäßigen Jahresverlauf."
    ,"Change assumptions": "Annahmen verändern"
    ,"The controls are a sensitivity analysis. They change the index ranges deterministically; they do not estimate probabilities.": "Die Regler bilden eine Sensitivitätsanalyse. Sie verändern die Indexbereiche nach festen Regeln und schätzen keine Wahrscheinlichkeiten."
    ,"Reset to base scenario": "Auf Basisszenario zurücksetzen"
    ,"What could this mean for a household?": "Was könnte das für einen Haushalt bedeuten?"
    ,"Daily life": "Alltag"
    ,"Taxes and social contributions": "Steuern und Sozialbeiträge"
    ,"Energy and mobility": "Energie und Mobilität"
    ,"Housing and insurance": "Wohnen und Versicherung"
    ,"Transfers and provision": "Transfers und Versorgung"
    ,"Employment risk": "Beschäftigungsrisiko"
    ,"Training": "Weiterbildung"
    ,"Helpful policy": "Hilfreiche Politik"
    ,"Area": "Bereich"
    ,"Measure": "Maßnahme"
    ,"Effect": "Wirkung"
    ,"Time": "Zeit"
    ,"Cost": "Kosten"
    ,"Value in stress case": "Wert im Stressfall"
    ,"Individual action cannot replace effective infrastructure, security, social or industrial policy. It can strengthen demand, local resilience, occupational adaptability and democratic pressure for delivery.": "Persönliches Handeln ersetzt keine wirksame Infrastruktur-, Sicherheits-, Sozial- oder Industriepolitik. Es kann aber Nachfrage, lokale Widerstandskraft, berufliche Anpassung und demokratischen Druck für gute Umsetzung stärken."
    ,"Supports": "Stärkt"
    ,"Helps prevent": "Hilft zu verhindern"
    ,"Sources and assumptions matrix": "Quellen- und Annahmenmatrix"
    ,"Reading key:": "Lesehilfe:"
    ,"observations describe the past, official projections extend published assumptions and institutional analyses support causal directions. The 2036 ranges, slider weights and stress events are RealityCheck assumptions.": "Beobachtungen beschreiben die Vergangenheit. Amtliche Projektionen führen veröffentlichte Annahmen fort. Institutionelle Analysen stützen Wirkungsrichtungen. Die Bereiche für 2036, Reglergewichte und Stressereignisse sind Annahmen von RealityCheck."
    ,"Type": "Typ"
    ,"Finding": "Aussage"
    ,"Use": "Verwendung"
    ,"A security-policy stress test — not a forecast": "Ein sicherheitspolitischer Stresstest – keine Prognose"
    ,"No probability": "Keine Wahrscheinlichkeit"
    ,"Reviewed": "Geprüft"
    ,"The purpose is to identify where deterrence, political cohesion, infrastructure protection and civil preparedness can interrupt escalation. It does not claim that Russia will attack Germany or that war is unavoidable.": "Ziel ist zu erkennen, wo Abschreckung, politischer Zusammenhalt, Infrastrukturschutz und zivile Vorsorge eine Eskalation stoppen können. Das Szenario behauptet weder einen russischen Angriff auf Deutschland noch einen unvermeidbaren Krieg."
    ,"Observed hybrid activity and official threat assessments form the starting point. A Russian victory in Ukraine, a limited attack on NATO and open strikes on Germany are explicitly set assumptions.": "Beobachtete hybride Aktivitäten und amtliche Bedrohungsbewertungen bilden den Ausgangspunkt. Ein russischer Sieg in der Ukraine, ein begrenzter Angriff auf die NATO und offene Angriffe auf Deutschland sind ausdrücklich gesetzte Annahmen."
    ,"Trade:": "Handel:"
    ,"Energy:": "Energie:"
    ,"Run the stress test": "Stresstest starten"
    ,"Every phase names both the assumed escalation and an intervention point. No real target list, coordinates, tactical instructions, casualty figures or attack frequencies are shown.": "Jede Phase nennt die angenommene Eskalation und einen möglichen Eingriffspunkt. Es gibt keine echten Ziellisten, Koordinaten, taktischen Anleitungen, Opferzahlen oder Angriffshäufigkeiten."
    ,"Prevention is broader than military capability. The same chain has diplomatic, economic, societal and civil-protection off-ramps.": "Vorbeugung ist mehr als militärische Fähigkeit. Die Kette hat auch diplomatische, wirtschaftliche, gesellschaftliche und zivilschutzbezogene Auswege."
    ,"Illustrative consequences after the fictional open attack. Personal preparation follows BBK guidance only.": "Beispielhafte Folgen nach dem fiktiven offenen Angriff. Persönliche Vorsorge folgt ausschließlich den Hinweisen des BBK."
    ,"Select a household perspective": "Haushaltsperspektive auswählen"
    ,"Pacifist and critical positions are treated as legitimate arguments, not as disloyalty.": "Pazifistische und kritische Positionen gelten als berechtigte Argumente und nicht als Untreue."
    ,"Model": "Modell"
    ,"Military effect": "Militärische Wirkung"
    ,"Build-up speed": "Tempo des Aufbaus"
    ,"Freedom": "Freiheit"
    ,"Fairness": "Fairness"
    ,"Specialists": "Fachkräfte"
    ,"Reserve / civil protection": "Reserve / Zivilschutz"
    ,"Education and labour": "Bildung und Arbeit"
    ,"The world map loads when this stress test is opened.": "Die Weltkarte lädt, sobald der Stresstest geöffnet wird."
    ,"Sources support starting conditions, legal rules and causal mechanisms. They do not estimate the fictional seven-phase chain.": "Quellen stützen Ausgangslage, Rechtsregeln und Wirkungsmechanismen. Sie berechnen nicht die fiktive Kette aus sieben Phasen."
    ,"Evidence type": "Evidenztyp"
    ,"Institution / author": "Institution / Autor"
    ,"Finding used here": "Hier verwendete Aussage"
  }));

  const originalText = new WeakMap();

  function preferredLanguage() {
    const serverLanguage = document.documentElement.dataset.dossierLanguage;
    return SUPPORTED.has(serverLanguage) ? serverLanguage : "en";
  }

  function translateTextNode(node, language) {
    if (!node || !node.parentElement) return;
    if (node.parentElement.closest("script, style, [lang], [data-no-dossier-translate]")) return;
    const current = node.nodeValue || "";
    const trimmed = current.trim();
    if (!trimmed) return;
    if (!originalText.has(node)) originalText.set(node, current);
    const source = originalText.get(node);
    const sourceTrimmed = source.trim();
    const replacement = language === "de" ? de.get(sourceTrimmed) : sourceTrimmed;
    if (!replacement) {
      node.nodeValue = source;
      return;
    }
    const leading = source.match(/^\s*/)?.[0] || "";
    const trailing = source.match(/\s*$/)?.[0] || "";
    node.nodeValue = `${leading}${replacement}${trailing}`;
  }

  function translateTree(root, language) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) translateTextNode(node, language);
  }

  function setLanguage(language, persist = true) {
    const next = SUPPORTED.has(language) ? language : "en";
    document.documentElement.dataset.dossierLanguage = next;
    document.documentElement.lang = next;
    document.querySelectorAll("[data-dossier-language-option]").forEach(button => {
      const selected = button.dataset.dossierLanguageOption === next;
      button.setAttribute("aria-pressed", String(selected));
    });
    translateTree(document.body, next);
    document.title = next === "de"
      ? "Deutschland-Dossier: Wohlstand, Szenarien, Sicherheit und Reformen | RealityCheck"
      : "Germany Dossier: Prosperity, Scenarios, Security and Reforms | RealityCheck";
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}
    }
    window.dispatchEvent(new CustomEvent("rc:dossierlanguagechange", { detail: { language: next } }));
  }

  function boot() {
    const language = preferredLanguage();
    document.querySelectorAll("[data-dossier-language-option]").forEach(button => {
      button.addEventListener("click", () => {
        const next = button.dataset.dossierLanguageOption;
        if (!SUPPORTED.has(next) || next === preferredLanguage()) return;
        try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}
        const url = new URL(window.location.href);
        if (next === "de") url.searchParams.set("lang", "de");
        else url.searchParams.delete("lang");
        window.location.assign(url.toString());
      });
    });
    setLanguage(language, false);
    const observer = new MutationObserver(records => {
      const active = document.documentElement.dataset.dossierLanguage || "en";
      records.forEach(record => record.addedNodes.forEach(node => {
        if (node.nodeType === Node.TEXT_NODE) translateTextNode(node, active);
        else if (node.nodeType === Node.ELEMENT_NODE) translateTree(node, active);
      }));
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
