<?php
declare(strict_types=1);

$data = require __DIR__ . '/../analysis-private/germany-reform-agenda.php';
assert(is_array($data));
assert(count($data['chapters'] ?? []) === 11);
assert(count($data['compassLabels'] ?? []) === 6);
assert(count($data['sources'] ?? []) >= 10);

$ids = [];
foreach ($data['chapters'] as $chapter) {
    assert(isset($chapter['id'], $chapter['title']['en'], $chapter['title']['de']));
    assert(!in_array($chapter['id'], $ids, true));
    $ids[] = $chapter['id'];
    foreach (['problem', 'germany', 'balance', 'conclusion'] as $field) {
        assert(is_string($chapter[$field]['en'] ?? null) && $chapter[$field]['en'] !== '');
        assert(is_string($chapter[$field]['de'] ?? null) && $chapter[$field]['de'] !== '');
    }
    assert(count($chapter['cases'] ?? []) >= 2);
    assert(count($chapter['options']['en'] ?? []) === count($chapter['options']['de'] ?? []));
    assert(count($chapter['compass'] ?? []) === 6);
    foreach ($chapter['compass'] as $score) assert(is_int($score) && $score >= 1 && $score <= 5);
    foreach ($chapter['sources'] as $sourceId) assert(isset($data['sources'][$sourceId]));
}
foreach ($data['sources'] as $source) assert(filter_var($source['url'] ?? '', FILTER_VALIDATE_URL));

$page = file_get_contents(__DIR__ . '/../germany-dossier.php');
assert(str_contains($page, 'id="germany-reform-agenda"'));
assert(str_contains($page, 'data-dossier-language-option="en"'));
assert(str_contains($page, 'data-dossier-language-option="de"'));
assert(str_contains($page, 'class="real-wages-page notranslate"'));
assert(str_contains($page, 'data-disable-google-translate'));
assert(str_contains($page, 'scripts/page_germany_dossier_i18n.js'));

echo "Germany reform agenda bilingual data: all assertions passed\n";
