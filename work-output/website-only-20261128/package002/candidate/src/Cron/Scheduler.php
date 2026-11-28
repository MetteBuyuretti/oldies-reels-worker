<?php
/**
 * Cron Scheduling and Background Automation Engine for Social & News Modules.
 *
 * @package OldiesRadyo\SocialAutomation\Cron
 */

declare(strict_types=1);

namespace OldiesRadyo\SocialAutomation\Cron;

use OldiesRadyo\SocialAutomation\Instagram\TokenManager;
use OldiesRadyo\SocialAutomation\Instagram\Publisher;
use OldiesRadyo\SocialAutomation\AI\ContentGenerator;
use OldiesRadyo\SocialAutomation\Security\SettingsManager;
use OldiesRadyo\SocialAutomation\Database\JobRepository;
use OldiesRadyo\SocialAutomation\Video\VideoRenderer;
use OldiesRadyo\SocialAutomation\Video\VideoJob;
use OldiesRadyo\SocialAutomation\News\NewsCoordinator;
use OldiesRadyo\SocialAutomation\Maintenance\RetentionCleaner;
use OldiesRadyo\SocialAutomation\Etsy\ProductSyncService;
use WP_Error;

if (!defined('ABSPATH')) {
    exit;
}

class Scheduler
{
    private TokenManager $tokenManager;
    private Publisher $publisher;
    private ContentGenerator $contentGenerator;
    private SettingsManager $settingsManager;
    private JobRepository $jobRepository;
    private ?VideoRenderer $videoRenderer;
    private ?NewsCoordinator $newsCoordinator;
    private RetentionCleaner $retentionCleaner;
    private ?ProductSyncService $etsyProductSync;

    public const CRON_DAILY_POST = 'oldies_social_daily_post_cron';
    public const CRON_TOKEN_HEALTH = 'oldies_social_token_health_cron';
    public const CRON_CLEANUP_HOOK = 'oldies_social_delayed_cleanup_hook';
    public const CRON_VIDEO_CLEANUP_HOOK = 'oldies_social_delayed_video_cleanup_hook';
    public const CRON_VIDEO_PERIODIC_CLEANUP = 'oldies_social_video_periodic_cleanup_cron';
    public const CRON_ASYNC_VIDEO_RENDER = 'oldies_social_async_video_render_hook';
    public const CRON_NEWS_SOURCE_CHECK = 'oldies_news_check_sources_cron';
    public const CRON_RETENTION_CLEANUP = 'oldies_social_retention_cleanup_cron';
    public const CRON_ETSY_PRODUCT_SYNC = 'oldies_etsy_product_sync_cron';

    public const TRANSIENT_LOCK = 'oldies_social_cron_lock';
    public const TRANSIENT_NEWS_LOCK = 'oldies_news_cron_lock';
    public const TRANSIENT_ETSY_LOCK = 'oldies_etsy_product_sync_lock';

    public function __construct(
        ?TokenManager $tokenManager = null,
        ?Publisher $publisher = null,
        ?ContentGenerator $contentGenerator = null,
        ?SettingsManager $settingsManager = null,
        ?JobRepository $jobRepository = null,
        ?VideoRenderer $videoRenderer = null,
        ?NewsCoordinator $newsCoordinator = null,
        ?RetentionCleaner $retentionCleaner = null,
        ?ProductSyncService $etsyProductSync = null
    ) {
        $this->settingsManager = $settingsManager ?? new SettingsManager();
        $this->tokenManager = $tokenManager ?? new TokenManager(null, $this->settingsManager);
        $this->publisher = $publisher ?? new Publisher(null, $this->tokenManager, null, null, $this->settingsManager);
        $this->contentGenerator = $contentGenerator ?? new ContentGenerator();
        $this->jobRepository = $jobRepository ?? new JobRepository();
        $this->videoRenderer = $videoRenderer;
        $this->newsCoordinator = $newsCoordinator;
        $this->retentionCleaner = $retentionCleaner ?? new RetentionCleaner($this->jobRepository, null, $this->settingsManager);
        $this->etsyProductSync = $etsyProductSync;
    }

