<?php
declare(strict_types=1);

if (isset($_SERVER['SCRIPT_FILENAME']) && realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    header('X-Robots-Tag: noindex, nofollow, noarchive', true);
    http_response_code(404);
    exit;
}

$data = require __DIR__ . '/income-pyramid-data.php';
$data['meta']['warning'] = 'Nur zur statistischen Einordnung. Die Bereiche zeigen transparente Abstände zum amtlichen EU-SILC-Durchschnitt des gewählten Haushaltstyps. Sie sind keine Einkommensperzentile und keine Steuer- oder Finanzberatung. DINKs ist hier eine verständliche Kurzbezeichnung; die amtliche Kategorie weist nicht nach, dass beide Erwachsenen ein Einkommen erzielen.';
$householdText = [
    'single' => ['label'=>'Alleinlebende Person','referenceLabel'=>'Einpersonenhaushalt','description'=>'Im Haushalt lebt genau eine Person.'],
    'dinks' => ['label'=>'DINKs* – 2 Erwachsene ohne Kind','referenceLabel'=>'Haushalt mit zwei Erwachsenen ohne Kinder','description'=>'Zwei Erwachsene und kein statistisch abhängiges Kind. Die Quelle zeigt weder, ob sie ein Paar sind, noch ob beide Einkommen beziehen. DINKs ist nur eine Kurzbezeichnung der Oberfläche.'],
    'multiAdultNoChildren' => ['label'=>'Sonstiger Haushalt ohne Kind – 3+ Erwachsene','referenceLabel'=>'Haushalt mit drei oder mehr Erwachsenen ohne Kinder','description'=>'Mindestens drei Erwachsene ohne statistisch abhängiges Kind, zum Beispiel eine Erwachsenen-WG, Eltern mit wirtschaftlich selbstständigem erwachsenem Kind oder ein Mehrgenerationenhaushalt.'],
    'singleParent' => ['label'=>'Alleinerziehendenhaushalt','referenceLabel'=>'Alleinerziehendenhaushalt','description'=>'Eine erwachsene Person lebt mit mindestens einem Kind. EU-SILC zählt Personen unter 18 Jahren sowie wirtschaftlich abhängige Personen von 18 bis 24 Jahren als Kinder.'],
    'twoAdultsChildren' => ['label'=>'2 Erwachsene mit Kind(ern)','referenceLabel'=>'Haushalt mit zwei Erwachsenen und mindestens einem Kind','description'=>'Zwei Erwachsene leben mit mindestens einem statistisch definierten Kind. Die Einkommenstabelle trennt nicht nach einem, zwei oder mehr Kindern.'],
    'multiAdultsChildren' => ['label'=>'Sonstiger Haushalt mit Kind – 3+ Erwachsene','referenceLabel'=>'Haushalt mit drei oder mehr Erwachsenen und mindestens einem Kind','description'=>'Mindestens drei Erwachsene leben mit mindestens einem Kind, zum Beispiel zwei Eltern, ein Kind und ein Großelternteil. Beziehungen und Kinderzahl werden nicht getrennt ausgewiesen.'],
];
foreach ($data['households'] as &$household) $household = array_replace($household, $householdText[$household['id']]);
unset($household);
$bandText = [
    'farBelow'=>['label'=>'Weit unter dem Vergleichswert','description'=>'Weniger als 50 % des Durchschnitts dieser Haushaltsgröße'],
    'below'=>['label'=>'Unter dem Vergleichswert','description'=>'50 % bis unter 75 % des Durchschnitts'],
    'somewhatBelow'=>['label'=>'Etwas darunter','description'=>'75 % bis unter 90 % des Durchschnitts'],
    'around'=>['label'=>'Im Bereich des Durchschnitts','description'=>'90 % bis unter 110 % des Durchschnitts'],
    'above'=>['label'=>'Über dem Vergleichswert','description'=>'110 % bis unter 150 % des Durchschnitts'],
    'wellAbove'=>['label'=>'Deutlich darüber','description'=>'150 % bis unter 200 % des Durchschnitts'],
    'farAbove'=>['label'=>'Weit über dem Vergleichswert','description'=>'Mindestens das Doppelte des Durchschnitts'],
];
foreach ($data['benchmarkBands'] as &$band) $band = array_replace($band, $bandText[$band['id']]);
unset($band);
$data['sources'][0] = array_replace($data['sources'][0], ['label'=>'Destatis EU-SILC 2025 nach Haushaltstyp','use'=>'Durchschnittliches jährliches Bruttohaushaltseinkommen für sechs amtliche Haushaltstypen; nicht als Perzentilschwelle verwendet']);
return $data;
