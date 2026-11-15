<?php
declare(strict_types=1);
namespace {
    define('ABSPATH', __DIR__ . '/');
    final class WP_Error { public function __construct(public string $code, public string $message='', public array $data=[]) {} public function get_error_code(){return $this->code;} public function get_error_message(){return $this->message;} }
    function is_wp_error($x): bool {return $x instanceof WP_Error;}
    function __($s,$d=null){return $s;}
    function current_time($t,$g=false){return '2026-11-15 19:00:00';}
    function sanitize_text_field($x){return trim((string)$x);}
    function sanitize_textarea_field($x){return trim((string)$x);}
    function esc_url_raw($x){return (string)$x;}
    function add_action(...$x){}
    function register_activation_hook(...$x){}
    function register_deactivation_hook(...$x){}
}
namespace OldiesRadyo\SocialAutomation\Security {
    class SettingsManager {public function getYoutubeDefaultVisibility(){return 'public';}}
}
namespace OldiesRadyo\SocialAutomation\Database {
    class SocialJobRepository {
        public function findDuplicateYoutube(...$x){return null;}
        public function saveToVideoArchive(...$x){throw new \RuntimeException('Unexpected archive mutation');}
    }
}
namespace OldiesRadyo\SocialAutomation\Social {
    class SocialJob {
        public const TYPE_REEL='reel', MODE_SOCIAL_ONLY='social_only', MODE_SOCIAL_ARCHIVE='social_archive';
        public string $id='', $url='';
        public function getYoutubeVideoId(){return $this->id;}
        public function getUuid(){return 'fixture';}
        public function getContentHash(){return 'fixture';}
        public function getMediaPath(){return __FILE__;}
        public function getMediaUrl(){return '';}
        public function getTitle(){return 'Fixture #Shorts';}
        public function getDescription(){return 'Fixture';}
        public function getContentType(){return self::TYPE_REEL;}
        public function getYoutubeVisibility(){return 'public';}
        public function getPublicationMode(){return self::MODE_SOCIAL_ONLY;}
        public function setYoutubeVideoId($v){$this->id=$v;}
        public function setYoutubeUrl($v){$this->url=$v;}
        public function appendErrorLog($x){}
    }
}
namespace OldiesRadyo\SocialAutomation\YouTube {
    class YouTubeClient {
        public int $calls=0;
        public function __construct(public array $receipt=[]){}
        public function getValidAccessToken(){return 'fixture-only';}
        public function uploadVideo(...$args){$this->calls++; return $this->receipt;}
    }
}
namespace {
    require __DIR__ . '/YouTubePublisher.php';
    require __DIR__ . '/bridge-candidate.php';
    use OldiesRadyo\SocialAutomation\YouTube\YouTubeClient;
    use OldiesRadyo\SocialAutomation\YouTube\YouTubePublisher;
    use OldiesRadyo\SocialAutomation\Database\SocialJobRepository;
    use OldiesRadyo\SocialAutomation\Security\SettingsManager;
    use OldiesRadyo\SocialAutomation\Social\SocialJob;
    $count=0;
    function check(bool $ok,string $label): void {global $count; if(!$ok){throw new RuntimeException($label);} $count++; echo 'PASS '.$label.PHP_EOL;}
    function publish(array $receipt,bool $dry=false): array {
        $client=new YouTubeClient($receipt);
        $publisher=new YouTubePublisher($client,new SocialJobRepository(),new SettingsManager());
        $result=$publisher->publish(new SocialJob(),$dry);
        return [$result,$client];
    }
    $id='abcdefghijk';
    [$r,$c]=publish(['id'=>$id,'status'=>['privacyStatus'=>'private','uploadStatus'=>'processed']]);
    check($r['status']==='uploaded_private' && !$r['publication_verified'] && $r['visibility']==='private' && $r['published_at']==='', 'requested public, returned private stays private');
    [$r]=publish(['id'=>$id,'status'=>['privacyStatus'=>'public','uploadStatus'=>'uploaded']]);
    check($r['status']==='uploaded_processing' && !$r['publication_verified'], 'uploaded is not processed publication');
    [$r]=publish(['id'=>$id,'status'=>['privacyStatus'=>'public','uploadStatus'=>'processed']]);
    check($r['status']==='published' && $r['publication_verified'] && $r['published_at']!=='', 'processed public receipt permits publication claim');
    [$r]=publish(['id'=>$id]);
    check($r['status']==='uploaded_unverified' && $r['visibility']==='unknown' && !$r['publication_verified'], 'missing remote status cannot inherit requested public');
    [$r]=publish(['id'=>$id,'status'=>['privacyStatus'=>'unlisted','uploadStatus'=>'processed']]);
    check($r['status']==='uploaded_unlisted' && !$r['publication_verified'], 'unlisted is not public');
    [$r]=publish(['id'=>$id,'status'=>['privacyStatus'=>'public','uploadStatus'=>'rejected']]);
    check(!$r['success'] && $r['status']==='upload_rejected' && !$r['publication_verified'], 'rejection cannot report publication success');
    [$r]=publish(['status'=>['privacyStatus'=>'public','uploadStatus'=>'processed']]);
    check(is_wp_error($r) && $r->get_error_code()==='youtube_upload_receipt_missing', 'missing ID cannot form successful permalink');
    [$r,$c]=publish([],true);
    check($r['status']==='simulated' && !$r['publication_verified'] && $c->calls===0, 'dry-run never publishes or calls upload');
    $sanitize=new ReflectionMethod(Oldies_Radyo_Reels_Bridge::class,'sanitizeDraftForAbility');
    $sanitize->setAccessible(true);
    $ig=['instagram_media_id'=>'123456','permalink'=>'https://www.instagram.com/reel/test/','media_url'=>'https://example.org/final.mp4','source'=>'instagram_graph'];
    $yt=['success'=>true,'dry_run'=>false,'status'=>'published','result'=>['success'=>true,'video_id'=>$id,'youtube_url'=>'https://youtube.com/shorts/'.$id,'status'=>'published','visibility'=>'public']];
    $r=$sanitize->invoke(null,['id'=>'legacy','instagram_result'=>$ig,'youtube_result'=>$yt]);
    check($r['youtube_status']==='uploaded_unverified' && !$r['youtube_verified_source'] && !$r['youtube_publication_verified'], 'legacy upload marker cannot verify source/publication');
    check($r['youtube_visibility']==='unknown', 'legacy requested visibility is not remote visibility evidence');
    $yt['source_origin']='instagram_published_final'; $yt['source_instagram_media_id']='123456'; $yt['source_instagram_permalink']=$ig['permalink']; $yt['source_final_media_url']=$ig['media_url'];
    $yt['result']['publication_verified']=true; $yt['result']['visibility']='public'; $yt['result']['upload_status']='processed';
    $r=$sanitize->invoke(null,['id'=>'bound','instagram_result'=>$ig,'youtube_result'=>$yt]);
    check($r['youtube_verified_source'] && $r['youtube_publication_verified'], 'exact provenance binding and public receipt verify independently');
    $yt['source_instagram_media_id']='999';
    $r=$sanitize->invoke(null,['id'=>'mismatch','instagram_result'=>$ig,'youtube_result'=>$yt]);
    check(!$r['youtube_verified_source'] && $r['youtube_publication_verified'], 'wrong Instagram source rejected even for public video');
    $yt['source_instagram_media_id']='123456'; $yt['source_final_media_url']='https://example.org/wrong.mp4';
    $r=$sanitize->invoke(null,['id'=>'wrong-file','instagram_result'=>$ig,'youtube_result'=>$yt]);
    check(!$r['youtube_verified_source'], 'different final video URL cannot inherit source confirmation');
    $yt['dry_run']=true;
    $r=$sanitize->invoke(null,['id'=>'simulation','instagram_result'=>$ig,'youtube_result'=>$yt]);
    check(!$r['youtube_success'] && !$r['youtube_publication_verified'] && $r['youtube_status']==='simulated', 'wrapper dry-run overrides apparent successful nested receipt');
    echo 'RESULT '.$count.'/14 passed; no provider/network/publication calls'.PHP_EOL;
}