    public function init(): void
    {
        add_filter('cron_schedules', [$this, 'registerCustomCronIntervals']);

        add_action(self::CRON_DAILY_POST, [$this, 'handleDailyPostExecution']);
        add_action(self::CRON_TOKEN_HEALTH, [$this, 'handleTokenHealthCheck']);
        add_action(self::CRON_CLEANUP_HOOK, [$this, 'handleDelayedMediaCleanup'], 10, 1);
        add_action(self::CRON_VIDEO_CLEANUP_HOOK, [$this, 'handleDelayedVideoCleanup'], 10, 1);
        add_action(self::CRON_VIDEO_PERIODIC_CLEANUP, [$this, 'handleVideoPeriodicCleanup']);
        add_action(self::CRON_ASYNC_VIDEO_RENDER, [$this, 'handleAsyncVideoRender'], 10, 1);

        // News Automation Cron Hook
        add_action(self::CRON_NEWS_SOURCE_CHECK, [$this, 'handleNewsSourceCheckExecution']);
        add_action(self::CRON_RETENTION_CLEANUP, [$this, 'handleRetentionCleanup']);
        add_action(self::CRON_ETSY_PRODUCT_SYNC, [$this, 'handleEtsyProductSync']);
    }

    /**
     * Registers 15-minute custom cron schedule.
     *
     * @param array<string, mixed> $schedules
     * @return array<string, mixed>
     */
    public function registerCustomCronIntervals(array $schedules): array
    {
        $schedules['oldies_5_minutes'] = [
            'interval' => 300,
            'display'  => __('Her 5 Dakikada Bir — Etsy Product Sync (Oldies Radyo)', 'oldies-radyo-social-automation'),
        ];
        $schedules['oldies_15_minutes'] = [
            'interval' => 900,
            'display'  => __('Her 15 Dakikada Bir (Oldies Radyo)', 'oldies-radyo-social-automation'),
        ];
        return $schedules;
    }

    /**
     * Sets up scheduled cron events upon plugin activation or settings update.
     */
    public function scheduleDefaultEvents(): void
    {
        // 1. Daily Token Health Check (Runs every 24 hours)
        if (!wp_next_scheduled(self::CRON_TOKEN_HEALTH)) {
            wp_schedule_event(time() + 3600, 'daily', self::CRON_TOKEN_HEALTH);
        }

        // 2. Video Temp Files Periodic Cleanup (Runs hourly)
        if (!wp_next_scheduled(self::CRON_VIDEO_PERIODIC_CLEANUP)) {
            wp_schedule_event(time() + 1800, 'hourly', self::CRON_VIDEO_PERIODIC_CLEANUP);
        }

        // 3. News Sources 15-Minute Monitoring Check
        if (!wp_next_scheduled(self::CRON_NEWS_SOURCE_CHECK)) {
            wp_schedule_event(time() + 300, 'oldies_15_minutes', self::CRON_NEWS_SOURCE_CHECK);
        }

        // 4. Database retention cleanup (daily, lightweight)
        if (!wp_next_scheduled(self::CRON_RETENTION_CLEANUP)) {
            wp_schedule_event(time() + 2700, 'daily', self::CRON_RETENTION_CLEANUP);
        }

        // 5. Etsy Product listing detection — separate isolated pipeline.
        if ($this->etsyProductSync && !wp_next_scheduled(self::CRON_ETSY_PRODUCT_SYNC)) {
            wp_schedule_event(time() + 180, 'oldies_5_minutes', self::CRON_ETSY_PRODUCT_SYNC);
        }

        // 6. Daily Automatic Post (if enabled)
        $this->rescheduleDailyPost();
    }

    /**
     * Reschedules daily post based on user-selected time in Europe/Istanbul timezone.
     */
    public function rescheduleDailyPost(): void
    {
        wp_clear_scheduled_hook(self::CRON_DAILY_POST);

        if (!$this->settingsManager->isAutoDailyPostEnabled()) {
            return;
        }

        $timeStr = $this->settingsManager->getDailyPostTime(); // e.g. "10:00"
        $parts = explode(':', $timeStr);
        $hour = isset($parts[0]) ? (int)$parts[0] : 10;
        $minute = isset($parts[1]) ? (int)$parts[1] : 0;

        // Calculate next occurrence in Europe/Istanbul timezone
        $tz = new \DateTimeZone('Europe/Istanbul');
        $targetDate = new \DateTime('now', $tz);
        $targetDate->setTime($hour, $minute, 0);

        $nowTz = new \DateTime('now', $tz);
        if ($targetDate <= $nowTz) {
            $targetDate->modify('+1 day');
        }

        $timestampGmt = $targetDate->getTimestamp();
        wp_schedule_event($timestampGmt, 'daily', self::CRON_DAILY_POST);
    }

