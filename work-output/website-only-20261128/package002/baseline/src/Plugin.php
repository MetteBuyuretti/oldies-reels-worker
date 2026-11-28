<?php
/**
 * Main Plugin Bootstrap Class for Social, Video & News Automation.
 *
 * @package OldiesRadyo\SocialAutomation
 */

declare(strict_types=1);

namespace OldiesRadyo\SocialAutomation;

use OldiesRadyo\SocialAutomation\Database\Schema;
use OldiesRadyo\SocialAutomation\Database\JobRepository;
use OldiesRadyo\SocialAutomation\Security\SettingsManager;
use OldiesRadyo\SocialAutomation\Security\Encryption;
use OldiesRadyo\SocialAutomation\Security\SsrfProtection;
use OldiesRadyo\SocialAutomation\Security\Authentication;
use OldiesRadyo\SocialAutomation\Instagram\Client as InstagramClient;
use OldiesRadyo\SocialAutomation\Instagram\TokenManager;
use OldiesRadyo\SocialAutomation\Instagram\Publisher as InstagramPublisher;
use OldiesRadyo\SocialAutomation\Media\ImageProcessor;
use OldiesRadyo\SocialAutomation\Media\MediaManager;
use OldiesRadyo\SocialAutomation\Media\ImageCompositor;
use OldiesRadyo\SocialAutomation\AI\OpenAIClient;
use OldiesRadyo\SocialAutomation\AI\ContentGenerator;
use OldiesRadyo\SocialAutomation\Video\FfmpegManager;
use OldiesRadyo\SocialAutomation\Video\SceneBuilder;
use OldiesRadyo\SocialAutomation\Video\VideoRenderer;
use OldiesRadyo\SocialAutomation\News\NewsRepository;
use OldiesRadyo\SocialAutomation\News\SourceManager;
use OldiesRadyo\SocialAutomation\News\NewsVerifier;
use OldiesRadyo\SocialAutomation\News\ArticleGenerator;
use OldiesRadyo\SocialAutomation\News\ImageCurator;
use OldiesRadyo\SocialAutomation\News\NewsPublisher;
use OldiesRadyo\SocialAutomation\News\NewsCoordinator;
use OldiesRadyo\SocialAutomation\Cron\Scheduler;
use OldiesRadyo\SocialAutomation\Rest\RestController;
use OldiesRadyo\SocialAutomation\Admin\AdminController;
use OldiesRadyo\SocialAutomation\Database\SocialJobRepository;
use OldiesRadyo\SocialAutomation\Social\SocialJobManager;
use OldiesRadyo\SocialAutomation\YouTube\YouTubeClient;
use OldiesRadyo\SocialAutomation\YouTube\YouTubePublisher;
use OldiesRadyo\SocialAutomation\Facebook\FacebookClient;
use OldiesRadyo\SocialAutomation\Facebook\FacebookPublisher;
use OldiesRadyo\SocialAutomation\Archive\VideoArchiveManager;
use OldiesRadyo\SocialAutomation\Instagram\InstagramShopClient;
use OldiesRadyo\SocialAutomation\Instagram\InstagramShopPublisher;
use OldiesRadyo\SocialAutomation\Maintenance\RetentionCleaner;
use OldiesRadyo\SocialAutomation\Etsy\EtsyBridgeAdapter;
use OldiesRadyo\SocialAutomation\Etsy\EtsyProductRepository;
use OldiesRadyo\SocialAutomation\Etsy\ProductSceneBuilder;
use OldiesRadyo\SocialAutomation\Etsy\ProductSyncService;
use OldiesRadyo\SocialAutomation\Etsy\EtsyProductDistributionService;
use OldiesRadyo\SocialAutomation\Pinterest\PinterestClient;
use OldiesRadyo\SocialAutomation\Pinterest\PinterestPublisher;
use OldiesRadyo\SocialAutomation\Admin\EtsyProductAdmin;

if (!defined('ABSPATH')) {
    exit;
}

class Plugin
{
    private static ?Plugin $instance = null;

