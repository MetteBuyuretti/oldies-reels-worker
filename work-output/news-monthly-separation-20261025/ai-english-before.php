<?php
/**
 * Oldies Radyo AI English layer.
 *
 * English pages live under /en/, are translated as coherent page chunks with
 * the Gemini API free tier, and are cached permanently until the Turkish
 * source changes. A background queue performs the work; public visitors never
 * wait for an API request and never receive a Google Translate proxy.
 */

if(!defined('ABSPATH')){exit;}

define('OLDIES_AI_ENGLISH_VERSION','1.3.0');
define('OLDIES_AI_DAILY_REQUEST_LIMIT',80);

function oldies_is_english(){
 if(get_query_var('oldies_lang')==='en'){return true;}
 $path=(string)wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']??'/'),PHP_URL_PATH);
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 return (bool)preg_match('#^/en(?:/|$)#',$path);
}

/**
 * True when WordPress is rendering a real Polylang English page.
 * Native English pages must bypass the legacy machine-translation buffer.
 */
function oldies_native_english_post($post_id=0){
 $post_id=(int)($post_id?:get_queried_object_id());
 if($post_id<=0){return false;}
 if(function_exists('pll_get_post_language')){return pll_get_post_language($post_id,'slug')==='en';}
 return oldies_is_english();
}

function oldies_counterpart_url($language='tr'){
 $post_id=(int)get_queried_object_id();
 if($post_id>0 && function_exists('pll_get_post')){
  $target_id=(int)pll_get_post($post_id,$language);
  if($target_id>0){return get_permalink($target_id);}
 }
 return oldies_language_url($language);
}

function oldies_english_page_url($slug=''){
 $slug=trim((string)$slug,'/');
 if($slug===''){return home_url('/en/');}
 $page=get_page_by_path($slug,OBJECT,'page');
 if($page instanceof WP_Post){
  $language=function_exists('pll_get_post_language')?pll_get_post_language($page->ID,'slug'):'en';
  if($language==='en'){return get_permalink($page);}
 }
 return home_url('/en/'.$slug.'/');
}

function oldies_english_page_is_live($slug){
 $page=get_page_by_path(trim((string)$slug,'/'),OBJECT,'page');
 if(!($page instanceof WP_Post) || $page->post_status!=='publish'){return false;}
 return !function_exists('pll_get_post_language') || pll_get_post_language($page->ID,'slug')==='en';
}

function oldies_original_request_path(){
 $path=(string)wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']??'/'),PHP_URL_PATH);
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 $path='/'.ltrim($path,'/');
 $path=preg_replace('#^/en(?=/|$)#','',$path,1);
 if($path==='' || $path===false){$path='/';}
 return trailingslashit($path);
}

function oldies_language_url($language='tr'){
 $path=oldies_original_request_path();
 $request=wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']??$path));
 $query=[];
 if(!empty($request['query'])){parse_str($request['query'],$query);}
 foreach(['oldies_warm','_oldies_nonce','_oldies_source','lang'] as $key){unset($query[$key]);}
 $target=$language==='en'?('/en'.($path==='/'?'/':$path)):$path;
 $url=home_url($target);
 return $query?add_query_arg($query,$url):$url;
}

function oldies_ai_english_url_for($url){
 $parts=wp_parse_url($url);
 $path=!empty($parts['path'])?$parts['path']:'/';
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 $path='/'.ltrim($path,'/');
 if(preg_match('#^/en(?:/|$)#',$path)){return $url;}
 $english='/en'.($path==='/'?'/':trailingslashit($path));
 $result=home_url($english);
 if(!empty($parts['query'])){$result.='?'.$parts['query'];}
 if(!empty($parts['fragment'])){$result.='#'.$parts['fragment'];}
 return $result;
}

function oldies_english_visual_urls($post_id=0){
 $post_id=(int)($post_id?:get_queried_object_id());
 $urls=[];
 $push=function($url) use (&$urls){if($url && !in_array($url,$urls,true)){$urls[]=$url;}};
 if($post_id>0){
  $push(get_the_post_thumbnail_url($post_id,'full'));
  if(function_exists('pll_get_post')){
   $turkish_id=(int)pll_get_post($post_id,'tr');
   if($turkish_id>0){$push(get_the_post_thumbnail_url($turkish_id,'full'));}
  }
  $slug=(string)get_post_field('post_name',$post_id);
  $slugs=[$slug];
  foreach(get_post_ancestors($post_id) as $ancestor_id){$slugs[]=(string)get_post_field('post_name',$ancestor_id);}
  $candidates=[];
  if(in_array('1960s',$slugs,true)){$candidates[]='assets/images/sixties-artists/'.$slug.'.webp';}
  elseif(in_array('1970s',$slugs,true)){$candidates[]='assets/images/seventies-artists/'.$slug.'.webp';}
  elseif(in_array('1980s',$slugs,true)){$candidates[]='assets/images/eighties-artists/'.$slug.'.webp';}
  elseif(in_array('1990s',$slugs,true)){$candidates[]='assets/images/nineties-artists/'.$slug.'.webp';}
  else{$candidates[]='assets/images/artists/'.$slug.'.webp';}

  if(preg_match('/^(195[0-9])(?:-|$)/',$slug,$m)){
   array_unshift($candidates,'assets/images/fifties-year-featured-v42/year-'.$m[1].'-nat-king-cole.webp');
   $candidates[]='assets/images/fifties-years-v33/year-'.$m[1].'-records.webp';
  }
  if(preg_match('/^(196[0-9])(?:-|$)/',$slug,$m)){$candidates[]='assets/images/year-'.$m[1].'-60s-v30.webp';}
  if($slug==='ska-rocksteady-early-reggae'){$candidates[]='assets/images/sixties-styles-v35/ska-rocksteady-ve-erken-reggae.webp';}
  foreach($candidates as $relative){
   $file=trailingslashit(get_template_directory()).ltrim($relative,'/');
   if(file_exists($file)){$push(trailingslashit(get_template_directory_uri()).ltrim($relative,'/'));}
  }
  $map=[
   '1950s'=>'hero-1950s.jpg',
   '1960s'=>'sixties-hero-v35.webp',
   '1970s'=>'history-decade-1970s-v7.webp',
   '1980s'=>'history-decade-1980s-v7.webp',
   '1990s'=>'history-decade-1990s-v7.webp',
  ];
  foreach($map as $decade=>$file){if(in_array($decade,$slugs,true)){$push(oldies_media_url($file));break;}}
 }
 if(!$urls){$push(oldies_media_url('oldies-radyo-share.webp'));}
 return $urls;
}

