<?php
declare(strict_types=1);

$scenarioEn = require __DIR__ . '/../analysis-private/germany-2036-scenarios.php';
$scenarioDe = require __DIR__ . '/../analysis-private/germany-2036-scenarios-de.php';
assert(array_keys($scenarioEn['scenarios']) === array_keys($scenarioDe['scenarios']));
assert(count($scenarioEn['households']) === count($scenarioDe['households']));
assert(count($scenarioEn['sources']) === count($scenarioDe['sources']));
assert(str_contains($scenarioDe['meta']['title'], 'Deutschland'));
assert(str_contains($scenarioDe['scenarios']['pressure']['story'], 'wohlhabendes'));

$warEn = require __DIR__ . '/../analysis-private/germany-war-stress-test.php';
$warB2 = require __DIR__ . '/../analysis-private/germany-war-stress-test-b2.php';
$warDe = require __DIR__ . '/../analysis-private/germany-war-stress-test-de.php';
foreach (['phases','hours72','households','objections','preventionMeasures','historicalCases','sources'] as $key) {
    assert(count($warEn[$key]) === count($warDe[$key]), "German war data count differs for {$key}");
}
assert(count($warDe['people']['serviceDebate']['models']) === 2);
assert(count($warDe['people']['models']) === 5);
assert(str_contains($warDe['meta']['title'], 'Deutschland'));
assert(str_contains($warDe['closing']['headline'], 'Verteidigungsfähig'));
assert(count($warB2['objections']) === count($warEn['objections']));
assert(str_contains($warB2['meta']['warning'], 'does not say what will happen'));

$wagesDe = require __DIR__ . '/../analysis-private/real-wages-data-de.php';
$incomeDe = require __DIR__ . '/../analysis-private/income-pyramid-data-de.php';
assert(str_contains($wagesDe['trendMeta']['title'], 'Reallohnindex'));
assert(count($incomeDe['households']) === 6);
assert(str_contains(strtolower($incomeDe['meta']['warning']), 'perzentile'));
assert(str_contains($incomeDe['households'][1]['label'], 'DINKs'));

$agenda = require __DIR__ . '/../analysis-private/germany-reform-agenda.php';
$depth = require __DIR__ . '/../analysis-private/germany-reform-agenda-depth.php';
assert(count($depth) === 11);
foreach ($agenda['chapters'] as $chapter) {
    $record = $depth[$chapter['id']] ?? null;
    assert(is_array($record));
    assert(count($record['problemDetail']['en'] ?? []) >= 2);
    assert(count($record['problemDetail']['en']) === count($record['problemDetail']['de']));
    assert(count($record['germanyDetail']['en'] ?? []) >= 2);
    assert(count($record['caseDetails'] ?? []) === count($chapter['cases']));
    assert(count($record['prerequisites']['en'] ?? []) >= 3);
    foreach ($record['caseDetails'] as $case) {
        foreach (['starting','implementation','results','transfer'] as $field) {
            assert(strlen($case[$field]['en'] ?? '') >= 60);
            assert(strlen($case[$field]['de'] ?? '') >= 60);
        }
    }
}

$page = file_get_contents(__DIR__ . '/../germany-dossier.php');
assert(str_contains($page, "(\$_GET['lang'] ?? '') === 'de'"));
assert(str_contains($page, 'germany-war-stress-test-de.php'));
assert(str_contains($page, 'germany-war-stress-test-b2.php'));
assert(str_contains($page, 'germany-reform-agenda-depth.php'));
assert(str_contains($page, 'dossier-login-language'));
assert(str_contains($page, 'const RC_DOSSIER_ACCESS_PROTECTION = false;'));
assert(str_contains($page, 'rc_dossier_translate_html'));
assert(strpos($page, 'dossier-i18n-4') > strrpos($page, '<?php endif; ?>'));

echo "Germany dossier complete bilingual data: all assertions passed\n";