    private Schema $schema;
    private JobRepository $jobRepository;
    private Encryption $encryption;
    private SettingsManager $settingsManager;
    private SsrfProtection $ssrfProtection;
    private Authentication $authentication;
    private InstagramClient $instagramClient;
    private TokenManager $tokenManager;
    private ImageProcessor $imageProcessor;
    private MediaManager $mediaManager;
    private ImageCompositor $imageCompositor;
    private InstagramPublisher $instagramPublisher;
    private OpenAIClient $openAIClient;
    private ContentGenerator $contentGenerator;
    private FfmpegManager $ffmpegManager;
    private SceneBuilder $sceneBuilder;
    private VideoRenderer $videoRenderer;

    // News Automation Components
    private NewsRepository $newsRepository;
    private SourceManager $sourceManager;
    private NewsVerifier $newsVerifier;
    private ArticleGenerator $articleGenerator;
    private ImageCurator $imageCurator;
    private NewsPublisher $newsPublisher;
    private NewsCoordinator $newsCoordinator;
    // Social Distribution & Video Archive Components
    private SocialJobRepository $socialJobRepository;
    private YouTubeClient $youtubeClient;
    private YouTubePublisher $youtubePublisher;
    private FacebookClient $facebookClient;
    private FacebookPublisher $facebookPublisher;
    private VideoArchiveManager $videoArchiveManager;
    private SocialJobManager $socialJobManager;
    private InstagramShopClient $instagramShopClient;
    private InstagramShopPublisher $instagramShopPublisher;

    // Isolated ETSY_PRODUCT pipeline components
    private EtsyBridgeAdapter $etsyBridgeAdapter;
    private EtsyProductRepository $etsyProductRepository;
    private ProductSceneBuilder $etsyProductSceneBuilder;
    private ProductSyncService $etsyProductSyncService;
    private PinterestClient $pinterestClient;
    private PinterestPublisher $pinterestPublisher;
    private EtsyProductDistributionService $etsyProductDistributionService;
    private EtsyProductAdmin $etsyProductAdmin;

    private Scheduler $scheduler;
    private RestController $restController;
    private AdminController $adminController;

