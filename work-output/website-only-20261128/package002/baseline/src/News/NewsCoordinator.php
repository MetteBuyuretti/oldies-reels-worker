<?php
/**
 * News Automation Workflow Coordinator.
 *
 * @package OldiesRadyo\SocialAutomation\News
 */

declare(strict_types=1);

namespace OldiesRadyo\SocialAutomation\News;

use OldiesRadyo\SocialAutomation\Security\SettingsManager;
use WP_Error;

if (!defined('ABSPATH')) {
    exit;
}

class NewsCoordinator
{
    private NewsRepository $repository;
    private SourceManager $sourceManager;
    private NewsVerifier $verifier;
    private ArticleGenerator $articleGenerator;
    private ImageCurator $imageCurator;
    private NewsPublisher $publisher;
    private SettingsManager $settingsManager;

    public function __construct(
        ?NewsRepository $repository = null,
        ?SourceManager $sourceManager = null,
        ?NewsVerifier $verifier = null,
        ?ArticleGenerator $articleGenerator = null,
        ?ImageCurator $imageCurator = null,
        ?NewsPublisher $publisher = null,
        ?SettingsManager $settingsManager = null
    ) {
        $this->repository = $repository ?? new NewsRepository();
        $this->sourceManager = $sourceManager ?? new SourceManager($this->repository);
        $this->verifier = $verifier ?? new NewsVerifier(null, $this->repository);
        $this->articleGenerator = $articleGenerator ?? new ArticleGenerator();
        $this->imageCurator = $imageCurator ?? new ImageCurator();
        $this->publisher = $publisher ?? new NewsPublisher($this->repository, $settingsManager);
        $this->settingsManager = $settingsManager ?? new SettingsManager();
    }

    /**
     * Executes the automatic news polling and ingestion cycle.
     */
    public function runScheduledCycle(): array
    {
        if (!$this->settingsManager->isNewsMonitoringEnabled()) {
            return [
                'status'  => 'skipped',
                'message' => __('Haber izleme (News Monitoring) devre dışı bırakılmış.', 'oldies-radyo-social-automation'),
            ];
        }

        // 1. Poll sources and ingest new articles
        $ingestResults = $this->sourceManager->pollAllSources();

        // 2. Process newly ingested pending articles
        $processed = [];
        if (!empty($ingestResults['ingested_ids'])) {
            foreach ($ingestResults['ingested_ids'] as $artId) {
                $res = $this->processArticle((int)$artId, false, false);
                $processed[] = [
                    'article_id' => $artId,
                    'result'     => is_wp_error($res) ? $res->get_error_message() : $res,
                ];
            }
        }

        return [
            'status'            => 'success',
            'ingestion'         => $ingestResults,
            'processed_count'   => count($processed),
            'processed_details' => $processed,
        ];
    }

    /**
     * Explicit manual editorial action to generate Turkish & English draft articles.
     * Generates drafts for both VERIFIED and NEEDS_REVIEW articles without auto-publishing.
     *
     * @param int $articleId
     * @return array<string, mixed>|WP_Error
     */
    public function generateDraft(int $articleId)
    {
        return $this->processArticle($articleId, false, true);
    }

