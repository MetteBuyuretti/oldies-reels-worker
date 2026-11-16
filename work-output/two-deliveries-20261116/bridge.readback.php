<?php
/**
 * Plugin Name: Oldies Radyo Reels Bridge
 * Description: Secure MP4 intake and authenticated REST bridge for the existing Oldies Radyo Instagram Reels publishing pipeline.
 * Version: 2.3.8-YT10-READBACK
 * Author: Oldies Radyo
 * Requires at least: 6.5
 * Requires PHP: 8.1
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class Oldies_Radyo_Reels_Bridge
{
    private const VERSION = '2.3.8-YT10-READBACK';
    private const REST_NAMESPACE = 'oldies/v1';
    private const META_GRAPH_BASE = 'https://graph.instagram.com/v26.0';
    private const MAX_UPLOAD_BYTES = 104857600; // 100 MiB.
    private const CLEANUP_HOOK = 'oldies_reels_bridge_cleanup';
    private const LIVE_OPTION = 'oldies_reels_bridge_live_enabled';
    private const LAST_RESULT_OPTION = 'oldies_reels_bridge_last_result';
    private const QUEUE_OPTION = 'oldies_reels_bridge_draft_queue';
    private const POLICY_OPTION = 'oldies_reels_bridge_content_policy';
    private const MAX_QUEUE_ITEMS = 50;
    private const UPLOAD_DIR = 'oldies-reels';

    public static function boot(): void
    {
        add_action('rest_api_init', [self::class, 'registerRestRoutes']);
        add_action('wp_abilities_api_categories_init', [self::class, 'registerAbilityCategory']);
        add_action('wp_abilities_api_init', [self::class, 'registerAbilities']);
        add_action('admin_menu', [self::class, 'registerAdminPage'], 30);
        add_action('admin_post_oldies_reels_bridge_dry_run', [self::class, 'handleAdminDryRun']);
        add_action('admin_post_oldies_reels_bridge_bundled_test', [self::class, 'handleBundledDryRun']);
        add_action('admin_post_oldies_reels_bridge_bearer_test', [self::class, 'handleBearerDryRun']);
        add_action('admin_post_oldies_reels_bridge_draft_dry_run', [self::class, 'handleDraftDryRun']);
        add_action('admin_post_oldies_reels_bridge_draft_approve', [self::class, 'handleDraftApprove']);
        add_action('admin_post_oldies_reels_bridge_draft_publish', [self::class, 'handleDraftPublish']);
        add_action('admin_post_oldies_reels_bridge_draft_reject', [self::class, 'handleDraftReject']);
        add_action(self::CLEANUP_HOOK, [self::class, 'cleanupExpiredFiles']);
    }

    public static function activate(): void
    {
        add_option(self::LIVE_OPTION, 0, '', false);
        add_option(self::QUEUE_OPTION, [], '', false);
        add_option(self::POLICY_OPTION, self::defaultContentPolicy(), '', false);
        if (!wp_next_scheduled(self::CLEANUP_HOOK)) {
            wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', self::CLEANUP_HOOK);
        }
    }

    public static function deactivate(): void
    {
        wp_clear_scheduled_hook(self::CLEANUP_HOOK);
    }

    public static function registerAbilityCategory(): void
    {
        if (!function_exists('wp_register_ability_category')) {
            return;
        }

        wp_register_ability_category('oldies-reels', [
            'label' => 'Oldies Radyo Reels',
            'description' => 'Safe abilities for reviewing and handing Oldies Radyo Reels drafts to Meta Edits. No live Instagram publishing or settings changes.',
        ]);
    }

    public static function registerAbilities(): void
    {
        if (!function_exists('wp_register_ability')) {
            return;
        }

        wp_register_ability('oldies-reels/list-drafts', [
            'label' => 'List Reels drafts',
            'description' => 'Lists the Oldies Radyo Reels queue with safe draft metadata, captions, sources, and video URLs. Read-only.',
            'category' => 'oldies-reels',
            'output_schema' => [
                'type' => 'array',
                'items' => [
                    'type' => 'object',
                    'properties' => self::abilityDraftOutputProperties(),
                    'additionalProperties' => false,
                ],
            ],
            'execute_callback' => [self::class, 'abilityListDrafts'],
            'permission_callback' => [self::class, 'canManageReelsAbility'],
            'meta' => [
                'public' => true,
                'show_in_rest' => true,
                'annotations' => ['readonly' => true],
            ],
        ]);

        wp_register_ability('oldies-reels/prepare-for-edits', [
            'label' => 'Prepare Reel for Edits',
            'description' => 'Marks exactly one eligible Reels draft READY_FOR_EDITS. It never publishes to Instagram, changes credentials, deletes content, or enables live publishing.',
            'category' => 'oldies-reels',
            'input_schema' => [
                'type' => 'object',
                'properties' => [
                    'draft_id' => [
                        'type' => 'string',
                        'description' => 'Exact Reels draft ID returned by list-drafts.',
                        'minLength' => 1,
                    ],
                ],
                'required' => ['draft_id'],
                'additionalProperties' => false,
            ],
            'output_schema' => [
                'type' => 'object',
                'properties' => self::abilityDraftOutputProperties(),
                'additionalProperties' => false,
            ],
            'execute_callback' => [self::class, 'abilityPrepareForEdits'],
            'permission_callback' => [self::class, 'canManageReelsAbility'],
            'meta' => [
                'public' => true,
                'show_in_rest' => true,
                'annotations' => ['readonly' => false],
            ],
        ]);

        wp_register_ability('oldies-reels/get-edits-handoff', [
            'label' => 'Get Edits handoff',
            'description' => 'Returns the safe video URL and caption for one Reels draft so the owner can download it on a phone and import it into Meta Edits. Read-only.',
            'category' => 'oldies-reels',
            'input_schema' => [
                'type' => 'object',
                'properties' => [
                    'draft_id' => [
                        'type' => 'string',
                        'description' => 'Exact Reels draft ID returned by list-drafts.',
                        'minLength' => 1,
                    ],
                ],
                'required' => ['draft_id'],
                'additionalProperties' => false,
            ],
            'output_schema' => [
                'type' => 'object',
                'properties' => self::abilityDraftOutputProperties(),
                'additionalProperties' => false,
            ],
            'execute_callback' => [self::class, 'abilityGetEditsHandoff'],
            'permission_callback' => [self::class, 'canManageReelsAbility'],
            'meta' => [
                'public' => true,
                'show_in_rest' => true,
                'annotations' => ['readonly' => true],
            ],
        ]);

        wp_register_ability('oldies-reels/list-instagram-recent', [
            'label' => 'List recent published Instagram videos',
            'description' => 'Reads recent VIDEO media from the configured Instagram account so an owner can match a final published Reel to a draft. Read-only.',
            'category' => 'oldies-reels',
            'output_schema' => [
                'type' => 'array',
                'items' => [
                    'type' => 'object',
                    'properties' => [
                        'media_id' => ['type' => 'string'],
                        'permalink' => ['type' => 'string'],
                        'media_url' => ['type' => 'string'],
                        'timestamp' => ['type' => 'string'],
                        'caption' => ['type' => 'string'],
                        'media_type' => ['type' => 'string'],
                        'media_product_type' => ['type' => 'string'],
                        'media_audio_type' => ['type' => 'string'],
                    ],
                    'additionalProperties' => false,
                ],
            ],
            'execute_callback' => [self::class, 'abilityListInstagramRecent'],
            'permission_callback' => [self::class, 'canManageReelsAbility'],
            'meta' => [
                'public' => true,
                'show_in_rest' => true,
                'annotations' => ['readonly' => true],
            ],
        ]);

        wp_register_ability('oldies-reels/confirm-instagram-published', [
            'label' => 'Confirm final published Instagram Reel',
            'description' => 'Links one exact published Instagram Reel to one READY_FOR_EDITS draft, stores only verified final Instagram media metadata, and mirrors that final Instagram media to YouTube. It never uses the raw draft video as a fallback.',
            'category' => 'oldies-reels',
            'input_schema' => [
                'type' => 'object',
                'properties' => [
                    'draft_id' => ['type' => 'string', 'minLength' => 1],
                    'instagram_media_id' => ['type' => 'string', 'minLength' => 1],
                ],
                'required' => ['draft_id', 'instagram_media_id'],
                'additionalProperties' => false,
            ],
            'output_schema' => [
                'type' => 'object',
                'properties' => self::abilityDraftOutputProperties(),
                'additionalProperties' => false,
            ],
            'execute_callback' => [self::class, 'abilityConfirmInstagramPublished'],
            'permission_callback' => [self::class, 'canManageReelsAbility'],
            'meta' => [
                'public' => true,
                'show_in_rest' => true,
                'annotations' => ['readonly' => false],
            ],
        ]);
    }

    public static function canManageReelsAbility($input = null): bool

    {
        unset($input);
        return current_user_can('manage_options');
    }

    public static function abilityListDrafts($input = null): array
    {
        unset($input);
        $queue = self::getQueue();
        $safe = [];
        foreach ($queue as $draft) {
            if (!is_array($draft) || (string)($draft['status'] ?? '') === 'REJECTED') {
                continue;
            }
            $safe[] = self::sanitizeDraftForAbility($draft);
        }
        return $safe;
    }

    /** @return array<string,mixed>|WP_Error */
    public static function abilityPrepareForEdits($input)
    {
        $input = is_array($input) ? $input : [];
        $draftId = sanitize_text_field((string)($input['draft_id'] ?? ''));
        if ($draftId === '') {
            return new WP_Error('oldies_reels_draft_id_required', 'Taslak kimliği gerekli.');
        }

        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null) {
            return new WP_Error('oldies_reels_draft_not_found', 'Taslak bulunamadı.');
        }

        $status = (string)($queue[$index]['status'] ?? 'DRAFT_REVIEW');
        if (!in_array($status, ['DRAFT_REVIEW', 'DRY_RUN_READY', 'APPROVED_FOR_LIVE', 'READY_FOR_EDITS'], true)) {
            return new WP_Error('oldies_reels_edits_not_allowed', 'Bu taslak mevcut durumda Edits aktarımı için hazırlanamaz.');
        }

        if ($status !== 'READY_FOR_EDITS') {
            $queue[$index]['status'] = 'READY_FOR_EDITS';
            $queue[$index]['edits_ready_at'] = current_time('mysql', true);
            $queue[$index]['edits_ready_by'] = get_current_user_id();
        }

        self::saveQueue($queue);

        return self::sanitizeDraftForAbility($queue[$index]);
    }

    /** @return array<string,mixed>|WP_Error */
    public static function abilityGetEditsHandoff($input)
    {
        $input = is_array($input) ? $input : [];
        $draftId = sanitize_text_field((string)($input['draft_id'] ?? ''));
        if ($draftId === '') {
            return new WP_Error('oldies_reels_draft_id_required', 'Taslak kimliği gerekli.');
        }

        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null) {
            return new WP_Error('oldies_reels_draft_not_found', 'Taslak bulunamadı.');
        }

        return self::sanitizeDraftForAbility($queue[$index]);
    }

    /** @return array<int,array<string,mixed>>|WP_Error */
    public static function abilityListInstagramRecent($input = null)
    {
        unset($input);
        $settings = self::settingsManager();
        if ($settings === null || !method_exists($settings, 'getInstagramUserId')) {
            return new WP_Error('instagram_settings_missing', 'Instagram hesap ayarları alınamadı.');
        }
        $userId = self::sanitizeMetaId($settings->getInstagramUserId());
        if ($userId === '') {
            return new WP_Error('instagram_user_missing', 'Instagram hesap kimliği alınamadı.');
        }
        $response = self::metaGraphRequest('/' . $userId . '/media', 'GET', [
            'fields' => 'id,caption,media_type,media_product_type,media_audio_type,permalink,media_url,timestamp',
            'limit' => 20,
        ]);
        if (is_wp_error($response)) {
            return $response;
        }
        $out = [];
        foreach ((array)($response['data'] ?? []) as $media) {
            if (!is_array($media) || strtoupper((string)($media['media_type'] ?? '')) !== 'VIDEO') {
                continue;
            }
            $permalink = esc_url_raw((string)($media['permalink'] ?? ''));
            $mediaUrl = esc_url_raw((string)($media['media_url'] ?? ''));
            if ($permalink === '' || !preg_match('~instagram\\.com/(?:reel|reels)/~i', $permalink)) {
                continue;
            }
            $out[] = [
                'media_id' => self::sanitizeMetaId($media['id'] ?? ''),
                'permalink' => $permalink,
                'media_url' => $mediaUrl,
                'timestamp' => sanitize_text_field((string)($media['timestamp'] ?? '')),
                'caption' => sanitize_textarea_field((string)($media['caption'] ?? '')),
                'media_type' => 'VIDEO',
                'media_product_type' => sanitize_text_field((string)($media['media_product_type'] ?? '')),
                'media_audio_type' => sanitize_text_field((string)($media['media_audio_type'] ?? '')),
            ];
        }
        return array_slice($out, 0, 20);
    }

    /** @return array<string,mixed>|WP_Error */
    public static function abilityConfirmInstagramPublished($input)
    {
        $input = is_array($input) ? $input : [];
        $draftId = sanitize_text_field((string)($input['draft_id'] ?? ''));
        $mediaId = self::sanitizeMetaId($input['instagram_media_id'] ?? '');
        if ($draftId === '' || $mediaId === '') {
            return new WP_Error('instagram_confirmation_ids_required', 'Taslak ve Instagram medya kimliği gerekli.');
        }
        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null) {
            return new WP_Error('oldies_reels_draft_not_found', 'Taslak bulunamadı.');
        }
        $status = (string)($queue[$index]['status'] ?? '');
        if (!in_array($status, ['READY_FOR_EDITS', 'INSTAGRAM_PUBLISHED_CONFIRMED'], true)) {
            return new WP_Error('instagram_confirmation_state', 'Yalnız Edits için hazır bir taslak final Instagram Reel ile eşleştirilebilir.');
        }
        $media = self::getInstagramFinalMedia($mediaId);
        if (is_wp_error($media)) {
            return $media;
        }
        $permalink = (string)$media['permalink'];
        if (!preg_match('~instagram\\.com/(?:reel|reels)/~i', $permalink)) {
            return new WP_Error('instagram_not_reel', 'Seçilen Instagram medya bağlantısı Reel olarak doğrulanamadı.');
        }
        $queue[$index]['status'] = 'INSTAGRAM_PUBLISHED_CONFIRMED';
        $queue[$index]['instagram_result'] = [
            'instagram_media_id' => $mediaId,
            'permalink' => $permalink,
            'media_url' => (string)$media['media_url'],
            'timestamp' => (string)$media['timestamp'],
            'media_audio_type' => (string)($media['media_audio_type'] ?? ''),
            'verified_at' => current_time('mysql', true),
            'source' => 'instagram_graph',
        ];
        $artist = sanitize_text_field((string)($queue[$index]['artist'] ?? ''));
        $eventDate = sanitize_text_field((string)($queue[$index]['event_date'] ?? ''));
        $title = trim($artist . ($eventDate !== '' ? ' — ' . $eventDate : '') . ' | Müzik Tarihinde Bugün #Shorts');
        if (function_exists('mb_substr')) {
            $title = mb_substr($title, 0, 95, 'UTF-8');
        } else {
            $title = substr($title, 0, 95);
        }
        $queue[$index]['youtube_result'] = self::mirrorToYouTube([
            'video_url' => (string)$media['media_url'],
            'caption' => (string)($queue[$index]['caption'] ?? ''),
            'topic' => $title !== '' ? $title : 'Oldies Radyo #Shorts',
            'dry_run' => false,
            'idempotency_key' => 'instagram-media-' . $mediaId,
            'origin' => 'instagram_published_final',
            'instagram_media_id' => $mediaId,
            'instagram_permalink' => $permalink,
        ]);
        self::saveQueue($queue);
        return self::sanitizeDraftForAbility($queue[$index]);
    }

    /** @return array<string,array<string,mixed>> */
    private static function abilityDraftOutputProperties(): array
    {
        return [
            'id' => ['type' => 'string'],
            'artist' => ['type' => 'string'],
            'topic' => ['type' => 'string'],
            'status' => ['type' => 'string'],
            'score' => ['type' => 'integer'],
            'event_date' => ['type' => 'string'],
            'caption' => ['type' => 'string'],
            'video_url' => ['type' => 'string'],
            'planned_music' => ['type' => 'string'],
            'sources' => [
                'type' => 'array',
                'items' => ['type' => 'string'],
            ],
            'edits_ready_at' => ['type' => 'string'],
            'instagram_media_id' => ['type' => 'string'],
            'instagram_permalink' => ['type' => 'string'],
            'final_media_url' => ['type' => 'string'],
            'final_media_source' => ['type' => 'string'],
            'instagram_published_at' => ['type' => 'string'],
            'instagram_media_audio_type' => ['type' => 'string'],
            'youtube_verified_source' => ['type' => 'boolean'],
            'youtube_success' => ['type' => 'boolean'],
            'youtube_status' => ['type' => 'string'],
            'youtube_publication_verified' => ['type' => 'boolean'],
            'youtube_visibility' => ['type' => 'string'],
            'youtube_url' => ['type' => 'string'],
            'youtube_error' => ['type' => 'string'],
        ];
    }

    /** @param array<string,mixed> $draft @return array<string,mixed> */
    private static function sanitizeDraftForAbility(array $draft): array
    {
        $audioRequest = is_array($draft['audio_request'] ?? null) ? $draft['audio_request'] : [];
        $sources = is_array($draft['sources'] ?? null) ? $draft['sources'] : [];
        $safeSources = [];
        foreach ($sources as $source) {
            $source = esc_url_raw((string)$source);
            if ($source !== '') {
                $safeSources[] = $source;
            }
        }

        $instagram = is_array($draft['instagram_result'] ?? null) ? $draft['instagram_result'] : [];
        $youtube = is_array($draft['youtube_result'] ?? null) ? $draft['youtube_result'] : [];
        $youtubeResult = is_array($youtube['result'] ?? null) ? $youtube['result'] : [];
        $youtubeError = (string)($youtube['error'] ?? $youtubeResult['error'] ?? '');
        $instagramMediaId = self::sanitizeMetaId($instagram['instagram_media_id'] ?? '');
        $finalMediaUrl = esc_url_raw((string)($instagram['media_url'] ?? ''));
        $verifiedSource = $instagramMediaId !== '' && $finalMediaUrl !== '' && (string)($instagram['source'] ?? '') === 'instagram_graph';
        $youtubeDryRun = !empty($youtube['dry_run']) || !empty($youtubeResult['dry_run']);
        $uploaded = !empty($youtube['success']) && !empty($youtubeResult['success']) && !$youtubeDryRun && !empty($youtubeResult['video_id']);
        $sourceBound = $verifiedSource && $uploaded
            && (string)($youtube['source_origin'] ?? '') === 'instagram_published_final'
            && hash_equals($instagramMediaId, (string)($youtube['source_instagram_media_id'] ?? ''))
            && hash_equals((string)($instagram['permalink'] ?? ''), (string)($youtube['source_instagram_permalink'] ?? ''))
            && hash_equals($finalMediaUrl, (string)($youtube['source_final_media_url'] ?? ''));
        $publicationVerified = $uploaded && !empty($youtubeResult['publication_verified'])
            && (string)($youtubeResult['visibility'] ?? '') === 'public'
            && (string)($youtubeResult['upload_status'] ?? '') === 'processed';
        $youtubeStatus = $youtubeDryRun ? 'simulated' : (string)($youtubeResult['status'] ?? '');
        if (!$publicationVerified && ($youtubeStatus === '' || $youtubeStatus === 'published')) {
            $youtubeStatus = !empty($youtube['success']) ? 'uploaded_unverified' : (string)($youtube['status'] ?? '');
        }

        return [
            'id' => sanitize_text_field((string)($draft['id'] ?? '')),
            'artist' => sanitize_text_field((string)($draft['artist'] ?? '')),
            'topic' => sanitize_text_field((string)($draft['topic'] ?? '')),
            'status' => sanitize_text_field((string)($draft['status'] ?? '')),
            'score' => (int)($draft['score'] ?? 0),
            'event_date' => sanitize_text_field((string)($draft['event_date'] ?? '')),
            'caption' => sanitize_textarea_field((string)($draft['caption'] ?? '')),
            'video_url' => esc_url_raw((string)($draft['video_url'] ?? '')),
            'planned_music' => sanitize_text_field((string)($audioRequest['display_name'] ?? $audioRequest['search_query'] ?? '')),
            'sources' => array_values(array_unique($safeSources)),
            'edits_ready_at' => sanitize_text_field((string)($draft['edits_ready_at'] ?? '')),
            'instagram_media_id' => $instagramMediaId,
            'instagram_permalink' => esc_url_raw((string)($instagram['permalink'] ?? '')),
            'final_media_url' => $finalMediaUrl,
            'final_media_source' => sanitize_text_field((string)($instagram['source'] ?? '')),
            'instagram_published_at' => sanitize_text_field((string)($instagram['timestamp'] ?? '')),
            'instagram_media_audio_type' => sanitize_text_field((string)($instagram['media_audio_type'] ?? '')),
            'youtube_verified_source' => $sourceBound,
            'youtube_success' => $uploaded,
            'youtube_status' => sanitize_text_field($youtubeStatus),
            'youtube_publication_verified' => $publicationVerified,
            'youtube_visibility' => array_key_exists('publication_verified', $youtubeResult)
                ? sanitize_text_field((string)($youtubeResult['visibility'] ?? 'unknown')) : 'unknown',
            'youtube_url' => esc_url_raw((string)($youtubeResult['youtube_url'] ?? '')),
            'youtube_error' => sanitize_text_field($youtubeError),
        ];
    }

    public static function registerRestRoutes(): void
    {
        register_rest_route(self::REST_NAMESPACE, '/instagram/reels/status', [
            'methods' => 'GET',
            'callback' => [self::class, 'restStatus'],
            'permission_callback' => [self::class, 'authorizeRestRequest'],
        ]);

        register_rest_route(self::REST_NAMESPACE, '/instagram/reels', [
            'methods' => 'POST',
            'callback' => [self::class, 'restPublish'],
            'permission_callback' => [self::class, 'authorizeRestRequest'],
            'args' => [
                'caption' => [
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_textarea_field',
                ],
                'topic' => [
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                ],
                'video_url' => [
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'esc_url_raw',
                ],
                'dry_run' => [
                    'required' => false,
                    'type' => 'boolean',
                    'default' => true,
                    'sanitize_callback' => 'rest_sanitize_boolean',
                ],
                'share_to_feed' => [
                    'required' => false,
                    'type' => 'boolean',
                    'default' => true,
                    'sanitize_callback' => 'rest_sanitize_boolean',
                ],
                'idempotency_key' => [
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => [self::class, 'sanitizeIdempotencyKey'],
                ],
            ],
        ]);

        register_rest_route(self::REST_NAMESPACE, '/instagram/reels/drafts', [
            [
                'methods' => 'GET',
                'callback' => [self::class, 'restListDrafts'],
                'permission_callback' => [self::class, 'authorizeRestRequest'],
            ],
            [
                'methods' => 'POST',
                'callback' => [self::class, 'restCreateDraft'],
                'permission_callback' => [self::class, 'authorizeRestRequest'],
            ],
            [
                'methods' => 'PUT',
                'callback' => [self::class, 'restCreateDraft'],
                'permission_callback' => [self::class, 'authorizeRestRequest'],
            ],
        ]);

        register_rest_route(self::REST_NAMESPACE, '/instagram/reels/audio', [
            'methods' => 'GET',
            'callback' => [self::class, 'restSearchAudio'],
            'permission_callback' => [self::class, 'authorizeRestRequest'],
        ]);
    }

    /**
     * Reuse the encrypted bearer secret and administrator-cookie authorization
     * provided by the main Oldies Social plugin.
     *
     * @return bool|WP_Error
     */
    public static function authorizeRestRequest(WP_REST_Request $request)
    {
        if (!self::dependenciesReady()) {
            return new WP_Error(
                'oldies_reels_dependency_missing',
                'Oldies Radyo Social & News Automation etkin olmalıdır.',
                ['status' => 503, 'bridge_version' => self::VERSION]
            );
        }

        $settings = self::settingsManager();
        if ($settings === null) {
            return new WP_Error(
                'oldies_reels_dependency_missing',
                'Oldies Radyo Social & News Automation ayarları yüklenemedi.',
                ['status' => 503, 'bridge_version' => self::VERSION]
            );
        }

        $authHeader = (string)$request->get_header('authorization');
        $configuredBearer = (string)$settings->getBearerSecret();
        $customSecret = trim((string)$request->get_header('x-oldies-reels-secret'));
        if ($customSecret !== '' && $configuredBearer !== '' && hash_equals($configuredBearer, $customSecret)) {
            return true;
        }
        if ($authHeader !== '' && $configuredBearer !== '' && preg_match('/^Bearer\s+(.+)$/i', $authHeader, $matches)) {
            $providedBearer = trim((string)$matches[1]);
            if ($providedBearer !== '' && hash_equals($configuredBearer, $providedBearer)) {
                return true;
            }
        }

        if (current_user_can('manage_options')) {
            return true;
        }

        return new WP_Error(
            'rest_forbidden',
            'Yetkisiz erişim: Geçerli bir Bearer Secret veya yönetici yetkisi gereklidir.',
            ['status' => 401]
        );
    }
    public static function restStatus(WP_REST_Request $request): WP_REST_Response
    {
        unset($request);
        $settings = self::settingsManager();
        $queue = self::getQueue();

        return new WP_REST_Response([
            'service_status' => self::dependenciesReady() ? 'ready' : 'dependency_missing',
            'bridge_version' => self::VERSION,
            'instagram_username' => $settings ? $settings->getInstagramUsername() : '',
            'token_healthy' => $settings ? $settings->isTokenHealthy() : false,
            'bearer_configured' => $settings ? $settings->getBearerSecret() !== '' : false,
            'master_auto_publish_enabled' => $settings ? $settings->isAutoPublishingEnabled() : false,
            'master_dry_run_enabled' => $settings ? $settings->isDryRunMode() : true,
            'bridge_live_enabled' => self::isLiveEnabled(),
            'approval_required' => true,
            'instagram_audio_api' => [
                'supported' => true,
                'catalog_rule' => 'Meta tarafından üçüncü taraf kullanımına yetkilendirilmiş hesap-bazlı sonuçlar',
                'preview_with_attached_audio' => false,
                'fallback' => 'exact_match_only_then_original_audio',
            ],
            'draft_queue_count' => count($queue),
            'content_policy' => self::getContentPolicy(),
            'max_upload_bytes' => self::MAX_UPLOAD_BYTES,
            'accepted_video' => [
                'container' => 'MP4',
                'video_codec' => 'H.264 recommended',
                'audio_codec' => 'AAC recommended',
                'aspect_ratio' => '9:16 recommended',
            ],
            'endpoints' => [
                'publish' => rest_url(self::REST_NAMESPACE . '/instagram/reels'),
                'drafts' => rest_url(self::REST_NAMESPACE . '/instagram/reels/drafts'),
                'audio' => rest_url(self::REST_NAMESPACE . '/instagram/reels/audio'),
                'status' => rest_url(self::REST_NAMESPACE . '/instagram/reels/status'),
            ],
        ], 200);
    }

    /**
     * @return WP_REST_Response|WP_Error
     */
    public static function restPublish(WP_REST_Request $request)
    {
        $dryRun = rest_sanitize_boolean($request->get_param('dry_run'));
        $shareToFeed = rest_sanitize_boolean($request->get_param('share_to_feed'));
        $caption = sanitize_textarea_field((string)$request->get_param('caption'));
        $topic = sanitize_text_field((string)($request->get_param('topic') ?: 'Oldies Radyo Reel'));
        $videoUrl = esc_url_raw((string)$request->get_param('video_url'));
        $audioId = self::sanitizeMetaId($request->get_param('audio_id'));
        $audioVolume = max(0, min(100, (int)($request->get_param('audio_volume') ?? 100)));
        $videoVolume = max(0, min(100, (int)($request->get_param('video_volume') ?? 15)));
        $files = $request->get_file_params();

        if ($caption === '') {
            return new WP_Error('empty_reel_caption', 'Reels açıklaması boş olamaz.', ['status' => 400]);
        }

        $stored = null;
        if (!empty($files['reel_video']) && is_array($files['reel_video'])) {
            $stored = self::storeUploadedMp4($files['reel_video']);
            if (is_wp_error($stored)) {
                return $stored;
            }
            $videoUrl = $stored['url'];
        }

        if ($videoUrl === '' || stripos($videoUrl, 'https://') !== 0 || !wp_http_validate_url($videoUrl)) {
            return new WP_Error(
                'invalid_reel_url',
                'Bir MP4 dosyası yükleyin veya herkese açık geçerli bir HTTPS video URL’si girin.',
                ['status' => 400]
            );
        }

        if (!$dryRun && !self::livePublishingAllowed()) {
            return new WP_Error(
                'live_publish_locked',
                'Canlı Reels yayını güvenlik kilidi nedeniyle kapalı. Önce Dry Run doğrulanmalı ve iki canlı yayın anahtarı açılmalıdır.',
                ['status' => 423]
            );
        }

        $idempotencyKey = self::resolveIdempotencyKey($request, $caption, $videoUrl, $stored);
        $idempotencyState = self::beginIdempotentRequest($idempotencyKey);
        if (is_wp_error($idempotencyState)) {
            return $idempotencyState;
        }

        $result = self::publish([
            'video_url' => $videoUrl,
            'caption' => $caption,
            'topic' => $topic,
            'dry_run' => $dryRun,
            'share_to_feed' => $shareToFeed,
            'idempotency_key' => $idempotencyKey,
            'origin' => 'rest_bridge',
            'audio_id' => $audioId,
            'audio_volume' => $audioVolume,
            'video_volume' => $videoVolume,
        ]);

        if (is_wp_error($result)) {
            self::recordIdempotentFailure($idempotencyKey, $result);
            return $result;
        }

        self::completeIdempotentRequest($idempotencyKey, $result);
        self::saveLastResult($result, $idempotencyKey, 'rest');

        return new WP_REST_Response([
            'success' => true,
            'bridge_version' => self::VERSION,
            'idempotency_key' => $idempotencyKey,
            'stored_video_url' => $videoUrl,
            'result' => $result,
        ], 200);
    }

    public static function restListDrafts(WP_REST_Request $request): WP_REST_Response
    {
        unset($request);
        return new WP_REST_Response([
            'success' => true,
            'approval_required' => true,
            'content_policy' => self::getContentPolicy(),
            'drafts' => self::getQueue(),
        ], 200);
    }

    /** @return WP_REST_Response|WP_Error */
    public static function restSearchAudio(WP_REST_Request $request)
    {
        $query = sanitize_text_field((string)$request->get_param('q'));
        $audioType = sanitize_key((string)($request->get_param('audio_type') ?: 'music'));
        if (!in_array($audioType, ['music', 'original_sound'], true)) {
            return new WP_Error('invalid_audio_type', 'Ses türü music veya original_sound olmalıdır.', ['status' => 400]);
        }
        $result = self::searchAudioAssets($query, $audioType);
        if (is_wp_error($result)) {
            return $result;
        }
        return new WP_REST_Response([
            'success' => true,
            'query' => $query,
            'audio_type' => $audioType,
            'note' => 'Yalnızca Meta tarafından üçüncü taraf kullanımına yetkilendirilmiş sesler döndürülür; uygulamadaki katalog farklı olabilir.',
            'audio' => $result,
        ], 200);
    }

    /**
     * Intake endpoint for the external research/render worker. It can create
     * review drafts only; it can never publish an Instagram Reel.
     *
     * @return WP_REST_Response|WP_Error
     */
    public static function restCreateDraft(WP_REST_Request $request)
    {
        $caption = sanitize_textarea_field((string)$request->get_param('caption'));
        $topic = sanitize_text_field((string)$request->get_param('topic'));
        $artist = sanitize_text_field((string)$request->get_param('artist'));
        $eventDate = sanitize_text_field((string)$request->get_param('event_date'));
        $videoUrl = esc_url_raw((string)$request->get_param('video_url'));
        $coverUrl = esc_url_raw((string)$request->get_param('cover_url'));
        $audioTitle = sanitize_text_field((string)$request->get_param('audio_title'));
        $audioArtist = sanitize_text_field((string)$request->get_param('audio_artist'));
        $audioQuery = sanitize_text_field((string)$request->get_param('audio_query'));
        $sources = self::normalizeStringList($request->get_param('sources'), true);
        $facts = self::normalizeStringList($request->get_param('facts'), false);
        $scoreBreakdown = self::normalizeScoreBreakdown($request->get_param('score_breakdown'));
        $score = array_sum($scoreBreakdown);
        $policy = self::getContentPolicy();
        $files = $request->get_file_params();

        if ($topic === '' || $artist === '' || $caption === '') {
            return new WP_Error('draft_fields_missing', 'Konu, sanatçı ve açıklama zorunludur.', ['status' => 400]);
        }
        if (strlen($caption) < 80 || strlen($caption) > 2200) {
            return new WP_Error('draft_caption_length', 'Açıklama 80–2200 karakter arasında olmalıdır.', ['status' => 400]);
        }
        if (!preg_match('/^\\d{4}-\\d{2}-\\d{2}$/', $eventDate)) {
            return new WP_Error('draft_event_date', 'Olay tarihi YYYY-MM-DD biçiminde olmalıdır.', ['status' => 400]);
        }
        if (count($sources) < (int)$policy['minimum_sources']) {
            return new WP_Error('draft_sources_missing', 'En az iki farklı güvenilir yabancı kaynak gereklidir.', ['status' => 400]);
        }
        if (count($facts) < 2) {
            return new WP_Error('draft_facts_missing', 'En az iki doğrulanmış bilgi gereklidir.', ['status' => 400]);
        }
        if ($score < (int)$policy['minimum_score']) {
            return new WP_Error('draft_quality_score', 'İçerik kalite puanı otomatik taslak eşiğinin altında.', ['status' => 422]);
        }

        $stored = null;
        if (!empty($files['reel_video']) && is_array($files['reel_video'])) {
            $stored = self::storeUploadedMp4($files['reel_video']);
            if (is_wp_error($stored)) {
                return $stored;
            }
            $videoUrl = $stored['url'];
        }
        if ($videoUrl === '' || stripos($videoUrl, 'https://') !== 0 || !wp_http_validate_url($videoUrl)) {
            return new WP_Error('draft_video_missing', 'Taslak için geçerli bir MP4 veya herkese açık HTTPS video URL’si gereklidir.', ['status' => 400]);
        }

        $fingerprint = hash('sha256', strtolower($artist . '|' . $eventDate . '|' . $topic));
        $queue = self::getQueue();
        $today = gmdate('Y-m-d');
        $todayCount = 0;
        foreach ($queue as $existing) {
            if (hash_equals((string)($existing['fingerprint'] ?? ''), $fingerprint)) {
                return new WP_Error('duplicate_draft', 'Aynı sanatçı, tarih ve konu için zaten bir taslak bulunuyor.', ['status' => 409]);
            }
            if (str_starts_with((string)($existing['created_at'] ?? ''), $today)) {
                ++$todayCount;
            }
            $existingCreated = strtotime((string)($existing['created_at'] ?? ''));
            if (
                strcasecmp((string)($existing['artist'] ?? ''), $artist) === 0
                && $existingCreated !== false
                && $existingCreated >= time() - ((int)$policy['artist_repeat_days'] * DAY_IN_SECONDS)
                && (string)($existing['status'] ?? '') !== 'REJECTED'
            ) {
                return new WP_Error('artist_repeat_window', 'Aynı sanatçı için tekrar aralığı henüz dolmadı.', ['status' => 409]);
            }
        }
        if ($todayCount >= (int)$policy['maximum_daily_drafts']) {
            return new WP_Error('daily_draft_limit', 'Günlük otomatik taslak sınırına ulaşıldı.', ['status' => 429]);
        }

        $draft = [
            'id' => wp_generate_uuid4(),
            'created_at' => current_time('mysql', true),
            'status' => 'DRAFT_REVIEW',
            'approval_required' => true,
            'topic' => $topic,
            'artist' => $artist,
            'event_date' => $eventDate,
            'caption' => $caption,
            'sources' => $sources,
            'facts' => $facts,
            'score' => $score,
            'score_breakdown' => $scoreBreakdown,
            'video_url' => $videoUrl,
            'cover_url' => $coverUrl,
            'audio_request' => [
                'audio_type' => 'music',
                'title' => $audioTitle,
                'artist' => $audioArtist,
                'search_query' => $audioQuery !== '' ? $audioQuery : trim($audioTitle . ' ' . $audioArtist),
                'audio_volume' => max(0, min(100, (int)($request->get_param('audio_volume') ?? 100))),
                'video_volume' => max(0, min(100, (int)($request->get_param('video_volume') ?? 12))),
            ],
            'video_sha256' => is_array($stored) ? (string)$stored['sha256'] : '',
            'fingerprint' => $fingerprint,
            'dry_run_result' => [],
        ];

        array_unshift($queue, $draft);
        self::saveQueue($queue);

        return new WP_REST_Response([
            'success' => true,
            'message' => 'Reels taslağı kalite kontrol kuyruğuna eklendi; canlı yayın yapılmadı.',
            'draft' => $draft,
        ], 201);
    }

    public static function sanitizeIdempotencyKey($value): string
    {
        $key = preg_replace('/[^A-Za-z0-9._:-]/', '', (string)$value);
        return substr((string)$key, 0, 128);
    }

    private static function sanitizeMetaId($value): string
    {
        return preg_replace('/[^0-9]/', '', (string)$value) ?: '';
    }

    public static function registerAdminPage(): void
    {
        global $admin_page_hooks;

        // Always expose a dedicated, touch-friendly mobile control panel.
        // It intentionally contains no settings, plugin-management, delete, or
        // direct Instagram live-publish controls. This gives the owner a safe
        // bookmarked URL for travel use without navigating the full WP admin.
        add_menu_page(
            'Oldies Mobil',
            'Oldies Mobil',
            'manage_options',
            'oldies-reels-mobile',
            [self::class, 'renderMobilePage'],
            'dashicons-smartphone',
            80
        );

        // Keep the historical submenu placement when the main Social Automation
        // admin menu exists. If that plugin is inactive, expose Reels Bridge as
        // its own top-level admin page so the queue and Dry Run controls remain
        // reachable instead of silently disappearing.
        if (isset($admin_page_hooks['oldies-social-automation'])) {
            add_submenu_page(
                'oldies-social-automation',
                'Reels Bridge',
                'Reels Bridge',
                'manage_options',
                'oldies-reels-bridge',
                [self::class, 'renderAdminPage']
            );
            return;
        }

        add_menu_page(
            'Reels Bridge',
            'Reels Bridge',
            'manage_options',
            'oldies-reels-bridge',
            [self::class, 'renderAdminPage'],
            'dashicons-format-video',
            81
        );
    }

    public static function renderMobilePage(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }

        $queue = self::getQueue();
        $noticeKey = 'oldies_reels_bridge_notice_' . get_current_user_id();
        $notice = get_transient($noticeKey);
        if (is_array($notice)) {
            delete_transient($noticeKey);
        }
        $visibleDrafts = array_values(array_filter($queue, static fn($draft): bool => is_array($draft) && (string)($draft['status'] ?? '') !== 'REJECTED'));
        ?>
        <div class="wrap oldies-mobile-wrap">
            <style>
                .oldies-mobile-wrap{max-width:760px;margin:0 auto;padding-bottom:48px}
                .oldies-mobile-head{position:sticky;top:32px;z-index:5;background:#f0f0f1;padding:10px 0 12px;border-bottom:1px solid #dcdcde}
                .oldies-mobile-head h1{font-size:24px;margin:0 0 6px}
                .oldies-mobile-safe{background:#fff;border-left:4px solid #00a32a;padding:10px 12px;margin:12px 0;border-radius:4px}
                .oldies-mobile-card{background:#fff;border:1px solid #c3c4c7;border-radius:12px;padding:14px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}
                .oldies-mobile-card video{width:100%;max-height:62vh;background:#111;border-radius:9px}
                .oldies-mobile-card h2{font-size:20px;margin:12px 0 6px;line-height:1.25}
                .oldies-mobile-meta{font-size:13px;color:#50575e;margin:0 0 10px}
                .oldies-mobile-caption{white-space:pre-wrap;max-height:180px;overflow:auto;background:#f6f7f7;border-radius:8px;padding:10px;font-size:14px}
                .oldies-mobile-actions{display:grid;grid-template-columns:1fr;gap:10px;margin-top:12px}
                .oldies-mobile-actions .button{display:flex;justify-content:center;align-items:center;min-height:48px;font-size:16px;text-align:center}
                .oldies-mobile-status{display:inline-block;padding:4px 8px;border-radius:999px;background:#f0f0f1;font-weight:600;font-size:12px}
                .oldies-mobile-ready{background:#edfaef;color:#116329}
                @media (max-width:782px){.oldies-mobile-head{top:0}.oldies-mobile-wrap{padding:0 4px}.oldies-mobile-card{padding:12px}.oldies-mobile-head h1{font-size:22px}}
            </style>
            <div class="oldies-mobile-head">
                <h1>Oldies Radyo — Mobil Reels</h1>
                <div><a class="button" href="<?php echo esc_url(admin_url('admin.php?page=oldies-reels-bridge')); ?>">Tam Reels Bridge</a></div>
            </div>

            <div class="oldies-mobile-safe"><strong>Güvenli mobil panel:</strong> burada canlı Instagram yayın, eklenti ayarı, silme veya sistem ayarı yok. Yalnız taslağı Edits için hazırlama, videoyu alma ve açıklamayı kopyalama var.</div>

            <?php if (is_array($notice) && !empty($notice['message'])) : ?>
                <div class="notice <?php echo !empty($notice['success']) ? 'notice-success' : 'notice-error'; ?> is-dismissible"><p><?php echo esc_html((string)$notice['message']); ?></p></div>
            <?php endif; ?>

            <?php if (empty($visibleDrafts)) : ?>
                <div class="oldies-mobile-card"><p>Henüz kullanılabilir Reels taslağı yok.</p></div>
            <?php else : foreach ($visibleDrafts as $draft) : ?>
                <?php
                $draftId = (string)($draft['id'] ?? '');
                $status = (string)($draft['status'] ?? 'DRAFT_REVIEW');
                $videoUrl = (string)($draft['video_url'] ?? '');
                ?>
                <div class="oldies-mobile-card">
                    <?php if ($videoUrl !== '') : ?><video controls preload="metadata" playsinline src="<?php echo esc_url($videoUrl); ?>"></video><?php endif; ?>
                    <h2><?php echo esc_html((string)($draft['artist'] ?? '')); ?> — <?php echo esc_html((string)($draft['topic'] ?? '')); ?></h2>
                    <p class="oldies-mobile-meta"><span class="oldies-mobile-status <?php echo $status === 'READY_FOR_EDITS' ? 'oldies-mobile-ready' : ''; ?>"><?php echo esc_html($status); ?></span> &nbsp; <?php echo esc_html((string)($draft['event_date'] ?? '')); ?> &nbsp; · &nbsp; <?php echo (int)($draft['score'] ?? 0); ?>/100</p>
                    <div class="oldies-mobile-caption"><?php echo esc_html((string)($draft['caption'] ?? '')); ?></div>
                    <div class="oldies-mobile-actions">
                        <?php if (in_array($status, ['DRAFT_REVIEW', 'DRY_RUN_READY', 'APPROVED_FOR_LIVE'], true)) : ?>
                            <a class="button button-primary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_draft_approve&draft_id=' . rawurlencode($draftId)), 'oldies_reels_bridge_draft_approve_' . $draftId)); ?>">Edits İçin Hazırla</a>
                        <?php elseif ($status === 'READY_FOR_EDITS') : ?>
                            <a class="button button-primary" href="<?php echo esc_url($videoUrl); ?>" download>Videoyu Telefona İndir</a>
                            <button type="button" class="button oldies-copy-caption" data-caption="<?php echo esc_attr((string)($draft['caption'] ?? '')); ?>">Açıklamayı Kopyala</button>
                        <?php elseif ($status === 'PUBLISHED') : ?>
                            <?php $liveResult = is_array($draft['live_result'] ?? null) ? $draft['live_result'] : []; ?>
                            <?php if (!empty($liveResult['permalink'])) : ?><a class="button" target="_blank" rel="noopener noreferrer" href="<?php echo esc_url((string)$liveResult['permalink']); ?>">Yayınlanan Reel’i Aç</a><?php else : ?><div>Daha önce yayınlandı.</div><?php endif; ?>
                        <?php else : ?>
                            <div>Bu taslak mevcut durumda mobil Edits aktarımına uygun değil.</div>
                        <?php endif; ?>
                    </div>
                </div>
            <?php endforeach; endif; ?>

            <p style="text-align:center;color:#646970;margin-top:24px;">Bu sayfayı telefon tarayıcınızda ana ekrana ekleyebilirsiniz. WordPress uygulamasındaki eklenti menülerini bulmanız gerekmez.</p>
        </div>
        <script>
        document.addEventListener('click', async (event) => {
            const button = event.target.closest('.oldies-copy-caption');
            if (!button) return;
            const text = button.getAttribute('data-caption') || '';
            try {
                await navigator.clipboard.writeText(text);
                const original = button.textContent;
                button.textContent = 'Kopyalandı';
                setTimeout(() => { button.textContent = original; }, 1400);
            } catch (e) {
                window.prompt('Açıklamayı kopyala:', text);
            }
        });
        </script>
        <?php
    }

    public static function renderAdminPage(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }

        $settings = self::settingsManager();
        $last = get_option(self::LAST_RESULT_OPTION, []);
        $policy = self::getContentPolicy();
        $queue = self::getQueue();
        $noticeKey = 'oldies_reels_bridge_notice_' . get_current_user_id();
        $notice = get_transient($noticeKey);
        if (is_array($notice)) {
            delete_transient($noticeKey);
        }
        ?>
        <div class="wrap">
            <h1>Oldies Radyo — Reels Bridge</h1>
            <p>MP4 Reels videosunu güvenli biçimde alır ve Edits uygulamasında ses/müzik eklenmesi için hazırlar. Doğrudan Instagram canlı yayını bu sürümde kapalıdır.</p>
            <p><a class="button button-primary" href="<?php echo esc_url(admin_url('admin.php?page=oldies-reels-mobile')); ?>">Telefon İçin Mobil Paneli Aç</a></p>

            <?php if (is_array($notice) && !empty($notice['message'])) : ?>
                <div class="notice <?php echo !empty($notice['success']) ? 'notice-success' : 'notice-error'; ?> is-dismissible">
                    <p><?php echo esc_html((string)$notice['message']); ?></p>
                </div>
            <?php endif; ?>

            <table class="widefat striped" style="max-width:900px;margin:20px 0;">
                <tbody>
                    <tr><th style="width:280px;">Köprü sürümü</th><td><?php echo esc_html(self::VERSION); ?></td></tr>
                    <tr><th>Instagram hesabı</th><td>@<?php echo esc_html($settings ? $settings->getInstagramUsername() : '—'); ?></td></tr>
                    <tr><th>Meta Token</th><td>Edits aktarımı için gerekli değil; yalnız isteğe bağlı Dry Run teknik testi kullanır.</td></tr>
                    <tr><th>Edits akışı</th><td>Video indir → telefonda Edits'e içe aktar → ses/müzik ekle → Instagram'da paylaş.</td></tr>
                    <tr><th>Doğrudan canlı yayın</th><td>Kapalı — Edits üzerinden manuel son düzenleme zorunlu.</td></tr>
                    <tr><th>MP4 saklama</th><td>WordPress video işleme/FFmpeg gerektirmeyen güvenli yükleme dizini</td></tr>
                </tbody>
            </table>

            <h2>Instagram → YouTube kaynak kontrolü</h2>
            <p><a class="button" href="<?php echo esc_url(wp_nonce_url(admin_url('admin.php?page=oldies-reels-bridge&oldies_read_instagram=1'), 'oldies_reels_read_instagram')); ?>">Son Instagram videolarını oku</a></p>
            <?php
            if (!empty($_GET['oldies_read_instagram'])) {
                $readNonce = sanitize_text_field(wp_unslash((string)($_GET['_wpnonce'] ?? '')));
                if (!wp_verify_nonce($readNonce, 'oldies_reels_read_instagram')) {
                    echo '<p>Kaynak kontrolü için sayfayı yeniden açın.</p>';
                } else {
                    $recentMedia = self::abilityListInstagramRecent();
                    if (is_wp_error($recentMedia)) {
                        echo '<div class="notice notice-error"><p>' . esc_html($recentMedia->get_error_code() . ': ' . $recentMedia->get_error_message()) . '</p></div>';
                    } elseif (empty($recentMedia)) {
                        echo '<p>Hesaptan okunabilen yeni video bulunamadı.</p>';
                    } else {
                        echo '<table class="widefat striped" style="max-width:1100px"><thead><tr><th>Tarih / kaynak kimliği</th><th>İçerik</th><th>Kaynak</th></tr></thead><tbody>';
                        foreach ($recentMedia as $recentVideo) {
                            echo '<tr><td>' . esc_html((string)$recentVideo['timestamp']) . '<br><code>' . esc_html((string)$recentVideo['media_id']) . '</code></td>';
                            echo '<td>' . esc_html((string)$recentVideo['caption']) . '</td><td><a target="_blank" rel="noopener noreferrer" href="' . esc_url((string)$recentVideo['permalink']) . '">Instagram’da aç</a>';
                            if (!empty($recentVideo['media_url'])) {
                                echo '<br><a target="_blank" rel="noopener noreferrer" href="' . esc_url((string)$recentVideo['media_url']) . '">Final videoyu aç</a>';
                            } else {
                                echo '<br>İndirilebilir final dosya yok.';
                            }
                            echo '<br>Ses: ' . esc_html((string)($recentVideo['media_audio_type'] ?? 'bilinmiyor')) . '</td></tr>';
                        }
                        echo '</tbody></table>';
                    }
                }
            }
            ?>
            <p class="description">Bu kontrol yalnız okur. Video yüklemez veya yayımlamaz; mevcut taslaklarla otomatik eşleştirme yapmaz.</p>

            <h2>Kalite Politikası</h2>
            <p>En az <?php echo (int)$policy['minimum_sources']; ?> farklı yabancı kaynak · kalite eşiği <?php echo (int)$policy['minimum_score']; ?>/100 · günde en fazla <?php echo (int)$policy['maximum_daily_drafts']; ?> taslak · aynı sanatçı için <?php echo (int)$policy['artist_repeat_days']; ?> gün ara · insan onayı zorunlu.</p>

            <h2>Reels Taslak Kuyruğu</h2>
            <?php $visibleDrafts = array_values(array_filter($queue, static fn($draft): bool => is_array($draft) && (string)($draft['status'] ?? '') !== 'REJECTED')); ?>
            <?php if (empty($visibleDrafts)) : ?>
                <p>Henüz inceleme taslağı yok.</p>
            <?php else : foreach ($visibleDrafts as $draft) : ?>
                <?php
                $draftId = (string)($draft['id'] ?? '');
                $status = (string)($draft['status'] ?? 'DRAFT_REVIEW');
                $dryRunResult = is_array($draft['dry_run_result'] ?? null) ? $draft['dry_run_result'] : [];
                ?>
                <div style="max-width:900px;background:#fff;border:1px solid #ccd0d4;padding:18px;margin:12px 0 20px;display:grid;grid-template-columns:minmax(220px,360px) 1fr;gap:22px;align-items:start;">
                    <video controls preload="metadata" playsinline style="width:100%;max-height:640px;background:#111;" src="<?php echo esc_url((string)($draft['video_url'] ?? '')); ?>"></video>
                    <div>
                        <h3 style="margin-top:0;"><?php echo esc_html((string)($draft['artist'] ?? '')); ?> — <?php echo esc_html((string)($draft['topic'] ?? '')); ?></h3>
                        <p><strong>Durum:</strong> <?php echo esc_html($status); ?> · <strong>Puan:</strong> <?php echo (int)($draft['score'] ?? 0); ?>/100 · <strong>Tarih:</strong> <?php echo esc_html((string)($draft['event_date'] ?? '')); ?></p>
                        <?php if (!empty($draft['audio_request']) && is_array($draft['audio_request'])) : ?>
                            <p><strong>Planlanan Instagram müziği:</strong> <?php echo esc_html(trim((string)($draft['audio_request']['artist'] ?? '') . ' — ' . (string)($draft['audio_request']['title'] ?? ''), " —")); ?> <span class="description">(Meta Audio API uygunluk araması)</span></p>
                        <?php endif; ?>
                        <p style="white-space:pre-wrap;"><?php echo esc_html((string)($draft['caption'] ?? '')); ?></p>
                        <?php if (!empty($draft['sources']) && is_array($draft['sources'])) : ?>
                            <p><strong>Kaynaklar:</strong>
                            <?php foreach ($draft['sources'] as $source) : ?>
                                <a href="<?php echo esc_url((string)$source); ?>" target="_blank" rel="noopener noreferrer" style="margin-right:10px;"><?php echo esc_html((string)wp_parse_url((string)$source, PHP_URL_HOST)); ?></a>
                            <?php endforeach; ?></p>
                        <?php endif; ?>
                        <?php if (!empty($dryRunResult)) : ?>
                            <p><strong>Meta Dry Run:</strong> başarılı; canlı medya oluşturulmadı.
                            <?php if (!empty($dryRunResult['audio'])) : ?><br><strong>Seçilen ses:</strong> <?php echo esc_html((string)($dryRunResult['audio']['display_artist'] ?? '')); ?> — <?php echo esc_html((string)($dryRunResult['audio']['title'] ?? '')); ?><?php endif; ?></p>
                        <?php endif; ?>
                        <p>
                            <?php if ($status === 'DRAFT_REVIEW') : ?>
                                <a class="button" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_draft_dry_run&draft_id=' . rawurlencode($draftId)), 'oldies_reels_bridge_draft_dry_run_' . $draftId)); ?>">İsteğe Bağlı Meta Dry Run</a>
                                <a class="button button-primary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_draft_approve&draft_id=' . rawurlencode($draftId)), 'oldies_reels_bridge_draft_approve_' . $draftId)); ?>">Edits İçin Hazırla</a>
                            <?php elseif (in_array($status, ['DRY_RUN_READY', 'APPROVED_FOR_LIVE'], true)) : ?>
                                <a class="button button-primary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_draft_approve&draft_id=' . rawurlencode($draftId)), 'oldies_reels_bridge_draft_approve_' . $draftId)); ?>">Edits İçin Hazırla</a>
                            <?php elseif ($status === 'READY_FOR_EDITS') : ?>
                                <a class="button button-primary" href="<?php echo esc_url((string)($draft['video_url'] ?? '')); ?>" download>Videoyu İndir</a>
                                <button type="button" class="button oldies-copy-caption" data-caption="<?php echo esc_attr((string)($draft['caption'] ?? '')); ?>">Açıklamayı Kopyala</button>
                                <button type="button" class="button oldies-phone-qr" data-video-url="<?php echo esc_attr((string)($draft['video_url'] ?? '')); ?>" data-qr-target="<?php echo esc_attr('oldies-qr-' . $draftId); ?>">Telefona Gönder (QR)</button>
                                <div id="<?php echo esc_attr('oldies-qr-' . $draftId); ?>" class="oldies-qr-box" style="display:none;margin-top:12px;padding:12px;background:#fff;border:1px solid #dcdcde;width:max-content;max-width:100%;"></div>
                                <strong style="margin-left:8px;">Edits’e aktarılmaya hazır.</strong>
                            <?php elseif ($status === 'PUBLISHED') : ?>
                                <?php $liveResult = is_array($draft['live_result'] ?? null) ? $draft['live_result'] : []; ?>
                                <strong>Daha önce Instagram’da yayınlandı.</strong>
                                <?php if (!empty($liveResult['permalink'])) : ?>
                                    <a class="button" target="_blank" rel="noopener noreferrer" href="<?php echo esc_url((string)$liveResult['permalink']); ?>">Reel’i Aç</a>
                                <?php endif; ?>
                            <?php endif; ?>
                            <?php if (!in_array($status, ['READY_FOR_EDITS', 'PUBLISHED'], true)) : ?>
                                <a class="button" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_draft_reject&draft_id=' . rawurlencode($draftId)), 'oldies_reels_bridge_draft_reject_' . $draftId)); ?>">Reddet</a>
                            <?php endif; ?>
                        </p>
                        <p class="description">Edits taslağına sunucu tarafından doğrudan yazılamaz. Video telefona indirilip Edits içinde yeni projeye içe aktarılır; ses ve müzik orada eklenir. Bu sürüm WordPress’ten Instagram’a doğrudan canlı yayın yapmaz.</p>
                    </div>
                </div>
            <?php endforeach; endif; ?>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
            <script>
            document.addEventListener('click', async (event) => {
                const copyButton = event.target.closest('.oldies-copy-caption');
                if (copyButton) {
                    const text = copyButton.getAttribute('data-caption') || '';
                    try {
                        await navigator.clipboard.writeText(text);
                        const original = copyButton.textContent;
                        copyButton.textContent = 'Kopyalandı';
                        setTimeout(() => { copyButton.textContent = original; }, 1400);
                    } catch (e) {
                        window.prompt('Açıklamayı kopyala:', text);
                    }
                    return;
                }

                const qrButton = event.target.closest('.oldies-phone-qr');
                if (!qrButton) return;
                const url = qrButton.getAttribute('data-video-url') || '';
                const box = document.getElementById(qrButton.getAttribute('data-qr-target') || '');
                if (!box || !url) return;
                if (box.dataset.ready === '1') {
                    box.style.display = box.style.display === 'none' ? 'block' : 'none';
                    return;
                }
                if (typeof QRCode === 'undefined') {
                    window.prompt('Telefonda açmak için bu video bağlantısını kopyala:', url);
                    return;
                }
                box.innerHTML = '<div style="font-weight:600;margin-bottom:8px;">Telefon kamerasıyla okut</div><div class="oldies-qr-target"></div><div style="font-size:12px;color:#646970;margin-top:8px;max-width:220px;">QR yalnız video bağlantısını içerir; parola veya token içermez.</div>';
                const target = box.querySelector('.oldies-qr-target');
                new QRCode(target, {text:url,width:220,height:220,correctLevel:QRCode.CorrectLevel.M});
                box.dataset.ready = '1';
                box.style.display = 'block';
            });
            </script>

            <h2>Kalite Kuyruğuna Taslak Yükle</h2>
            <form id="oldies-reels-draft-form" action="<?php echo esc_url(add_query_arg('rest_route', '/' . self::REST_NAMESPACE . '/instagram/reels/drafts', home_url('/'))); ?>" enctype="multipart/form-data" style="max-width:900px;">
                <table class="form-table">
                    <tr><th><label for="ord_video">Reels MP4</label></th><td><input id="ord_video" name="reel_video" type="file" accept="video/mp4,.mp4" required></td></tr>
                    <tr><th><label for="ord_artist">Sanatçı</label></th><td><input id="ord_artist" name="artist" type="text" class="regular-text" required></td></tr>
                    <tr><th><label for="ord_topic">Konu</label></th><td><input id="ord_topic" name="topic" type="text" class="regular-text" required></td></tr>
                    <tr><th><label for="ord_date">Olay tarihi</label></th><td><input id="ord_date" name="event_date" type="date" required></td></tr>
                    <tr><th><label for="ord_caption">Açıklama</label></th><td><textarea id="ord_caption" name="caption" rows="5" class="large-text" required></textarea></td></tr>
                    <tr><th><label for="ord_sources">Yabancı kaynaklar</label></th><td><textarea id="ord_sources" name="sources" rows="3" class="large-text" placeholder="Her satıra bir HTTPS adresi" required></textarea></td></tr>
                    <tr><th><label for="ord_facts">Doğrulanmış bilgiler</label></th><td><textarea id="ord_facts" name="facts" rows="3" class="large-text" placeholder="Her satıra bir bilgi" required></textarea></td></tr>
                    <tr><th><label for="ord_audio_title">Instagram müziği</label></th><td><input id="ord_audio_title" name="audio_title" type="text" placeholder="Şarkı" class="regular-text"> <input name="audio_artist" type="text" placeholder="Sanatçı" class="regular-text"><p class="description">Meta Audio API yalnızca hesap için üçüncü taraf kullanımına yetkili sonuçları bağlar.</p></td></tr>
                    <tr><th>Kalite puanları</th><td><input name="date_relevance" type="number" min="0" max="30" value="30" style="width:65px"> tarih · <input name="audience_fit" type="number" min="0" max="25" value="25" style="width:65px"> kitle · <input name="source_confidence" type="number" min="0" max="20" value="20" style="width:65px"> kaynak · <input name="visual_strength" type="number" min="0" max="15" value="13" style="width:65px"> görsel · <input name="freshness" type="number" min="0" max="10" value="8" style="width:65px"> tazelik</td></tr>
                </table>
                <?php submit_button('Taslağı İnceleme Kuyruğuna Ekle', 'secondary'); ?>
                <p id="oldies-reels-draft-feedback" aria-live="polite"></p>
            </form>
            <script>
            (() => {
                const form = document.getElementById('oldies-reels-draft-form');
                const feedback = document.getElementById('oldies-reels-draft-feedback');
                if (!form || !feedback) return;
                form.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    const button = form.querySelector('input[type="submit"]');
                    if (button) button.disabled = true;
                    feedback.textContent = 'MP4 yükleniyor ve kalite kuyruğu oluşturuluyor…';
                    const body = new FormData(form);
                    body.set('sources', JSON.stringify(String(body.get('sources')).split(/\r?\n/).map(v => v.trim()).filter(Boolean)));
                    body.set('facts', JSON.stringify(String(body.get('facts')).split(/\r?\n/).map(v => v.trim()).filter(Boolean)));
                    body.set('score_breakdown', JSON.stringify({date_relevance:Number(body.get('date_relevance')),audience_fit:Number(body.get('audience_fit')),source_confidence:Number(body.get('source_confidence')),visual_strength:Number(body.get('visual_strength')),freshness:Number(body.get('freshness'))}));
                    try {
                        const response = await fetch(form.action, {method:'POST',credentials:'same-origin',headers:{'Accept':'application/json','X-WP-Nonce':<?php echo wp_json_encode(wp_create_nonce('wp_rest')); ?>},body});
                        const data = await response.json().catch(() => ({}));
                        if (!response.ok || !data.success) throw new Error(data.message || 'Taslak yüklenemedi.');
                        feedback.textContent = 'Taslak eklendi; canlı yayın yapılmadı.';
                        window.setTimeout(() => window.location.reload(), 700);
                    } catch (error) {
                        feedback.textContent = 'Taslak yüklenemedi: ' + (error && error.message ? error.message : 'Bilinmeyen hata');
                        if (button) button.disabled = false;
                    }
                });
            })();
            </script>

            <h2>Reels Dry Run Testi</h2>
            <p>
                <a class="button button-secondary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_bundled_test'), 'oldies_reels_bridge_bundled_test')); ?>">
                    Paketli Test Videosuyla Dry Run Çalıştır
                </a>
                <a class="button button-secondary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=oldies_reels_bridge_bearer_test'), 'oldies_reels_bridge_bearer_test')); ?>">
                    Bearer REST Dry Run Self-Test
                </a>
            </p>
            <p class="description">İlk seçenek paketli MP4 ile Meta hattını; Bearer Self-Test ise yönetici çerezi olmadan dış otomasyonun kullanacağı REST yetkilendirmesini sınar.</p>

            <form id="oldies-reels-bridge-form" method="post" action="<?php echo esc_url(add_query_arg('rest_route', '/' . self::REST_NAMESPACE . '/instagram/reels', home_url('/'))); ?>" enctype="multipart/form-data" style="max-width:900px;">

                <table class="form-table">
                    <tr>
                        <th><label for="orb_video">Reels MP4</label></th>
                        <td><input id="orb_video" name="reel_video" type="file" accept="video/mp4,.mp4"></td>
                    </tr>
                    <tr>
                        <th><label for="orb_url">Veya herkese açık MP4 URL</label></th>
                        <td><input id="orb_url" name="video_url" type="url" class="regular-text" placeholder="https://.../reel.mp4"></td>
                    </tr>
                    <tr>
                        <th><label for="orb_topic">Konu</label></th>
                        <td><input id="orb_topic" name="topic" type="text" class="regular-text" value="Oldies Radyo Reels Teknik Dry Run Testi" required></td>
                    </tr>
                    <tr>
                        <th><label for="orb_caption">Instagram açıklaması</label></th>
                        <td><textarea id="orb_caption" name="caption" rows="5" class="large-text" required>Oldies Radyo Reels otomasyon hattı teknik testidir. Dry Run modunda hazırlanmıştır; canlı yayınlanmayacaktır.</textarea></td>
                    </tr>
                    <tr>
                        <th>Profil akışı</th>
                        <td><label><input type="checkbox" name="share_to_feed" value="1" checked> Reels’i profil akışında da göster</label></td>
                    </tr>
                </table>

                <?php submit_button('Reels Dry Run Testini Çalıştır'); ?>
                <p id="oldies-reels-bridge-feedback" aria-live="polite"></p>
                <p><strong>Güvenlik:</strong> Bu panel canlı paylaşım yapmaz. Dry Run sunucu tarafında zorunludur.</p>
            </form>

            <script>
            (() => {
                const form = document.getElementById('oldies-reels-bridge-form');
                const feedback = document.getElementById('oldies-reels-bridge-feedback');
                if (!form || !feedback) return;

                form.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    const button = form.querySelector('input[type="submit"], button[type="submit"]');
                    if (button) button.disabled = true;
                    feedback.textContent = 'Video yükleniyor ve Meta Dry Run işleniyor…';

                    const body = new FormData(form);
                    body.set('dry_run', '1');
                    body.set('share_to_feed', form.querySelector('[name="share_to_feed"]')?.checked ? '1' : '0');
                    body.set('idempotency_key', 'admin-rest-' + Date.now());

                    try {
                        const response = await fetch(form.action, {
                            method: 'POST',
                            credentials: 'same-origin',
                            headers: {
                                'Accept': 'application/json',
                                'X-WP-Nonce': <?php echo wp_json_encode(wp_create_nonce('wp_rest')); ?>
                            },
                            body
                        });
                        const data = await response.json().catch(() => ({}));
                        if (!response.ok || !data.success) {
                            throw new Error(data.message || 'Reels Dry Run isteği başarısız oldu.');
                        }
                        feedback.textContent = 'Dry Run başarılı: Video Meta tarafından işlendi, Instagram’da canlı yayınlanmadı.';
                        window.setTimeout(() => window.location.reload(), 800);
                    } catch (error) {
                        feedback.textContent = 'Dry Run başarısız: ' + (error && error.message ? error.message : 'Bilinmeyen hata');
                        if (button) button.disabled = false;
                    }
                });
            })();
            </script>

            <?php if (is_array($last) && !empty($last)) : ?>
                <h2>Son Köprü İşlemi</h2>
                <pre style="max-width:900px;white-space:pre-wrap;background:#fff;border:1px solid #ccd0d4;padding:14px;"><?php echo esc_html((string)wp_json_encode($last, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)); ?></pre>
            <?php endif; ?>
        </div>
        <?php
    }

    public static function handleAdminDryRun(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        $nonce = sanitize_text_field(wp_unslash((string)($_GET['orb_nonce'] ?? '')));
        if ($nonce === '' || !wp_verify_nonce($nonce, 'oldies_reels_bridge_dry_run')) {
            wp_die('Reels Bridge güvenlik anahtarı geçersiz. Lütfen sayfayı yenileyip tekrar deneyin.');
        }

        $caption = sanitize_textarea_field(wp_unslash((string)($_POST['caption'] ?? '')));
        $topic = sanitize_text_field(wp_unslash((string)($_POST['topic'] ?? 'Oldies Radyo Reel')));
        $videoUrl = esc_url_raw(wp_unslash((string)($_POST['video_url'] ?? '')));
        $stored = null;

        if (!empty($_FILES['reel_video']['tmp_name']) && is_array($_FILES['reel_video'])) {
            $stored = self::storeUploadedMp4($_FILES['reel_video']);
            if (!is_wp_error($stored)) {
                $videoUrl = $stored['url'];
            }
        }

        $result = is_wp_error($stored) ? $stored : self::publish([
            'video_url' => $videoUrl,
            'caption' => $caption,
            'topic' => $topic,
            'dry_run' => true,
            'share_to_feed' => isset($_POST['share_to_feed']),
            'idempotency_key' => 'admin-' . wp_generate_uuid4(),
            'origin' => 'admin_bridge',
        ]);

        $success = !is_wp_error($result);
        $message = $success
            ? 'Dry Run başarılı: Video Meta tarafından işlendi, Instagram’da canlı yayınlanmadı.'
            : 'Dry Run başarısız: ' . $result->get_error_message();

        if ($success && is_array($result)) {
            self::saveLastResult($result, (string)($result['idempotency_key'] ?? ''), 'admin');
        }

        set_transient('oldies_reels_bridge_notice_' . get_current_user_id(), [
            'success' => $success,
            'message' => $message,
        ], 120);

        wp_safe_redirect(admin_url('admin.php?page=oldies-reels-bridge'));
        exit;
    }

    public static function handleBundledDryRun(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        check_admin_referer('oldies_reels_bridge_bundled_test');

        $result = self::publish([
            'video_url' => plugins_url('oldies-reels-dry-run.mp4', __FILE__),
            'caption' => 'Oldies Radyo Reels otomasyon hattı teknik testidir. Dry Run modunda hazırlanmıştır; canlı yayınlanmayacaktır.',
            'topic' => 'Oldies Radyo Reels Teknik Dry Run Testi',
            'dry_run' => true,
            'share_to_feed' => true,
            'idempotency_key' => 'bundled-admin-' . wp_generate_uuid4(),
            'origin' => 'admin_bundled_test',
        ]);

        $success = !is_wp_error($result);
        $message = $success
            ? 'Dry Run başarılı: Paketli video Meta tarafından işlendi, Instagram’da canlı yayınlanmadı.'
            : 'Dry Run başarısız: ' . $result->get_error_message();

        if ($success && is_array($result)) {
            self::saveLastResult($result, (string)($result['idempotency_key'] ?? ''), 'admin_bundled_test');
        }

        set_transient('oldies_reels_bridge_notice_' . get_current_user_id(), [
            'success' => $success,
            'message' => $message,
        ], 120);

        wp_safe_redirect(admin_url('admin.php?page=oldies-reels-bridge'));
        exit;
    }

    public static function handleBearerDryRun(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        check_admin_referer('oldies_reels_bridge_bearer_test');

        $settings = self::settingsManager();
        $secret = $settings ? (string)$settings->getBearerSecret() : '';
        if ($secret === '') {
            self::redirectWithNotice(false, 'Bearer Self-Test başarısız: Automation Bearer Secret tanımlı değil.');
        }

        $endpoint = add_query_arg('rest_route', '/' . self::REST_NAMESPACE . '/instagram/reels', home_url('/'));
        $payload = [
            'video_url' => plugins_url('oldies-reels-dry-run.mp4', __FILE__),
            'caption' => 'Oldies Radyo Reels dış otomasyon Bearer testi. Dry Run modundadır; canlı yayınlanmayacaktır.',
            'topic' => 'Oldies Radyo Reels Bearer REST Dry Run',
            'dry_run' => true,
            'share_to_feed' => true,
            'idempotency_key' => 'bearer-self-test-' . wp_generate_uuid4(),
        ];

        $response = wp_remote_post($endpoint, [
            'timeout' => 120,
            'redirection' => 2,
            'headers' => [
                'Authorization' => 'Bearer ' . $secret,
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
            ],
            'body' => wp_json_encode($payload),
            'data_format' => 'body',
        ]);

        if (is_wp_error($response)) {
            self::redirectWithNotice(false, 'Bearer Self-Test başarısız: ' . $response->get_error_message());
        }

        $status = (int)wp_remote_retrieve_response_code($response);
        $data = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status !== 200 || !is_array($data) || empty($data['success'])) {
            $message = is_array($data) && !empty($data['message']) ? (string)$data['message'] : 'HTTP ' . $status;
            self::redirectWithNotice(false, 'Bearer Self-Test başarısız: ' . $message);
        }

        self::redirectWithNotice(true, 'Bearer Self-Test başarılı: Dış REST yetkilendirmesi ve Meta Dry Run tamamlandı; canlı yayın yapılmadı.');
    }

    public static function handleDraftDryRun(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        $draftId = sanitize_text_field(wp_unslash((string)($_GET['draft_id'] ?? '')));
        check_admin_referer('oldies_reels_bridge_draft_dry_run_' . $draftId);
        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null || (string)($queue[$index]['status'] ?? '') !== 'DRAFT_REVIEW') {
            self::redirectWithNotice(false, 'Taslak bulunamadı veya Dry Run için uygun durumda değil.');
        }

        $audioRequest = is_array($queue[$index]['audio_request'] ?? null) ? $queue[$index]['audio_request'] : [];
        $audioSelection = [];
        $audioWarning = '';
        unset($queue[$index]['audio_warning']);
        if (!empty($audioRequest['search_query'])) {
            $resolvedAudio = self::selectExactAudio($audioRequest);
            if (!is_wp_error($resolvedAudio)) {
                $audioSelection = $resolvedAudio;
            } else {
                $audioWarning = $resolvedAudio->get_error_message();
                $queue[$index]['audio_warning'] = $audioWarning;
            }
        }

        $result = self::publish([
            'video_url' => (string)$queue[$index]['video_url'],
            'caption' => (string)$queue[$index]['caption'],
            'topic' => (string)$queue[$index]['topic'],
            'dry_run' => true,
            'share_to_feed' => true,
            'idempotency_key' => 'draft-dry-run-' . $draftId . '-' . time(),
            'origin' => 'draft_review',
            'audio_id' => (string)($audioSelection['audio_id'] ?? ''),
            'audio_volume' => (int)($audioRequest['audio_volume'] ?? 100),
            'video_volume' => (int)($audioRequest['video_volume'] ?? 12),
        ]);
        if (is_wp_error($result)) {
            self::redirectWithNotice(false, 'Taslak Dry Run başarısız: ' . $result->get_error_message());
        }

        $queue[$index]['status'] = 'DRY_RUN_READY';
        $queue[$index]['dry_run_result'] = [
            'tested_at' => current_time('mysql', true),
            'mode' => (string)($result['mode'] ?? 'DRY_RUN'),
            'job_id' => (int)($result['job_id'] ?? 0),
            'container_id' => (string)($result['container_id'] ?? ''),
            'instagram_media_id' => '',
            'permalink' => '',
            'audio' => $audioSelection,
        ];
        self::saveQueue($queue);
        self::saveLastResult($result, (string)($result['idempotency_key'] ?? ''), 'draft_review');
        $notice = 'Taslak Meta Dry Run testini geçti; Instagram’da canlı yayın yapılmadı.';
        if ($audioWarning !== '') {
            $notice .= ' Müzik notu: ' . $audioWarning . ' Test özgün video sesiyle tamamlandı.';
        }
        self::redirectWithNotice(true, $notice);
    }

    public static function handleDraftApprove(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        $draftId = sanitize_text_field(wp_unslash((string)($_GET['draft_id'] ?? '')));
        check_admin_referer('oldies_reels_bridge_draft_approve_' . $draftId);
        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null) {
            self::redirectWithNotice(false, 'Taslak bulunamadı.');
        }
        $status = (string)($queue[$index]['status'] ?? 'DRAFT_REVIEW');
        if (!in_array($status, ['DRAFT_REVIEW', 'DRY_RUN_READY', 'APPROVED_FOR_LIVE', 'READY_FOR_EDITS'], true)) {
            self::redirectWithNotice(false, 'Bu taslak Edits aktarımı için hazırlanamaz.');
        }

        $queue[$index]['status'] = 'READY_FOR_EDITS';
        $queue[$index]['edits_ready_at'] = current_time('mysql', true);
        $queue[$index]['edits_ready_by'] = get_current_user_id();
        self::saveQueue($queue);
        self::redirectWithNotice(true, 'Taslak Edits için hazırlandı; Instagram’a canlı yayın yapılmadı. YouTube da beklemede. Videoyu indirip Edits içinde ses ve müzik ekleyebilirsiniz.');
    }

    public static function handleDraftPublish(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        $draftId = sanitize_text_field(wp_unslash((string)($_GET['draft_id'] ?? '')));
        check_admin_referer('oldies_reels_bridge_draft_publish_' . $draftId);
        self::redirectWithNotice(false, 'Doğrudan Instagram canlı yayını devre dışı. Bu sürüm Edits aktarım akışını kullanır.');
    }

    /**
     * Publish exactly one administrator-approved draft without opening the global
     * automation live switches. A prior successful Dry Run and APPROVED_FOR_LIVE
     * state are mandatory, and a DB lock prevents accidental double publishing.
     *
     * @param array<int,array<string,mixed>> $queue
     * @return array<string,mixed>|WP_Error
     */
    private static function publishApprovedDraftLive(array &$queue, int $index, string $draftId)
    {
        if ((string)($queue[$index]['status'] ?? '') !== 'APPROVED_FOR_LIVE') {
            return new WP_Error('approved_draft_required', 'Taslak canlı yayın için yönetici tarafından onaylanmış olmalıdır.');
        }

        $dryRun = is_array($queue[$index]['dry_run_result'] ?? null) ? $queue[$index]['dry_run_result'] : [];
        if (empty($dryRun['tested_at']) || strtoupper((string)($dryRun['mode'] ?? '')) !== 'DRY_RUN') {
            return new WP_Error('approved_dry_run_required', 'Canlı yayından önce başarılı Meta Dry Run kaydı bulunmalıdır.');
        }

        if (!empty($queue[$index]['live_result']) || !empty($queue[$index]['published_at'])) {
            return new WP_Error('draft_already_published', 'Bu taslak daha önce canlı yayınlanmış görünüyor; ikinci kez gönderilmedi.');
        }

        $lockKey = 'oldies_reels_live_lock_' . md5($draftId);
        $lockTime = (int)get_option($lockKey, 0);
        if ($lockTime > 0 && (time() - $lockTime) < 600) {
            return new WP_Error('draft_live_in_progress', 'Bu taslak için canlı yayın işlemi zaten devam ediyor.');
        }
        if ($lockTime > 0) {
            delete_option($lockKey);
        }
        if (!add_option($lockKey, time(), '', false)) {
            return new WP_Error('draft_live_lock_failed', 'Canlı yayın kilidi alınamadı; yinelenen paylaşım önlendi.');
        }

        try {
            $audio = is_array($dryRun['audio'] ?? null) ? $dryRun['audio'] : [];
            $audioRequest = is_array($queue[$index]['audio_request'] ?? null) ? $queue[$index]['audio_request'] : [];
            $result = self::publish([
                'video_url' => (string)($queue[$index]['video_url'] ?? ''),
                'caption' => (string)($queue[$index]['caption'] ?? ''),
                'topic' => (string)($queue[$index]['topic'] ?? 'Oldies Radyo Reel'),
                'dry_run' => false,
                'share_to_feed' => true,
                'idempotency_key' => 'draft-live-' . $draftId,
                'origin' => 'draft_approved_live',
                'audio_id' => (string)($audio['audio_id'] ?? ''),
                'audio_volume' => (int)($audioRequest['audio_volume'] ?? 100),
                'video_volume' => (int)($audioRequest['video_volume'] ?? 12),
                'approved_admin_override' => true,
            ]);
            if (is_wp_error($result)) {
                return $result;
            }

            $queue[$index]['status'] = 'PUBLISHED';
            $queue[$index]['published_at'] = current_time('mysql', true);
            $queue[$index]['published_by'] = get_current_user_id();
            $queue[$index]['live_result'] = [
                'mode' => (string)($result['mode'] ?? 'LIVE'),
                'container_id' => (string)($result['container_id'] ?? ''),
                'instagram_media_id' => (string)($result['instagram_media_id'] ?? ''),
                'permalink' => (string)($result['permalink'] ?? ''),
                'audio' => $audio,
            ];
            self::saveQueue($queue);
            return $result;
        } finally {
            delete_option($lockKey);
        }
    }

    public static function handleDraftReject(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Bu işlem için yetkiniz yok.');
        }
        $draftId = sanitize_text_field(wp_unslash((string)($_GET['draft_id'] ?? '')));
        check_admin_referer('oldies_reels_bridge_draft_reject_' . $draftId);
        $queue = self::getQueue();
        $index = self::findDraftIndex($queue, $draftId);
        if ($index === null) {
            self::redirectWithNotice(false, 'Taslak bulunamadı.');
        }
        $queue[$index]['status'] = 'REJECTED';
        $queue[$index]['rejected_at'] = current_time('mysql', true);
        $queue[$index]['rejected_by'] = get_current_user_id();
        self::saveQueue($queue);
        self::redirectWithNotice(true, 'Taslak reddedildi; herhangi bir paylaşım yapılmadı.');
    }

    private static function redirectWithNotice(bool $success, string $message): void
    {
        set_transient('oldies_reels_bridge_notice_' . get_current_user_id(), [
            'success' => $success,
            'message' => $message,
        ], 120);
        wp_safe_redirect(admin_url('admin.php?page=oldies-reels-bridge'));
        exit;
    }

    /** @return array<int,array<string,mixed>>|WP_Error */
    private static function searchAudioAssets(string $query, string $audioType = 'music')
    {
        $settings = self::settingsManager();
        if ($settings === null || !method_exists($settings, 'getInstagramUserId')) {
            return new WP_Error('audio_settings_missing', 'Instagram hesap kimliği alınamadı.', ['status' => 503]);
        }
        $response = self::metaGraphRequest('/ig_audio', 'GET', [
            'audio_type' => $audioType,
            'user_id' => (string)$settings->getInstagramUserId(),
            'search_query' => $query,
        ]);
        if (is_wp_error($response)) {
            return $response;
        }
        $items = is_array($response['audio'] ?? null) ? $response['audio'] : [];
        $safe = [];
        foreach ($items as $item) {
            if (!is_array($item) || self::sanitizeMetaId($item['audio_id'] ?? '') === '') {
                continue;
            }
            $safe[] = [
                'audio_id' => self::sanitizeMetaId($item['audio_id']),
                'audio_type' => sanitize_key((string)($item['audio_type'] ?? $audioType)),
                'title' => sanitize_text_field((string)($item['title'] ?? '')),
                'display_artist' => sanitize_text_field((string)($item['display_artist'] ?? '')),
                'duration_in_ms' => max(0, (int)($item['duration_in_ms'] ?? 0)),
                'is_ads_eligible' => isset($item['is_ads_eligible']) ? (bool)$item['is_ads_eligible'] : null,
                'on_platform_audio_preview_link' => esc_url_raw((string)($item['on_platform_audio_preview_link'] ?? '')),
                'cover_artwork_thumbnail_uri' => esc_url_raw((string)($item['cover_artwork_thumbnail_uri'] ?? '')),
            ];
        }
        return $safe;
    }

    /** @param array<string,mixed> $request @return array<string,mixed>|WP_Error */
    private static function selectExactAudio(array $request)
    {
        $query = sanitize_text_field((string)($request['search_query'] ?? ''));
        $title = self::normalizeAudioText((string)($request['title'] ?? ''));
        $artist = self::normalizeAudioText((string)($request['artist'] ?? ''));
        $items = self::searchAudioAssets($query, 'music');
        if (is_wp_error($items)) {
            return $items;
        }
        foreach ($items as $item) {
            $foundTitle = self::normalizeAudioText((string)($item['title'] ?? ''));
            $foundArtist = self::normalizeAudioText((string)($item['display_artist'] ?? ''));
            $titleMatches = $title === '' || $foundTitle === $title;
            $artistMatches = $artist === '' || $foundArtist === $artist;
            if ($titleMatches && $artistMatches) {
                return $item;
            }
        }
        return new WP_Error(
            'exact_audio_not_authorized',
            'İstenen şarkı hesabın Meta Audio API kataloğunda tam eşleşmeyle bulunamadı; yanlış müzik seçilmedi ve özgün ses korunacak.',
            ['status' => 404]
        );
    }

    private static function normalizeAudioText(string $value): string
    {
        $value = trim($value);
        $value = function_exists('mb_strtolower') ? mb_strtolower($value, 'UTF-8') : strtolower($value);
        $value = remove_accents($value);
        return trim((string)preg_replace('/[^a-z0-9]+/u', ' ', $value));
    }

    /** @return array<string,mixed>|WP_Error */
    private static function getInstagramFinalMedia(string $mediaId)
    {
        $mediaId = self::sanitizeMetaId($mediaId);
        if ($mediaId === '') {
            return new WP_Error('instagram_media_id_required', 'Instagram medya kimliği gerekli.');
        }
        $response = self::metaGraphRequest('/' . $mediaId, 'GET', [
            'fields' => 'id,caption,media_type,media_product_type,media_audio_type,permalink,media_url,timestamp',
        ]);
        if (is_wp_error($response)) {
            return $response;
        }
        if (self::sanitizeMetaId($response['id'] ?? '') !== $mediaId) {
            return new WP_Error('instagram_media_mismatch', 'Instagram medya kimliği doğrulanamadı.');
        }
        if (strtoupper((string)($response['media_type'] ?? '')) !== 'VIDEO') {
            return new WP_Error('instagram_media_not_video', 'Seçilen Instagram medya video değil.');
        }
        $permalink = esc_url_raw((string)($response['permalink'] ?? ''));
        $mediaUrl = esc_url_raw((string)($response['media_url'] ?? ''));
        $audioType = strtoupper(sanitize_text_field((string)($response['media_audio_type'] ?? '')));
        if ($permalink === '') {
            return new WP_Error('instagram_final_permalink_missing', 'Instagram final Reel permalink vermedi.');
        }
        if ($mediaUrl === '') {
            if ($audioType === 'MUSIC') {
                return new WP_Error('instagram_final_media_licensed_audio_unavailable', 'Instagram lisanslı müzik içeren bu Reel için indirilebilir final media_url vermiyor. Ham videoya geri düşülmedi; YouTube aktarımı güvenli biçimde bloklandı.');
            }
            return new WP_Error('instagram_final_media_missing', 'Instagram final video URL vermedi. Ham videoya geri düşülmedi.');
        }
        return [
            'id' => $mediaId,
            'permalink' => $permalink,
            'media_url' => $mediaUrl,
            'timestamp' => sanitize_text_field((string)($response['timestamp'] ?? '')),
            'caption' => sanitize_textarea_field((string)($response['caption'] ?? '')),
            'media_audio_type' => $audioType,
            'media_product_type' => sanitize_text_field((string)($response['media_product_type'] ?? '')),
        ];
    }

    /** @return array<string,mixed>|WP_Error */
    private static function metaGraphRequest(string $endpoint, string $method, array $params)
    {
        $settings = self::settingsManager();
        if ($settings === null || !method_exists($settings, 'getInstagramAccessToken')) {
            return new WP_Error('audio_token_unavailable', 'Instagram erişim anahtarı alınamadı.', ['status' => 503]);
        }
        $token = (string)$settings->getInstagramAccessToken();
        if ($token === '') {
            return new WP_Error('audio_token_missing', 'Instagram erişim anahtarı tanımlı değil.', ['status' => 503]);
        }
        $params['access_token'] = $token;
        $url = self::META_GRAPH_BASE . '/' . ltrim($endpoint, '/');
        $args = [
            'method' => strtoupper($method),
            'timeout' => 45,
            'redirection' => 2,
            'sslverify' => true,
            'headers' => ['Accept' => 'application/json'],
        ];
        if (strtoupper($method) === 'GET') {
            $url = add_query_arg($params, $url);
        } else {
            $args['body'] = $params;
        }
        $response = wp_remote_request($url, $args);
        if (is_wp_error($response)) {
            return new WP_Error('meta_audio_http_error', 'Meta Audio API bağlantı hatası: ' . $response->get_error_message(), ['status' => 502]);
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        $data = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status >= 400 || !is_array($data) || isset($data['error'])) {
            $message = is_array($data) ? sanitize_text_field((string)($data['error']['message'] ?? 'Meta Audio API isteği reddedildi.')) : 'Meta Audio API geçersiz yanıt verdi.';
            return new WP_Error('meta_audio_api_error', $message, ['status' => $status >= 400 ? $status : 502]);
        }
        return $data;
    }

    /**
     * @param array<string,mixed> $publisherArgs
     * @param array{audio_id:string,audio_volume:int,video_volume:int} $audio
     * @return array<string,mixed>|WP_Error
     */
    private static function publishReelWithAudio(array $publisherArgs, array $audio, bool $approvedAdminOverride = false)
    {
        $settings = self::settingsManager();
        if ($settings === null || !method_exists($settings, 'getInstagramUserId')) {
            return new WP_Error('audio_publish_settings_missing', 'Instagram hesap ayarları alınamadı.');
        }
        $userId = self::sanitizeMetaId($settings->getInstagramUserId());
        if ($userId === '') {
            return new WP_Error('audio_publish_user_missing', 'Instagram hesap kimliği alınamadı.');
        }
        $container = self::metaGraphRequest('/' . $userId . '/media', 'POST', [
            'media_type' => 'REELS',
            'video_url' => (string)$publisherArgs['video_url'],
            'caption' => (string)$publisherArgs['caption'],
            'share_to_feed' => !empty($publisherArgs['share_to_feed']) ? 'true' : 'false',
            'audio_configuration' => wp_json_encode([
                'audio_id' => $audio['audio_id'],
                'audio_volume' => $audio['audio_volume'],
                'video_volume' => $audio['video_volume'],
            ]),
        ]);
        if (is_wp_error($container)) {
            return $container;
        }
        $containerId = self::sanitizeMetaId($container['id'] ?? '');
        if ($containerId === '') {
            return new WP_Error('audio_container_missing', 'Meta Audio API container kimliği döndürmedi.');
        }

        $finished = false;
        for ($attempt = 0; $attempt < 18; ++$attempt) {
            $status = self::metaGraphRequest('/' . $containerId, 'GET', ['fields' => 'status_code,status']);
            if (is_wp_error($status)) {
                return $status;
            }
            $statusCode = strtoupper((string)($status['status_code'] ?? ''));
            if ($statusCode === 'FINISHED') {
                $finished = true;
                break;
            }
            if (in_array($statusCode, ['ERROR', 'EXPIRED'], true)) {
                return new WP_Error('audio_container_failed', 'Sesli Reels container işlemesi başarısız oldu: ' . $statusCode);
            }
            sleep(5);
        }
        if (!$finished) {
            return new WP_Error('audio_container_timeout', 'Sesli Reels container işlemesi zaman aşımına uğradı.');
        }

        $result = [
            'success' => true,
            'mode' => 'DRY_RUN',
            'job_id' => 0,
            'container_id' => $containerId,
            'video_url' => (string)$publisherArgs['video_url'],
            'audio_id' => $audio['audio_id'],
            'audio_configuration' => $audio,
        ];
        if (!empty($publisherArgs['dry_run'])) {
            return $result;
        }
        if (!self::livePublishingAllowed() && !$approvedAdminOverride) {
            return new WP_Error('live_publish_locked', 'Canlı Reels yayını güvenlik kilidi nedeniyle kapalı.');
        }
        $published = self::metaGraphRequest('/' . $userId . '/media_publish', 'POST', ['creation_id' => $containerId]);
        if (is_wp_error($published)) {
            return $published;
        }
        $mediaId = self::sanitizeMetaId($published['id'] ?? '');
        $permalink = '';
        if ($mediaId !== '') {
            $media = self::metaGraphRequest('/' . $mediaId, 'GET', ['fields' => 'permalink,id']);
            if (!is_wp_error($media)) {
                $permalink = esc_url_raw((string)($media['permalink'] ?? ''));
            }
        }
        $result['mode'] = 'LIVE';
        $result['instagram_media_id'] = $mediaId;
        $result['permalink'] = $permalink;
        return $result;
    }

    /**
     * Publish a Reel directly through the Meta Graph API.
     * This deliberately avoids depending on a concrete Publisher method name,
     * so Bridge dry-runs remain compatible across Social Automation releases.
     *
     * @param array<string,mixed> $publisherArgs
     * @return array<string,mixed>|WP_Error
     */
    private static function publishReelDirect(array $publisherArgs, bool $approvedAdminOverride = false)
    {
        $settings = self::settingsManager();
        if ($settings === null || !method_exists($settings, 'getInstagramUserId')) {
            return new WP_Error('reel_publish_settings_missing', 'Instagram hesap ayarları alınamadı.');
        }

        $userId = self::sanitizeMetaId($settings->getInstagramUserId());
        if ($userId === '') {
            return new WP_Error('reel_publish_user_missing', 'Instagram hesap kimliği alınamadı.');
        }

        $container = self::metaGraphRequest('/' . $userId . '/media', 'POST', [
            'media_type' => 'REELS',
            'video_url' => (string)$publisherArgs['video_url'],
            'caption' => (string)$publisherArgs['caption'],
            'share_to_feed' => !empty($publisherArgs['share_to_feed']) ? 'true' : 'false',
        ]);
        if (is_wp_error($container)) {
            return $container;
        }

        $containerId = self::sanitizeMetaId($container['id'] ?? '');
        if ($containerId === '') {
            return new WP_Error('reel_container_missing', 'Meta Reels container kimliği döndürmedi.');
        }

        $finished = false;
        for ($attempt = 0; $attempt < 18; ++$attempt) {
            $status = self::metaGraphRequest('/' . $containerId, 'GET', ['fields' => 'status_code,status']);
            if (is_wp_error($status)) {
                return $status;
            }
            $statusCode = strtoupper((string)($status['status_code'] ?? ''));
            if ($statusCode === 'FINISHED') {
                $finished = true;
                break;
            }
            if (in_array($statusCode, ['ERROR', 'EXPIRED'], true)) {
                return new WP_Error('reel_container_failed', 'Reels container işlemesi başarısız oldu: ' . $statusCode);
            }
            sleep(5);
        }

        if (!$finished) {
            return new WP_Error('reel_container_timeout', 'Reels container işlemesi zaman aşımına uğradı.');
        }

        $result = [
            'success' => true,
            'mode' => 'DRY_RUN',
            'job_id' => 0,
            'container_id' => $containerId,
            'video_url' => (string)$publisherArgs['video_url'],
            'instagram_media_id' => '',
            'permalink' => '',
        ];

        if (!empty($publisherArgs['dry_run'])) {
            return $result;
        }
        if (!self::livePublishingAllowed() && !$approvedAdminOverride) {
            return new WP_Error('live_publish_locked', 'Canlı Reels yayını güvenlik kilidi nedeniyle kapalı.');
        }

        $published = self::metaGraphRequest('/' . $userId . '/media_publish', 'POST', ['creation_id' => $containerId]);
        if (is_wp_error($published)) {
            return $published;
        }

        $mediaId = self::sanitizeMetaId($published['id'] ?? '');
        $permalink = '';
        if ($mediaId !== '') {
            $media = self::metaGraphRequest('/' . $mediaId, 'GET', ['fields' => 'permalink,id']);
            if (!is_wp_error($media)) {
                $permalink = esc_url_raw((string)($media['permalink'] ?? ''));
            }
        }

        $result['mode'] = 'LIVE';
        $result['instagram_media_id'] = $mediaId;
        $result['permalink'] = $permalink;
        return $result;
    }

    /**
     * @param array<string,mixed> $args
     * @return array<string,mixed>|WP_Error
     */
    private static function publish(array $args)
    {
        if (!self::dependenciesReady()) {
            return new WP_Error('oldies_reels_dependency_missing', 'Ana Oldies Social eklentisi etkin değil.');
        }

        if (empty($args['video_url']) || stripos((string)$args['video_url'], 'https://') !== 0) {
            return new WP_Error('missing_reel_video', 'Geçerli bir MP4 dosyası veya herkese açık HTTPS URL gereklidir.');
        }

        if (empty($args['caption'])) {
            return new WP_Error('empty_reel_caption', 'Reels açıklaması boş olamaz.');
        }

        $approvedAdminOverride = !empty($args['approved_admin_override']);

        $publisherArgs = [
            'video_url' => (string)$args['video_url'],
            'caption' => (string)$args['caption'],
            'topic' => (string)($args['topic'] ?? 'Oldies Radyo Reel'),
            'dry_run' => (bool)($args['dry_run'] ?? true),
            'live_request' => !(bool)($args['dry_run'] ?? true) && (self::livePublishingAllowed() || $approvedAdminOverride),
            'share_to_feed' => (bool)($args['share_to_feed'] ?? true),
            'metadata' => [
                'bridge_version' => self::VERSION,
                'idempotency_key' => (string)($args['idempotency_key'] ?? ''),
                'origin' => (string)($args['origin'] ?? 'bridge'),
            ],
        ];

        $audioId = self::sanitizeMetaId($args['audio_id'] ?? '');
        if ($audioId !== '') {
            $result = self::publishReelWithAudio($publisherArgs, [
                'audio_id' => $audioId,
                'audio_volume' => max(0, min(100, (int)($args['audio_volume'] ?? 100))),
                'video_volume' => max(0, min(100, (int)($args['video_volume'] ?? 12))),
            ], $approvedAdminOverride);
        } else {
            $result = self::publishReelDirect($publisherArgs, $approvedAdminOverride);
        }

        if (is_wp_error($result)) {
            return $result;
        }

        if (is_array($result)) {
            $result['idempotency_key'] = (string)($args['idempotency_key'] ?? '');
            $isConfirmedInstagramPublish = empty($publisherArgs['dry_run'])
                && !empty($result['instagram_media_id'])
                && strtoupper((string)($result['mode'] ?? '')) === 'LIVE';
            if ($isConfirmedInstagramPublish) {
                $finalMedia = self::getInstagramFinalMedia((string)$result['instagram_media_id']);
                if (is_wp_error($finalMedia)) {
                    $result['youtube'] = [
                        'success' => false,
                        'skipped' => true,
                        'reason' => 'waiting_final_instagram_media',
                    ];
                } else {
                    $youtubeArgs = $args;
                    $youtubeArgs['video_url'] = (string)$finalMedia['media_url'];
                    $youtubeArgs['dry_run'] = false;
                    $youtubeArgs['idempotency_key'] = 'instagram-media-' . (string)$result['instagram_media_id'];
                    $youtubeArgs['origin'] = 'instagram_published_final';
                    $youtubeArgs['instagram_media_id'] = (string)$result['instagram_media_id'];
                    $youtubeArgs['instagram_permalink'] = (string)$finalMedia['permalink'];
                    $result['instagram_final_media'] = $finalMedia;
                    $result['youtube'] = self::mirrorToYouTube($youtubeArgs);
                }
            } else {
                $result['youtube'] = [
                    'success' => false,
                    'skipped' => true,
                    'reason' => 'waiting_for_confirmed_instagram_publish',
                ];
            }
        }
        return $result;
    }

    /**
     * Legacy guard: raw draft videos must never be mirrored to YouTube.
     * A final Instagram Graph media URL is mandatory.
     *
     * @param array<string,mixed> $draft
     * @return array<string,mixed>
     */
    private static function syncApprovedDraftToYouTube(array $draft): array
    {
        unset($draft);
        return [
            'success' => false,
            'skipped' => true,
            'reason' => 'raw_draft_youtube_disabled',
        ];
    }
    /**
     * Mirror verified final Instagram media to the main Social Automation YouTube dispatcher.
     * YouTube failures are isolated and never turn an Instagram result into a failure.
     *
     * @param array<string,mixed> $args
     * @return array<string,mixed>
     */
    private static function mirrorToYouTube(array $args): array
    {
        $managerClass = '\\OldiesRadyo\\SocialAutomation\\Social\\SocialJobManager';
        if (!class_exists($managerClass)) {
            return ['success' => false, 'skipped' => true, 'error' => 'YouTube dispatcher unavailable.'];
        }

        $idempotencyKey = trim((string)($args['idempotency_key'] ?? ''));
        if ($idempotencyKey === '') {
            $idempotencyKey = hash('sha256', (string)$args['video_url'] . '|' . (string)($args['topic'] ?? ''));
        }

        $manager = new $managerClass();
        $job = $manager->createJob([
            'title' => (string)($args['topic'] ?? 'Oldies Radyo Reel'),
            'publication_mode' => 'social_only',
            'platforms' => ['youtube'],
            'content_type' => 'reel',
            'media_url' => (string)$args['video_url'],
            'description' => (string)$args['caption'],
            'youtube_visibility' => 'public',
            'dedupe_key' => 'reels-youtube|' . $idempotencyKey,
            'metadata' => [
                'source' => 'reels_bridge',
                'bridge_version' => self::VERSION,
                'idempotency_key' => $idempotencyKey,
                'origin' => sanitize_text_field((string)($args['origin'] ?? '')),
                'instagram_media_id' => self::sanitizeMetaId($args['instagram_media_id'] ?? ''),
                'instagram_permalink' => esc_url_raw((string)($args['instagram_permalink'] ?? '')),
            ],
        ]);

        if (is_wp_error($job)) {
            if ($job->get_error_code() === 'duplicate_job_detected') {
                return ['success' => true, 'skipped' => true, 'reason' => 'duplicate_guard'];
            }
            return ['success' => false, 'error' => $job->get_error_message()];
        }

        $processed = $manager->processJob($job, (bool)($args['dry_run'] ?? true));
        return [
            'success' => (bool)($processed['success'] ?? false),
            'dry_run' => (bool)($processed['dry_run'] ?? true),
            'job_id' => (int)($processed['job_id'] ?? 0),
            'status' => (string)($processed['status'] ?? ''),
            'result' => $processed['platform_results']['youtube'] ?? [],
            'source_origin' => sanitize_text_field((string)($args['origin'] ?? '')),
            'source_instagram_media_id' => self::sanitizeMetaId($args['instagram_media_id'] ?? ''),
            'source_instagram_permalink' => esc_url_raw((string)($args['instagram_permalink'] ?? '')),
            'source_final_media_url' => esc_url_raw((string)($args['video_url'] ?? '')),
        ];
    }

    /**
     * Store MP4 without invoking WordPress image/video metadata processing.
     * The file is still tightly validated, uniquely named, isolated and cleaned.
     *
     * @param array<string,mixed> $file
     * @return array{path:string,url:string,sha256:string,size:int}|WP_Error
     */
    private static function storeUploadedMp4(array $file)
    {
        $error = (int)($file['error'] ?? UPLOAD_ERR_NO_FILE);
        if ($error !== UPLOAD_ERR_OK) {
            return new WP_Error('reel_upload_error', self::uploadErrorMessage($error), ['status' => 400]);
        }

        $tmp = (string)($file['tmp_name'] ?? '');
        $name = sanitize_file_name((string)($file['name'] ?? 'reel.mp4'));
        $size = (int)($file['size'] ?? 0);

        if ($tmp === '' || !is_uploaded_file($tmp)) {
            return new WP_Error('invalid_reel_upload', 'Yüklenen MP4 dosyası doğrulanamadı.', ['status' => 400]);
        }
        if ($size < 1024 || $size > self::MAX_UPLOAD_BYTES) {
            return new WP_Error('invalid_reel_size', 'MP4 boyutu 1 KB ile 100 MB arasında olmalıdır.', ['status' => 413]);
        }
        if (strtolower((string)pathinfo($name, PATHINFO_EXTENSION)) !== 'mp4') {
            return new WP_Error('invalid_reel_extension', 'Yalnızca .mp4 uzantılı dosyalar kabul edilir.', ['status' => 415]);
        }

        $handle = fopen($tmp, 'rb');
        $header = is_resource($handle) ? (string)fread($handle, 64) : '';
        if (is_resource($handle)) {
            fclose($handle);
        }
        $ftypPosition = strpos($header, 'ftyp');
        if ($ftypPosition === false || $ftypPosition < 4 || $ftypPosition > 16) {
            return new WP_Error('invalid_reel_signature', 'Dosyanın MP4 imzası geçerli değil.', ['status' => 415]);
        }

        if (function_exists('finfo_open')) {
            $finfo = finfo_open(FILEINFO_MIME_TYPE);
            $mime = is_resource($finfo) || $finfo instanceof finfo ? (string)finfo_file($finfo, $tmp) : '';
            if ($finfo) {
                finfo_close($finfo);
            }
            $allowedMimes = ['video/mp4', 'application/mp4', 'application/octet-stream'];
            if ($mime !== '' && !in_array(strtolower($mime), $allowedMimes, true)) {
                return new WP_Error('invalid_reel_mime', 'Dosya içeriği MP4 olarak doğrulanamadı.', ['status' => 415]);
            }
        }

        $upload = wp_upload_dir(null, false);
        if (!empty($upload['error'])) {
            return new WP_Error('reel_upload_directory_error', (string)$upload['error'], ['status' => 500]);
        }

        $relative = self::UPLOAD_DIR . '/' . gmdate('Y/m');
        $directory = trailingslashit((string)$upload['basedir']) . $relative;
        $baseUrl = trailingslashit((string)$upload['baseurl']) . $relative;
        if (!wp_mkdir_p($directory)) {
            return new WP_Error('reel_upload_directory_create_failed', 'Reels yükleme dizini oluşturulamadı.', ['status' => 500]);
        }

        $safeBase = sanitize_file_name((string)pathinfo($name, PATHINFO_FILENAME));
        $safeBase = $safeBase !== '' ? $safeBase : 'oldies-reel';
        $filename = wp_unique_filename($directory, $safeBase . '-' . gmdate('Ymd-His') . '.mp4');
        $destination = trailingslashit($directory) . $filename;

        if (!move_uploaded_file($tmp, $destination)) {
            return new WP_Error('reel_upload_move_failed', 'MP4 güvenli yükleme dizinine taşınamadı.', ['status' => 500]);
        }
        @chmod($destination, 0644);

        return [
            'path' => $destination,
            'url' => trailingslashit($baseUrl) . rawurlencode($filename),
            'sha256' => (string)hash_file('sha256', $destination),
            'size' => (int)filesize($destination),
        ];
    }

    private static function resolveIdempotencyKey(WP_REST_Request $request, string $caption, string $videoUrl, ?array $stored): string
    {
        $header = self::sanitizeIdempotencyKey($request->get_header('x-idempotency-key'));
        $param = self::sanitizeIdempotencyKey($request->get_param('idempotency_key'));
        if ($header !== '') {
            return $header;
        }
        if ($param !== '') {
            return $param;
        }
        $contentHash = is_array($stored) ? (string)($stored['sha256'] ?? '') : hash('sha256', $videoUrl);
        return 'auto-' . substr(hash('sha256', $caption . '|' . $contentHash), 0, 48);
    }

    /**
     * @return true|WP_Error
     */
    private static function beginIdempotentRequest(string $key)
    {
        $transientKey = self::idempotencyTransientKey($key);
        $existing = get_transient($transientKey);
        if (is_array($existing)) {
            return new WP_Error(
                'duplicate_reel_request',
                'Bu Reels isteği daha önce alındı; mükerrer yayın engellendi.',
                ['status' => 409, 'previous' => $existing]
            );
        }
        set_transient($transientKey, ['status' => 'processing', 'started_at' => time()], 30 * MINUTE_IN_SECONDS);
        return true;
    }

    private static function completeIdempotentRequest(string $key, array $result): void
    {
        set_transient(self::idempotencyTransientKey($key), [
            'status' => 'complete',
            'mode' => (string)($result['mode'] ?? ''),
            'job_id' => (int)($result['job_id'] ?? 0),
            'container_id' => (string)($result['container_id'] ?? ''),
            'completed_at' => time(),
        ], 7 * DAY_IN_SECONDS);
    }

    private static function recordIdempotentFailure(string $key, WP_Error $error): void
    {
        set_transient(self::idempotencyTransientKey($key), [
            'status' => 'failed',
            'code' => $error->get_error_code(),
            'failed_at' => time(),
        ], 10 * MINUTE_IN_SECONDS);
    }

    private static function idempotencyTransientKey(string $key): string
    {
        return 'oldies_reels_idem_' . substr(hash('sha256', $key), 0, 40);
    }

    private static function saveLastResult(array $result, string $idempotencyKey, string $origin): void
    {
        update_option(self::LAST_RESULT_OPTION, [
            'recorded_at' => current_time('mysql', true),
            'origin' => $origin,
            'mode' => (string)($result['mode'] ?? ''),
            'job_id' => (int)($result['job_id'] ?? 0),
            'uuid' => (string)($result['uuid'] ?? ''),
            'container_id' => (string)($result['container_id'] ?? ''),
            'instagram_media_id' => (string)($result['instagram_media_id'] ?? ''),
            'permalink' => esc_url_raw((string)($result['permalink'] ?? '')),
            'video_url' => esc_url_raw((string)($result['video_url'] ?? '')),
            'idempotency_key' => self::sanitizeIdempotencyKey($idempotencyKey),
        ], false);
    }

    public static function cleanupExpiredFiles(): void
    {
        // SAFE1: destructive retention is disabled until durable delivery receipts
        // and verified recovery backups exist. Never delete queue records or MP4s
        // by age alone; terminal items remain available for explicit archive review.
        return;
    }

    /** @return array<string,mixed> */
    private static function defaultContentPolicy(): array
    {
        return [
            'daily_time' => '12:00',
            'timezone' => 'Europe/Istanbul',
            'maximum_daily_drafts' => 1,
            'minimum_sources' => 2,
            'minimum_score' => 80,
            'artist_repeat_days' => 14,
            'era_priority' => ['1980s', '1990s', '1970s', '1960s', '1950s'],
            'foreign_sources_only' => true,
            'approval_required' => true,
            'live_publish_default' => false,
        ];
    }

    /** @return array<string,mixed> */
    private static function getContentPolicy(): array
    {
        $stored = get_option(self::POLICY_OPTION, []);
        return array_merge(self::defaultContentPolicy(), is_array($stored) ? $stored : []);
    }

    /** @return array<int,array<string,mixed>> */
    private static function getQueue(): array
    {
        $queue = get_option(self::QUEUE_OPTION, []);
        return is_array($queue) ? array_values(array_filter($queue, 'is_array')) : [];
    }

    /** @param array<int,array<string,mixed>> $queue */
    private static function saveQueue(array $queue): void
    {
        // SAFE1: never silently truncate active, unresolved, or terminal-review items.
        update_option(self::QUEUE_OPTION, array_values($queue), false);
    }

    /** @param array<int,array<string,mixed>> $queue */
    private static function findDraftIndex(array $queue, string $draftId): ?int
    {
        foreach ($queue as $index => $draft) {
            if ($draftId !== '' && hash_equals((string)($draft['id'] ?? ''), $draftId)) {
                return $index;
            }
        }
        return null;
    }

    /** @return array<int,string> */
    private static function normalizeStringList($value, bool $urls): array
    {
        if (is_string($value)) {
            $decoded = json_decode($value, true);
            $value = is_array($decoded) ? $decoded : preg_split('/[\r\n,]+/', $value);
        }
        if (!is_array($value)) {
            return [];
        }

        $items = [];
        $hosts = [];
        foreach ($value as $raw) {
            $item = trim((string)$raw);
            if ($item === '') {
                continue;
            }
            if ($urls) {
                $item = esc_url_raw($item);
                $host = strtolower((string)wp_parse_url($item, PHP_URL_HOST));
                if ($item === '' || stripos($item, 'https://') !== 0 || !wp_http_validate_url($item) || $host === '' || str_ends_with($host, '.tr')) {
                    continue;
                }
                if (isset($hosts[$host])) {
                    continue;
                }
                $hosts[$host] = true;
            } else {
                $item = sanitize_text_field($item);
            }
            $items[] = $item;
        }
        return array_values(array_unique($items));
    }

    /** @return array<string,int> */
    private static function normalizeScoreBreakdown($value): array
    {
        if (is_string($value)) {
            $decoded = json_decode($value, true);
            $value = is_array($decoded) ? $decoded : [];
        }
        $value = is_array($value) ? $value : [];
        $limits = [
            'date_relevance' => 30,
            'audience_fit' => 25,
            'source_confidence' => 20,
            'visual_strength' => 15,
            'freshness' => 10,
        ];
        $scores = [];
        foreach ($limits as $key => $maximum) {
            $scores[$key] = max(0, min($maximum, (int)($value[$key] ?? 0)));
        }
        return $scores;
    }

    private static function dependenciesReady(): bool
    {
        $encryptionClass = '\\OldiesRadyo\\SocialAutomation\\Security\\Encryption';
        $settingsClass = '\\OldiesRadyo\\SocialAutomation\\Security\\SettingsManager';

        if (class_exists($encryptionClass, false) && class_exists($settingsClass, false)) {
            return true;
        }

        $baseDir = defined('OLDIES_SOCIAL_PLUGIN_DIR')
            ? trailingslashit((string)OLDIES_SOCIAL_PLUGIN_DIR)
            : (defined('WP_PLUGIN_DIR')
                ? trailingslashit(WP_PLUGIN_DIR) . 'oldies-radyo-social-automation/'
                : '');
        if ($baseDir === '') {
            return false;
        }

        $dependencies = [
            $encryptionClass => $baseDir . 'src/Security/Encryption.php',
            $settingsClass => $baseDir . 'src/Security/SettingsManager.php',
        ];
        foreach ($dependencies as $class => $file) {
            if (!class_exists($class, false) && is_readable($file)) {
                require_once $file;
            }
        }

        return class_exists($encryptionClass, false) && class_exists($settingsClass, false);
    }
    private static function settingsManager(): ?object
    {
        if (!self::dependenciesReady()) {
            return null;
        }
        $class = '\\OldiesRadyo\\SocialAutomation\\Security\\SettingsManager';
        return new $class();
    }

    private static function isLiveEnabled(): bool
    {
        return (bool)get_option(self::LIVE_OPTION, 0);
    }

    private static function livePublishingAllowed(): bool
    {
        $settings = self::settingsManager();
        return self::isLiveEnabled()
            && $settings !== null
            && $settings->isAutoPublishingEnabled()
            && !$settings->isDryRunMode();
    }

    private static function uploadErrorMessage(int $error): string
    {
        $messages = [
            UPLOAD_ERR_INI_SIZE => 'MP4 sunucunun yükleme boyutu sınırını aşıyor.',
            UPLOAD_ERR_FORM_SIZE => 'MP4 form yükleme boyutu sınırını aşıyor.',
            UPLOAD_ERR_PARTIAL => 'MP4 yalnızca kısmen yüklendi.',
            UPLOAD_ERR_NO_FILE => 'MP4 dosyası seçilmedi.',
            UPLOAD_ERR_NO_TMP_DIR => 'Sunucunun geçici yükleme dizini bulunmuyor.',
            UPLOAD_ERR_CANT_WRITE => 'MP4 sunucu diskine yazılamadı.',
            UPLOAD_ERR_EXTENSION => 'Bir sunucu eklentisi MP4 yüklemesini durdurdu.',
        ];
        return $messages[$error] ?? 'MP4 yüklemesi bilinmeyen bir hatayla durdu.';
    }
}

register_activation_hook(__FILE__, [Oldies_Radyo_Reels_Bridge::class, 'activate']);
register_deactivation_hook(__FILE__, [Oldies_Radyo_Reels_Bridge::class, 'deactivate']);
Oldies_Radyo_Reels_Bridge::boot();

