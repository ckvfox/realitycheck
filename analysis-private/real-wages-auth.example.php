<?php
declare(strict_types=1);

// Copy this file to real-wages-auth.php (gitignored) or, preferably, place it
// outside the public web root as ../private/realitycheck-real-wages-auth.php.
return [
    'password_hash' => 'REPLACE_WITH_PASSWORD_HASH',
    'session_idle_seconds' => 1800,
    'max_attempts' => 5,
    'lock_seconds' => 300,
    'failure_delay_microseconds' => 750000,
];