    /**
     * Clears all scheduled cron hooks.
     */
    public function clearScheduledEvents(): void
    {
        wp_clear_scheduled_hook(self::CRON_DAILY_POST);
        wp_clear_scheduled_hook(self::CRON_TOKEN_HEALTH);
        wp_clear_scheduled_hook(self::CRON_VIDEO_PERIODIC_CLEANUP);
        wp_clear_scheduled_hook(self::CRON_ASYNC_VIDEO_RENDER);
        wp_clear_scheduled_hook(self::CRON_NEWS_SOURCE_CHECK);
        wp_clear_scheduled_hook(self::CRON_RETENTION_CLEANUP);
        wp_clear_scheduled_hook(self::CRON_ETSY_PRODUCT_SYNC);
    }

    /**
     * Handles Periodic News Source Check & Ingestion Cron (Runs every 10-15 mins).
     */
    public function handleNewsSourceCheckExecution(): void
    {
        // Concurrency Guard: prevent simultaneous runs
        if (get_transient(self::TRANSIENT_NEWS_LOCK)) {
            return;
        }
        set_transient(self::TRANSIENT_NEWS_LOCK, 1, 600); // 10 mins lock

        try {
            if (!$this->newsCoordinator) {
                $this->newsCoordinator = new NewsCoordinator(null, null, null, null, null, null, $this->settingsManager);
            }

            $this->newsCoordinator->runScheduledCycle();
        } catch (\Throwable $e) {
            // Fixed diagnostic fields only: never log messages, URLs or credentials.
            error_log(sprintf(
                'Oldies news cron failed [%s] at %s:%d',
                get_class($e),
                basename($e->getFile()),
                $e->getLine()
            ));
        } finally {
            delete_transient(self::TRANSIENT_NEWS_LOCK);
        }
    }

    /**
     * Handles Asynchronous Video Render Execution Hook.
     *
     * @param array<string, mixed> $renderOptions
     */
    public function handleAsyncVideoRender(array $renderOptions): void
    {
        if (empty($renderOptions['job_uuid'])) {
            return;
        }

        $uuid = (string)$renderOptions['job_uuid'];
        $job = VideoJob::findByUuid($this->jobRepository, $uuid);
        if (!$job) {
            return;
        }

        // Concurrency guard: Only run if job is still in PENDING state
        if ($job->getStatus() !== VideoJob::STATUS_PENDING) {
            return;
        }

        $lockKey = 'oldies_async_video_lock_' . md5($uuid);
        if (get_transient($lockKey)) {
            return;
        }
        set_transient($lockKey, 1, 600); // 10 mins transient lock

        try {
            if (!$this->videoRenderer || !$this->videoRenderer->isAvailable()) {
                $job->markFailed('ffmpeg_unavailable', __('Bu sunucuda yerel video render desteklenmiyor.', 'oldies-radyo-social-automation'));
                return;
            }

            $renderOptions['job_uuid'] = $uuid;
            $renderOptions['skip_job_creation'] = true;

            $result = $this->videoRenderer->render($renderOptions);

            if (is_wp_error($result)) {
                $job->markFailed($result->get_error_code(), $result->get_error_message());
            } elseif (is_array($result)) {
                $refetchedJob = VideoJob::findByUuid($this->jobRepository, $uuid);
                if ($refetchedJob && $refetchedJob->getStatus() !== VideoJob::STATUS_SUCCESS) {
                    $refetchedJob->markSuccess($result);
                }
            }
        } catch (\Throwable $e) {
            $job->markFailed('uncaught_render_exception', $e->getMessage());
        } finally {
            delete_transient($lockKey);
        }
    }

