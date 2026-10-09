<?php
defined('ABSPATH') || exit;

final class Oldies_X_News_Policy
{
    public const LIMIT = 280;
    public const SOURCES = [
        'loudersound.com' => 'louder', 'ultimateclassicrock.com' => 'townsquare',
        'goldradio.com' => 'global', 'goldradiouk.com' => 'global', 'smoothradio.com' => 'global',
        'rockcellarmagazine.com' => 'rockcellar', 'bestclassicbands.com' => 'bestclassicbands',
        'retropopmagazine.com' => 'retropop', 'udiscovermusic.com' => 'universal',
        'billboard.com' => 'pmc', 'rollingstone.com' => 'pmc', 'variety.com' => 'pmc',
        'nme.com' => 'nme', 'theguardian.com' => 'guardian', 'consequence.net' => 'consequence',
        'stereogum.com' => 'stereogum', 'people.com' => 'people',
        'officialcharts.com' => 'officialcharts', 'pollstar.com' => 'pollstar',
        'musicbusinessworldwide.com' => 'mbw', 'digitalmusicnews.com' => 'dmn',
        'grammy.com' => 'recordingacademy', 'rockhall.com' => 'rockhall', 'bbc.com' => 'bbc', 'bbc.co.uk' => 'bbc',
    ];
    public const OFFICIAL = [
        'paulmccartney.com', 'rollingstones.com', 'rodstewart.com', 'eltonjohn.com',
        'steviewonder.net', 'madonna.com', 'cher.com', 'brucespringsteen.net', 'billyjoel.com',
        'lionelrichie.com', 'cyndilauper.com', 'sting.com', 'dollyparton.com', 'dianaross.com',
        'thebeatles.com', 'queenonline.com', 'abbasite.com', 'abbavoyage.com',
        'universalmusic.com', 'umusic.com', 'sonymusic.com', 'warnermusic.com', 'rhino.com',
        'livenation.com', 'aegpresents.com',
    ];

    public static function host(string $url): string
    {
        return strtolower(preg_replace('/^www\./i', '', (string) parse_url($url, PHP_URL_HOST)));
    }

    public static function canonical(string $url): string
    {
        $p = parse_url($url);
        if (!$p || empty($p['host']) || !in_array(strtolower($p['scheme'] ?? ''), ['https', 'http'], true) || isset($p['user']) || isset($p['pass']) || isset($p['port'])) {
            return '';
        }
        $query = [];
        parse_str($p['query'] ?? '', $query);
        foreach (array_keys($query) as $key) {
            if (preg_match('/^(utm_|fbclid$|gclid$|mc_cid$|mc_eid$)/i', $key)) { unset($query[$key]); }
        }
        ksort($query);
        return 'https://' . self::host($url) . '/' . ltrim(rtrim($p['path'] ?? '', '/'), '/') . ($query ? '?' . http_build_query($query) : '');
    }

    public static function group(string $url): string
    {
        $host = self::host($url);
        return self::SOURCES[$host] ?? (in_array($host, self::OFFICIAL, true) ? 'official:' . $host : '');
    }

    public static function sensitive(array $row, array $x): bool
    {
        $s = implode(' ', [$row['headline'] ?? '', $row['en_title'] ?? '', $row['summary_raw'] ?? '', $row['tr_title'] ?? '', $x['text'] ?? '', $x['category'] ?? '']);
        return (bool) preg_match('/\b(die[sd]?|dead|death|passed away|hospital\w*|surg\w*|illness|health|cancer|stroke|heart|cardiac|ill|sick|injur\w*|recover\w*|pneumonia|sepsis|disease|lawsuit|legal|court|accus\w*|alleg\w*|arrest\w*|scandal|controvers\w*|suicide|abuse|assault|charged|dementia|diagnos\w*|operation|treatment|custody|crime)\b|ölüm|öldü|vefat|hastan|hastal|ameliyat|sağlık|kanser|kalp|dava|suçlama|tutukla/iu', $s);
    }

    /** The editor attests to actual evidence, not merely the existence of URLs. */
    public static function evidence(array $row, array $x): bool
    {
        $e = $x['evidence'] ?? [];
        if (empty($e['reviewed_by']) || empty($e['reviewed_at']) || trim($e['note'] ?? '') === '') { return false; }
        $a = trim($e['primary'] ?? '');
        $b = trim($e['second'] ?? '');
        $ga = self::group($a);
        if ($ga === '' || !self::canonical($a)) { return false; }
        if (!self::sensitive($row, $x)) { return true; }
        $gb = self::group($b);
        return $gb !== '' && $ga !== $gb && self::canonical($b) !== '' && self::canonical($a) !== self::canonical($b);
    }

