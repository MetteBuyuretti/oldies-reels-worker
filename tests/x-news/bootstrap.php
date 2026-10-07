<?php
define('ABSPATH', __DIR__ . '/');
define('ARRAY_A', 'ARRAY_A');
class WP_Error { public function __construct(public string $code, public string $message = '') {} }
function is_wp_error($v) { return $v instanceof WP_Error; }
function wp_json_encode($v, $flags = 0) { return json_encode($v, $flags); }
function wp_remote_retrieve_response_code($v) { return (int) ($v['response']['code'] ?? 0); }
function wp_remote_retrieve_body($v) { return $v['body'] ?? ''; }
function wp_remote_retrieve_header($v, $key) { return $v['headers'][$key] ?? ''; }
function get_post($id) { return $GLOBALS['posts'][$id] ?? null; }
function get_permalink($id) { return $GLOBALS['urls'][$id] ?? ''; }
function pll_get_post_language($id, $kind) { return $GLOBALS['languages'][$id] ?? null; }
function get_the_post_thumbnail_url($id, $size) { return 'https://oldiesradyo.com/media/artist.jpg'; }
function get_option($k, $default = false) { return $GLOBALS['options'][$k] ?? $default; }
function update_option($k, $v, $autoload = null) { $GLOBALS['options'][$k] = $v; return true; }
function current_user_can($cap) { return $GLOBALS['can_manage'] ?? true; }
function wp_die($text) { throw new RuntimeException($text); }
function absint($n) { return abs((int) $n); }
function sanitize_key($v) { return preg_replace('/[^a-z0-9_\-]/', '', strtolower($v)); }
function sanitize_text_field($v) { return trim(strip_tags($v)); }
function sanitize_textarea_field($v) { return trim(strip_tags($v)); }
function wp_unslash($v) { return $v; }
function esc_url_raw($v) { return $v; }
function get_current_user_id() { return 42; }
function check_admin_referer($v) { if (($GLOBALS['nonce_valid'] ?? true) === false) { throw new RuntimeException('BAD_NONCE'); } }
function admin_url($v) { return 'https://oldiesradyo.com/wp-admin/' . $v; }
function add_query_arg($args, $url) { return $url . '&' . http_build_query($args); }
function wp_redirect($v) { echo json_encode(['redirect' => $v, 'rows' => $GLOBALS['wpdb']->data, 'calls' => $GLOBALS['network_calls'] ?? 0, 'sources'=>$GLOBALS['sources']??[]]); }
function wp_safe_redirect($v) { wp_redirect($v); }
function wp_remote_request($url, $args) { $GLOBALS['network_calls'] = ($GLOBALS['network_calls'] ?? 0) + 1; return $GLOBALS['network_response'] ?? new WP_Error('offline'); }
function add_action(...$args) { $GLOBALS['hooks'][] = $args; }
function add_submenu_page(...$args) { $GLOBALS['menus'][] = $args; }
function get_the_terms($id,$taxonomy) { return $GLOBALS['terms'][$id]??[]; }
function esc_url($v) { return htmlspecialchars($v,ENT_QUOTES,'UTF-8'); }
function esc_html($v) { return htmlspecialchars($v,ENT_QUOTES,'UTF-8'); }
function esc_attr($v) { return htmlspecialchars($v,ENT_QUOTES,'UTF-8'); }
function esc_textarea($v) { return htmlspecialchars($v,ENT_QUOTES,'UTF-8'); }
function selected($a,$b,$echo=true) { $out=$a===$b?'selected':'';if($echo){echo $out;}return $out; }
function wp_nonce_field($v) { echo '<input name="_wpnonce" value="fixture">'; }