    /**
     * Handles Daily Automated Post Execution.
     */
    public function handleDailyPostExecution(): void
    {
        // Check concurrency lock (prevent duplicate runs within 15 minutes)
        if (get_transient(self::TRANSIENT_LOCK)) {
            return;
        }
        set_transient(self::TRANSIENT_LOCK, 1, 900); // 15 mins

        try {
            // Safety Check: Token Health
            if (!$this->settingsManager->isTokenHealthy()) {
                $this->jobRepository->createJob([
                    'type'          => 'cron_ai',
                    'status'        => 'FAILED',
                    'error_code'    => 'unhealthy_token',
                    'error_message' => sprintf(__('Instagram token doğrulanamadığı için günlük otomatik yayın iptal edildi: %s', 'oldies-radyo-social-automation'), $this->settingsManager->getTokenError()),
                ]);
                delete_transient(self::TRANSIENT_LOCK);
                return;
            }

            // Safety Check: Master switches
            $autoPublishEnabled = $this->settingsManager->isAutoPublishingEnabled();
            $dryRunMode = $this->settingsManager->isDryRunMode();

            // 1. Generate Music History Content with Responses API Web Search
            $eraFocus = $this->settingsManager->getMusicEraFocus();
            $content = $this->contentGenerator->generateContent('', $eraFocus);

            if (is_wp_error($content)) {
                $this->jobRepository->createJob([
                    'type'          => 'cron_ai',
                    'status'        => 'FAILED',
                    'error_code'    => $content->get_error_code(),
                    'error_message' => sprintf(__('Otomatik içerik üretimi başarısız: %s', 'oldies-radyo-social-automation'), $content->get_error_message()),
                ]);
                delete_transient(self::TRANSIENT_LOCK);
                return;
            }

            $metadata = [
                'verified_fact'       => $content['verified_fact'] ?? '',
                'sources_verified'    => $content['sources_verified'] ?? false,
                'verification_status' => $content['verification_status'] ?? 'unverified',
                'source_1_evidence'   => $content['source_1_evidence'] ?? '',
                'source_2_evidence'   => $content['source_2_evidence'] ?? '',
            ];

            // 2. Check Verification Confidence & Needs Review Rule
            if ($content['needs_review']) {
                $this->jobRepository->createJob([
                    'type'           => 'cron_ai',
                    'status'         => 'NEEDS_REVIEW',
                    'topic'          => $content['topic'],
                    'caption'        => $content['caption'],
                    'source_url_1'   => $content['source_url_1'] ?? null,
                    'source_url_2'   => $content['source_url_2'] ?? null,
                    'source_title_1' => $content['source_title_1'] ?? null,
                    'source_title_2' => $content['source_title_2'] ?? null,
                    'metadata'       => $metadata,
                    'error_code'     => 'dual_source_unverified',
                    'error_message'  => sprintf(__('Kaynak doğrulama eşiği (%s). İnceleme kuyruğuna alındı.', 'oldies-radyo-social-automation'), $content['review_reason']),
                ]);
                delete_transient(self::TRANSIENT_LOCK);
                return;
            }

            // 3. Generate Matching Retro Visual
            $imagePrompt = !empty($content['image_prompt']) ? $content['image_prompt'] : $content['topic'];
            $imageFile = $this->contentGenerator->generateAndComposeVisual($imagePrompt, $content['image_headline']);

            if (is_wp_error($imageFile)) {
                $this->jobRepository->createJob([
                    'type'           => 'cron_ai',
                    'status'         => 'FAILED',
                    'topic'          => $content['topic'],
                    'caption'        => $content['caption'],
                    'source_url_1'   => $content['source_url_1'] ?? null,
                    'source_url_2'   => $content['source_url_2'] ?? null,
                    'source_title_1' => $content['source_title_1'] ?? null,
                    'source_title_2' => $content['source_title_2'] ?? null,
                    'metadata'       => $metadata,
                    'error_code'     => $imageFile->get_error_code(),
                    'error_message'  => sprintf(__('Görsel üretimi başarısız: %s', 'oldies-radyo-social-automation'), $imageFile->get_error_message()),
                ]);
                delete_transient(self::TRANSIENT_LOCK);
                return;
            }

            // 4. Publish / Dry-Run Pipeline (Cron cannot bypass master autoPublishEnabled switch)
            $this->publisher->publishInstagramImage([
                'image_path'     => $imageFile,
                'caption'        => $content['caption'],
                'topic'          => $content['topic'],
                'type'           => 'cron_ai',
                'source_url_1'   => $content['source_url_1'] ?? null,
                'source_url_2'   => $content['source_url_2'] ?? null,
                'source_title_1' => $content['source_title_1'] ?? null,
                'source_title_2' => $content['source_title_2'] ?? null,
                'metadata'       => $metadata,
                'dry_run'        => $dryRunMode || !$autoPublishEnabled,
                'live_request'   => $autoPublishEnabled && !$dryRunMode,
            ]);
        } finally {
            delete_transient(self::TRANSIENT_LOCK);
        }
    }

