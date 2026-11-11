<?php
/** Offline QA fixture only. php 03-oldies-gsc41-repair-fixture-test.php
 * No WordPress install, network access, or production changes required.
 */
error_reporting(E_ALL);
define('ABSPATH', __DIR__ . '/');
define('OBJECT', 'OBJECT');
define('OLDIES_GSC41_ENABLE_REDIRECTS', true);
define('OLDIES_GSC41_ENABLE_FEEDS', true);
class WP_Post {
    public $ID;
    public function __construct($id) { $this->ID = $id; }
}
function add_action($name, $cb, $priority = 10) { $GLOBALS['callbacks'][$name][] = array($cb, $priority); }
function add_filter($name, $cb, $priority = 10) { $GLOBALS['callbacks'][$name][] = array($cb, $priority); }
function wp_parse_url($u, $piece) { return parse_url($u, $piece); }
function home_url($path = '/') { return 'https://oldiesradyo.com' . $path; }
function get_page_by_path($slug, $output, $post_type) {
    if ($post_type !== 'post' || empty($GLOBALS['test_post_exists'])) { return null; }
    return new WP_Post(456);
}
function get_post_status($id) { return $GLOBALS['test_post_status']; }
function pll_get_post_language($id, $format) { return $GLOBALS['test_post_lang']; }
function get_term_by($field, $value, $tax) {
    if ($value !== 'arastirmalar-en' || $tax !== 'category' || empty($GLOBALS['test_term_exists'])) { return false; }
    return (object) array('term_id' => 77);
}
function is_wp_error($x) { return false; }
function wp_safe_redirect($url, $code, $by) { throw new Exception('Direct redirect handler should not be called in this offline fixture'); }
function ok($check, $message) {
    $GLOBALS['checks']++;
    if (!$check) { throw new Exception('FAIL: ' . $message); }
}
$GLOBALS['checks'] = 0;
$GLOBALS['test_post_exists'] = true;
$GLOBALS['test_post_status'] = 'publish';
$GLOBALS['test_post_lang'] = 'en';
$GLOBALS['test_term_exists'] = true;
$_SERVER['REQUEST_METHOD'] = 'GET';
require __DIR__ . '/02-oldies-gsc41-repair-candidate.php';
$map = oldies_gsc41_redirect_map();
$feeds = oldies_gsc41_broken_feed_map();
ok(count($map) === 16, '16 exact redirects');
ok(count(array_unique(array_values($map))) === 12, '12 unique canonical destinations');
ok(count($feeds) === 9, '9 feeds exactly');
ok(oldies_gsc41_redirect_target_for('/1950ler/1958-2/') === '/1950ler/1958-yili/', '1958 single hop');
ok(oldies_gsc41_redirect_target_for('/some-other-path/') === null, 'no blanket redirects');
ok(oldies_gsc41_redirect_target_for('/wp-content/themes/oldies-radyo-ready/*') === null, 'no security wildcard');
ok(isset($GLOBALS['callbacks']['request']) && $GLOBALS['callbacks']['request'][0][1] === 6, 'priority 6 after historical priority 5');
$csv = fopen(__DIR__ . '/404-gsc-failed-triage-20261111.csv', 'r');
ok((bool) $csv, 'GSC source CSV present');
$header = fgetcsv($csv);
$index = array_flip($header);
$nRedirect = 0;
$nFeeds = 0;
while (($r = fgetcsv($csv)) !== false) {
    if (count($r) !== count($header)) { continue; }
    $url = $r[$index['url']];
    $path = substr($url, strlen('https://oldiesradyo.com'));
    if ($r[$index['type']] === '1950_duplicate_slug') {
        $nRedirect++;
        $expected = substr($r[$index['candidate_target']], strlen('https://oldiesradyo.com'));
        if ($expected === '/1950ler/1958/') { $expected = '/1950ler/1958-yili/'; }
        ok(oldies_gsc41_redirect_target_for($path) === $expected, 'exact target ' . $path);
    }
    if ($r[$index['type']] === 'broken_advertised_rss') {
        $nFeeds++;
        ok(isset($feeds[$path]), 'feed allowlist ' . $path);
        $_SERVER['REQUEST_URI'] = $path;
        $vars = oldies_gsc41_repair_en_feeds(array('pagename'=>'feed'));
        ok(isset($vars['feed']) && $vars['feed'] === 'rss2', 'feed query ' . $path);
        ok(isset($vars['lang']) && $vars['lang'] === 'en', 'feed language ' . $path);
    }
}
fclose($csv);
ok($nRedirect === 16 && $nFeeds === 9, 'CSV and code counts match');
$_SERVER['REQUEST_URI'] = '/en/not-in-the-source/feed/';
ok(oldies_gsc41_repair_en_feeds(array('pagename'=>'feed')) === array('pagename'=>'feed'), 'not-allowlisted feed untouched');
$_SERVER['REQUEST_URI'] = '/en/2026/11/01/rolling-stones-who-you-callin-crazy-october-2026/feed/';
$GLOBALS['test_post_lang'] = 'tr';
ok(oldies_gsc41_repair_en_feeds(array('pagename'=>'feed')) === array('pagename'=>'feed'), 'TR post not served as EN');
$GLOBALS['test_post_lang'] = 'en';
$GLOBALS['test_post_status'] = 'draft';
ok(oldies_gsc41_repair_en_feeds(array('pagename'=>'feed')) === array('pagename'=>'feed'), 'draft not exposed');
$GLOBALS['test_post_status'] = 'publish';
$_SERVER['REQUEST_METHOD'] = 'POST';
ok(oldies_gsc41_repair_en_feeds(array('pagename'=>'feed')) === array('pagename'=>'feed'), 'non-read method untouched');
echo 'FIXTURE PASS: ' . $GLOBALS['checks'] . " assertions; no live changes\n";