function oldies_english_visual_url($post_id=0){
 $urls=oldies_english_visual_urls($post_id);
 return $urls[0]??oldies_media_url('oldies-radyo-share.webp');
}

function oldies_ai_register_routes(){
 add_rewrite_rule('^en/?$','index.php?oldies_lang=en','top');
 add_rewrite_rule('^en/(.+?)/?$','index.php?oldies_lang=en&oldies_target=$matches[1]','top');
 add_rewrite_rule('^oldies-english-sitemap\.xml$','index.php?oldies_en_sitemap=1','top');
}
add_action('init','oldies_ai_register_routes',4);

function oldies_ai_query_vars($vars){
 $vars[]='oldies_lang';
 $vars[]='oldies_target';
 $vars[]='oldies_en_sitemap';
 return $vars;
}
add_filter('query_vars','oldies_ai_query_vars');

function oldies_ai_request_target(){
 $path=(string)wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']??'/'),PHP_URL_PATH);
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 $path=trim($path,'/');
 if($path==='en'){return '';}
 if(strpos($path,'en/')===0){return trim(substr($path,3),'/');}
 return null;
}

function oldies_ai_resolve_english_request($vars){
 $target=oldies_ai_request_target();
 if($target===null){return $vars;}

 $vars=['oldies_lang'=>'en','lang'=>'en'];
 if($target===''){
  $requested_page_id=isset($_GET['page_id'])?absint($_GET['page_id']):0;
  if($requested_page_id>0 && get_post_status($requested_page_id)==='publish'){
   $requested_language=function_exists('pll_get_post_language')?pll_get_post_language($requested_page_id,'slug'):'en';
   if($requested_language==='en'){$vars['page_id']=$requested_page_id;return $vars;}
  }
  $front_id=(int)get_option('page_on_front');
  if($front_id>0 && function_exists('pll_get_post')){
   $translated=(int)pll_get_post($front_id,'en');
   if($translated>0){$front_id=$translated;}
  }
  if($front_id>0){$vars['page_id']=$front_id;}
  return $vars;
 }

 $vars['oldies_target']=$target;
 $object=get_page_by_path($target,OBJECT,['page','post']);
 if(!($object instanceof WP_Post) && strpos($target,'/')!==false){
  $post_slug=basename($target);
  $object=get_page_by_path($post_slug,OBJECT,'post');
 }
 if($object instanceof WP_Post){
  $object_language=function_exists('pll_get_post_language')?pll_get_post_language($object->ID,'slug'):'en';
  if($object_language==='en'){
   if($object->post_type==='page'){$vars['page_id']=$object->ID;}
   else{$vars['p']=$object->ID;$vars['post_type']=$object->post_type;}
   return $vars;
  }
 }
 $vars['pagename']=$target;
 return $vars;
}
add_filter('request','oldies_ai_resolve_english_request',5);

function oldies_native_english_links($content){
 if(!oldies_native_english_post()){return $content;}
 $base=home_url('/en/');
 return preg_replace_callback('#'.preg_quote($base,'#').'\?page_id=([0-9]+)#',function($match){
  $target_id=(int)$match[1];
  if($target_id<=0 || get_post_status($target_id)!=='publish'){return $match[0];}
  return get_permalink($target_id);
 },$content);
}
add_filter('the_content','oldies_native_english_links',8);

add_filter('redirect_canonical',function($redirect){return oldies_is_english()?false:$redirect;},10,1);
add_filter('language_attributes',function($output){
 if(!oldies_is_english()){return $output;}
 $output=preg_replace('/\blang=("|\')[^"\']*("|\')/i','lang="en-US"',$output,1);
 return $output.' dir="ltr"';
});
add_filter('body_class',function($classes){if(oldies_is_english()){$classes[]='oldies-english-view';}return $classes;});

function oldies_ai_turkish_hreflang(){
 if(oldies_is_english() || is_admin() || !(is_front_page() || is_singular())){return;}
 $turkish=oldies_current_original_url();
 $path=(string)wp_parse_url($turkish,PHP_URL_PATH);
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 $path=trailingslashit('/'.ltrim($path,'/'));
 if(!oldies_ai_has_translation($path)){return;}
 $english=oldies_ai_english_url_for($turkish);
 echo '<link rel="alternate" hreflang="tr" href="'.esc_url($turkish).'">'."\n";
 echo '<link rel="alternate" hreflang="en" href="'.esc_url($english).'">'."\n";
 echo '<link rel="alternate" hreflang="x-default" href="'.esc_url($turkish).'">'."\n";
}
add_action('wp_head','oldies_ai_turkish_hreflang',6);

function oldies_ai_api_key(){
 if(defined('OLDIES_GEMINI_API_KEY') && trim((string)OLDIES_GEMINI_API_KEY)!==''){return trim((string)OLDIES_GEMINI_API_KEY);}
 return trim((string)get_option('oldies_gemini_api_key',''));
}

function oldies_ai_model(){
 // This theme deliberately uses only the model with a documented free tier.
 // It never falls back to a paid model when the free quota is exhausted.
 return 'gemini-3.5-flash-lite';
}

function oldies_ai_translation_option($path){return 'oldies_ai_en_'.sha1($path);}

function oldies_ai_has_translation($path){
 $record=get_option(oldies_ai_translation_option(trailingslashit('/'.ltrim((string)$path,'/'))),[]);
 return is_array($record) && !empty($record['html']);
}

