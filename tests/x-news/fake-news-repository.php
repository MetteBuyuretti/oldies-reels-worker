<?php
namespace OldiesRadyo\SocialAutomation\News;
final class NewsRepository
{
    public function getAllSources() { return $GLOBALS['sources'] ?? []; }
    public function createSource($s) { $id=count($GLOBALS['sources']??[])+1;$s['id']=$id;$GLOBALS['sources'][]=$s;return $id; }
    public function getArticleByArticleUrl($url) { foreach($GLOBALS['wpdb']->data as $r){if(($r['article_url']??'')===$url){return $r;}}return null; }
    public function updateArticle($id,$data) { $GLOBALS['wpdb']->data[$id]=array_merge($GLOBALS['wpdb']->data[$id],$data);return true; }
    public function createArticle($data) { $id=max(array_keys($GLOBALS['wpdb']->data))+1;$data+=['id'=>$id,'updated_at'=>gmdate('Y-m-d H:i:s')];$data['metadata']=json_encode($data['metadata']);$GLOBALS['wpdb']->data[$id]=$data;return $id; }
}
