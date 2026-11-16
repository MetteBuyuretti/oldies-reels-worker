<?php
/**
 * High-Level YouTube Video Publisher with Duplicate Guards & Shorts Architecture.
 *
 * @package OldiesRadyo\SocialAutomation\YouTube
 */

declare(strict_types=1);

namespace OldiesRadyo\SocialAutomation\YouTube;

use OldiesRadyo\SocialAutomation\Social\SocialJob;
use OldiesRadyo\SocialAutomation\Database\SocialJobRepository;
use OldiesRadyo\SocialAutomation\Security\SettingsManager;
use WP_Error;

if (!defined('ABSPATH')) {
    exit;
}

class YouTubePublisher
{
    private YouTubeClient $client;
    private SocialJobRepository $repository;
    private SettingsManager $settingsManager;

    public function __construct(
        ?YouTubeClient $client = null,
        ?SocialJobRepository $repository = null,
        ?SettingsManager $settingsManager = null
    ) {
        $this->settingsManager = $settingsManager ?? new SettingsManager();
        $this->client = $client ?? new YouTubeClient($this->settingsManager);
        $this->repository = $repository ?? new SocialJobRepository();
    }

    public function getClient(): YouTubeClient
    {
        return $this->client;
    }

    /**
     * Publishes a SocialJob to YouTube or performs Dry Run simulation.
     *
     * @param SocialJob $job
     * @param bool $dryRun
     * @return array<string, mixed>|WP_Error
     */
    public function publish(SocialJob $job, bool $dryRun = true)
    {
        // 1. Duplicate Upload Guard
        if (!empty($job->getYoutubeVideoId())) {
            return new WP_Error(
                'youtube_duplicate_detected',
                sprintf(__('Bu iş daha önce YouTube\'a yüklenmiş (Video ID: %s). Duplicate engellendi.', 'oldies-radyo-social-automation'), $job->getYoutubeVideoId())
            );
        }

        $existing = $this->repository->findDuplicateYoutube($job->getUuid(), $job->getContentHash());
        if ($existing && !empty($existing['youtube_video_id'])) {
            return new WP_Error(
                'youtube_duplicate_detected',
                sprintf(__('Aynı içerik veya UUID ile eşleşen bir YouTube videosu zaten mevcut (Video ID: %s).', 'oldies-radyo-social-automation'), $existing['youtube_video_id'])
            );
        }

        // 2. Validate Media Path / URL
        $videoPath = $job->getMediaPath();
        if (empty($videoPath) || !file_exists($videoPath)) {
            // Check media URL if path not provided
            $mediaUrl = $job->getMediaUrl();
            if (empty($mediaUrl) && empty($videoPath)) {
                return new WP_Error('missing_media', __('YouTube yayını için video dosyası veya URL belirtilmedi.', 'oldies-radyo-social-automation'));
            }
        }

        // 3. Prepare Title, Description & Shorts Tags
        $title = trim($job->getTitle());
        if ($title === '') {
            $title = 'Oldies Radyo — Classic Vintage Hits';
        }

        $description = trim((string)$job->getDescription());
        if ($description === '') {
            $description = "Oldies Radyo — 7/24 Kesintisiz Nostalji ve Müzik Tarihi.\nDinle: https://oldiesradyo.com/";
        }

        $isShort = ($job->getContentType() === SocialJob::TYPE_REEL) || str_contains($title, '#Shorts') || str_contains($description, '#Shorts');
        if ($isShort && !str_contains($title, '#Shorts') && !str_contains($description, '#Shorts')) {
            $description .= "\n\n#Shorts #OldiesRadyo #VintageMusic";
        }

        $visibility = $job->getYoutubeVisibility();
        if (!in_array($visibility, ['public', 'unlisted', 'private'], true)) {
            $visibility = $this->settingsManager->getYoutubeDefaultVisibility();
        }

        // 4. Dry Run Guard
        if ($dryRun) {
            $simulatedVideoId = 'dry_run_yt_' . substr(md5($job->getUuid() . microtime()), 0, 11);
            $simulatedUrl = $isShort ? "https://www.youtube.com/shorts/{$simulatedVideoId}" : "https://www.youtube.com/watch?v={$simulatedVideoId}";
            $publishedAt = current_time('mysql', 1);

            $job->setYoutubeVideoId($simulatedVideoId);
            $job->setYoutubeUrl($simulatedUrl);
            $job->appendErrorLog("[DRY RUN] YouTube upload simulated successfully. Video ID: {$simulatedVideoId}, Visibility: {$visibility}");

            // Register to central video archive in dry run mode if requested
            if ($job->getPublicationMode() === SocialJob::MODE_SOCIAL_ARCHIVE) {
                $this->repository->saveToVideoArchive([
                    'video_id'      => $simulatedVideoId,
                    'title'         => $title,
                    'description'   => $description,
                    'youtube_url'   => $simulatedUrl,
                    'thumbnail_url' => "https://i.ytimg.com/vi/{$simulatedVideoId}/hqdefault.jpg",
                    'published_at'  => $publishedAt,
                    'source'        => 'dry_run',
                ]);
            }

            return [
                'success'      => true,
                'dry_run'      => true,
                'video_id'     => $simulatedVideoId,
                'youtube_url'  => $simulatedUrl,
                'published_at' => $publishedAt,
                'visibility'   => $visibility,
                'is_shorts'    => $isShort,
                'status'       => 'published',
            ];
        }

        // 5. Live Upload via YouTube Client
        $accessToken = $this->client->getValidAccessToken();
        if (is_wp_error($accessToken)) {
            return $accessToken;
        }

        $snippet = [
            'title'       => $title,
            'description' => $description,
            'tags'        => ['Oldies Radyo', 'Retro Music', 'Vintage Radio', $isShort ? 'Shorts' : 'Classic Hits'],
            'categoryId'  => '10', // Music
        ];

        $status = [
            'privacyStatus'           => $visibility,
            'selfDeclaredMadeForKids' => false,
        ];

        $uploadResult = $this->client->uploadVideo((string)$videoPath, $snippet, $status);
        if (is_wp_error($uploadResult)) {
            $job->appendErrorLog("[YOUTUBE ERROR] " . $uploadResult->get_error_message());
            return $uploadResult;
        }

        $realVideoId = (string)($uploadResult['id'] ?? '');
        $realUrl = $isShort ? "https://www.youtube.com/shorts/{$realVideoId}" : "https://www.youtube.com/watch?v={$realVideoId}";
        $publishedAt = current_time('mysql', 1);

        $job->setYoutubeVideoId($realVideoId);
        $job->setYoutubeUrl($realUrl);
        $job->appendErrorLog("[YOUTUBE SUCCESS] Uploaded successfully: {$realUrl}");

        // Register to central video archive if required
        if ($job->getPublicationMode() === SocialJob::MODE_SOCIAL_ARCHIVE) {
            $this->repository->saveToVideoArchive([
                'video_id'      => $realVideoId,
                'title'         => $title,
                'description'   => $description,
                'youtube_url'   => $realUrl,
                'thumbnail_url' => "https://i.ytimg.com/vi/{$realVideoId}/hqdefault.jpg",
                'published_at'  => $publishedAt,
                'source'        => 'job',
            ]);
        }

        return [
            'success'      => true,
            'dry_run'      => false,
            'video_id'     => $realVideoId,
            'youtube_url'  => $realUrl,
            'published_at' => $publishedAt,
            'visibility'   => $visibility,
            'is_shorts'    => $isShort,
            'status'       => 'published',
        ];
    }
}

