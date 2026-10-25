<?php
/* Template Name: Oldies News Hub */
get_header();
$news_en=function_exists('oldies_is_english') && oldies_is_english();
$all_news=[];
if(!$news_en){$all_news=oldies_latest_news_items();}
else{
 $news_query=new WP_Query(['post_type'=>'post','posts_per_page'=>100,'post_status'=>'publish','ignore_sticky_posts'=>true,'orderby'=>'date','order'=>'DESC','category__in'=>[786935904],'lang'=>'en']);
 foreach($news_query->posts as $news_post){
  $news_thumb=get_post_thumbnail_id($news_post);
  $all_news[]=['date'=>get_the_date('F j, Y',$news_post),'category'=>'Music News','title'=>get_the_title($news_post),'excerpt'=>wp_trim_words(get_the_excerpt($news_post),28,'…'),'url'=>get_permalink($news_post),'image'=>get_the_post_thumbnail_url($news_post,'full')?:oldies_media_url('oldies-radyo-share.webp'),'alt'=>get_post_meta($news_thumb,'_wp_attachment_image_alt',true)?:get_the_title($news_post),'image_mode'=>'cover','key'=>$news_post->post_name];
 }
 wp_reset_postdata();
}
$monthly_news=[];$daily_news=[];
foreach($all_news as $news_item){
 if(preg_match('/(?:aylik-haber|monthly-news|agustos-2026-oldies-music-haberleri)/i',(string)($news_item['key']??''))){$monthly_news[]=$news_item;}
 else{$daily_news[]=$news_item;}
}
?>
<main class="news-archive-page"><section class="page-hero"><div class="wrap"><div class="kicker">OLDIES RADYO</div><h1><?php echo $news_en?'Music News':'Yeni Haberler'; ?></h1><p class="intro"><?php echo $news_en?'Monthly roundups and individual music stories, in separate sections.':'Ayın önemli gelişmelerini bir araya getiren aylık dosyalar ve ay içinde yayımlanan tekil müzik haberleri.'; ?></p><nav aria-label="<?php echo $news_en?'News sections':'Haber bölümleri'; ?>"><a class="btn" href="#monthly-news"><?php echo $news_en?'Monthly News':'Aylık Haberler'; ?></a> <a class="btn" href="#daily-news"><?php echo $news_en?'Individual News':'Ay İçi Haberler'; ?></a></nav></div></section>
<?php foreach([['monthly-news',$news_en?'Monthly News':'Aylık Haberler',$news_en?'The month in review: music legends, releases and major developments.':'Ağustos, Eylül ve sonraki ayların toplu müzik haber dosyaları.',$monthly_news],['daily-news',$news_en?'Individual News':'Ay İçi Haberler',$news_en?'Individual stories, from newest to oldest.':'Güncel gelişmeler ve tekil haberler, en yeniden eskiye.',$daily_news]] as $news_section): ?>
<section id="<?php echo esc_attr($news_section[0]); ?>" style="scroll-margin-top:100px"><div class="wrap article wide-article"><div class="section-head"><div><div class="kicker"><?php echo $news_en?'OLDIES RADYO NEWS':'OLDIES RADYO HABER'; ?></div><h2><?php echo esc_html($news_section[1]); ?></h2><p><?php echo esc_html($news_section[2]); ?></p></div></div><div class="news-card-grid">
<?php if($news_section[3]): foreach($news_section[3] as $item): ?><article class="news-card"><a href="<?php echo esc_url($item['url']); ?>"><img loading="lazy" style="object-fit:<?php echo esc_attr($item['image_mode']??'contain'); ?>;background:#080908" src="<?php echo esc_url($item['image']); ?>" alt="<?php echo esc_attr($item['alt']); ?>"><div><span><?php echo esc_html($item['date'].' • '.$news_section[1]); ?></span><h3><?php echo esc_html($item['title']); ?></h3><p><?php echo esc_html($item['excerpt']); ?></p><b><?php echo $news_en?'Read the story →':'Haberi oku →'; ?></b></div></a></article><?php endforeach; else: ?><p><?php echo $news_en?'No published stories in this section yet.':'Bu bölümde henüz yayımlanmış haber bulunmuyor.'; ?></p><?php endif; ?>
</div></div></section><?php endforeach; ?>
</main><?php get_footer(); ?>
