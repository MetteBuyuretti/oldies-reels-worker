<?php
require __DIR__ . '/bootstrap.php';
require __DIR__ . '/fake-news-repository.php';
[$row,$x]=setup();
$scenario=$argv[1]??'intent';
$_POST=['id'=>1,'intent'=>'intent','confirmed'=>'1'];
switch($scenario){
    case 'intent': break;
    case 'sources':
        $_POST=['id'=>0,'intent'=>'sources'];
        $GLOBALS['sources']=[['name'=>'Keep custom name','feed_url'=>'https://ultimateclassicrock.com/feed/','is_active'=>0]];
        break;
    case 'import_existing':case 'import_new':case 'import_old':case 'import_page':case 'import_draft':case 'import_tr':case 'import_project_category':case 'import_same_source_other_post':
        $_POST=['id'=>0,'intent'=>'import','post_id'=>$scenario==='import_existing'?10:20,'artist'=>'Elton John','primary'=>'https://www.bbc.com/news/other'];
        $GLOBALS['posts'][20]=(object)['ID'=>20,'post_status'=>'publish','post_type'=>'post','post_excerpt'=>'Fresh announcement','post_title'=>'Fresh Elton announcement','post_date_gmt'=>gmdate('Y-m-d H:i:s')];
        $GLOBALS['posts'][10]->post_date_gmt=gmdate('Y-m-d H:i:s');
        $GLOBALS['urls'][20]='https://oldiesradyo.com/en/new-announcement/';$GLOBALS['languages'][20]='en';
        $GLOBALS['terms'][20]=[(object)['slug'=>'news-en']];$GLOBALS['terms'][10]=$GLOBALS['terms'][20];
        if($scenario==='import_old'){$GLOBALS['posts'][20]->post_date_gmt='2016-01-01 00:00:00';}
        if($scenario==='import_page'){$GLOBALS['posts'][20]->post_type='page';}
        if($scenario==='import_draft'){$GLOBALS['posts'][20]->post_status='draft';}
        if($scenario==='import_tr'){$GLOBALS['languages'][20]='tr';}
        if($scenario==='import_project_category'){$GLOBALS['terms'][20]=[(object)['slug'=>'projects']];}
        if($scenario==='import_same_source_other_post'){$_POST['primary']='https://www.bbc.com/news/example';}
        break;
    case 'posted':$x['status']='POSTED';break;
    case 'unapproved':$x['approved_by']=null;break;
    case 'changed_news':$GLOBALS['posts'][10]->post_modified_gmt='2026-10-08 00:00:00';break;
    case 'unpublished':$GLOBALS['posts'][10]->post_status='draft';break;
    case 'sensitive':$row['headline']='Elton John hospitalized';$GLOBALS['wpdb']->data[1]=$row;break;
    case 'no_confirm':$_POST['intent']='approve';unset($_POST['confirmed']);break;
    case 'unauthorized':$GLOBALS['can_manage']=false;break;
    case 'bad_nonce':$GLOBALS['nonce_valid']=false;break;
    case 'duplicate':$other=$x;$other['status']='POSTED';$GLOBALS['wpdb']->data[2]=['id'=>2,'metadata'=>json_encode(['x_news'=>$other])];break;
    case 'api_disabled':$_POST['intent']='api';break;
    case 'api_budget_missing':$_POST['intent']='api';putenv('OLDIES_X_API_ENABLED=true');break;
    case 'api_identity_missing':$_POST['intent']='api';putenv('OLDIES_X_API_ENABLED=true');putenv('OLDIES_X_MAX_REQUEST_USD=0.20');putenv('OLDIES_X_MONTHLY_BUDGET_USD=1');break;
    case 'confirm':$x['status']='AWAITING_CONFIRMATION';$_POST['intent']='confirm';$_POST['post_url']='https://x.com/OldiesTest/status/123456789';break;
    case 'confirm_fake_url':$x['status']='AWAITING_CONFIRMATION';$_POST['intent']='confirm';$_POST['post_url']='https://evil.test/status/123';break;
    case 'confirm_unreserved':$_POST['intent']='confirm';$_POST['post_url']='https://x.com/OldiesTest/status/123';break;
    case 'cancel':$x['status']='AWAITING_CONFIRMATION';$_POST['intent']='cancel_intent';break;
    case 'cancel_uncertain':$x['status']='OUTCOME_UNKNOWN';$_POST['intent']='cancel_intent';break;
    case 'retry_uncertain':$x['status']='OUTCOME_UNKNOWN';$_POST['intent']='retry';break;
    case 'retry_failed':$x['status']='FAILED';$x['retryable']=true;$x['retry_after']=time()-1;$_POST['intent']='retry';break;
    case 'retry_early':$x['status']='FAILED';$x['retryable']=true;$x['retry_after']=time()+300;$_POST['intent']='retry';break;
    case 'approve':$x['status']='VERIFIED';$x['approved_by']=null;$_POST['intent']='approve';break;
    case 'reject':$_POST['intent']='reject';break;
    case 'save':$_POST+=['artist'=>'Elton John','category'=>'archive','story_key'=>'artist-album-event','text'=>$x['text'],'primary'=>'https://bbc.com/news/example','second'=>'','evidence_note'=>'Source reviewed','evidence_reviewed'=>'1','english_reviewed'=>'1'];$_POST['intent']='save';break;
    case 'missing_english_review':$x['english_reviewed_by']=null;$_POST['intent']='approve';break;
    case 'api_success':case 'api_timeout':case 'api_429':
        $_POST['intent']='api';putenv('OLDIES_X_API_ENABLED=true');putenv('OLDIES_X_MAX_REQUEST_USD=0.20');putenv('OLDIES_X_MONTHLY_BUDGET_USD=1');
        putenv('OLDIES_X_USER_ACCESS_TOKEN=unit-test-only');putenv('OLDIES_X_OAUTH2_SCOPES=tweet.read tweet.write users.read');putenv('OLDIES_X_EXPECTED_USERNAME=OldiesTest');
        $GLOBALS['options']['oldies_x_verified_identity']=['id'=>'42','username'=>'OldiesTest','credential_hash'=>Oldies_X_News_Publisher::credentialHash(),'checked_at'=>gmdate('c')];
        $GLOBALS['network_response']=$scenario==='api_success'?['response'=>['code'=>201],'body'=>'{"data":{"id":"123456789"}}']:($scenario==='api_429'?['response'=>['code'=>429],'body'=>'','headers'=>['x-rate-limit-reset'=>time()+300]]:new WP_Error('timeout'));
        break;
}
$meta=json_decode($row['metadata'],true);$meta['x_news']=$x;$GLOBALS['wpdb']->data[1]['metadata']=json_encode($meta);
$_POST['revision']=Oldies_X_News_Controller::revision($GLOBALS['wpdb']->data[1]);
if($scenario==='stale_editor'){$GLOBALS['wpdb']->data[1]['summary_raw']='Changed after opening editor';}
if($scenario==='confirm_duplicate_id'){
    $_POST['intent']='confirm';$_POST['post_url']='https://x.com/OldiesTest/status/123456789';
    $x['status']='AWAITING_CONFIRMATION';$meta['x_news']=$x;$GLOBALS['wpdb']->data[1]['metadata']=json_encode($meta);
    $_POST['revision']=Oldies_X_News_Controller::revision($GLOBALS['wpdb']->data[1]);
    $GLOBALS['wpdb']->data[2]=['id'=>2,'metadata'=>json_encode(['x_news'=>['status'=>'POSTED','post_id'=>'123456789']])];
}
try{Oldies_X_News_Controller::handle();}catch(Throwable $e){echo json_encode(['error'=>$e->getMessage(),'calls'=>$GLOBALS['network_calls'],'rows'=>$GLOBALS['wpdb']->data]);}