    /**
     * Handles Daily Token Health Check Cron.
     */
    public function handleTokenHealthCheck(): void
    {
        $this->tokenManager->runDailyHealthCheck();
    }

    /**
     * Handles Delayed Media Cleanup Hook.
     */
    public function handleDelayedMediaCleanup(int $attachmentId): void
    {
        if ($attachmentId > 0 && $this->settingsManager->isDeleteTempMediaEnabled()) {
            $isOldiesMedia = get_post_meta($attachmentId, '_oldies_social_temp_media', true);
            if (!empty($isOldiesMedia)) {
                wp_delete_attachment($attachmentId, true);
            }
        }
    }

    /**
     * Handles Delayed Video File Cleanup Hook.
     */
    public function handleDelayedVideoCleanup(string $filePath): void
    {
        if (!empty($filePath) && @file_exists($filePath)) {
            $tempDir = sys_get_temp_dir();
            $realTemp = realpath($tempDir) ?: $tempDir;
            $realFile = realpath($filePath) ?: $filePath;

            // Verify file is inside system temp directory
            if (str_starts_with($realFile, $realTemp)) {
                @unlink($filePath);
            }
        }
    }

    /**
     * Periodic hourly cleanup for any lingering oldies video temp files older than 60 minutes.
     */
    public function handleVideoPeriodicCleanup(): void
    {
        $tempDir = sys_get_temp_dir();
        $patterns = [
            $tempDir . '/oldies_render_*.mp4',
            $tempDir . '/oldies_txt_*.txt',
            $tempDir . '/oldies_scene_bg_*.jpg',
            $tempDir . '/oldies_safe_img_*.jpg',
            $tempDir . '/oldies_safe_img_*.png',
            $tempDir . '/oldies_safe_img_*.webp',
            $tempDir . '/oldies_safe_audio_*.mp3',
            $tempDir . '/oldies_safe_audio_*.wav',
        ];

        $now = time();
        foreach ($patterns as $pattern) {
            $files = glob($pattern);
            if (!empty($files)) {
                foreach ($files as $file) {
                    if (is_file($file) && ($now - filemtime($file)) > 3600) {
                        @unlink($file);
                    }
                }
            }
        }
    }


    /**
     * Detects new/updated Etsy listings without touching the MUSIC/RADIO pipeline.
     * First run establishes a baseline so installing v1.7.1 does not render the
     * entire historic shop. Review/live publishing switches remain OFF by default.
     */
    public function handleEtsyProductSync(): void
    {
        if (!$this->etsyProductSync || !$this->settingsManager->isEtsyProductSyncEnabled()) {
            return;
        }
        if (get_transient(self::TRANSIENT_ETSY_LOCK)) {
            return;
        }
        set_transient(self::TRANSIENT_ETSY_LOCK, 1, 240);
        try {
            $this->etsyProductSync->runScheduledSync();
        } catch (\Throwable $e) {
            // Keep Etsy failures isolated: never interrupt News/Reels/MUSIC cron.
        } finally {
            delete_transient(self::TRANSIENT_ETSY_LOCK);
        }
    }

    /**
     * Daily DB retention cleanup. Heavy media files are handled by the existing
     * short-lived video cleanup; this pass only prunes stale history/metadata.
     */
    public function handleRetentionCleanup(): void
    {
        try {
            $this->retentionCleaner->run();
        } catch (\Throwable $e) {
            // Never allow maintenance to interrupt publishing/news cron flows.
        }
    }

}
