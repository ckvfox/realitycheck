<?php
declare(strict_types=1);

$data = require __DIR__ . '/../analysis-private/income-pyramid-data.php';
assert(is_array($data));
assert(count($data['households'] ?? []) === 6);
assert(count($data['benchmarkBands'] ?? []) === 7);
$householdsById = array_column($data['households'], null, 'id');
assert(($householdsById['dinks']['grossAverage'] ?? null) === 78641);
assert(($householdsById['singleParent']['grossAverage'] ?? null) === 49273);
assert(($data['meta']['referenceYear'] ?? null) === 2025);
foreach ($data['households'] as $household) {
    assert($household['grossAverage'] > 0);
    assert(strlen($household['description'] ?? '') >= 30);
}
foreach ($data['sources'] as $source) {
    assert(filter_var($source['url'], FILTER_VALIDATE_URL));
}
echo "income-pyramid protected data: all assertions passed\n";