function oldies_ai_normalize_source($html){
 $html=preg_replace('/\b(?:_wpnonce|nonce)["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]+["\']/i','nonce=""',$html);
 $html=preg_replace('/\b(?:logged-in|admin-bar)\b/','',$html);
 return preg_replace('/ver=[0-9A-Za-z._-]+/','ver=VERSION',$html);
}

function oldies_ai_source_hash($html){
 return hash('sha256',OLDIES_AI_ENGLISH_VERSION.'|'.oldies_ai_model().'|'.oldies_ai_normalize_source($html));
}

function oldies_ai_path_from_url($url){
 $path=(string)wp_parse_url($url,PHP_URL_PATH);
 $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
 if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
 $path=preg_replace('#^/en(?=/|$)#','',$path,1);
 return trailingslashit('/'.ltrim((string)$path,'/'));
}

function oldies_ai_queue(){
 $queue=get_option('oldies_ai_translation_queue',[]);
 return is_array($queue)?$queue:[];
}

function oldies_ai_enqueue_url($url,$reason='automatic',$priority=false){
 $url=esc_url_raw((string)$url);
 if($url==='' || oldies_ai_api_key()===''){return false;}
 $path=oldies_ai_path_from_url($url);
 $queue=oldies_ai_queue();
 $existing=$queue[$path]??[];
 $queue[$path]=[
  'url'=>home_url($path),
  'path'=>$path,
  'reason'=>sanitize_key($reason),
  'priority'=>$priority?10:(int)($existing['priority']??0),
  'queued_at'=>(int)($existing['queued_at']??time()),
  'attempts'=>(int)($existing['attempts']??0),
  'next_attempt'=>(int)($existing['next_attempt']??0),
  'last_error'=>(string)($existing['last_error']??''),
 ];
 update_option('oldies_ai_translation_queue',$queue,false);
 oldies_ai_schedule_worker();
 return true;
}

function oldies_ai_enqueue_all($reason='full_scan'){
 if(oldies_ai_api_key()===''){return 0;}
 $count=0;
 foreach(oldies_ai_public_urls() as $position=>$url){
  if(oldies_ai_enqueue_url($url,$reason,$position===0)){$count++;}
 }
 return $count;
}

function oldies_ai_remove_from_queue($path){
 $queue=oldies_ai_queue();
 $path=trailingslashit('/'.ltrim((string)$path,'/'));
 if(isset($queue[$path])){unset($queue[$path]);update_option('oldies_ai_translation_queue',$queue,false);}
}

function oldies_ai_cron_schedules($schedules){
 $schedules['oldies_five_minutes']=['interval'=>300,'display'=>'Oldies Radyo: every five minutes'];
 return $schedules;
}
add_filter('cron_schedules','oldies_ai_cron_schedules');

function oldies_ai_schedule_worker(){
 if(oldies_ai_api_key()!=='' && !wp_next_scheduled('oldies_ai_translation_worker')){
  wp_schedule_event(time()+60,'oldies_five_minutes','oldies_ai_translation_worker');
 }
}

function oldies_ai_bootstrap(){
 $installed=(string)get_option('oldies_ai_installed_version','');
 if($installed!==OLDIES_AI_ENGLISH_VERSION){
  update_option('oldies_ai_installed_version',OLDIES_AI_ENGLISH_VERSION,false);
  oldies_ai_enqueue_all('theme_update');
  flush_rewrite_rules(false);
 }
 oldies_ai_schedule_worker();
}
add_action('init','oldies_ai_bootstrap',30);

function oldies_ai_queue_saved_post($post_id,$post,$update){
 if(wp_is_post_revision($post_id) || !($post instanceof WP_Post) || $post->post_status!=='publish' || !in_array($post->post_type,['page','post'],true)){return;}
 oldies_ai_enqueue_url(get_permalink($post),'content_update',true);
}
add_action('save_post','oldies_ai_queue_saved_post',30,3);
add_action('customize_save_after',function(){oldies_ai_enqueue_all('design_update');});

function oldies_ai_daily_usage(){
 $today=gmdate('Y-m-d');
 $usage=get_option('oldies_ai_daily_usage',[]);
 if(!is_array($usage) || ($usage['date']??'')!==$today){$usage=['date'=>$today,'requests'=>0];}
 return $usage;
}

function oldies_ai_take_daily_request(){
 $usage=oldies_ai_daily_usage();
 if((int)$usage['requests']>=OLDIES_AI_DAILY_REQUEST_LIMIT){
  $retry=max(900,strtotime('tomorrow 00:05 UTC')-time());
  return new WP_Error('oldies_daily_guard','Günlük güvenlik sınırına ulaşıldı; sistem yarın otomatik devam edecek.',['retry_after'=>$retry]);
 }
 $usage['requests']=(int)$usage['requests']+1;
 update_option('oldies_ai_daily_usage',$usage,false);
 return true;
}

function oldies_ai_save_record($path,$hash,$translated){
 $record=['source_hash'=>$hash,'html'=>$translated,'updated_at'=>gmdate('c'),'model'=>oldies_ai_model(),'path'=>$path];
 update_option(oldies_ai_translation_option($path),$record,false);
 $index=get_option('oldies_ai_translation_index',[]);
 if(!is_array($index)){$index=[];}
 $index[$path]=array_diff_key($record,['html'=>true]);
 update_option('oldies_ai_translation_index',$index,false);
 return $record;
}