    private bool $initialized = false;

    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct()
    {
        $this->schema = new Schema();
        $this->jobRepository = new JobRepository();
        $this->encryption = new Encryption();
        $this->settingsManager = new SettingsManager($this->encryption);
        $this->ssrfProtection = new SsrfProtection();
        $this->authentication = new Authentication($this->settingsManager);
        
        $this->instagramClient = new InstagramClient($this->settingsManager);
        $this->tokenManager = new TokenManager($this->instagramClient, $this->settingsManager);
        
        $this->imageProcessor = new ImageProcessor();
        $this->mediaManager = new MediaManager($this->imageProcessor, $this->settingsManager);
        $this->imageCompositor = new ImageCompositor();
        
        $this->instagramPublisher = new InstagramPublisher(
            $this->instagramClient,
            $this->tokenManager,
            $this->mediaManager,
            $this->jobRepository,
            $this->settingsManager
        );

        $this->openAIClient = new OpenAIClient($this->settingsManager);
        $this->contentGenerator = new ContentGenerator($this->openAIClient, $this->imageCompositor);

        // Video / Reels Module Initialization
        $this->ffmpegManager = new FfmpegManager($this->settingsManager);
        $this->sceneBuilder = new SceneBuilder($this->ffmpegManager);
        $this->videoRenderer = new VideoRenderer(
            $this->ffmpegManager,
            $this->sceneBuilder,
            $this->settingsManager,
            $this->ssrfProtection,
            $this->mediaManager,
            $this->jobRepository
        );

        // News Automation Module Initialization
        $this->newsRepository = new NewsRepository($this->schema);
        $this->sourceManager = new SourceManager($this->newsRepository);
        $this->newsVerifier = new NewsVerifier($this->openAIClient, $this->newsRepository);
        $this->articleGenerator = new ArticleGenerator($this->openAIClient);
        $this->imageCurator = new ImageCurator($this->openAIClient, $this->mediaManager, $this->imageCompositor);
        $this->newsPublisher = new NewsPublisher($this->newsRepository, $this->settingsManager);
        $this->newsCoordinator = new NewsCoordinator(
            $this->newsRepository,
            $this->sourceManager,
            $this->newsVerifier,
            $this->articleGenerator,
            $this->imageCurator,
            $this->newsPublisher,
            $this->settingsManager
        );
        
        // Social Distribution & Video Archive Module Initialization
        $this->socialJobRepository = new SocialJobRepository($this->schema);
        $this->youtubeClient = new YouTubeClient($this->settingsManager);
        $this->youtubePublisher = new YouTubePublisher($this->youtubeClient, $this->socialJobRepository, $this->settingsManager);
        $this->facebookClient = new FacebookClient($this->settingsManager);
        $this->facebookPublisher = new FacebookPublisher($this->facebookClient, $this->socialJobRepository, $this->settingsManager);
        $this->instagramShopClient = new InstagramShopClient($this->settingsManager);
        $this->instagramShopPublisher = new InstagramShopPublisher($this->instagramShopClient, $this->socialJobRepository, $this->settingsManager);

        $this->videoArchiveManager = new VideoArchiveManager($this->youtubeClient, $this->socialJobRepository, $this->settingsManager);
        $this->socialJobManager = new SocialJobManager(
            $this->socialJobRepository,
            $this->youtubePublisher,
            $this->facebookPublisher,
            $this->videoArchiveManager,
            $this->settingsManager,
            $this->instagramShopPublisher
        );

        // ETSY_PRODUCT is an isolated content pipeline. It reuses the separate Etsy OAuth Bridge
        // for Etsy credentials and NEVER falls back to main @oldiesradyo publishing credentials.
        $this->etsyBridgeAdapter = new EtsyBridgeAdapter();
        $this->etsyProductRepository = new EtsyProductRepository($this->schema);
        $this->etsyProductSceneBuilder = new ProductSceneBuilder($this->settingsManager);
        $this->etsyProductSyncService = new ProductSyncService(
            $this->etsyBridgeAdapter,
            $this->etsyProductRepository,
            $this->etsyProductSceneBuilder,
            $this->settingsManager
        );
        $this->pinterestClient = new PinterestClient($this->settingsManager);
        $this->pinterestPublisher = new PinterestPublisher($this->pinterestClient, $this->settingsManager);
        $this->etsyProductDistributionService = new EtsyProductDistributionService(
            $this->etsyProductRepository,
            $this->socialJobRepository,
            $this->instagramShopPublisher,
            $this->pinterestPublisher,
            $this->settingsManager
        );
        $retentionCleaner = new RetentionCleaner(
            $this->jobRepository,
            $this->socialJobRepository,
            $this->settingsManager,
            $this->etsyProductRepository
        );

        $this->scheduler = new Scheduler(
            $this->tokenManager,
            $this->instagramPublisher,
            $this->contentGenerator,
            $this->settingsManager,
            $this->jobRepository,
            $this->videoRenderer,
            $this->newsCoordinator,
            $retentionCleaner,
            $this->etsyProductSyncService
        );

        $this->restController = new RestController(
            $this->authentication,
            $this->ssrfProtection,
            $this->instagramClient,
            $this->tokenManager,
            $this->instagramPublisher,
            $this->contentGenerator,
            $this->jobRepository,
            $this->settingsManager,
            $this->videoRenderer,
            $this->newsRepository,
            $this->newsCoordinator
        );

        $this->adminController = new AdminController(
            $this->instagramClient,
            $this->tokenManager,
            $this->instagramPublisher,
            $this->contentGenerator,
            $this->jobRepository,
            $this->settingsManager,
            $this->openAIClient,
            $this->videoRenderer,
            $this->ffmpegManager,
            $this->newsRepository,
            $this->newsCoordinator,
            $this->socialJobManager,
            $this->socialJobRepository,
            $this->videoArchiveManager,
            $this->youtubeClient,
            $this->facebookClient,
            $this->instagramShopClient,
            $this->instagramShopPublisher
        );
        $this->etsyProductAdmin = new EtsyProductAdmin(
            $this->etsyProductRepository,
            $this->etsyProductSyncService,
            $this->etsyProductDistributionService,
            $this->etsyBridgeAdapter,
            $this->settingsManager,
            $this->pinterestClient,
            $this->pinterestPublisher
        );
    }

    public function init(): void
    {
        if ($this->initialized) {
            return;
        }
        $this->initialized = true;

        // Ensure new defaults/cron/schema are applied on in-place plugin updates.
        $storedDbVersion = (string)get_option('oldies_social_db_version', '');
        if ($storedDbVersion !== OLDIES_SOCIAL_DB_VERSION) {
            $this->schema->migrate();
            $this->settingsManager->setDefaults();
            $this->scheduler->scheduleDefaultEvents();
        }

        // Initialize REST API
        add_action('rest_api_init', [$this->restController, 'registerRoutes']);

        // Initialize Scheduler / Cron hooks
        $this->scheduler->init();
        $this->videoArchiveManager->init();

        // Initialize Admin UI if in admin area
        if (is_admin()) {
            $this->adminController->init();
            $this->etsyProductAdmin->init();
        }
    }

