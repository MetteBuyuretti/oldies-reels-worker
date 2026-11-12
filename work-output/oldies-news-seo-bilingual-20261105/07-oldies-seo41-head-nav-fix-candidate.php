<?php
/**
 * Plugin Name: Oldies Radyo #41 Head and Draft Language Link Repair
 * Description: Surgical front-end output correction of duplicate meta descriptions and one known unpublished-language header link. Does not edit content, routes, Polylang, or other plugins.
 * Version: 0.1.0
 * Author: Oldies Radyo
 */

defined('ABSPATH') || exit;

add_action('template_redirect', 'oldies_seo41_begin_html_filter', 999);
function oldies_seo41_begin_html_filter() {
    if (is_admin() || !is_singular('post') || is_feed() || is_preview() || wp_doing_ajax()) {
        return;
    }
    if (defined('REST_REQUEST') && REST_REQUEST) {
        return;
    }
    ob_start('oldies_seo41_repair_html');
}

function oldies_seo41_repair_html($html) {
    if (!is_string($html) || strlen($html) > 2097152) {
        return $html;
    }
    $head_end = stripos($html, '</head>');
    if ($head_end === false || $head_end > 524288) {
        return $html;
    }
    $head_end += strlen('</head>');
    $head = substr($html, 0, $head_end);
    $rest = substr($html, $head_end);

    // Keep the final meta description (on this site it is the complete one).
    // Leave all canonical, hreflang, OG, Twitter and other head entries untouched.
    $pattern = '~<meta\b(?=[^>]*\bname\s*=\s*(["\'])description\1)[^>]*>~i';
    $found = preg_match_all($pattern, $head, $unused);
    if ($found !== false && $found > 1) {
        $index = 0;
        $count = $found;
        $head = preg_replace_callback($pattern, static function($match) use (&$index, $count) {
            $index++;
            return $index === $count ? $match[0] : '';
        }, $head);
    }

    // Only this post has a verified link to an unpublished EN draft. Do not
    // publish the draft or change the underlying Polylang relationship.
    if (function_exists('get_queried_object_id') && (int) get_queried_object_id() === 4261) {
        $header_start = stripos($rest, '<header');
        if ($header_start !== false) {
            $header_end = stripos($rest, '</header>', $header_start);
            if ($header_end !== false && $header_end - $header_start < 131072) {
                $header_end += strlen('</header>');
                $before = substr($rest, 0, $header_start);
                $header = substr($rest, $header_start, $header_end - $header_start);
                $after = substr($rest, $header_end);
                $header = preg_replace_callback('~<a\b[^>]*>.*?</a\s*>~is', static function($match) {
                    $open_end = strpos($match[0], '>');
                    if ($open_end === false) {
                        return $match[0];
                    }
                    $tag = substr($match[0], 0, $open_end + 1);
                    $is_en_selector = preg_match('~\bclass\s*=\s*["\'][^"\']*\blanguage-en\b[^"\']*["\']~i', $tag);
                    $is_draft_link = preg_match('~\bhref\s*=\s*["\']https://oldiesradyo\.com/en/\?p=4974["\']~i', $tag);
                    return $is_en_selector && $is_draft_link ? '' : $match[0];
                }, $header);
                $rest = $before . $header . $after;
            }
        }
    }
    return $head . $rest;
}
