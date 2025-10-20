<?php
// RealityCheck Visitor Tracking
// ------------------------------
// This script counts total visits globally and writes them to tracking.json
// Works on InfinityFree / standard PHP 7–8 environments

header("Content-Type: application/json; charset=UTF-8");
error_reporting(0);

// === Paths ===
$trackingFile = __DIR__ . '/tracking.json';

// === Load existing data or initialize ===
if (file_exists($trackingFile)) {
    $data = json_decode(file_get_contents($trackingFile), true);
    if (!is_array($data)) {
        $data = ["total" => 0];
    }
} else {
    $data = ["total" => 0];
}

// === Increment visitor count ===
$data["total"] = isset($data["total"]) ? intval($data["total"]) + 1 : 1;

// === Save updated file (atomic write for safety) ===
$tmpFile = $trackingFile . '.tmp';
file_put_contents($tmpFile, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
rename($tmpFile, $trackingFile);

// === Output JSON to browser ===
echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
?>