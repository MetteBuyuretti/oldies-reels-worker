<?php
/**
 * Plugin Name: Oldies GSC #41 404 Repair — QA CANDIDATE, DISABLED
 * Description: #41 narrow exact-match redirects and English comment/category feed routing. OFF by default. Requires founder live approval and independent WATCHDOG QA.
 * Version: 0.1.0-candidate
 * Author: Oldies Radyo — Ana Kumanda
 */
defined('ABSPATH') || exit;

/**
 * Activation gates must be provided by approved environment / wp-config.
 * Installing this plugin alone does NOT make any live changes.
 * define('OLDIES_GSC41_ENABLE_REDIRECTS', true);
 * define('OLDIES_GSC41_ENABLE_FEEDS', true);
 */
function oldies_gsc41_flag_enabled($name) {
    return defined($name) && constant($name) === true;
}

function oldies_gsc41_request_path() {
    if (!isset($_SERVER['REQUEST_URI']) || !is_string($_SERVER['REQUEST_URI'])) {
        return '';
    }
    $path = wp_parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    return is_string($path) ? $path : '';
}

function oldies_gsc41_redirect_map() {
    // Exact source paths only. Targets are site-local; never map to a wildcard or homepage.
    return array(
        '/1950ler/bo-diddley-3/' => '/1950ler/bo-diddley/',
        '/1950ler/1958-2/' => '/1950ler/1958-yili/',
        '/1950ler/yillara-gore-1950ler-2/' => '/1950ler/yillara-gore-1950ler/',
        '/1950ler/blues-rhythm-and-blues-3/' => '/1950ler/blues-rhythm-and-blues/',
        '/1950ler/rock-n-rollun-dogusu-4/' => '/1950ler/rock-n-rollun-dogusu/',
        '/1950ler/rock-n-roll-dan-sonra-4/' => '/1950ler/rock-n-roll-dan-sonra/',
        '/1950ler/1952-yili-2/' => '/1950ler/1952-yili/',
        '/1950ler/rock-n-roll-dan-once-5/' => '/1950ler/rock-n-roll-dan-once/',
        '/1950ler/muzik-tarzlari-2/' => '/1950ler/muzik-tarzlari/',
        '/1950ler/muzik-tarzlari-4/' => '/1950ler/muzik-tarzlari/',
        '/1950ler/rock-n-roll-dan-once-4/' => '/1950ler/rock-n-roll-dan-once/',
        '/1950ler/rock-n-rollun-dogusu-2/' => '/1950ler/rock-n-rollun-dogusu/',
        '/1950ler/radyo-jukebox-plak-4/' => '/1950ler/radyo-jukebox-plak/',
        '/1950ler/yillara-gore-1950ler-3/' => '/1950ler/yillara-gore-1950ler/',
        '/1950ler/one-cikan-sanatcilar-4/' => '/1950ler/one-cikan-sanatcilar/',
        '/1950ler/longplay-1950s-1960s-3/' => '/1950ler/longplay-1950s-1960s/',
    );
}

function oldies_gsc41_redirect_target_for($path) {
    $map = oldies_gsc41_redirect_map();
    return isset($map[$path]) ? $map[$path] : null;
}

function oldies_gsc41_handle_redirect() {
    if (!oldies_gsc41_flag_enabled('OLDIES_GSC41_ENABLE_REDIRECTS')) {
        return;
    }
    $method = isset($_SERVER['REQUEST_METHOD']) ? strtoupper((string)$_SERVER['REQUEST_METHOD']) : '';
    if ($method !== 'GET' && $method !== 'HEAD') {
        return;
    }
    $to = oldies_gsc41_redirect_target_for(oldies_gsc41_request_path());
    if ($to === null || !is_string($to) || substr($to, 0, 1) !== '/') {
        return;
    }
    $absolute = home_url($to);
    // Redirect only to a whitelisted same-site target; querystring is intentionally not reflected.
    if (wp_safe_redirect($absolute, 301, 'Oldies-GSC41-Exact')) {
        exit;
    }
}
add_action('template_redirect', 'oldies_gsc41_handle_redirect', 0);

/**
 * Exact paths observed in the official GSC 404 validation export.
 * Do NOT blanket-change English routing or unrelated RSS feeds.
 */
function oldies_gsc41_broken_feed_map() {
    return array(
        '/en/2026/11/01/rolling-stones-who-you-callin-crazy-october-2026/feed/' => true,
        '/en/2026/11/02/fleetwood-mac-the-chain-documentary-january-2027/feed/' => true,
        '/en/2026/09/26/rock-stars-who-died-before-50/feed/' => true,
        '/en/2026/10/31/beatles-story-liverpool-2028-new-museum/feed/' => true,
        '/en/2026/09/04/scorpions-mexico-las-vegas-shows-rescheduled-2027/feed/' => true,
        '/en/2026/10/31/michael-jackson-uk-biggest-album-2026/feed/' => true,
        '/en/2026/10/30/1960s-italian-singers/feed/' => true,
        '/en/category/ozel-dosyalar-en/arastirmalar-en/feed/' => true,
        '/en/2026/09/05/oasis-dont-look-back-in-anger-documentary-venice-premiere/feed/' => true,
    );
}

/**
 * Fires AFTER the historical English request resolver priority 5.
 * If the installed theme's current request hook differs, do not enable
 * until its active source / version and staging tests are verified.
 */
function oldies_gsc41_repair_en_feeds($vars) {
    if (!oldies_gsc41_flag_enabled('OLDIES_GSC41_ENABLE_FEEDS')) {
        return $vars;
    }
    $method = isset($_SERVER['REQUEST_METHOD']) ? strtoupper((string)$_SERVER['REQUEST_METHOD']) : '';
    if ($method !== 'GET' && $method !== 'HEAD') {
        return $vars;
    }
    $path = oldies_gsc41_request_path();
    $map = oldies_gsc41_broken_feed_map();
    if (!isset($map[$path])) {
        return $vars;
    }
    if ($path === '/en/category/ozel-dosyalar-en/arastirmalar-en/feed/') {
        $category = get_term_by('slug', 'arastirmalar-en', 'category');
        if (!$category || is_wp_error($category)) {
            return $vars;
        }
        return array('cat' => (int)$category->term_id, 'feed' => 'rss2', 'lang' => 'en');
    }
    // Site-specific English comment feeds; only published English posts qualify.
    $prefix = '/en/';
    $post_path = substr($path, strlen($prefix), -strlen('/feed/'));
    $slug = basename(rtrim($post_path, '/'));
    $post = get_page_by_path($slug, OBJECT, 'post');
    if (!$post || !($post instanceof WP_Post) || get_post_status($post->ID) !== 'publish') {
        return $vars;
    }
    if (!function_exists('pll_get_post_language') || pll_get_post_language($post->ID, 'slug') !== 'en') {
        return $vars;
    }
    return array(
        'p' => (int)$post->ID,
        'post_type' => 'post',
        'feed' => 'rss2',
        'withcomments' => 1,
        'lang' => 'en',
    );
}
add_filter('request', 'oldies_gsc41_repair_en_feeds', 6, 1);
