<?php
// tracking.php
// Logs visitors by IP and country (ISO-3 codes only) and returns statistics as JSON

header('Content-Type: application/json');

// === Helper: determine client IP ===
function getClientIp() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) return $_SERVER['HTTP_CLIENT_IP'];
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) return explode(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0];
    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

// === Helper: map IP to country ISO-3 ===
// Note: here we use a simple GeoIP lookup (fallback Germany if not resolvable)
function ipToCountryIso3($ip) {
    $countryCode2 = null;

    if (function_exists('geoip_country_code_by_name')) {
        $countryCode2 = @geoip_country_code_by_name($ip);
    }

    if (!$countryCode2) {
        // fallback if GeoIP is not available
        $countryCode2 = "DE";
    }

    // map ISO-2 to ISO-3
    $isoMap = json_decode(file_get_contents(__DIR__ . "/countries.json"), true);
    if ($isoMap && isset($isoMap[$countryCode2]['iso3'])) {
        return $isoMap[$countryCode2]['iso3'];
    }

    return $countryCode2; // fallback: return ISO-2 if mapping not found
}

// === File to log ===
$logFile = __DIR__ . "/tracking.json";

// Load existing data
$data = [];
if (file_exists($logFile)) {
    $json = file_get_contents($logFile);
    $data = json_decode($json, true);
}
if (!$data) {
    $data = ["total" => 0, "countries" => []];
}

// Update stats
$ip = getClientIp();
$countryIso3 = ipToCountryIso3($ip);

$data["total"]++;
if (!isset($data["countries"][$countryIso3])) {
    $data["countries"][$countryIso3] = 0;
}
$data["countries"][$countryIso3]++;

// Save back
file_put_contents($logFile, json_encode($data, JSON_PRETTY_PRINT));

// Output current stats
echo json_encode($data, JSON_PRETTY_PRINT);