function oldies_ai_process_queue($limit=1){
 if(oldies_ai_api_key()==='' || get_transient('oldies_ai_worker_lock')){return ['processed'=>0,'message'=>'not_ready'];}
 $paused_until=(int)get_option('oldies_ai_paused_until',0);
 if($paused_until>time()){return ['processed'=>0,'message'=>'paused'];}
 set_transient('oldies_ai_worker_lock',1,240);
 $queue=oldies_ai_queue();
 uasort($queue,function($a,$b){
  $priority=((int)($b['priority']??0))<=>((int)($a['priority']??0));
  return $priority!==0?$priority:((int)($a['queued_at']??0)<=> (int)($b['queued_at']??0));
 });
 $processed=0;$last_message='empty';
 foreach($queue as $path=>$item){
  if($processed>=$limit){break;}
  if((int)($item['next_attempt']??0)>time()){continue;}
  $processed++;
  $source_token=oldies_ai_internal_source_token();
  $source_url=add_query_arg('_oldies_source',$source_token,oldies_ai_english_url_for($item['url']));
  $source=wp_remote_get($source_url,['timeout'=>45,'redirection'=>3,'headers'=>[
   'X-Oldies-Translation-Worker'=>'1',
   'X-Oldies-Translation-Source'=>$source_token,
  ]]);
  if(is_wp_error($source) || (int)wp_remote_retrieve_response_code($source)!==200){
   $error=is_wp_error($source)?$source->get_error_message():'Kaynak sayfa HTTP '.(int)wp_remote_retrieve_response_code($source);
   $queue[$path]['attempts']=(int)($item['attempts']??0)+1;
   $queue[$path]['last_error']=$error;
   $queue[$path]['next_attempt']=time()+min(86400,900*(2**min(6,$queue[$path]['attempts'])));
   $last_message=$error;continue;
  }
  $html=(string)wp_remote_retrieve_body($source);
  $hash=oldies_ai_source_hash($html);
  $cached=get_option(oldies_ai_translation_option($path),[]);
  if(is_array($cached) && ($cached['source_hash']??'')===$hash && !empty($cached['html'])){
   unset($queue[$path]);$last_message='already_current';continue;
  }
  $translated=oldies_ai_translate_html($html,$path);
  if(is_wp_error($translated)){
   $queue[$path]['attempts']=(int)($item['attempts']??0)+1;
   $queue[$path]['last_error']=$translated->get_error_message();
   $data=$translated->get_error_data();
   $retry=is_array($data)?(int)($data['retry_after']??0):0;
   if(in_array($translated->get_error_code(),['oldies_api_limit','oldies_daily_guard'],true)){
    $retry=max(900,$retry);update_option('oldies_ai_paused_until',time()+$retry,false);
   }
   $queue[$path]['next_attempt']=time()+max(900,$retry);
   $last_message=$translated->get_error_message();
   break;
  }
  oldies_ai_save_record($path,$hash,$translated);
  unset($queue[$path]);$last_message='translated';
 }
 update_option('oldies_ai_translation_queue',$queue,false);
 update_option('oldies_ai_worker_status',['time'=>gmdate('c'),'processed'=>$processed,'message'=>$last_message,'remaining'=>count($queue)],false);
 delete_transient('oldies_ai_worker_lock');
 return ['processed'=>$processed,'message'=>$last_message,'remaining'=>count($queue)];
}
add_action('oldies_ai_translation_worker',function(){oldies_ai_process_queue(1);});

function oldies_ai_native_english_template($template){
 if(!oldies_native_english_post() || !is_page()){return $template;}
 $front_id=(int)get_option('page_on_front');
 if($front_id>0 && function_exists('pll_get_post')){$front_id=(int)pll_get_post($front_id,'en');}
 if($front_id>0 && get_queried_object_id()===$front_id){return get_template_directory().'/front-page.php';}
 return get_template_directory().'/index.php';
}
add_filter('template_include','oldies_ai_native_english_template',99);

function oldies_ai_begin_buffer(){
 if(oldies_ai_is_internal_source_request() || oldies_native_english_post()){return;}
 if(!oldies_is_english() || is_admin() || wp_doing_ajax() || is_feed() || is_404() || !(is_front_page() || is_singular())){return;}
 if(!oldies_ai_has_translation(oldies_original_request_path())){nocache_headers();}
 show_admin_bar(false);
 ob_start('oldies_ai_translate_document');
}
add_action('template_redirect','oldies_ai_begin_buffer',99);

function oldies_ai_internal_source_token(){
 $timestamp=time();
 $signature=hash_hmac('sha256','oldies-ai-source|'.home_url('/').'|'.$timestamp,wp_salt('auth'));
 return $timestamp.'.'.$signature;
}

function oldies_ai_is_internal_source_request(){
 $token=(string)($_SERVER['HTTP_X_OLDIES_TRANSLATION_SOURCE']??'');
 if($token===''){$token=sanitize_text_field(wp_unslash($_GET['_oldies_source']??''));}
 $parts=explode('.',$token,2);
 if(count($parts)!==2 || !ctype_digit($parts[0])){return false;}
 $timestamp=(int)$parts[0];
 if(abs(time()-$timestamp)>300){return false;}
 $expected=hash_hmac('sha256','oldies-ai-source|'.home_url('/').'|'.$timestamp,wp_salt('auth'));
 return hash_equals($expected,$parts[1]);
}

function oldies_ai_translate_document($html){
 if(trim($html)===''){return $html;}
 $path=oldies_original_request_path();
 $hash=oldies_ai_source_hash($html);
 $option=oldies_ai_translation_option($path);
 $cached=get_option($option,[]);
 if(is_array($cached) && ($cached['source_hash']??'')===$hash && !empty($cached['html'])){return $cached['html'];}

 if(oldies_ai_api_key()===''){
  return oldies_ai_add_notice($html,'English is being prepared','The English edition is not active yet. Please return to the Turkish page for the complete article.');
 }
 oldies_ai_enqueue_url(home_url($path),'english_visit',true);
 return oldies_ai_add_notice($html,'English update queued','This page is being prepared automatically. Please return shortly or use the complete Turkish edition.');
}

function oldies_ai_add_notice($html,$title,$message){
 $notice='<aside class="oldies-language-notice" lang="en"><strong>'.esc_html($title).'</strong><span>'.esc_html($message).'</span><a href="'.esc_url(oldies_language_url('tr')).'">Türkçe sayfaya dön</a></aside>';
 $robots='<meta name="robots" content="noindex,follow">';
 if(stripos($html,'</head>')!==false){$html=preg_replace('/<\/head>/i',$robots.'</head>',$html,1);}
 $position=stripos($html,'</header>');
 if($position!==false){$position+=9;return substr($html,0,$position).$notice.substr($html,$position);}
 return $notice.$html;
}

