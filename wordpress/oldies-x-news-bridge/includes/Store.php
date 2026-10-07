<?php
defined('ABSPATH') || exit;

final class Oldies_X_News_Store
{
    private string $table;
    public function __construct()
    {
        global $wpdb;
        $this->table = $wpdb->prefix . 'oldies_news_articles';
        if (!preg_match('/^[A-Za-z0-9_]+$/D', $this->table)) { throw new RuntimeException('INVALID_TABLE'); }
    }
    public function available(): bool
    {
        global $wpdb;
        $wpdb->get_results("SELECT * FROM `{$this->table}` LIMIT 0");
        if ($wpdb->last_error) { return false; }
        $columns = (array) $wpdb->get_col_info('name');
        return !array_diff(['id', 'metadata', 'en_post_id', 'headline', 'updated_at', 'fingerprint', 'artist_topic', 'article_url'], $columns);
    }
    public function row(int $id): ?array
    {
        global $wpdb;
        $row = $wpdb->get_row($wpdb->prepare("SELECT * FROM `{$this->table}` WHERE id=%d", $id), ARRAY_A);
        return is_array($row) ? $row : null;
    }
    public function rows(int $page = 1, int $limit = 20): array
    {
        global $wpdb;
        return (array) $wpdb->get_results($wpdb->prepare("SELECT * FROM `{$this->table}` ORDER BY id DESC LIMIT %d OFFSET %d", $limit, max(0, $page - 1) * $limit), ARRAY_A);
    }
    public static function metadata(array $row): array
    {
        $m = json_decode($row['metadata'] ?? '{}', true);
        if ($m === null && !empty($row['metadata']) && $row['metadata'] !== 'null') { throw new RuntimeException('INVALID_EXISTING_METADATA'); }
        return is_array($m) ? $m : [];
    }
    /** Atomic merge; a concurrent scanner/editor change cannot be overwritten. */
    public function save(array $before, array $x): void
    {
        global $wpdb;
        $m = self::metadata($before); $m['x_news'] = $x;
        $where = $before['metadata'] === null ? 'metadata IS NULL' : $wpdb->prepare('BINARY metadata=BINARY %s', $before['metadata']);
        $changed = $wpdb->query($wpdb->prepare("UPDATE `{$this->table}` SET metadata=%s,updated_at=%s WHERE id=%d AND {$where}", wp_json_encode($m, JSON_UNESCAPED_UNICODE), gmdate('Y-m-d H:i:s'), $before['id']));
        if ($changed !== 1) { throw new RuntimeException('STATE_CHANGED'); }
    }
    /** Global X lock covers duplicate check, publication and final save. */
    public function locked(callable $callback)
    {
        global $wpdb;
        $key = 'oldies_x_' . substr(hash('sha256', $wpdb->dbname . ':' . $this->table), 0, 40);
        if ((string) $wpdb->get_var($wpdb->prepare('SELECT GET_LOCK(%s,0)', $key)) !== '1') { throw new RuntimeException('X_BUSY'); }
        try { return $callback(); } finally { $wpdb->get_var($wpdb->prepare('SELECT RELEASE_LOCK(%s)', $key)); }
    }
    /** Cursor scans all previously delivered/reserved items, including older news. */
    public function duplicate(int $id, array $x): bool
    {
        global $wpdb;
        $cursor = 0;
        do {
            $rows = $wpdb->get_results($wpdb->prepare("SELECT id,metadata FROM `{$this->table}` WHERE id>%d AND metadata LIKE %s ORDER BY id LIMIT 200", $cursor, '%' . $wpdb->esc_like('"x_news"') . '%'), ARRAY_A);
            if ($wpdb->last_error) { throw new RuntimeException('DUPLICATE_CHECK_FAILED'); }
            foreach ((array) $rows as $row) {
                $cursor = (int) $row['id'];
                if ($cursor === $id) { continue; }
                $other = self::metadata($row)['x_news'] ?? [];
                if (in_array($other['status'] ?? '', ['POSTED', 'SENDING', 'OUTCOME_UNKNOWN', 'AWAITING_CONFIRMATION'], true) && Oldies_X_News_Policy::similar($x, $other)) { return true; }
            }
        } while (count((array) $rows) === 200);
        return false;
    }
    public function spentThisMonth(): float
    {
        global $wpdb;
        $rows = $wpdb->get_results($wpdb->prepare("SELECT metadata FROM `{$this->table}` WHERE metadata LIKE %s", '%' . $wpdb->esc_like('"x_news"') . '%'), ARRAY_A);
        if ($wpdb->last_error) { throw new RuntimeException('BUDGET_CHECK_FAILED'); }
        $total = 0.0;
        foreach ((array) $rows as $row) {
            $x = self::metadata($row)['x_news'] ?? [];
            foreach ($x['spend_reservations'] ?? [] as $reservation) {
                if (substr($reservation['at'] ?? '', 0, 7) === gmdate('Y-m')) { $total += (float) ($reservation['usd'] ?? 0); }
            }
        }
        return $total;
    }
    public function usedPostId(int $id, string $postId): bool
    {
        global $wpdb;
        $rows = $wpdb->get_results($wpdb->prepare("SELECT id,metadata FROM `{$this->table}` WHERE metadata LIKE %s", '%' . $wpdb->esc_like('"x_news"') . '%'), ARRAY_A);
        if ($wpdb->last_error) { throw new RuntimeException('POST_ID_CHECK_FAILED'); }
        foreach ((array) $rows as $row) {
            if ((int) $row['id'] !== $id && (self::metadata($row)['x_news']['post_id'] ?? '') === $postId) { return true; }
        }
        return false;
    }
}
