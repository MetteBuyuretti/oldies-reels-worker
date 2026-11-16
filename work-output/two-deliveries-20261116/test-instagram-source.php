<?php
declare(strict_types=1);
namespace {
    define('ABSPATH', __DIR__ . '/');
    final class WP_Error {
        public function __construct(public string $code, public string $message='', public array $data=[]) {}
        public function get_error_code(){return $this->code;}
        public function get_error_message(){return $this->message;}
    }
    function is_wp_error($x){return $x instanceof WP_Error;}
    function add_action(...$x){}
    function register_activation_hook(...$x){}
    function register_deactivation_hook(...$x){}
    function sanitize_text_field($x){return trim((string)$x);}
    function sanitize_textarea_field($x){return trim((string)$x);}
    function esc_url_raw($x){return (string)$x;}
    function add_query_arg($params,$url){return $url.'?'.http_build_query($params);}
    function wp_remote_request($url,$args){
        if($args['method']!=='GET') throw new \RuntimeException('Mutation attempted');
        parse_str(parse_url($url,PHP_URL_QUERY),$q);
        if(str_contains($q['fields']??'','media_audio_type')) throw new \RuntimeException('Unsupported field regression');
        $GLOBALS['calls']++;
        return $GLOBALS['response'];
    }
    function wp_remote_retrieve_response_code($r){return $r['status'];}
    function wp_remote_retrieve_body($r){return json_encode($r['body']);}
}
namespace OldiesRadyo\SocialAutomation\Security {
    class Encryption {}
    class SettingsManager {
        public function getInstagramUserId(){return '12345';}
        public function getInstagramAccessToken(){return 'offline-fixture-only';}
    }
}
namespace {
    require $argv[1] ?? __DIR__.'/bridge.readback.php';
    $count=0; $calls=0;
    function check($ok,$label){global $count;if(!$ok)throw new \RuntimeException($label);$count++;echo 'PASS '.$label.PHP_EOL;}
    $media=['id'=>'98765','media_type'=>'VIDEO','media_product_type'=>'REELS','permalink'=>'https://www.instagram.com/reel/fixture/','caption'=>'Fixture','timestamp'=>'2026-11-16T00:00:00+0000'];
    $GLOBALS['response']=['status'=>200,'body'=>['data'=>[$media]]];
    $r=Oldies_Radyo_Reels_Bridge::abilityListInstagramRecent();
    check(count($r)===1 && $r[0]['media_id']==='98765','list succeeds without unsupported audio field');
    check($r[0]['media_url']==='' && $r[0]['media_audio_type']==='','missing file and audio type remain unknown');
    $probe=new \ReflectionMethod(Oldies_Radyo_Reels_Bridge::class,'getInstagramFinalMedia');
    $probe->setAccessible(true);
    $GLOBALS['response']=['status'=>200,'body'=>$media];
    $r=$probe->invoke(null,'98765');
    check(is_wp_error($r)&&$r->get_error_code()==='instagram_final_media_missing','no final URL blocks transfer without raw fallback');
    $GLOBALS['response']['body']['media_url']='https://example.org/verified-final.mp4';
    $r=$probe->invoke(null,'98765');
    check($r['id']==='98765'&&$r['media_url']==='https://example.org/verified-final.mp4','exact API final source accepted');
    $GLOBALS['response']['body']['id']='111';
    $r=$probe->invoke(null,'98765');
    check(is_wp_error($r)&&$r->get_error_code()==='instagram_media_mismatch','wrong source identity rejected');
    $GLOBALS['response']=['status'=>200,'body'=>array_merge($media,['media_type'=>'IMAGE'])];
    $r=$probe->invoke(null,'98765');
    check(is_wp_error($r)&&$r->get_error_code()==='instagram_media_not_video','nonvideo rejected');
    $GLOBALS['response']=['status'=>400,'body'=>['error'=>['message'=>'Fixture API rejection']]];
    $r=$probe->invoke(null,'98765');
    check(is_wp_error($r)&&$r->get_error_code()==='meta_audio_api_error','upstream errors remain explicit');
    check($calls===6,'six read-only requests; no upload or publication');
    echo 'RESULT '.$count.'/8 passed; offline fixture, no real network'.PHP_EOL;
}