function oldies_ai_translate_html($html,$path){
 if(!class_exists('DOMDocument')){return new WP_Error('oldies_dom_missing','Sunucuda PHP DOM eklentisi etkin değil.');}
 $previous=libxml_use_internal_errors(true);
 $dom=new DOMDocument('1.0','UTF-8');
 $loaded=$dom->loadHTML('<?xml encoding="UTF-8">'.$html,LIBXML_HTML_NOIMPLIED|LIBXML_HTML_NODEFDTD);
 libxml_clear_errors();
 libxml_use_internal_errors($previous);
 if(!$loaded){return new WP_Error('oldies_html_parse','Sayfa HTML yapısı okunamadı.');}

 $xpath=new DOMXPath($dom);
 $query='//text()[normalize-space(.)!="" and not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript) and not(ancestor::svg) and not(ancestor::code) and not(ancestor::pre) and not(ancestor::*[@translate="no"]) and not(ancestor::*[contains(concat(" ",normalize-space(@class)," ")," notranslate ")]) and not(ancestor::*[contains(concat(" ",normalize-space(@class)," ")," language-content-en ")]) and not(ancestor::*[contains(concat(" ",normalize-space(@class)," ")," language-content-tr ")])]';
 $items=[];
 $id=0;
 foreach($xpath->query($query) as $node){
  $text=trim((string)$node->nodeValue);
  if($text==='' || !preg_match('/[\p{L}]/u',$text)){continue;}
  preg_match('/^\s*/u',(string)$node->nodeValue,$lead);
  preg_match('/\s*$/u',(string)$node->nodeValue,$trail);
  $parent=$node->parentNode;
  $context=$parent instanceof DOMElement?$parent->tagName:'';
  if($parent instanceof DOMElement && $parent->hasAttribute('class')){$context.='.'.substr($parent->getAttribute('class'),0,80);}
  $items[]=['id'=>$id++,'text'=>$text,'context'=>$context,'node'=>$node,'attribute'=>null,'lead'=>$lead[0]??'','trail'=>$trail[0]??''];
 }

 $attribute_queries=[
  ['//*[@alt]','alt'],['//*[@title]','title'],['//*[@placeholder]','placeholder'],['//*[@aria-label]','aria-label'],
  ['//input[@type="submit" or @type="button"]','value'],
  ['//meta[@name="description" or @property="og:title" or @property="og:description" or @name="twitter:title" or @name="twitter:description"]','content'],
 ];
 foreach($attribute_queries as [$selector,$attribute]){
  foreach($xpath->query($selector) as $node){
   if(!($node instanceof DOMElement) || oldies_ai_node_excluded($node)){continue;}
   $text=trim($node->getAttribute($attribute));
   if($text==='' || !preg_match('/[\p{L}]/u',$text)){continue;}
   $items[]=['id'=>$id++,'text'=>$text,'context'=>$node->tagName.'@'.$attribute,'node'=>$node,'attribute'=>$attribute,'lead'=>'','trail'=>''];
  }
 }

 if(!$items){return new WP_Error('oldies_no_text','Çevrilecek sayfa metni bulunamadı.');}
 $translations=[];
 $chunks=oldies_ai_translation_chunks($items);
 foreach($chunks as $chunk){
  $result=oldies_ai_translate_chunk($chunk,$path);
  if(is_wp_error($result)){return $result;}
  $translations+=$result;
 }
 foreach($items as $item){
  if(!array_key_exists($item['id'],$translations)){return new WP_Error('oldies_missing_segment','Yapay zekâ yanıtında eksik metin bölümü bulundu.');}
  $value=(string)$translations[$item['id']];
  if($item['attribute']!==null){$item['node']->setAttribute($item['attribute'],$value);}
  else{$item['node']->nodeValue=$item['lead'].$value.$item['trail'];}
 }

 oldies_ai_finish_english_dom($dom,$xpath,$path);
 $output=$dom->saveHTML();
 $output=preg_replace('/^<\?xml[^>]+>\s*/','',$output);
 return $output;
}

function oldies_ai_node_excluded($node){
 for($current=$node;$current instanceof DOMElement;$current=$current->parentNode){
  $classes=' '.$current->getAttribute('class').' ';
  if($current->getAttribute('translate')==='no' || strpos($classes,' notranslate ')!==false || strpos($classes,' language-content-en ')!==false || strpos($classes,' language-content-tr ')!==false){return true;}
 }
 return false;
}

function oldies_ai_translation_chunks($items){
 $chunks=[];$chunk=[];$chars=0;
 foreach($items as $item){
  $length=function_exists('mb_strlen')?mb_strlen($item['text'],'UTF-8'):strlen($item['text']);
  if($chunk && (count($chunk)>=70 || $chars+$length>16000)){$chunks[]=$chunk;$chunk=[];$chars=0;}
  $chunk[]=$item;$chars+=$length;
 }
 if($chunk){$chunks[]=$chunk;}
 return $chunks;
}

