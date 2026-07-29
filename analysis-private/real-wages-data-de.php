<?php
declare(strict_types=1);

if (isset($_SERVER['SCRIPT_FILENAME']) && realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    header('X-Robots-Tag: noindex, nofollow, noarchive', true);
    http_response_code(404);
    exit;
}

$data = require __DIR__ . '/real-wages-data.php';
$data['meta'] = array_replace($data['meta'], [
    'definition' => 'Durchschnittlicher Jahreslohn je abhängig beschäftigter Vollzeitkraft in der Gesamtwirtschaft',
    'sourceName' => 'OECD Data Explorer – durchschnittliche Jahreslöhne',
    'title' => 'Durchschnittliche OECD-Jahreslöhne',
    'unit' => 'konstante US-Dollar von 2025, kaufkraftbereinigt',
]);
$data['trendMeta'] = array_replace($data['trendMeta'], [
    'definition' => 'Nominallohnindex geteilt durch den Verbraucherpreisindex; Bruttomonatsverdienste einschließlich Sonderzahlungen',
    'methodBreakNote' => '2007–2021 basiert die Reihe auf der Vierteljährlichen Verdiensterhebung, ab 2022 auf der Verdiensterhebung. Der Übergang 2021/2022 ist methodisch nur eingeschränkt vergleichbar.',
    'sourceName' => 'Destatis GENESIS – Tabelle 62361-0020',
    'title' => 'Reallohnindex Deutschland',
    'unit' => 'Reallohnindex (2025 = 100)',
]);
return $data;
