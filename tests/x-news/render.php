<?php
require __DIR__ . '/bootstrap.php';
[$row,$x]=setup();
$scenario=$argv[1]??'ready';
$m=json_decode($row['metadata'],true);$m['x_news']=$x;$GLOBALS['wpdb']->data[1]['metadata']=json_encode($m);
$_GET=['id'=>1];
if($scenario==='candidate'){$GLOBALS['posts'][10]->post_status='draft';$m['x_news']['status']='NEWS CANDIDATE';$GLOBALS['wpdb']->data[1]['metadata']=json_encode($m);}
if($scenario==='list'){$_GET=[];}
ob_start();Oldies_X_News_Controller::render();$html=ob_get_clean();
echo json_encode(['html'=>$html,'network_calls'=>$GLOBALS['network_calls']]);