    public static function activate(): void
    {
        $instance = self::getInstance();
        $instance->schema->migrate();
        $instance->settingsManager->setDefaults();
        $instance->sourceManager->seedDefaultSources();
        $instance->scheduler->scheduleDefaultEvents();
    }

    public static function deactivate(): void
    {
        $instance = self::getInstance();
        $instance->scheduler->clearScheduledEvents();
    }

    // Getters for dependency injection / service access
    public function getSchema(): Schema { return $this->schema; }
    public function getJobRepository(): JobRepository { return $this->jobRepository; }
    public function getSettingsManager(): SettingsManager { return $this->settingsManager; }
    public function getEncryption(): Encryption { return $this->encryption; }
    public function getSsrfProtection(): SsrfProtection { return $this->ssrfProtection; }
    public function getAuthentication(): Authentication { return $this->authentication; }
    public function getInstagramClient(): InstagramClient { return $this->instagramClient; }
    public function getTokenManager(): TokenManager { return $this->tokenManager; }
    public function getImageProcessor(): ImageProcessor { return $this->imageProcessor; }
    public function getMediaManager(): MediaManager { return $this->mediaManager; }
    public function getImageCompositor(): ImageCompositor { return $this->imageCompositor; }
    public function getInstagramPublisher(): InstagramPublisher { return $this->instagramPublisher; }
    public function getOpenAIClient(): OpenAIClient { return $this->openAIClient; }
    public function getContentGenerator(): ContentGenerator { return $this->contentGenerator; }
    public function getFfmpegManager(): FfmpegManager { return $this->ffmpegManager; }
    public function getSceneBuilder(): SceneBuilder { return $this->sceneBuilder; }
    public function getVideoRenderer(): VideoRenderer { return $this->videoRenderer; }
    public function getNewsRepository(): NewsRepository { return $this->newsRepository; }
    public function getSourceManager(): SourceManager { return $this->sourceManager; }
    public function getNewsVerifier(): NewsVerifier { return $this->newsVerifier; }
    public function getArticleGenerator(): ArticleGenerator { return $this->articleGenerator; }
    public function getImageCurator(): ImageCurator { return $this->imageCurator; }
    public function getNewsPublisher(): NewsPublisher { return $this->newsPublisher; }
    public function getNewsCoordinator(): NewsCoordinator { return $this->newsCoordinator; }
    public function getScheduler(): Scheduler { return $this->scheduler; }
    public function getRestController(): RestController { return $this->restController; }
    public function getAdminController(): AdminController { return $this->adminController; }

    public function getSocialJobRepository(): SocialJobRepository { return $this->socialJobRepository; }
    public function getYouTubeClient(): YouTubeClient { return $this->youtubeClient; }
    public function getYouTubePublisher(): YouTubePublisher { return $this->youtubePublisher; }
    public function getFacebookClient(): FacebookClient { return $this->facebookClient; }
    public function getFacebookPublisher(): FacebookPublisher { return $this->facebookPublisher; }
    public function getVideoArchiveManager(): VideoArchiveManager { return $this->videoArchiveManager; }
    public function getSocialJobManager(): SocialJobManager { return $this->socialJobManager; }

    public function getInstagramShopClient(): InstagramShopClient { return $this->instagramShopClient; }
    public function getInstagramShopPublisher(): InstagramShopPublisher { return $this->instagramShopPublisher; }

    public function getEtsyBridgeAdapter(): EtsyBridgeAdapter { return $this->etsyBridgeAdapter; }
    public function getEtsyProductRepository(): EtsyProductRepository { return $this->etsyProductRepository; }
    public function getEtsyProductSyncService(): ProductSyncService { return $this->etsyProductSyncService; }
    public function getEtsyProductDistributionService(): EtsyProductDistributionService { return $this->etsyProductDistributionService; }
    public function getPinterestClient(): PinterestClient { return $this->pinterestClient; }
    public function getPinterestPublisher(): PinterestPublisher { return $this->pinterestPublisher; }

}