    /** Conservative server upper bound; browser uses X's official twitter-text parser. */
    public static function weight(string $text): int
    {
        if (!preg_match('//u', $text) || preg_match('/[\x{0000}-\x{0008}\x{000B}\x{000C}\x{000E}-\x{001F}\x{FEFF}\x{FFFE}\x{FFFF}]/u', $text)) { return PHP_INT_MAX; }
        $urls = 0;
        $plain = preg_replace_callback('~https?://[^\s<>()]+~u', static function () use (&$urls) { $urls++; return ''; }, $text);
        $count = 23 * $urls;
        foreach (preg_split('//u', $plain, -1, PREG_SPLIT_NO_EMPTY) as $char) {
            $cp = mb_ord($char, 'UTF-8');
            $count += ($cp <= 0x10FF || ($cp >= 0x2000 && $cp <= 0x200D) || ($cp >= 0x2010 && $cp <= 0x201F) || ($cp >= 0x2032 && $cp <= 0x2037)) ? 1 : 2;
        }
        return $count;
    }

    public static function draft(string $excerpt, string $url): string
    {
        $excerpt = trim(html_entity_decode(strip_tags($excerpt), ENT_QUOTES | ENT_HTML5, 'UTF-8'));
        $excerpt = preg_replace('~https?://\S+~u', '', $excerpt);
        $sentences = preg_split('/(?<=[.!?])\s+/u', $excerpt);
        $lead = trim($sentences[0] ?? '');
        $tail = "\n\nRead more → " . $url;
        if ($lead === '') { return ''; }
        while (self::weight($lead . $tail) > self::LIMIT && mb_strlen($lead) > 1) {
            $lead = preg_replace('/\s+\S+$/u', '', $lead, 1, $changed);
            if (!$changed) { return ''; }
        }
        return $lead . $tail;
    }

    public static function textError(string $text, string $url): string
    {
        if (trim($text) === '') { return 'TEXT_REQUIRED'; }
        if (self::weight($text) > self::LIMIT) { return 'CHARACTER_LIMIT'; }
        preg_match_all('~https?://[^\s<>()]+~u', $text, $links);
        if (count($links[0]) !== 1 || self::canonical($links[0][0]) !== self::canonical($url)) { return 'ONE_OLDIES_LINK_REQUIRED'; }
        if (preg_match_all('/(?:^|\s)#[\p{L}\p{N}_]+/u', $text) > 3) { return 'HASHTAG_LIMIT'; }
        return '';
    }

    public static function similar(array $a, array $b): bool
    {
        if (!empty($a['wp_url']) && self::canonical($a['wp_url']) === self::canonical($b['wp_url'] ?? '')) { return true; }
        if (!empty($a['story_key']) && $a['story_key'] === ($b['story_key'] ?? '')) { return true; }
        $artistA = mb_strtolower(trim($a['artist'] ?? ''), 'UTF-8');
        $artistB = mb_strtolower(trim($b['artist'] ?? ''), 'UTF-8');
        if (!$artistA || $artistA !== $artistB) { return false; }
        $tokens = static function (string $text): array {
            $text = preg_replace('~https?://\S+~u', '', mb_strtolower($text, 'UTF-8'));
            $words = preg_split('/[^\p{L}\p{N}]+/u', $text, -1, PREG_SPLIT_NO_EMPTY);
            return array_values(array_unique(array_diff($words, ['the', 'and', 'for', 'with', 'has', 'have', 'will', 'from', 'more', 'read', 'this', 'that', 'a', 'an', 'is', 'to', 'of', 'in', 'on'])));
        };
        $ta = $tokens($a['text'] ?? ''); $tb = $tokens($b['text'] ?? '');
        return count($ta) >= 4 && count(array_intersect($ta, $tb)) / max(1, count(array_unique(array_merge($ta, $tb)))) >= 0.65;
    }

    public static function initialStatus(array $row, array $x): string
    {
        if (in_array($x['status'] ?? '', ['POSTED', 'REJECTED', 'SENDING', 'OUTCOME_UNKNOWN'], true)) { return $x['status']; }
        if (empty($x['wp_url'])) { return 'NEWS CANDIDATE'; }
        if (!self::evidence($row, $x)) { return 'HOLD'; }
        if (self::textError($x['text'] ?? '', $x['wp_url']) !== '') { return 'VERIFIED'; }
        return empty($x['approved_by']) ? 'VERIFIED' : 'READY';
    }
}
