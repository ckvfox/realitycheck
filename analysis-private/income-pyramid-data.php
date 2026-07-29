<?php
declare(strict_types=1);

if (isset($_SERVER['SCRIPT_FILENAME']) && realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    header('X-Robots-Tag: noindex, nofollow, noarchive', true);
    http_response_code(404);
    exit;
}

return json_decode(<<<'JSON'
{
  "meta": {
    "updatedAt": "2026-07-25",
    "referenceYear": 2025,
    "warning": "Statistical orientation only. The bands are transparent distances from an official EU-SILC average for the selected household type, not income percentiles and not tax or financial advice. DINKs is used as a familiar short label, but the official category does not establish that both adults earn an income."
  },
  "households": [
    {"id":"single","label":"Single adult","size":1,"grossAverage":37764,"referenceLabel":"single-person household","description":"Exactly one person lives in the household."},
    {"id":"dinks","label":"DINKs* — 2 adults, no children","size":2,"grossAverage":78641,"referenceLabel":"household with two adults and no children","description":"Two adults and no statistically dependent child. The source does not say whether they are a couple or whether both receive an income; DINKs is only a short interface label."},
    {"id":"multiAdultNoChildren","label":"Other household without children — 3+ adults","size":3,"grossAverage":114696,"referenceLabel":"household with three or more adults and no children","description":"At least three adults and no statistically dependent child, for example an adult shared flat, parents with an economically independent adult child, or a multigenerational household."},
    {"id":"singleParent","label":"Single-parent household","size":2,"grossAverage":49273,"referenceLabel":"single-parent household","description":"One adult lives with at least one child. EU-SILC counts people under 18 and economically dependent people aged 18 to 24 as children."},
    {"id":"twoAdultsChildren","label":"2 adults with child(ren)","size":3,"grossAverage":112017,"referenceLabel":"household with two adults and one or more children","description":"Two adults live with at least one statistically defined child. The income table does not separate one, two or more children."},
    {"id":"multiAdultsChildren","label":"Other household with children — 3+ adults","size":4,"grossAverage":126271,"referenceLabel":"household with three or more adults and one or more children","description":"At least three adults live with at least one child, for example two parents, a child and a grandparent. Exact relationships and the number of children are not separated."}
  ],
  "benchmarkBands": [
    {"id":"farBelow","maxRatio":0.5,"width":38,"label":"Far below the reference","description":"Less than 50% of the average for this household size"},
    {"id":"below","minRatio":0.5,"maxRatio":0.75,"width":52,"label":"Below the reference","description":"50% to under 75% of the average"},
    {"id":"somewhatBelow","minRatio":0.75,"maxRatio":0.9,"width":66,"label":"Somewhat below","description":"75% to under 90% of the average"},
    {"id":"around","minRatio":0.9,"maxRatio":1.1,"width":80,"label":"Around the average","description":"90% to under 110% of the average"},
    {"id":"above","minRatio":1.1,"maxRatio":1.5,"width":88,"label":"Above the reference","description":"110% to under 150% of the average"},
    {"id":"wellAbove","minRatio":1.5,"maxRatio":2,"width":95,"label":"Well above the reference","description":"150% to under 200% of the average"},
    {"id":"farAbove","minRatio":2,"width":100,"label":"Far above the reference","description":"At least twice the average"}
  ],
  "sources":[
    {"label":"Destatis EU-SILC 2025 by household type","url":"https://genesis.destatis.de/datenbank/online/statistic/12241/table/12241-0001","use":"Average annual gross household income for six official household-type categories; not used as percentile thresholds"}
  ]
}
JSON
, true, 512, JSON_THROW_ON_ERROR);
