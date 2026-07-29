<?php
declare(strict_types=1);

$data = require __DIR__ . '/../analysis-private/germany-war-stress-test.php';
assert(is_array($data));
assert(count($data['phases'] ?? []) === 7);
assert(count($data['hours72'] ?? []) === 4);
assert(count($data['households'] ?? []) >= 5);
assert(count($data['objections'] ?? []) === 11);
assert(str_contains($data['objections'][2]['title'] ?? '', 'I will just leave'));
assert(str_contains($data['objections'][2]['uncertainty'] ?? '', 'does not promise'));
assert(count($data['people']['models'] ?? []) === 5);
assert(count($data['people']['serviceDebate']['models'] ?? []) === 2);
assert(count($data['people']['serviceDebate']['enforcement'] ?? []) >= 6);
assert(str_contains($data['people']['serviceDebate']['learning'] ?? '', 'does not prove'));
assert(str_contains($data['people']['refusalParadox']['limit'] ?? '', 'not a forecast'));
assert(array_column($data['preventionMeasures'] ?? [], 'category') === ['Military','Diplomatic','Economic','Societal','Civil protection']);
assert(count($data['historicalCases'] ?? []) >= 3);
assert(count($data['sources'] ?? []) >= 15);
assert(str_contains($data['strategicDoctrine']['text'] ?? '', 'military means'));
assert(count($data['conscriptionMap']['democratic'] ?? []) >= 20);
assert(count($data['conscriptionMap']['nonDemocratic'] ?? []) >= 30);
assert(array_intersect($data['conscriptionMap']['democratic'], $data['conscriptionMap']['nonDemocratic']) === []);
assert(!in_array('Germany', $data['conscriptionMap']['democratic'], true));
assert(!in_array('Germany', $data['conscriptionMap']['nonDemocratic'], true));
$geo = json_decode(file_get_contents(__DIR__ . '/../data/meta/world_countries_geo.json'), true, 512, JSON_THROW_ON_ERROR);
$mappings = json_decode(file_get_contents(__DIR__ . '/../data/meta/country_mappings.json'), true, 512, JSON_THROW_ON_ERROR);
$mappedFeatures = array_map(
    static fn(array $feature): string => $mappings[$feature['properties']['name']] ?? $feature['properties']['name'],
    $geo['features']
);
foreach (array_merge($data['conscriptionMap']['democratic'], $data['conscriptionMap']['nonDemocratic']) as $country) {
    assert(
        in_array($country, $mappedFeatures, true) || isset($data['conscriptionMap']['pointCountries'][$country]),
        "Conscription-map country missing in GeoJSON and point layer: {$country}"
    );
}
$sourceIds = array_column($data['sources'], 'id');
$sourcesById = array_column($data['sources'], null, 'id');
assert(($sourcesById['masala']['url'] ?? '') === 'https://www.chbeck.de/masala-russland-gewinnt/product/37085065');
assert(str_contains($sourcesById['masala']['organisation'] ?? '', '978-3-406-82448-7'));
foreach ($data['conscriptionMap']['sources'] as $sourceId) {
    assert(in_array($sourceId, $sourceIds, true), "Conscription-map source missing: {$sourceId}");
}
foreach (array_merge($data['people']['serviceDebate']['sources'], $data['people']['refusalParadox']['sources']) as $sourceId) {
    assert(in_array($sourceId, $sourceIds, true), "Service-debate source missing: {$sourceId}");
}

$evidenceTypes = array_keys($data['evidenceTypes'] ?? []);
foreach ($data['phases'] as $index => $phase) {
    assert(($phase['id'] ?? null) === $index + 1);
    assert(in_array($phase['evidence'] ?? '', $evidenceTypes, true));
    foreach (['event','aim','response','citizens','risk','prevention'] as $field) {
        assert(is_string($phase[$field] ?? null) && $phase[$field] !== '');
    }
}
foreach ($data['sources'] as $source) {
    assert(isset($source['id'], $source['type'], $source['title'], $source['organisation'], $source['url'], $source['finding']));
    assert(filter_var($source['url'], FILTER_VALIDATE_URL));
}
foreach ($data['objections'] as $objection) {
    $objectionSources = $objection['sources'] ?? [$objection['source'] ?? null];
    foreach ($objectionSources as $sourceId) {
        assert(in_array($sourceId, $sourceIds, true), "Objection source missing: {$sourceId}");
    }
}

$page = file_get_contents(__DIR__ . '/../germany-dossier.php');
assert(strpos($page, 'id="germany-war-stress-test"') > strpos($page, 'id="germany-2036"'));
assert(strpos($page, 'id="germany-prosperity"') < strpos($page, 'id="income-pyramid"'));
assert(strpos($page, 'id="income-pyramid"') < strpos($page, 'id="germany-2036"'));
assert(!str_contains($page, 'id="europe-2036"'));
assert(substr_count($page, 'class="analysis-index-card ') === 4);
assert(substr_count($page, 'data-dossier-tab=') === 4);
assert(substr_count($page, 'data-dossier-panel') === 4);
assert(str_contains($page, 'data-dossier-frame'));
assert(str_contains($page, 'scripts/page_germany_dossier.js'));
$styles = file_get_contents(__DIR__ . '/../style.css');
assert(str_contains($styles, '.war-stress-closing p { color: #294237; }'));
assert(str_contains($page, 'id="why-germany-title"'));
assert(str_contains($page, 'That is an ambition and a responsibility'));
assert(substr_count($page, 'data-scenario-tabs') === 1);
assert(str_contains($page, 'data-war-activate'));
assert(str_contains($page, 'id="war-conscription-map"'));
assert(str_contains($page, 'data-war-service-comparison'));
assert(str_contains($page, 'data-war-refusal-title'));

echo "Germany war stress-test protected data: all assertions passed\n";