    /**
     * Processes a single article: verify -> generate -> publish/draft.
     *
     * @param int $articleId
     * @param bool $forcePublish If true, forces WordPress publish status
     * @param bool $isManualDraft If true, manual draft action bypasses NEEDS_REVIEW block and generates drafts
     * @return array<string, mixed>|WP_Error
     */
    public function processArticle(int $articleId, bool $forcePublish = false, bool $isManualDraft = false)
    {
        $article = $this->repository->getArticleById($articleId);
        if (!$article) {
            return new WP_Error('article_not_found', __('Makale bulunamadı.', 'oldies-radyo-social-automation'));
        }

        // 1. Verification
        if ($article['status'] === 'VERIFIED') {
            $verification = [
                'status'                 => 'VERIFIED',
                'priority'               => $article['priority'] ?? 'NORMAL',
                'is_verified'            => true,
                'source_1'               => ['url' => $article['article_url'] ?? '', 'name' => $article['source_name'] ?? 'Primary Source'],
                'source_2'               => !empty($article['source_url_2']) ? ['url' => $article['source_url_2'], 'name' => $article['source_name_2'] ?? 'Secondary Source'] : null,
                'verified_facts'         => [],
                'notes'                  => $article['verification_notes'] ?? '',
                'requires_review_reason' => '',
            ];
        } elseif ($article['status'] === 'NEEDS_REVIEW' && $isManualDraft) {
            $verification = [
                'status'                 => 'NEEDS_REVIEW',
                'priority'               => $article['priority'] ?? 'NORMAL',
                'is_verified'            => false,
                'source_1'               => ['url' => $article['article_url'] ?? '', 'name' => $article['source_name'] ?? 'Primary Source'],
                'source_2'               => !empty($article['source_url_2']) ? ['url' => $article['source_url_2'], 'name' => $article['source_name_2'] ?? 'Secondary Source'] : null,
                'verified_facts'         => [],
                'notes'                  => $article['verification_notes'] ?? '',
                'requires_review_reason' => $article['verification_notes'] ?? '',
            ];
        } else {
            $verification = $this->verifier->verifyArticle($article);
            if (is_wp_error($verification)) {
                $this->repository->updateArticle($articleId, [
                    'status'        => 'NEEDS_REVIEW',
                    'error_message' => $verification->get_error_message(),
                ]);
                return $verification;
            }
        }

        // Handle NEEDS_REVIEW during automated / scheduled flow (non-manual, non-forcePublish)
        if ($verification['status'] === 'NEEDS_REVIEW' && !$isManualDraft && !$forcePublish) {
            $this->repository->updateArticle($articleId, [
                'status'             => 'NEEDS_REVIEW',
                'priority'           => $verification['priority'],
                'verification_notes' => $verification['notes'],
                'source_url_2'       => $verification['source_2']['url'] ?? null,
                'source_name_2'      => $verification['source_2']['name'] ?? null,
            ]);

            return [
                'status'                 => 'NEEDS_REVIEW',
                'article_id'             => $articleId,
                'message'                => __('Haber en az 2 kaynakla doğrulanamadı veya uyuşmazlık var. İnceleme kuyruğuna alındı.', 'oldies-radyo-social-automation'),
                'requires_review_reason' => $verification['requires_review_reason'] ?? '',
                'notes'                  => $verification['notes'] ?? '',
            ];
        }

        // Update evidence and verification details in DB
        $this->repository->updateArticle($articleId, [
            'priority'           => $verification['priority'],
            'verification_notes' => $verification['notes'] ?? null,
            'source_url_2'       => $verification['source_2']['url'] ?? null,
            'source_name_2'      => $verification['source_2']['name'] ?? null,
        ]);

        // 2. Generate original TR & EN content (or reuse existing if force-publishing already drafted content)
        if ($forcePublish && !empty($article['tr_title']) && !empty($article['tr_content']) && !empty($article['en_title']) && !empty($article['en_content'])) {
            $dualContent = [
                'tr_title'     => $article['tr_title'],
                'tr_excerpt'   => $article['tr_excerpt'] ?? '',
                'tr_content'   => $article['tr_content'],
                'en_title'     => $article['en_title'],
                'en_excerpt'   => $article['en_excerpt'] ?? '',
                'en_content'   => $article['en_content'],
                'tags'         => [],
                'image_prompt' => '',
            ];
        } else {
            $dualContent = $this->articleGenerator->generateDualArticles($article, $verification);
            if (is_wp_error($dualContent)) {
                $this->repository->updateArticle($articleId, [
                    'error_message' => sprintf(__('Makale üretimi başarısız: %s', 'oldies-radyo-social-automation'), $dualContent->get_error_message()),
                ]);
                return $dualContent;
            }
        }

        // 3. Curate / Generate Visual
        $imageId = (!empty($article['featured_image_id']) && (int)$article['featured_image_id'] > 0)
            ? (int)$article['featured_image_id']
            : null;

        if (!$imageId && !empty($dualContent['image_prompt'])) {
            $visual = $this->imageCurator->curateVisual($article, $dualContent['image_prompt']);
            if (!is_wp_error($visual) && !empty($visual['attachment_id'])) {
                $imageId = (int)$visual['attachment_id'];
            }
        }

        // 4. Publish / Draft to WordPress
        // If isManualDraft is true, forcePublish is false, ensuring status is always draft
        $publishResult = $this->publisher->publishArticles($articleId, $dualContent, $verification, $imageId, $forcePublish);
        if (is_wp_error($publishResult)) {
            $this->repository->updateArticle($articleId, [
                'error_message' => sprintf(__('WordPress işlemi başarısız: %s', 'oldies-radyo-social-automation'), $publishResult->get_error_message()),
            ]);
            return $publishResult;
        }

        $finalStatus = ($verification['status'] === 'NEEDS_REVIEW' && !$forcePublish)
            ? 'NEEDS_REVIEW'
            : ($isManualDraft ? 'DRAFT' : ($publishResult['published'] ? 'PUBLISHED' : 'DRAFT'));

        return [
            'status'                 => $finalStatus,
            'post_status'            => $publishResult['status'],
            'published'              => $publishResult['published'],
            'tr_post_id'             => $publishResult['tr_post_id'],
            'en_post_id'             => $publishResult['en_post_id'],
            'tr_url'                 => $publishResult['tr_url'],
            'en_url'                 => $publishResult['en_url'],
            'tr_title'               => $dualContent['tr_title'],
            'tr_excerpt'             => $dualContent['tr_excerpt'] ?? '',
            'en_title'               => $dualContent['en_title'],
            'en_excerpt'             => $dualContent['en_excerpt'] ?? '',
            'article_id'             => $articleId,
            'is_verified'            => $verification['status'] === 'VERIFIED',
            'requires_review_reason' => $verification['requires_review_reason'] ?? '',
            'notes'                  => $verification['notes'] ?? '',
        ];
    }

    /**
     * Rejects an article.
     */
    public function rejectArticle(int $articleId): bool
    {
        return $this->repository->updateArticle($articleId, [
            'status' => 'REJECTED',
        ]);
    }

    // Getters
    public function getRepository(): NewsRepository { return $this->repository; }
    public function getSourceManager(): SourceManager { return $this->sourceManager; }
    public function getVerifier(): NewsVerifier { return $this->verifier; }
    public function getArticleGenerator(): ArticleGenerator { return $this->articleGenerator; }
    public function getImageCurator(): ImageCurator { return $this->imageCurator; }
    public function getPublisher(): NewsPublisher { return $this->publisher; }
}