final class TestDB
{
    public string $prefix = 'wp_';
    public string $dbname = 'test';
    public string $last_error = '';
    public array $data = [];
    public array $writes = [];
    public bool $lockAvailable = true;
    public int $releases = 0;
    public bool $failCas = false;
    public array $columns = ['id','metadata','en_post_id','headline','updated_at','fingerprint','artist_topic','article_url'];
    public function prepare($sql, ...$args)
    {
        $i = 0;
        return preg_replace_callback('/%[sd]/', function ($m) use ($args, &$i) {
            $v = $args[$i++]; return $m[0] === '%d' ? (string) (int) $v : "'" . str_replace("'", "''", (string) $v) . "'";
        }, $sql);
    }
    public function esc_like($s) { return addcslashes($s, '_%\\'); }
    public function get_col_info($n) { return $this->columns; }
    public function get_row($sql, $mode)
    {
        if (preg_match('/WHERE en_post_id=(\d+)/', $sql, $m)) { foreach ($this->data as $r) { if (($r['en_post_id'] ?? 0) == $m[1]) { return $r; } } return null; }
        preg_match('/WHERE id=(\d+)/', $sql, $m); return $this->data[(int) ($m[1] ?? 0)] ?? null;
    }
    public function get_results($sql, $mode = null)
    {
        if (str_contains($sql, 'LIMIT 0')) { return []; }
        $rows = array_values($this->data);
        if (str_contains($sql, 'metadata LIKE')) { $rows = array_values(array_filter($rows, fn($r) => str_contains($r['metadata'] ?? '', '"x_news"'))); }
        if (preg_match('/WHERE id>(\d+)/', $sql, $m)) { $rows = array_values(array_filter($rows, fn($r) => $r['id'] > $m[1])); }
        if (str_contains($sql, 'ORDER BY id DESC')) { usort($rows, fn($a,$b) => $b['id'] <=> $a['id']); }
        else { usort($rows, fn($a,$b) => $a['id'] <=> $b['id']); }
        if (preg_match('/LIMIT (\d+)(?: OFFSET (\d+))?/', $sql, $m)) { $rows = array_slice($rows, (int) ($m[2] ?? 0), (int) $m[1]); }
        return $rows;
    }
    public function get_var($sql)
    {
        if (str_contains($sql, 'GET_LOCK')) { return $this->lockAvailable ? '1' : '0'; }
        if (str_contains($sql, 'RELEASE_LOCK')) { $this->releases++; return '1'; }
        throw new RuntimeException('UNEXPECTED_SQL');
    }
    public function query($sql)
    {
        if (!preg_match("/SET metadata='((?:''|[^'])*)',updated_at='[^']*' WHERE id=(\d+) AND (.*)$/s", $sql, $m)) { throw new RuntimeException('BAD_UPDATE_SQL'); }
        $id = (int) $m[2]; $raw = $this->data[$id]['metadata'] ?? null;
        $where = $m[3];
        if ($where !== 'metadata IS NULL') {
            preg_match("/BINARY metadata=BINARY '((?:''|[^'])*)'/s", $where, $expected);
            if ($raw !== str_replace("''", "'", $expected[1] ?? '')) { return 0; }
        } elseif ($raw !== null) { return 0; }
        if ($this->failCas) { return 0; }
        $this->writes[] = $id; $this->data[$id]['metadata'] = str_replace("''", "'", $m[1]);
        return 1;
    }
}

require __DIR__ . '/../../wordpress/oldies-x-news-bridge/includes/Policy.php';
require __DIR__ . '/../../wordpress/oldies-x-news-bridge/includes/Store.php';
require __DIR__ . '/../../wordpress/oldies-x-news-bridge/includes/Publisher.php';
require __DIR__ . '/../../wordpress/oldies-x-news-bridge/includes/Controller.php';

function setup(): array
{
    $GLOBALS['wpdb'] = new TestDB(); $GLOBALS['options'] = []; $GLOBALS['network_calls'] = 0;
    $row = ['id'=>1, 'en_post_id'=>10, 'metadata'=>'{"existing":{"keep":"do not overwrite"}}', 'headline'=>'Elton John announces archival album', 'summary_raw'=>'An archival album is on the way.', 'article_url'=>'https://www.bbc.com/news/example', 'artist_topic'=>'Elton John', 'fingerprint'=>'event1', 'status'=>'PUBLISHED', 'en_content'=>'original English article', 'updated_at'=>'2026-10-07 00:00:00'];
    $GLOBALS['posts'] = [10 => (object) ['ID'=>10, 'post_status'=>'publish', 'post_type'=>'post', 'post_excerpt'=>'Elton John has announced a newly restored archival album. Details follow.', 'post_modified_gmt'=>'2026-10-07 00:00:00']];
    $GLOBALS['urls'] = [10=>'https://oldiesradyo.com/en/elton-archive/']; $GLOBALS['languages'] = [10=>'en'];
    $GLOBALS['wpdb']->data[1] = $row;
    $x = Oldies_X_News_Controller::article($row);
    $x['category'] = 'archive'; $x['text'] = 'Elton John opens the vaults with a restored archival release.' . "\n\nRead more → " . $x['wp_url'];
    $x['evidence'] = ['primary'=>'https://www.bbc.com/news/example', 'second'=>'', 'reviewed_by'=>42, 'reviewed_at'=>gmdate('c'), 'note'=>'Opened announcement and checked date and artist.'];
    $x['english_reviewed_by'] = 42; $x['status'] = 'READY'; $x['approved_by']=42; $x['approved_at']=gmdate('c');
    $x['approved_hash'] = Oldies_X_News_Controller::approvalHash($row, $x);
    return [$row,$x];
}