function oldies_ai_translate_chunk($items,$path){
 $guard=oldies_ai_take_daily_request();
 if(is_wp_error($guard)){return $guard;}
 $segments=array_map(fn($item)=>['id'=>$item['id'],'context'=>$item['context'],'text'=>$item['text']],$items);
 $instructions='You are the senior English editor for Oldies Radyo, a selective music-history publication. Translate the supplied Turkish page segments into polished, natural American English while preserving the page\'s warm, knowledgeable, magazine-like voice and the meaning across neighboring segments. You may lightly reshape syntax for idiomatic English, but never add, remove, exaggerate, or alter facts. Preserve every date, number, chart position, quotation meaning, artist name, band name, album title, song title, venue, label, brand, URL-like text, and source name exactly unless an established English form is clearly required. Never translate the brand Oldies Radyo. Keep Rock ’n’ Roll, R&B, New Wave, Synth-pop and other music terminology idiomatic. Translate headings as strong editorial English, not literal machine English. Return one translation for every numeric id, in the same order. Do not include commentary.';
 $schema=[
  'type'=>'object',
  'properties'=>['translations'=>[
   'type'=>'array',
   'items'=>[
    'type'=>'object',
    'properties'=>['id'=>['type'=>'integer'],'text'=>['type'=>'string']],
    'required'=>['id','text'],
    'additionalProperties'=>false,
   ],
  ]],
  'required'=>['translations'],
  'additionalProperties'=>false,
 ];
 $payload=[
  'systemInstruction'=>['parts'=>[['text'=>$instructions]]],
  'contents'=>[[
   'role'=>'user',
   'parts'=>[['text'=>'Page path: '.$path."\nTranslate this JSON array. Return JSON matching the required schema:\n".wp_json_encode($segments,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]],
  ]],
  'generationConfig'=>[
   'responseMimeType'=>'application/json',
   'responseJsonSchema'=>$schema,
   'temperature'=>0.2,
   'maxOutputTokens'=>20000,
  ],
 ];
 $endpoint='https://generativelanguage.googleapis.com/v1beta/models/'.rawurlencode(oldies_ai_model()).':generateContent';
 $response=wp_remote_post($endpoint,[
  'timeout'=>180,
  'headers'=>['x-goog-api-key'=>oldies_ai_api_key(),'Content-Type'=>'application/json'],
  'body'=>wp_json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),
 ]);
 if(is_wp_error($response)){return new WP_Error('oldies_api_transport','Gemini bağlantısı kurulamadı: '.$response->get_error_message());}
 $status=(int)wp_remote_retrieve_response_code($response);
 $body=json_decode(wp_remote_retrieve_body($response),true);
 if($status<200 || $status>=300){
 $message=$body['error']['message']??('HTTP '.$status);
  if($status===429){
   $retry=(int)wp_remote_retrieve_header($response,'retry-after');
   return new WP_Error('oldies_api_limit','Ücretsiz Gemini kotası şu an dolu. Ücret oluşmadı; sistem kota yenilendiğinde devam edecek.',['retry_after'=>$retry>0?$retry:3600]);
  }
  return new WP_Error('oldies_api_error','Gemini API hatası: '.$message);
 }
 $text='';
 foreach(($body['candidates']??[]) as $candidate){
  foreach(($candidate['content']['parts']??[]) as $part){if(isset($part['text'])){$text.=(string)$part['text'];}}
 }
 $decoded=json_decode($text,true);
 if(!is_array($decoded) || !isset($decoded['translations']) || !is_array($decoded['translations'])){return new WP_Error('oldies_api_format','Yapay zekâ geçerli çeviri verisi döndürmedi.');}
 $map=[];
 foreach($decoded['translations'] as $translation){
  if(isset($translation['id'],$translation['text'])){$map[(int)$translation['id']]=(string)$translation['text'];}
 }
 foreach($items as $item){if(!array_key_exists($item['id'],$map)){return new WP_Error('oldies_api_incomplete','Yapay zekâ bir veya daha fazla bölümü eksik çevirdi.');}}
 return $map;
}

function oldies_ai_finish_english_dom($dom,$xpath,$path){
 $html=$dom->getElementsByTagName('html')->item(0);
 if($html instanceof DOMElement){$html->setAttribute('lang','en-US');$html->setAttribute('dir','ltr');}
 $body=$dom->getElementsByTagName('body')->item(0);
 if($body instanceof DOMElement && strpos(' '.$body->getAttribute('class').' ',' oldies-english-view ')===false){$body->setAttribute('class',trim($body->getAttribute('class').' oldies-english-view'));}

 $turkish=home_url($path);
 $english=oldies_ai_english_url_for($turkish);
 foreach($xpath->query('//a[@href]') as $anchor){
  if(!($anchor instanceof DOMElement)){continue;}
  $href=$anchor->getAttribute('href');
  if($anchor->getAttribute('data-oldies-language')==='tr'){$anchor->setAttribute('href',$turkish);continue;}
  if($anchor->getAttribute('data-oldies-language')==='en'){$anchor->setAttribute('href',$english);continue;}
  if(oldies_ai_is_internal_public_url($href)){$anchor->setAttribute('href',oldies_ai_english_url_for($href));}
 }
 foreach($xpath->query('//link[@rel="canonical"]') as $link){$link->setAttribute('href',$english);}
 foreach($xpath->query('//meta[@property="og:url"]') as $meta){$meta->setAttribute('content',$english);}
 foreach($xpath->query('//meta[@property="og:locale"]') as $meta){$meta->setAttribute('content','en_US');}
 $head=$dom->getElementsByTagName('head')->item(0);
 if($head instanceof DOMElement){
  foreach([['en',$english],['tr',$turkish],['x-default',$turkish]] as [$lang,$href]){
   $link=$dom->createElement('link');$link->setAttribute('rel','alternate');$link->setAttribute('hreflang',$lang);$link->setAttribute('href',$href);$head->appendChild($link);
  }
 }
}

function oldies_ai_is_internal_public_url($url){
 if($url==='' || strpos($url,'#')===0 || preg_match('#^(mailto:|tel:|javascript:)#i',$url)){return false;}
 $parts=wp_parse_url($url);
 if($parts===false){return false;}
 if(!empty($parts['host']) && strtolower($parts['host'])!==strtolower((string)wp_parse_url(home_url('/'),PHP_URL_HOST))){return false;}
 $path=$parts['path']??'/';
 return !preg_match('#/(wp-admin|wp-login\.php|wp-json)(/|$)#',$path);
}

function oldies_ai_settings_menu(){add_theme_page('Oldies Radyo English','Oldies Radyo English','manage_options','oldies-ai-english','oldies_ai_settings_page');}
add_action('admin_menu','oldies_ai_settings_menu');

