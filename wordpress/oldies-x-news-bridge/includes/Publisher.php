<?php
defined('ABSPATH') || exit;

final class Oldies_X_News_Publisher
{
    public const LINK_POST_USD = 0.20; // Official docs checked 2026-10-07; verify in console before enabling.
    private $transport;
    public function __construct(?callable $transport = null) { $this->transport = $transport ?? 'wp_remote_request'; }
    public static function config(string $key, string $default = ''): string
    {
        return defined($key) ? (string) constant($key) : (getenv($key) ?: $default);
    }
    public static function enabled(): bool { return self::config('OLDIES_X_API_ENABLED') === 'true'; }
    public static function credentialHash(): string
    {
        return hash('sha256', implode('|', array_map([self::class, 'config'], ['OLDIES_X_API_KEY', 'OLDIES_X_API_SECRET', 'OLDIES_X_ACCESS_TOKEN', 'OLDIES_X_ACCESS_TOKEN_SECRET', 'OLDIES_X_USER_ACCESS_TOKEN'])));
    }
    public static function mode(): string
    {
        if (self::config('OLDIES_X_USER_ACCESS_TOKEN') !== '') { return 'oauth2'; }
        foreach (['OLDIES_X_API_KEY', 'OLDIES_X_API_SECRET', 'OLDIES_X_ACCESS_TOKEN', 'OLDIES_X_ACCESS_TOKEN_SECRET'] as $key) {
            if (self::config($key) === '') { return 'missing'; }
        }
        return 'oauth1';
    }
    /** OAuth1 header; JSON request bodies are not included in OAuth parameters. */
    public static function authorization(string $method, string $url): string
    {
        if (self::mode() === 'oauth2') {
            $scopes = preg_split('/[ ,]+/', self::config('OLDIES_X_OAUTH2_SCOPES'));
            if (array_diff(['tweet.read', 'tweet.write', 'users.read'], $scopes)) { throw new RuntimeException('USER_WRITE_SCOPES_REQUIRED'); }
            return 'Bearer ' . self::config('OLDIES_X_USER_ACCESS_TOKEN');
        }
        if (self::mode() !== 'oauth1') { throw new RuntimeException('X_CREDENTIALS_MISSING'); }
        $params = [
            'oauth_consumer_key' => self::config('OLDIES_X_API_KEY'), 'oauth_token' => self::config('OLDIES_X_ACCESS_TOKEN'),
            'oauth_nonce' => bin2hex(random_bytes(16)), 'oauth_timestamp' => (string) time(),
            'oauth_signature_method' => 'HMAC-SHA1', 'oauth_version' => '1.0',
        ];
        ksort($params);
        $pairs = []; foreach ($params as $k => $v) { $pairs[] = rawurlencode($k) . '=' . rawurlencode($v); }
        $base = strtoupper($method) . '&' . rawurlencode($url) . '&' . rawurlencode(implode('&', $pairs));
        $key = rawurlencode(self::config('OLDIES_X_API_SECRET')) . '&' . rawurlencode(self::config('OLDIES_X_ACCESS_TOKEN_SECRET'));
        $params['oauth_signature'] = base64_encode(hash_hmac('sha1', $base, $key, true));
        $header = []; foreach ($params as $k => $v) { $header[] = rawurlencode($k) . '="' . rawurlencode($v) . '"'; }
        return 'OAuth ' . implode(', ', $header);
    }
    public static function budgetError(float $spent, float $cost): string
    {
        if (!self::enabled()) { return 'API_DISABLED_ZERO_COST_MODE'; }
        if ((float) self::config('OLDIES_X_MAX_REQUEST_USD') < $cost || (float) self::config('OLDIES_X_MONTHLY_BUDGET_USD') < $spent + $cost) { return 'PAID_API_NOT_AUTHORIZED'; }
        return '';
    }
    public function identityCheck(float $spent): array
    {
        if ($error = self::budgetError($spent, 0.01)) { throw new RuntimeException($error); }
        $expected = ltrim(self::config('OLDIES_X_EXPECTED_USERNAME'), '@');
        if (!preg_match('/^[A-Za-z0-9_]{1,15}$/D', $expected)) { throw new RuntimeException('EXPECTED_ACCOUNT_REQUIRED'); }
        $response = ($this->transport)('https://api.x.com/2/users/me', [
            'method' => 'GET', 'timeout' => 20, 'redirection' => 0, 'sslverify' => true,
            'headers' => ['Authorization' => self::authorization('GET', 'https://api.x.com/2/users/me')],
        ]);
        if (is_wp_error($response)) { throw new RuntimeException('X_IDENTITY_NETWORK_ERROR'); }
        if (wp_remote_retrieve_response_code($response) !== 200) { throw new RuntimeException('X_IDENTITY_HTTP_' . wp_remote_retrieve_response_code($response)); }
        $d = json_decode(wp_remote_retrieve_body($response), true)['data'] ?? [];
        if (empty($d['id']) || !preg_match('/^[0-9]+$/D', (string) $d['id']) || strcasecmp($d['username'] ?? '', $expected) !== 0) { throw new RuntimeException('X_ACCOUNT_MISMATCH'); }
        return ['id' => (string) $d['id'], 'username' => $d['username'], 'credential_hash' => self::credentialHash(), 'checked_at' => gmdate('c')];
    }
    public static function identityValid(array $identity): bool
    {
        return !empty($identity['id']) && hash_equals($identity['credential_hash'] ?? '', self::credentialHash()) &&
            strcasecmp($identity['username'] ?? '', ltrim(self::config('OLDIES_X_EXPECTED_USERNAME'), '@')) === 0 &&
            strtotime($identity['checked_at'] ?? '') > time() - 86400;
    }
    /** No automatic retry: a network/5xx response may have created a real post. */
    public function send(string $text): array
    {
        $url = 'https://api.x.com/2/tweets';
        $response = ($this->transport)($url, [
            'method' => 'POST', 'timeout' => 30, 'redirection' => 0, 'sslverify' => true,
            'headers' => ['Authorization' => self::authorization('POST', $url), 'Content-Type' => 'application/json'],
            'body' => wp_json_encode(['text' => $text], JSON_UNESCAPED_UNICODE),
        ]);
        if (is_wp_error($response)) { return ['status' => 'OUTCOME_UNKNOWN', 'error' => 'X_POST_FAILED_NETWORK_UNCERTAIN']; }
        $code = wp_remote_retrieve_response_code($response);
        $data = json_decode(wp_remote_retrieve_body($response), true)['data'] ?? [];
        if ($code === 201 && !empty($data['id']) && preg_match('/^[0-9]+$/D', (string) $data['id'])) {
            return ['status' => 'POSTED', 'post_id' => (string) $data['id'], 'error' => ''];
        }
        if (in_array($code, [400, 401, 402, 403, 404, 422, 429], true)) {
            return ['status' => 'FAILED', 'error' => 'X_POST_FAILED_HTTP_' . $code, 'retryable' => true,
                'retry_after' => $code === 429 ? max(time() + 60, (int) wp_remote_retrieve_header($response, 'x-rate-limit-reset')) : time() + 60];
        }
        return ['status' => 'OUTCOME_UNKNOWN', 'error' => 'X_POST_FAILED_HTTP_' . $code . '_UNCERTAIN'];
    }
}
