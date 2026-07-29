<?php
declare(strict_types=1);

function rc_rw_is_https(): bool
{
    return (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (isset($_SERVER['HTTP_X_FORWARDED_PROTO'])
            && strtolower((string) $_SERVER['HTTP_X_FORWARDED_PROTO']) === 'https');
}

function rc_rw_load_config(string $webRoot): ?array
{
    $candidates = [
        dirname($webRoot) . '/private/realitycheck-real-wages-auth.php',
        $webRoot . '/analysis-private/real-wages-auth.php',
    ];
    foreach ($candidates as $candidate) {
        if (is_file($candidate)) {
            $config = require $candidate;
            return is_array($config) ? $config : null;
        }
    }

    $environmentHash = getenv('REAL_WAGES_PASSWORD_HASH');
    if (is_string($environmentHash) && $environmentHash !== '') {
        return ['password_hash' => $environmentHash];
    }
    return null;
}

function rc_rw_config(array $config): array
{
    return array_merge([
        'password_hash' => '',
        'session_idle_seconds' => 1800,
        'max_attempts' => 5,
        'lock_seconds' => 300,
        'failure_delay_microseconds' => 750000,
    ], $config);
}

function rc_rw_lock_remaining(array $session, array $config, int $now): int
{
    $lockedUntil = (int) ($session['rc_rw_locked_until'] ?? 0);
    return max(0, $lockedUntil - $now);
}

function rc_rw_record_failure(array &$session, array $config, int $now): void
{
    $attempts = (int) ($session['rc_rw_failed_attempts'] ?? 0) + 1;
    $session['rc_rw_failed_attempts'] = $attempts;
    if ($attempts >= (int) $config['max_attempts']) {
        $session['rc_rw_locked_until'] = $now + (int) $config['lock_seconds'];
        $session['rc_rw_failed_attempts'] = 0;
    }
}

function rc_rw_csrf_token(array &$session): string
{
    if (empty($session['rc_rw_csrf'])) {
        $session['rc_rw_csrf'] = bin2hex(random_bytes(32));
    }
    return (string) $session['rc_rw_csrf'];
}

function rc_rw_csrf_valid(array $session, $submitted): bool
{
    return is_string($submitted)
        && isset($session['rc_rw_csrf'])
        && hash_equals((string) $session['rc_rw_csrf'], $submitted);
}

function rc_rw_authenticated(array &$session, array $config, int $now): bool
{
    if (empty($session['rc_rw_authenticated'])) {
        return false;
    }
    $lastSeen = (int) ($session['rc_rw_last_seen'] ?? 0);
    if ($lastSeen <= 0 || ($now - $lastSeen) > (int) $config['session_idle_seconds']) {
        unset($session['rc_rw_authenticated'], $session['rc_rw_last_seen']);
        return false;
    }
    $session['rc_rw_last_seen'] = $now;
    return true;
}