function oldies_ai_save_settings(){
 if(!current_user_can('manage_options')){wp_die('Yetkiniz yok.');}
 check_admin_referer('oldies_ai_save_settings');
 $key=trim(sanitize_text_field(wp_unslash($_POST['api_key']??'')));
 if($key!==''){
  update_option('oldies_gemini_api_key',$key,false);
  delete_option('oldies_ai_paused_until');
  oldies_ai_enqueue_all('api_key_saved');
  oldies_ai_schedule_worker();
 }
 wp_safe_redirect(add_query_arg(['page'=>'oldies-ai-english','settings-updated'=>'true'],admin_url('themes.php')));
 exit;
}
add_action('admin_post_oldies_ai_save_settings','oldies_ai_save_settings');

function oldies_ai_manual_queue(){
 if(!current_user_can('manage_options')){wp_die('Yetkiniz yok.');}
 check_admin_referer('oldies_ai_manual_queue');
 delete_option('oldies_ai_paused_until');
 $queued=oldies_ai_enqueue_all('manual_scan');
 $result=oldies_ai_process_queue(1);
 wp_safe_redirect(add_query_arg(['page'=>'oldies-ai-english','queued'=>$queued,'processed'=>(int)($result['processed']??0)],admin_url('themes.php')));
 exit;
}
add_action('admin_post_oldies_ai_manual_queue','oldies_ai_manual_queue');

function oldies_ai_manual_run(){
 if(!current_user_can('manage_options')){wp_die('Yetkiniz yok.');}
 check_admin_referer('oldies_ai_manual_run');
 delete_option('oldies_ai_paused_until');
 $result=oldies_ai_process_queue(1);
 wp_safe_redirect(add_query_arg(['page'=>'oldies-ai-english','processed'=>(int)($result['processed']??0)],admin_url('themes.php')));
 exit;
}
add_action('admin_post_oldies_ai_manual_run','oldies_ai_manual_run');

function oldies_ai_ajax_run(){
 if(!current_user_can('manage_options')){wp_send_json_error(['message'=>'Yetkiniz yok.'],403);}
 check_ajax_referer('oldies_ai_batch','nonce');
 $result=oldies_ai_process_queue(1);
 $result['remaining']=count(oldies_ai_queue());
 $result['paused_until']=(int)get_option('oldies_ai_paused_until',0);
 wp_send_json_success($result);
}
add_action('wp_ajax_oldies_ai_run_batch','oldies_ai_ajax_run');

function oldies_ai_public_urls(){
 $urls=[home_url('/')];
 $posts=get_posts(['post_type'=>['page','post'],'post_status'=>'publish','numberposts'=>-1,'orderby'=>'ID','order'=>'ASC']);
 foreach($posts as $post){
  $url=get_permalink($post);
  $path=(string)wp_parse_url($url,PHP_URL_PATH);
  $home_path=rtrim((string)wp_parse_url(home_url('/'),PHP_URL_PATH),'/');
  if($home_path!=='' && strpos($path,$home_path)===0){$path=substr($path,strlen($home_path));}
  if(preg_match('#^/en(?:/|$)#',$path)){continue;}
  $urls[]=$url;
 }
 return array_values(array_unique(array_filter($urls)));
}

