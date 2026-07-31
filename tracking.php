<?php
// RealityCheck Visitor Tracking
// ------------------------------
// Counts top-level page loads without collecting identifiers.

declare(strict_types=1);

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
error_reporting(0);

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    header('Allow: POST');
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$trackingFile = __DIR__ . '/tracking.json';
$handle = fopen($trackingFile, 'c+');
if ($handle === false || !flock($handle, LOCK_EX)) {
    if (is_resource($handle)) {
        fclose($handle);
    }
    http_response_code(503);
    echo json_encode(['error' => 'Counter temporarily unavailable']);
    exit;
}

rewind($handle);
$raw = stream_get_contents($handle);
$data = is_string($raw) && $raw !== '' ? json_decode($raw, true) : null;
if (!is_array($data)) {
    $data = ['total' => 0];
}
$data['total'] = max(0, (int) ($data['total'] ?? 0)) + 1;
$encoded = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

$written = false;
if (is_string($encoded)) {
    rewind($handle);
    if (ftruncate($handle, 0)) {
        $written = fwrite($handle, $encoded) !== false;
        fflush($handle);
    }
}
flock($handle, LOCK_UN);
fclose($handle);

if (!$written) {
    http_response_code(503);
    echo json_encode(['error' => 'Counter temporarily unavailable']);
    exit;
}

echo $encoded;
