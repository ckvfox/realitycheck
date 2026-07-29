<?php
declare(strict_types=1);

$data = require __DIR__ . '/../analysis-private/germany-2036-scenarios.php';
assert(is_array($data));
assert(($data['meta']['defaultScenario'] ?? null) === 'pressure');
assert(($data['meta']['scenarioOrder'][0] ?? null) === 'pressure');
assert(count($data['scenarios'] ?? []) === 3);
assert(count($data['households'] ?? []) >= 4);
assert(count($data['sliders'] ?? []) >= 5);
assert(count($data['citizenActions'] ?? []) >= 6);
assert(count($data['strategicPrinciples'] ?? []) === 3);
assert(count($data['sources'] ?? []) >= 10);

foreach ($data['scenarios'] as $scenario) {
    assert(isset($scenario['story'], $scenario['premise'], $scenario['drivers'], $scenario['bands'], $scenario['sliderBase']));
    assert(strlen($scenario['story']) >= 300);
    assert(count($scenario['drivers']) === 5);
    foreach ($data['metrics'] as $metric) {
        $band = $scenario['bands'][$metric['id']] ?? null;
        assert(is_array($band) && count($band) === 2);
        assert(is_numeric($band[0]) && is_numeric($band[1]) && $band[0] <= $band[1]);
    }
}
foreach ($data['sources'] as $source) {
    assert(isset($source['kind'], $source['claim'], $source['source'], $source['url'], $source['use']));
    assert($source['url'][0] === '#' || filter_var($source['url'], FILTER_VALIDATE_URL));
}

echo "Germany 2036 protected data: all assertions passed\n";