function oldies_ai_settings_page(){
 $has_key=oldies_ai_api_key()!=='';
 $urls=oldies_ai_public_urls();
 $index=get_option('oldies_ai_translation_index',[]);if(!is_array($index)){$index=[];}
 $queue=oldies_ai_queue();
 $usage=oldies_ai_daily_usage();
 $status=get_option('oldies_ai_worker_status',[]);if(!is_array($status)){$status=[];}
 $paused_until=(int)get_option('oldies_ai_paused_until',0);
 $batch_nonce=wp_create_nonce('oldies_ai_batch');
 ?>
 <div class="wrap oldies-ai-admin">
  <h1>Oldies Radyo · AI English</h1>
  <p>Türkçe sayfaları bağlamı ve Oldies Radyo anlatım tonunu koruyarak kalıcı İngilizce sayfalara dönüştürür. Çeviriler arka planda sırayla hazırlanır; Google Translate ve ücretli OpenAI API kullanılmaz.</p>
  <?php if(isset($_GET['settings-updated'])):?><div class="notice notice-success"><p>Ayarlar kaydedildi.</p></div><?php endif;?>
  <?php if(isset($_GET['queued'])):?><div class="notice notice-success"><p>Site tarandı; <?php echo (int)$_GET['queued']; ?> adres çeviri kuyruğuna eklendi veya güncellendi.</p></div><?php endif;?>
  <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="max-width:760px;background:#fff;padding:22px;border:1px solid #ccd0d4">
   <input type="hidden" name="action" value="oldies_ai_save_settings"><?php wp_nonce_field('oldies_ai_save_settings'); ?>
   <table class="form-table"><tbody>
    <tr><th><label for="oldies-api-key">Ücretsiz Gemini API anahtarı</label></th><td><input id="oldies-api-key" class="regular-text" type="password" name="api_key" value="" autocomplete="new-password" placeholder="<?php echo $has_key?'Kayıtlı anahtarı değiştirmek için yenisini yazın':'Google AI Studio anahtarı'; ?>"><p class="description">Google AI Studio’da ücretsiz katmandaki, faturalandırması açılmamış bir projeden anahtar oluşturun. Anahtar yalnız sunucuda kullanılır; ziyaretçinin tarayıcısına gönderilmez. wp-config.php içinde OLDIES_GEMINI_API_KEY sabiti tanımlıysa bu alan kullanılmaz.</p></td></tr>
    <tr><th>Çeviri modeli</th><td><strong>Gemini 3.5 Flash-Lite · Free Tier</strong><p class="description">Model sabitlenmiştir; başka modele otomatik geçiş yapılmaz. Faturalandırması açılmamış Free Tier projesi kullanılmalıdır.</p></td></tr>
    <tr><th>Günlük güvenlik sınırı</th><td><strong><?php echo OLDIES_AI_DAILY_REQUEST_LIMIT; ?> yapay zekâ isteği</strong><p class="description">Bugün <?php echo (int)$usage['requests']; ?> istek kullanıldı. Bu yerel sınır aşılırsa sistem ertesi gün devam eder.</p></td></tr>
   </tbody></table>
   <?php submit_button('Ayarları kaydet'); ?>
  </form>
  <hr>
  <h2>Otomatik çeviri durumu</h2>
  <p>Yayınlanmış adres: <strong><?php echo count($urls); ?></strong> · Hazır İngilizce sayfa: <strong><?php echo count($index); ?></strong> · Kuyrukta: <strong><?php echo count($queue); ?></strong></p>
  <p>WordPress arka planda yaklaşık beş dakikada bir sayfa işler. Türkçe bir yazı yayımlandığında veya güncellendiğinde kendiliğinden kuyruğa eklenir.</p>
  <?php if($paused_until>time()):?><div class="notice notice-warning inline"><p>Ücretsiz kota veya güvenlik sınırı nedeniyle bekleniyor. Sistem <?php echo esc_html(wp_date('j F Y H:i',$paused_until)); ?> sonrasında otomatik devam edecek.</p></div><?php endif;?>
  <?php if(!empty($status['time'])):?><p class="description">Son çalışma: <?php echo esc_html($status['time']); ?> · <?php echo esc_html($status['message']??''); ?> · Kalan: <?php echo (int)($status['remaining']??count($queue)); ?></p><?php endif;?>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">
   <button type="button" id="oldies-ai-build-all" class="button button-primary" <?php disabled(!$has_key || !$queue || $paused_until>time()); ?>>Otomatik toplu çeviriyi başlat</button>
   <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="oldies_ai_manual_run"><?php wp_nonce_field('oldies_ai_manual_run'); ?><button type="submit" class="button button-primary" <?php disabled(!$has_key || !$queue); ?>>Kuyruktaki sıradaki sayfayı şimdi hazırla</button></form>
   <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="oldies_ai_manual_queue"><?php wp_nonce_field('oldies_ai_manual_queue'); ?><button type="submit" class="button" <?php disabled(!$has_key); ?>>Bütün siteyi yeniden tara</button></form>
  </div>
  <div id="oldies-ai-progress" style="max-width:760px;margin-top:16px" aria-live="polite"></div>
  <?php if(!$has_key):?><p style="color:#b32d2e"><strong>Önce ücretsiz Gemini API anahtarını kaydedin.</strong></p><?php endif;?>
 </div>
 <script>
 (()=>{
  const button=document.getElementById('oldies-ai-build-all');
  const progress=document.getElementById('oldies-ai-progress');
  if(!button||!progress)return;
  let running=false;
  const endpoint=<?php echo wp_json_encode(admin_url('admin-ajax.php')); ?>;
  const nonce=<?php echo wp_json_encode($batch_nonce); ?>;
  button.addEventListener('click',async()=>{
   if(running)return;running=true;button.disabled=true;
   let completed=0;
   while(running){
    progress.textContent=`${completed} sayfa işlendi; sıradaki sayfa hazırlanıyor…`;
    const body=new URLSearchParams({action:'oldies_ai_run_batch',nonce});
    try{
     const response=await fetch(endpoint,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:body.toString(),cache:'no-store'});
     const payload=await response.json();
     if(!payload.success)throw new Error(payload.data?.message||'İşlem tamamlanamadı');
     const data=payload.data||{};
     if(data.message==='translated'||data.message==='already_current')completed+=1;
     if(Number(data.paused_until||0)>Math.floor(Date.now()/1000)){
      progress.innerHTML=`<strong>${completed} sayfa işlendi.</strong><p>Ücretsiz kota veya günlük güvenlik sınırı nedeniyle beklemeye geçti. Sistem daha sonra otomatik devam edecek.</p>`;break;
     }
     if(Number(data.remaining||0)===0){progress.innerHTML=`<strong>Tamamlandı.</strong><p>Kuyruktaki bütün İngilizce sayfalar hazırlandı.</p>`;break;}
     if(Number(data.processed||0)===0){progress.innerHTML=`<strong>${completed} sayfa işlendi.</strong><p>Kuyruktaki bazı sayfalar yeniden deneme saatini bekliyor. Sistem arka planda devam edecek.</p>`;break;}
     await new Promise(resolve=>setTimeout(resolve,1200));
    }catch(error){progress.textContent='İşlem durdu: '+error.message;break;}
   }
   running=false;button.disabled=false;
  });
 })();
 </script>
 <?php
}

function oldies_ai_output_sitemap(){
 if(!get_query_var('oldies_en_sitemap')){return;}
 status_header(200);nocache_headers();header('Content-Type: application/xml; charset=UTF-8');
 echo '<?xml version="1.0" encoding="UTF-8"?>';
 echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';
 $posts=get_posts(['post_type'=>['page','post'],'post_status'=>'publish','numberposts'=>-1,'orderby'=>'ID','order'=>'ASC','lang'=>'en','suppress_filters'=>false]);
 foreach($posts as $post){
  $language=function_exists('pll_get_post_language')?pll_get_post_language($post->ID,'slug'):'en';
  if($language!=='en'){continue;}
  echo '<url><loc>'.esc_url(get_permalink($post)).'</loc>';
  $modified=get_post_modified_time('c',true,$post);
  if($modified){echo '<lastmod>'.esc_html($modified).'</lastmod>';}
  echo '</url>';
 }
 echo '</urlset>';exit;
}
add_action('template_redirect','oldies_ai_output_sitemap',0);
add_filter('robots_txt',function($output,$public){
 if($public){$output.="\nSitemap: ".home_url('/oldies-english-sitemap.xml')."\n";}
 return $output;
},30,2);

function oldies_ai_activation(){
 flush_rewrite_rules(false);
 oldies_ai_enqueue_all('theme_activation');
 oldies_ai_schedule_worker();
}
add_action('after_switch_theme','oldies_ai_activation',99);

function oldies_ai_deactivation(){
 $timestamp=wp_next_scheduled('oldies_ai_translation_worker');
 if($timestamp){wp_unschedule_event($timestamp,'oldies_ai_translation_worker');}
}
add_action('switch_theme','oldies_ai_deactivation');
