<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/analysis-private/real-wages-auth-lib.php';

$config = rc_rw_config([
    'max_attempts' => 2,
    'lock_seconds' => 60,
    'session_idle_seconds' => 30,
]);
$session = [];
$now = 1000;

assert(rc_rw_lock_remaining($session, $config, $now) === 0);
rc_rw_record_failure($session, $config, $now);
assert($session['rc_rw_failed_attempts'] === 1);
rc_rw_record_failure($session, $config, $now);
assert(rc_rw_lock_remaining($session, $config, $now) === 60);

$session = ['rc_rw_authenticated' => true, 'rc_rw_last_seen' => 980];
assert(rc_rw_authenticated($session, $config, $now) === true);
assert($session['rc_rw_last_seen'] === $now);
$session['rc_rw_last_seen'] = 900;
assert(rc_rw_authenticated($session, $config, $now) === false);

$session = [];
$token = rc_rw_csrf_token($session);
assert(rc_rw_csrf_valid($session, $token) === true);
assert(rc_rw_csrf_valid($session, 'wrong') === false);

echo "real-wages PHP auth helpers: all assertions passed\n";

