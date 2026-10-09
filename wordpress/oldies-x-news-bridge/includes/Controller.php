<?php
defined('ABSPATH') || exit;

final class Oldies_X_News_Controller
{
    private static array $renderRow = [];
    public static function boot(): void
    {
        add_action('admin_menu', [self::class, 'menu'], 90);
        add_action('admin_post_oldies_x_news', [self::class, 'handle']);
        add_action('transition_post_status', [self::class, 'published'], 20, 3);
        add_action('admin_enqueue_scripts', [self::class, 'assets']);
    }
    public static function menu(): void
    {
        add_submenu_page('oldies-cc-dashboard', 'X NEWS', 'X NEWS', 'manage_options', 'oldies-cc-x-news', [self::class, 'render']);
    }
    public static function assets(): void
    {
        if (($_GET['page'] ?? '') === 'oldies-cc-x-news') {
            wp_enqueue_script('oldies-x-news', plugins_url('../assets/editor.js', __FILE__), [], '0.1.0', true);
        }
    }
    private static function url(array $args = []): string
    {
        return add_query_arg($args, admin_url('admin.php?page=oldies-cc-x-news'));
    }
    public static function article(array $row): array
    {
        $x = Oldies_X_News_Store::metadata($row)['x_news'] ?? [];
        $post = get_post((int) ($row['en_post_id'] ?? 0));
        $eligible = $post && $post->post_type === 'post' && $post->post_status === 'publish' && function_exists('pll_get_post_language') && pll_get_post_language($post->ID, 'slug') === 'en';
        $url = $eligible ? get_permalink($post->ID) : '';
        if ($url && Oldies_X_News_Policy::host($url) !== 'oldiesradyo.com') { $url = ''; }
        $x['wp_url'] = $url;
        $x['wp_post_modified_gmt'] = $eligible ? $post->post_modified_gmt : '';
        $x['artist'] = $x['artist'] ?? ($row['artist_topic'] ?? '');
        $x['story_key'] = $x['story_key'] ?? ($row['fingerprint'] ?? '');
        $x['language'] = 'en';
        $x['image_url'] = $eligible ? (get_the_post_thumbnail_url($post->ID, 'medium') ?: '') : '';
        $x['image_mode'] = 'link_preview'; // No image download, upload or license assumption.
        if (!isset($x['text'])) { $x['text'] = $eligible ? Oldies_X_News_Policy::draft($post->post_excerpt ?: ($row['en_excerpt'] ?? ''), $url) : ''; }
        $x['status'] = $x['status'] ?? ($url ? 'NEW' : 'NEWS CANDIDATE');
        return $x;
    }
    /** Existing queue entries only: this never scans or creates unrelated historical pages. */
    public static function published($new, $old, $post): void
    {
        if ($new !== 'publish' || $old === 'publish' || !$post || $post->post_type !== 'post') { return; }
        try {
            $store = new Oldies_X_News_Store();
            if (!$store->available() || !function_exists('pll_get_post_language') || pll_get_post_language($post->ID, 'slug') !== 'en') { return; }
            global $wpdb;
            $table = $wpdb->prefix . 'oldies_news_articles';
            $row = $wpdb->get_row($wpdb->prepare("SELECT * FROM `{$table}` WHERE en_post_id=%d ORDER BY id LIMIT 1", $post->ID), ARRAY_A);
            if ($row && empty(Oldies_X_News_Store::metadata($row)['x_news'])) { $store->save($row, self::article($row)); }
        } catch (Throwable $e) {
            // X failure is isolated: never bubble into WordPress publication or another platform.
            error_log('X_POST_FAILED: QUEUE_PREPARE_FAILED');
        }
    }
    private static function form(string $action, int $id = 0): void
    {
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        echo '<input type="hidden" name="action" value="oldies_x_news"><input type="hidden" name="intent" value="' . esc_attr($action) . '"><input type="hidden" name="id" value="' . $id . '">';
        if ($id && self::$renderRow) { echo '<input type="hidden" name="revision" value="' . esc_attr(self::revision(self::$renderRow)) . '">'; }
        wp_nonce_field('oldies_x_news_' . $action . '_' . $id);
    }
    public static function render(): void
    {
        if (!current_user_can('manage_options')) { wp_die('FORBIDDEN'); }
        echo '<div class="wrap"><h1>X NEWS</h1><p>İngilizce haberler · 1950–1990 ve aktif klasik sanatçılar · günlük hedef 3–6 kaliteli paylaşım · editoryal onay zorunlu.</p>';
        if (!extension_loaded('mbstring')) { echo '<p>BLOCKED: mbstring gerekli.</p></div>'; return; }
        $store = new Oldies_X_News_Store();
        if (!$store->available()) { echo '<p>BLOCKED: Mevcut haber tablosu/şeması bulunamadı. Social &amp; News altyapısı doğrulanmalı.</p></div>'; return; }
        $identity = get_option('oldies_x_verified_identity', []);
        echo '<p><strong>Yayın modu:</strong> ' . (Oldies_X_News_Publisher::enabled() ? 'API açık; bütçe ve hesap doğrulaması gerekli' : 'Ücretsiz: X paylaşım penceresi + gönderi bağlantısıyla teyit') . ' · <strong>Hesap:</strong> ' . esc_html($identity['username'] ?? 'Doğrulanmadı') . ' · <strong>Auto posting:</strong> Kapalı</p>';
        if (isset($_GET['result'])) { echo '<div class="notice notice-info"><p>' . esc_html(sanitize_text_field(wp_unslash($_GET['result']))) . '</p></div>'; }
        $id = absint($_GET['id'] ?? 0);
        if ($id) {
            $row = $store->row($id);
            if (!$row) { echo '<p>Haber bulunamadı.</p></div>'; return; }
            self::detail($row);
        } else {
            $page = max(1, absint($_GET['paged'] ?? 1));
            echo '<table class="widefat striped"><thead><tr><th>Başlık / Sanatçı</th><th>Kaynak / Tarih</th><th>WordPress</th><th>X Durumu</th><th>İşlem</th></tr></thead><tbody>';
            foreach ($store->rows($page) as $row) {
                $x = self::article($row);
                echo '<tr><td><strong>' . esc_html($row['headline']) . '</strong><br>' . esc_html($x['artist']) . '</td><td>' . esc_html($row['source_name']) . '<br>' . esc_html($row['published_date'] ?? $row['detected_date']) . '</td><td>';
                echo $x['wp_url'] ? '<a href="' . esc_url($x['wp_url']) . '" target="_blank" rel="noopener">EN Haber</a>' : 'NEWS CANDIDATE';
                echo '</td><td>' . esc_html($x['status']) . '</td><td><a class="button" href="' . esc_url(self::url(['id' => $row['id']])) . '">Edit before publish</a></td></tr>';
            }
            echo '</tbody></table><p>';
            if ($page > 1) { echo '<a href="' . esc_url(self::url(['paged' => $page - 1])) . '">← Önceki</a> · '; }
            echo '<a href="' . esc_url(self::url(['paged' => $page + 1])) . '">Sonraki →</a></p>';
            self::form('sources'); echo '<button class="button">Kaynak havuzundaki eksikleri mevcut tarayıcıya ekle</button><p>Mevcut kaynak ayarları korunur. Yeni kaynaklar pasif eklenir; canlı parser testi sonrası mevcut Kaynaklar ekranından etkinleştirilir.</p></form>';
            self::form('import'); echo '<p><label>Yayınlanmış EN haber ID <input name="post_id" type="number" min="1" required></label> <label>Sanatçı <input name="artist" required></label></p><p><label>Haberin yabancı kaynak URL’si <input name="primary" type="url" class="large-text" required></label></p><button class="button">WordPress haberini mevcut haber kuyruğuna bağla</button><p>Yalnız son 90 günde yayınlanmış İngilizce haber yazıları. Proje sayfaları ve eski içerikler alınmaz; yayın onayı verilmez.</p></form>';
            self::form('identity'); echo '<button class="button">API hesap bağlantısını kontrol et</button><p>Bu kontrol varsayılan olarak kapalıdır; ücretli istek için açık bütçe ve beklenen hesap adı gerekir.</p></form>';
        }
        echo '</div>';
    }
    private static function detail(array $row): void
    {
        self::$renderRow = $row;
        $x = self::article($row);
        echo '<p><a href="' . esc_url(self::url()) . '">← Kuyruk</a></p><h2>' . esc_html($row['headline']) . '</h2><p><strong>' . esc_html($x['status']) . '</strong> · ' . (Oldies_X_News_Policy::sensitive($row, $x) ? 'Hassas haber: iki bağımsız kanıt + manuel onay' : 'Kaynak incelemesi + manuel onay') . '</p>';
        if ($x['image_url']) { echo '<img src="' . esc_url($x['image_url']) . '" alt="" style="max-width:260px;height:auto"><p>Site görseli. X’e yeniden yüklenmez; bağlantı kartı kullanılır.</p>'; }
        if ($x['wp_url']) { echo '<p><a target="_blank" rel="noopener" href="' . esc_url($x['wp_url']) . '">EN WordPress haberi</a></p>'; }
        if (in_array($x['status'], ['POSTED', 'SENDING', 'OUTCOME_UNKNOWN', 'AWAITING_CONFIRMATION'], true)) {
            echo '<p>' . esc_html($x['text']) . '</p>';
            if (!empty($x['post_id'])) { echo '<a href="https://x.com/i/status/' . esc_attr($x['post_id']) . '">X gönderisi</a>'; }
            if ($x['status'] === 'OUTCOME_UNKNOWN' || $x['status'] === 'SENDING') { echo '<p>Sonuç belirsiz. Otomatik tekrar kapalı; hesabı kontrol edip gerçek gönderi bağlantısını teyit edin.</p>'; }
            if ($x['status'] !== 'POSTED') {
                self::form('confirm', (int) $row['id']);
                echo '<p><label>X gönderi URL’si <input name="post_url" type="url" required class="large-text" placeholder="https://x.com/hesap/status/123..."></label></p><p><label><input type="checkbox" name="confirmed" value="1" required> Hesap, metin ve Oldies bağlantısını X üzerinde kontrol ettim.</label></p><button class="button button-primary">POSTED olarak teyit et</button></form>';
                if ($x['status'] === 'AWAITING_CONFIRMATION') {
                    self::form('cancel_intent', (int) $row['id']);
                    echo '<p><label><input type="checkbox" name="confirmed" value="1" required> X penceresini kapattım ve bu gönderiyi yayınlamadım.</label></p><button class="button">Yayınlanmamış taslağı READY durumuna geri al</button></form>';
                }
            }
            return;
        }
        $e = $x['evidence'] ?? [];
        self::form('save', (int) $row['id']);
        echo '<p><label>Sanatçı <input class="regular-text" name="artist" required value="' . esc_attr($x['artist']) . '"></label> <label>Kategori <select name="category">';
        foreach (['album', 'tour', 'reunion', 'archive', 'chart', 'award', 'biopic', 'interview', 'on_this_day', 'death', 'health', 'legal', 'controversy', 'other'] as $category) { echo '<option ' . selected($x['category'] ?? 'other', $category, false) . '>' . esc_html($category) . '</option>'; }
        echo '</select></label></p><p><label>Olay anahtarı (aynı haber için aynı: sanatçı/konu/tarih) <input class="large-text" name="story_key" value="' . esc_attr($x['story_key']) . '" required></label></p>';
        echo '<p><label>İngilizce X metni (1 Oldies bağlantısı, en fazla 3 hashtag)<textarea id="oldies-x-text" class="large-text" rows="5" name="text">' . esc_textarea($x['text']) . '</textarea></label><span id="oldies-x-count"></span></p>';
        foreach (['primary' => 'Birinci yabancı kaynak', 'second' => 'İkinci bağımsız kaynak / resmî açıklama'] as $key => $label) { $default = $key === 'primary' ? ($row['article_url'] ?? '') : ($row['source_url_2'] ?? ''); echo '<p><label>' . esc_html($label) . '<input type="url" class="large-text" name="' . $key . '" value="' . esc_attr($e[$key] ?? $default) . '"></label></p>'; }
        echo '<p><label>Doğrulama notu<textarea class="large-text" rows="2" name="evidence_note">' . esc_textarea($e['note'] ?? '') . '</textarea></label></p><p><label><input type="checkbox" name="evidence_reviewed" value="1"> Kaynakları açtım; tarih, sanatçı ve aynı olay için kanıtı karşılaştırdım.</label></p><p><label><input type="checkbox" name="english_reviewed" value="1"> Metnin tamamen İngilizce ve haberle uyumlu olduğunu kontrol ettim.</label></p><button class="button button-primary">Kaydet ve doğrula</button></form>';
        if (in_array($x['status'], ['VERIFIED', 'READY'], true)) {
            self::form('approve', (int) $row['id']); echo '<p><label><input type="checkbox" name="confirmed" value="1" required> Bu metni, kaynakları ve yayın tarihinin güncelliğini onaylıyorum.</label></p><button class="button">READY: yayına onayla</button></form>';
        }
        if ($x['status'] === 'READY') {
            self::form('intent', (int) $row['id']); echo '<p><button class="button button-primary">Publish: ücretsiz X paylaşım penceresini aç</button></p></form>';
            if (Oldies_X_News_Publisher::enabled()) { self::form('api', (int) $row['id']); echo '<p><label><input type="checkbox" name="confirmed" value="1" required> Bütçe içindeki ücretli API gönderisini yayınla.</label></p><button class="button">Publish via API</button></form>'; }
        }
        if ($x['status'] === 'FAILED' && !empty($x['retryable'])) {
            self::form('retry', (int) $row['id']); echo '<p><label><input type="checkbox" name="confirmed" value="1" required> Sorunu düzelttim; yeniden yayın onayına al.</label></p><button class="button">FAILED → yeniden doğrula</button></form>';
        }
        self::form('reject', (int) $row['id']); echo '<p><button class="button">Reject</button></p></form>';
        if (!empty($x['error'])) { echo '<p>' . esc_html($x['error']) . '</p>'; }
    }
    private static function ready(array $row, array $x): void
    {
        if ($x['status'] !== 'READY' || !$x['wp_url'] || !Oldies_X_News_Policy::evidence($row, $x) || empty($x['english_reviewed_by']) || empty($x['approved_by']) || strtotime($x['approved_at'] ?? '') < time() - 86400) { throw new RuntimeException('FRESH_EDITORIAL_APPROVAL_REQUIRED'); }
        if ($error = Oldies_X_News_Policy::textError($x['text'], $x['wp_url'])) { throw new RuntimeException($error); }
        if (!hash_equals($x['approved_hash'] ?? '', self::approvalHash($row, $x))) { throw new RuntimeException('NEWS_CHANGED_REAPPROVAL_REQUIRED'); }
    }
    public static function approvalHash(array $row, array $x): string
    {
        return hash('sha256', wp_json_encode([
            $row['headline'] ?? '', $row['summary_raw'] ?? '', $x['wp_url'] ?? '', $x['wp_post_modified_gmt'] ?? '',
            $x['artist'] ?? '', $x['category'] ?? '', $x['story_key'] ?? '', $x['text'] ?? '', $x['evidence'] ?? [],
        ], JSON_UNESCAPED_UNICODE));
    }
    public static function revision(array $row): string
    {
        $x = self::article($row);
        return hash('sha256', wp_json_encode([$row['metadata'] ?? null, $row['headline'] ?? '', $row['summary_raw'] ?? '', $x['wp_url'], $x['wp_post_modified_gmt']]));
    }
    public static function handle(): void
    {
        if (!current_user_can('manage_options')) { wp_die('FORBIDDEN'); }
        $id = absint($_POST['id'] ?? 0); $intent = sanitize_key($_POST['intent'] ?? '');
        $allowed = ['save', 'approve', 'reject', 'retry', 'intent', 'confirm', 'cancel_intent', 'api', 'sources', 'identity', 'import'];
        if (!in_array($intent, $allowed, true)) { wp_die('INVALID_INTENT'); }
        check_admin_referer('oldies_x_news_' . $intent . '_' . $id);
        if (in_array($intent, ['approve', 'retry', 'api', 'confirm', 'cancel_intent'], true) && ($_POST['confirmed'] ?? '') !== '1') { wp_die('CONFIRMATION_REQUIRED'); }
        $destination = self::url(['id' => $id]);
        try {
            if (!extension_loaded('mbstring')) { throw new RuntimeException('MBSTRING_REQUIRED'); }
            $store = new Oldies_X_News_Store();
            if (!$store->available()) { throw new RuntimeException('EXISTING_NEWS_SCHEMA_REQUIRED'); }
            $destination = $store->locked(static function () use ($store, $id, $intent, $destination) {
                if ($intent === 'sources') { self::sources(); return self::url(['result' => 'Kaynaklar mevcut havuza pasif eklendi; canlı parser doğrulaması bekliyor.']); }
                if ($intent === 'import') { $imported = self::import(); return self::url(['id' => $imported, 'result' => 'Haber mevcut kuyruğa bağlandı; kaynak doğrulaması ve yayın onayı gerekiyor.']); }
                if ($intent === 'identity') {
                    $costs = get_option('oldies_x_read_spend', []); $costs = is_array($costs) ? $costs : [];
                    $spent = $store->spentThisMonth() + (float) ($costs[gmdate('Y-m')] ?? 0);
                    if ($error = Oldies_X_News_Publisher::budgetError($spent, 0.01)) { throw new RuntimeException($error); }
                    $costs[gmdate('Y-m')] = (float) ($costs[gmdate('Y-m')] ?? 0) + 0.01;
                    update_option('oldies_x_read_spend', $costs, false);
                    $identity = (new Oldies_X_News_Publisher())->identityCheck($spent);
                    update_option('oldies_x_verified_identity', $identity, false);
                    return self::url(['result' => 'X_ACCOUNT_VERIFIED_' . $identity['username']]);
                }
                $row = $store->row($id); if (!$row) { throw new RuntimeException('NEWS_NOT_FOUND'); }
                if (!hash_equals(self::revision($row), (string) ($_POST['revision'] ?? ''))) { throw new RuntimeException('EDITOR_STATE_CHANGED_RELOAD'); }
                $x = self::article($row); $actor = get_current_user_id(); $now = gmdate('c');
                if ($intent === 'confirm') {
                    if (!in_array($x['status'], ['AWAITING_CONFIRMATION', 'SENDING', 'OUTCOME_UNKNOWN'], true)) { throw new RuntimeException('NOT_AWAITING_CONFIRMATION'); }
                    $url = trim(wp_unslash($_POST['post_url'] ?? ''));
                    if (!preg_match('~^https://(?:www\.)?(?:x\.com|twitter\.com)/(?:[A-Za-z0-9_]{1,15}/status|i/status)/(\d{1,25})/?(?:\?[^\s]*)?$~D', $url, $m)) { throw new RuntimeException('VALID_X_POST_URL_REQUIRED'); }
                    if ($store->usedPostId($id, $m[1])) { throw new RuntimeException('X_POST_ID_ALREADY_RECORDED'); }
                    $journal = get_option('oldies_x_outcome_' . $id, []);
                    if (!empty($journal['post_id']) && $journal['post_id'] !== $m[1]) { throw new RuntimeException('RECORDED_API_OUTCOME_MISMATCH'); }
                    $x['status'] = 'POSTED'; $x['post_id'] = $m[1]; $x['published_at'] = $now; $x['confirmed_by'] = $actor; $x['confirmation_method'] = 'manual_account_text_link_review'; $x['error'] = '';
                    $store->save($row, $x); return self::url(['id' => $id, 'result' => 'POSTED']);
                }
                if ($intent === 'cancel_intent') {
                    if ($x['status'] !== 'AWAITING_CONFIRMATION') { throw new RuntimeException('ONLY_UNUSED_WEB_INTENT_CAN_CANCEL'); }
                    $x['status'] = 'READY'; $x['approved_by'] = null; $x['approved_at'] = null;
                    $store->save($row, $x); return self::url(['id' => $id, 'result' => 'Yeni yayın onayı gerekiyor.']);
                }
                if (in_array($x['status'], ['POSTED', 'SENDING', 'OUTCOME_UNKNOWN', 'AWAITING_CONFIRMATION'], true)) { throw new RuntimeException('ALREADY_POSTED_OR_RESERVED_NO_RETRY'); }
                if ($intent === 'save') {
                    $x['text'] = trim(sanitize_textarea_field(wp_unslash($_POST['text'] ?? '')));
                    $x['artist'] = sanitize_text_field(wp_unslash($_POST['artist'] ?? ''));
                    $x['story_key'] = sanitize_text_field(wp_unslash($_POST['story_key'] ?? ''));
                    $x['category'] = sanitize_key($_POST['category'] ?? 'other');
                    $x['approved_by'] = null; $x['approved_at'] = null;
                    $x['english_reviewed_by'] = ($_POST['english_reviewed'] ?? '') === '1' ? $actor : null;
                    $x['evidence'] = ['primary' => esc_url_raw(wp_unslash($_POST['primary'] ?? '')), 'second' => esc_url_raw(wp_unslash($_POST['second'] ?? '')), 'note' => sanitize_textarea_field(wp_unslash($_POST['evidence_note'] ?? '')), 'reviewed_by' => ($_POST['evidence_reviewed'] ?? '') === '1' ? $actor : null, 'reviewed_at' => $now];
                    $x['status'] = Oldies_X_News_Policy::initialStatus($row, $x);
                } elseif ($intent === 'approve') {
                    if (!in_array($x['status'], ['VERIFIED', 'READY'], true) || !Oldies_X_News_Policy::evidence($row, $x) || !$x['wp_url'] || empty($x['artist']) || empty($x['story_key']) || empty($x['english_reviewed_by']) || Oldies_X_News_Policy::textError($x['text'], $x['wp_url'])) { throw new RuntimeException('HOLD_VERIFY_TEXT_AND_EVIDENCE'); }
                    $x['approved_by'] = $actor; $x['approved_at'] = $now; $x['status'] = 'READY';
                    $x['approved_hash'] = self::approvalHash($row, $x);
                } elseif ($intent === 'reject') { $x['status'] = 'REJECTED'; $x['rejected_by'] = $actor;
                } elseif ($intent === 'retry') {
                    if ($x['status'] !== 'FAILED' || empty($x['retryable']) || ($x['retry_after'] ?? 0) > time()) { throw new RuntimeException('RETRY_NOT_SAFE_OR_TOO_EARLY'); }
                    $x['approved_by'] = null; $x['status'] = Oldies_X_News_Policy::initialStatus($row, $x); $x['error'] = '';
                } elseif ($intent === 'intent' || $intent === 'api') {
                    self::ready($row, $x);
                    if ($store->duplicate($id, $x)) { throw new RuntimeException('DUPLICATE_POST_BLOCKED'); }
                    if ($intent === 'intent') {
                        $x['status'] = 'AWAITING_CONFIRMATION'; $x['reserved_at'] = $now;
                        $store->save($row, $x);
                        return 'https://twitter.com/intent/tweet?text=' . rawurlencode($x['text']);
                    }
                    $reads = get_option('oldies_x_read_spend', []);
                    $spent = $store->spentThisMonth() + (float) ($reads[gmdate('Y-m')] ?? 0);
                    if ($error = Oldies_X_News_Publisher::budgetError($spent, Oldies_X_News_Publisher::LINK_POST_USD)) { throw new RuntimeException($error); }
                    if (!Oldies_X_News_Publisher::identityValid(get_option('oldies_x_verified_identity', []))) { throw new RuntimeException('VERIFY_EXPECTED_X_ACCOUNT_FIRST'); }
                    // Validate credentials before reserving a possibly billable request.
                    Oldies_X_News_Publisher::authorization('POST', 'https://api.x.com/2/tweets');
                    $x['status'] = 'SENDING'; $x['attempts'] = (int) ($x['attempts'] ?? 0) + 1;
                    $x['spend_reservations'][] = ['at' => $now, 'usd' => Oldies_X_News_Publisher::LINK_POST_USD];
                    $store->save($row, $x); // Crash leaves SENDING: never automatically repost.
                    $result = (new Oldies_X_News_Publisher())->send($x['text']);
                    // Recovery journal survives a metadata CAS conflict after successful posting.
                    update_option('oldies_x_outcome_' . $id, $result + ['at' => $now], false);
                    $fresh = $store->row($id); $x = array_merge(Oldies_X_News_Store::metadata($fresh)['x_news'], $result);
                    if ($x['status'] === 'POSTED') { $x['published_at'] = gmdate('c'); }
                    $store->save($fresh, $x);
                }
                $x['updated_at'] = gmdate('c');
                if ($intent !== 'api') { $store->save($row, $x); }
                return self::url(['id' => $id, 'result' => $x['status']]);
            });
        } catch (Throwable $e) {
            $message = preg_match('/^[A-Z][A-Z0-9_]*$/D', $e->getMessage()) ? $e->getMessage() : 'X_OPERATION_FAILED';
            $destination = self::url(['id' => $id, 'result' => $message]);
        }
        if (str_starts_with($destination, 'https://twitter.com/intent/tweet?')) { wp_redirect($destination); } else { wp_safe_redirect($destination); }
        exit;
    }
    private static function sources(): void
    {
        $class = 'OldiesRadyo\\SocialAutomation\\News\\NewsRepository';
        if (!class_exists($class)) { throw new RuntimeException('EXISTING_SOURCE_MANAGER_REQUIRED'); }
        $repo = new $class(); $existing = $repo->getAllSources();
        $catalog = json_decode(file_get_contents(dirname(__DIR__) . '/sources.json'), true);
        foreach ($catalog as $source) {
            $found = false;
            foreach ($existing as $s) { if (Oldies_X_News_Policy::canonical($s['feed_url']) === Oldies_X_News_Policy::canonical($source['url'])) { $found = true; break; } }
            if (!$found) {
                $created = $repo->createSource(['name' => $source['name'], 'feed_url' => $source['url'], 'feed_type' => $source['type'], 'category' => $source['group'], 'is_active' => 0]);
                if (is_wp_error($created) || !$created) { throw new RuntimeException('SOURCE_REGISTRATION_FAILED'); }
            }
        }
    }
    /** Controlled import for English news published outside the scanner. */
    private static function import(): int
    {
        $id = absint($_POST['post_id'] ?? 0); $post = get_post($id);
        if (!$post || $post->post_type !== 'post' || $post->post_status !== 'publish' || !function_exists('pll_get_post_language') || pll_get_post_language($id, 'slug') !== 'en') { throw new RuntimeException('PUBLISHED_EN_NEWS_REQUIRED'); }
        $date = strtotime($post->post_date_gmt . ' UTC');
        if (!$date || $date < time() - 90 * 86400 || $date > time() + 300) { throw new RuntimeException('RECENT_NEWS_REQUIRED'); }
        $terms = get_the_terms($id, 'category'); $news = false;
        if (!is_wp_error($terms)) {
            foreach ((array) $terms as $term) { if (preg_match('/(?:^|[-_])(news|haberler|haberleri)(?:[-_]|$)/i', $term->slug)) { $news = true; } }
        }
        if (!$news || Oldies_X_News_Policy::host(get_permalink($id)) !== 'oldiesradyo.com') { throw new RuntimeException('NEWS_CATEGORY_AND_OLDIES_URL_REQUIRED'); }
        $primary = esc_url_raw(wp_unslash($_POST['primary'] ?? '')); $artist = sanitize_text_field(wp_unslash($_POST['artist'] ?? ''));
        if ($artist === '' || !Oldies_X_News_Policy::canonical($primary) || Oldies_X_News_Policy::group($primary) === '') { throw new RuntimeException('ARTIST_AND_TRUSTED_SOURCE_REQUIRED'); }
        $class = 'OldiesRadyo\\SocialAutomation\\News\\NewsRepository';
        if (!class_exists($class)) { throw new RuntimeException('EXISTING_NEWS_REPOSITORY_REQUIRED'); }
        $repo = new $class();
        global $wpdb; $table = $wpdb->prefix . 'oldies_news_articles';
        $already = $wpdb->get_row($wpdb->prepare("SELECT * FROM `{$table}` WHERE en_post_id=%d ORDER BY id LIMIT 1", $id), ARRAY_A);
        if ($already) { return (int) $already['id']; }
        $existing = $repo->getArticleByArticleUrl($primary);
        if ($existing) {
            if (!empty($existing['en_post_id']) && (int) $existing['en_post_id'] !== $id) { throw new RuntimeException('SOURCE_ALREADY_LINKED_TO_OTHER_EN_POST'); }
            if (!$repo->updateArticle((int) $existing['id'], ['en_post_id' => $id])) { throw new RuntimeException('IMPORT_LINK_FAILED'); }
            return (int) $existing['id'];
        }
        $result = $repo->createArticle([
            'source_name' => Oldies_X_News_Policy::host($primary), 'source_url' => $primary, 'article_url' => $primary,
            'headline' => $post->post_title, 'artist_topic' => $artist, 'published_date' => $post->post_date_gmt,
            'fingerprint' => hash('sha256', 'oldies-wp-news:' . $id), 'en_post_id' => $id, 'en_title' => $post->post_title,
            'en_excerpt' => $post->post_excerpt, 'status' => 'PENDING', 'metadata' => ['x_import' => ['post_id' => $id, 'by' => get_current_user_id(), 'at' => gmdate('c')]],
        ]);
        if (is_wp_error($result) || !$result) { throw new RuntimeException('IMPORT_FAILED'); }
        return (int) $result;
    }
}
